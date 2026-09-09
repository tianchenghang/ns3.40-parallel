#!/usr/bin/env node
// @ts-check
/**
 * Recursively converts CRLF line endings to LF for every text file under the
 * directory that contains this script. Conversion runs across WORKER_COUNT
 * concurrent worker threads.
 *
 * Usage:
 *   node clrf-to-lf.js           # default dry-run, reports only
 *   node clrf-to-lf.js --apply   # writes the changes to disk
 */

import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';

const WORKER_COUNT = 3;
const CR = 0x0d;
const LF = 0x0a;
const NUL = 0x00;
const BINARY_PROBE_BYTES = 8192;

/** Directory names excluded from the scan: VCS, dependencies, build output, caches. */
const SKIP_DIRS = new Set([
  '.git',
  'node_modules',
  '.venv',
  'venv',
  'build',
  'dist',
  'out',
  'target',
  '__pycache__',
  '.mypy_cache',
  '.ruff_cache',
  '.pytest_cache',
  '.cache',
  '.codegraph',
]);

/**
 * @typedef {object} WorkerPayload
 * @property {string[]} files Absolute paths of the candidate files.
 * @property {Int32Array} cursor Shared task cursor backed by a SharedArrayBuffer.
 * @property {boolean} apply When true the worker writes files, otherwise it only counts.
 * @property {string} root Scan root, used to render paths relative in reports.
 */

/**
 * @typedef {object} FileChange
 * @property {number} crlf Number of CRLF pairs found in the file.
 * @property {boolean} written Whether the result was written to disk.
 */

/**
 * @typedef {object} FileReport
 * @property {string} file Path relative to the scan root.
 * @property {number} crlf
 * @property {boolean} written
 */

/**
 * @typedef {object} FileFailure
 * @property {string} file
 * @property {string} message
 */

/**
 * @typedef {object} WorkerResult
 * @property {FileReport[]} reports
 * @property {FileFailure[]} failures
 */

/**
 * Collects candidate files recursively, skipping SKIP_DIRS and symlinks.
 * @param {string} root
 * @returns {Promise<string[]>} Absolute paths.
 */
async function scanFiles(root) {
  /** @type {string[]} */
  const files = [];
  /** @type {string[]} */
  const pending = [root];

  while (pending.length > 0) {
    const dir = pending.pop();
    if (dir === undefined) break;

    /** @type {import('node:fs').Dirent[]} */
    let entries;
    try {
      entries = await readdir(dir, { withFileTypes: true });
    } catch {
      continue;
    }

    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name)) pending.push(full);
      } else if (entry.isFile()) {
        files.push(full);
      }
    }
  }

  return files;
}

/**
 * A NUL byte within the first BINARY_PROBE_BYTES marks the file as binary;
 * rewriting such content would corrupt it, so it is left untouched.
 * @param {Buffer} buf
 * @returns {boolean}
 */
function looksBinary(buf) {
  return buf.subarray(0, BINARY_PROBE_BYTES).includes(NUL);
}

/**
 * Returns the offset of the CR in every CRLF pair. Lone CR bytes are ignored.
 * @param {Buffer} buf
 * @returns {number[]}
 */
function findCrOffsets(buf) {
  /** @type {number[]} */
  const offsets = [];
  let pos = 0;

  while (pos < buf.length) {
    const lf = buf.indexOf(LF, pos);
    if (lf === -1) break;
    if (lf > 0 && buf[lf - 1] === CR) offsets.push(lf - 1);
    pos = lf + 1;
  }

  return offsets;
}

/**
 * Drops the CR at each listed offset while keeping the LF that follows it.
 * @param {Buffer} buf
 * @param {number[]} crOffsets
 * @returns {Buffer}
 */
function stripCr(buf, crOffsets) {
  /** @type {Buffer[]} */
  const parts = [];
  let prev = 0;

  for (const cr of crOffsets) {
    parts.push(buf.subarray(prev, cr));
    prev = cr + 1;
  }
  parts.push(buf.subarray(prev));

  return Buffer.concat(parts);
}

/**
 * Processes one file. Returns null when nothing needs converting, i.e. the file
 * is already LF-only or binary.
 * @param {string} file Absolute path.
 * @param {boolean} apply
 * @returns {Promise<FileChange | null>}
 */
async function convertFile(file, apply) {
  const buf = await readFile(file);
  if (looksBinary(buf)) return null;

  const crOffsets = findCrOffsets(buf);
  if (crOffsets.length === 0) return null;

  if (!apply) return { crlf: crOffsets.length, written: false };

  await writeFile(file, stripCr(buf, crOffsets));
  return { crlf: crOffsets.length, written: true };
}

/** Worker entry point: claims tasks through the atomic cursor until the queue drains. */
function runWorker() {
  const port = parentPort;
  if (port === null) throw new Error('worker is missing parentPort');

  const { files, cursor, apply, root } = /** @type {WorkerPayload} */ (workerData);
  /** @type {FileReport[]} */
  const reports = [];
  /** @type {FileFailure[]} */
  const failures = [];

  const drain = async () => {
    for (;;) {
      const index = Atomics.add(cursor, 0, 1);
      if (index >= files.length) return;

      const file = /** @type {string} */ (files[index]);
      const relative = path.relative(root, file);
      try {
        const change = await convertFile(file, apply);
        if (change !== null) reports.push({ file: relative, ...change });
      } catch (err) {
        failures.push({ file: relative, message: err instanceof Error ? err.message : String(err) });
      }
    }
  };

  drain().then(() => {
    /** @type {WorkerResult} */
    const result = { reports, failures };
    port.postMessage(result);
  });
}

/**
 * Spawns one worker and resolves with its reported result.
 * @param {WorkerPayload} payload
 * @returns {Promise<WorkerResult>}
 */
function runInWorker(payload) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(fileURLToPath(import.meta.url), { workerData: payload });
    worker.once('message', (message) => resolve(/** @type {WorkerResult} */ (message)));
    worker.once('error', reject);
    worker.once('exit', (code) => {
      if (code !== 0) reject(new Error(`worker exited unexpectedly (code ${code})`));
    });
  });
}

/**
 * @param {string[]} argv
 * @returns {{ apply: boolean }}
 */
function parseArgs(argv) {
  let apply = false;

  for (const arg of argv) {
    switch (arg) {
      case '--apply':
        apply = true;
        break;
      case '-h':
      case '--help':
        console.log('Usage: node clrf-to-lf.js [--apply]\n  Dry-run by default, reports only. Pass --apply to write.');
        process.exit(0);
        break;
      default:
        throw new Error(`unknown argument: ${arg}`);
    }
  }

  return { apply };
}

async function main() {
  const { apply } = parseArgs(process.argv.slice(2));
  const root = path.dirname(fileURLToPath(import.meta.url));

  const files = await scanFiles(root);
  console.log(`Scanned ${files.length} files; converting across ${WORKER_COUNT} threads (${apply ? 'apply' : 'dry-run'})...`);

  /** @type {WorkerPayload} */
  const payload = {
    files,
    cursor: new Int32Array(new SharedArrayBuffer(4)),
    apply,
    root,
  };

  const results = await Promise.all(
    Array.from({ length: WORKER_COUNT }, () => runInWorker(payload)),
  );

  /** @type {FileReport[]} */
  const reports = [];
  /** @type {FileFailure[]} */
  const failures = [];
  for (const result of results) {
    reports.push(...result.reports);
    failures.push(...result.failures);
  }

  reports.sort((a, b) => a.file.localeCompare(b.file));
  for (const report of reports) {
    const tag = report.written ? 'converted' : '[dry-run]';
    console.log(`${tag} ${report.file} (${report.crlf} CRLF)`);
  }

  const total = reports.reduce((sum, report) => sum + report.crlf, 0);
  const tail = apply ? 'written to disk' : 'no files modified; pass --apply to write';
  const fileLabel = reports.length === 1 ? 'file' : 'files';
  console.log(`\n${reports.length} ${fileLabel} / ${total} CRLF in total (${tail})`);

  if (failures.length > 0) {
    for (const failure of failures) console.error(`failed ${failure.file}: ${failure.message}`);
    process.exitCode = 1;
  }
}

if (isMainThread) {
  main().catch((err) => {
    console.error(err instanceof Error ? err.message : String(err));
    process.exitCode = 1;
  });
} else {
  runWorker();
}
