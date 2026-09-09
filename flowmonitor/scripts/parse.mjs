// @ts-check

import { readFileSync, writeFileSync, readdirSync, mkdirSync } from "fs";
import { join, basename } from "path";

const LOGS_DIR = join(import.meta.dirname, "../../logs");
const OUT_DIR = join(import.meta.dirname, "../public/data");

const ALGOS = ["TcpSwift", "TcpBbr", "TcpCubic", "TcpNewReno"];

/**
 *
 * @param {string} str
 * @returns {number}
 */
function parseNs3Time(str) {
  if (!str) return 0;
  const s = str.replace(/^\+/, "");
  if (s.endsWith("ns")) return parseFloat(s);
  return parseFloat(s);
}

/**
 * @typedef {{
 *   start: number;
 *   width: number;
 *   count: number;
 * }} DelayHist
 *
 * @typedef {{
 *   flowId: number;
 *   txBytes: number;
 *   rxBytes: number;
 *   txPackets: number;
 *   rxPackets: number;
 *   lostPackets: number;
 *   durationS: number;
 *   throughputMbps: number;
 *   avgDelayUs: number;
 *   avgJitterUs: number;
 *   lossRate: number;
 *   lastDelayUs: number;
 *   delayHist: DelayHist[];
 * }} Flow
 *
 * @param {string} xml
 * @returns {Flow[]}
 */
function parseFlowXml(xml) {
  const flows = [];
  const flowRegex = /<Flow flowId="(\d+)"([^>]+)>([\s\S]*?)<\/Flow>/g;
  let m;
  while ((m = flowRegex.exec(xml)) !== null) {
    const flowId = parseInt(m[1]);
    const attrs = m[2];
    const inner = m[3];

    /**
     *
     * @param {string} name
     * @returns {string}
     */
    const get = (name) => {
      const r = new RegExp(`${name}="([^"]*)"`).exec(attrs);
      return r ? r[1] : "0";
    };

    const txBytes = parseInt(get("txBytes")) || 0;
    const rxBytes = parseInt(get("rxBytes")) || 0;
    const txPackets = parseInt(get("txPackets")) || 0;
    const rxPackets = parseInt(get("rxPackets")) || 0;
    const lostPackets = parseInt(get("lostPackets")) || 0;
    const delaySum = parseNs3Time(get("delaySum"));
    const jitterSum = parseNs3Time(get("jitterSum"));
    const lastDelay = parseNs3Time(get("lastDelay"));
    const timeFirstTx = parseNs3Time(get("timeFirstTxPacket"));
    const timeLastRx = parseNs3Time(get("timeLastRxPacket"));

    const durationNs = timeLastRx - timeFirstTx;
    const durationS = durationNs / 1e9;
    const throughputMbps = durationS > 0 ? (rxBytes * 8) / durationS / 1e6 : 0;
    const avgDelayUs = rxPackets > 0 ? delaySum / rxPackets / 1000 : 0;
    const avgJitterUs = rxPackets > 1 ? jitterSum / (rxPackets - 1) / 1000 : 0;
    const lossRate = txPackets > 0 ? lostPackets / txPackets : 0;

    const delayHist = [];
    const dhRegex =
      /<bin index="(\d+)" start="([^"]*)" width="([^"]*)" count="(\d+)"/g;
    const dhSection = /<delayHistogram[^>]*>([\s\S]*?)<\/delayHistogram>/.exec(
      inner,
    );
    if (dhSection) {
      let bm;
      while ((bm = dhRegex.exec(dhSection[1])) !== null) {
        delayHist.push({
          start: parseFloat(bm[2]),
          width: parseFloat(bm[3]),
          count: parseInt(bm[4]),
        });
      }
    }

    flows.push({
      flowId,
      txBytes,
      rxBytes,
      txPackets,
      rxPackets,
      lostPackets,
      durationS,
      throughputMbps,
      avgDelayUs,
      avgJitterUs,
      lossRate,
      lastDelayUs: lastDelay / 1000,
      delayHist,
    });
  }
  return flows;
}

/**
 * @typedef {{
 *   src: string;
 *   dst: string;
 *   protocol: "TCP" | "UDP";
 *   srcPort: number;
 *   dstPort: number;
 * }} FlowClassifier
 *
 * @param {string} xml
 * @returns {Record<number, FlowClassifier>}
 */
function parseClassifier(xml) {
  const /** @type {Record<number, FlowClassifier>} */ map = {};
  const section = /<Ipv4FlowClassifier>([\s\S]*?)<\/Ipv4FlowClassifier>/.exec(
    xml,
  );
  if (!section) return map;
  const flowRegex =
    /<Flow flowId="(\d+)" sourceAddress="([^"]*)" destinationAddress="([^"]*)" protocol="(\d+)" sourcePort="(\d+)" destinationPort="(\d+)"/g;
  let m;
  while ((m = flowRegex.exec(section[1])) !== null) {
    map[parseInt(m[1])] = {
      src: m[2],
      dst: m[3],
      protocol: parseInt(m[4]) === 6 ? "TCP" : "UDP",
      srcPort: parseInt(m[5]),
      dstPort: parseInt(m[6]),
    };
  }
  return map;
}

/**
 *
 * @param {Flow} flow
 * @param {Record<number, FlowClassifier>} classifier
 * @returns {string}
 */
function classifyFlow(flow, classifier) {
  const info = classifier[flow.flowId];
  if (!info) return "unknown";
  if (info.protocol === "UDP") return "udp-cross";
  if (info.dstPort === 5000) return "tcp-data";
  return "tcp-ack";
}

/**
 * @typedef {{
 *   throughputMbps: number;
 *   avgDelayUs: number;
 *   avgJitterUs: number;
 *   lossRate: number;
 *   totalRxGB: number;
 *   tcpFlowCount: number;
 *   durationS: number;
 * }} Summary
 *
 * @param {string} filePath
 * @returns {{
 *   flows: Flow[];
 *   summary: Summary;
 * }}
 */
function processFile(filePath) {
  const xml = readFileSync(filePath, "utf-8");
  const flows = parseFlowXml(xml);
  const classifier = parseClassifier(xml);

  const classified = flows.map((f) => ({
    ...f,
    ...classifier[f.flowId],
    type: classifyFlow(f, classifier),
  }));

  const tcpData = classified.filter((f) => f.type === "tcp-data");
  const totalRxBytes = tcpData.reduce((s, f) => s + f.rxBytes, 0);
  const totalTxPackets = tcpData.reduce((s, f) => s + f.txPackets, 0);
  const totalRxPackets = tcpData.reduce((s, f) => s + f.rxPackets, 0);
  const totalLost = tcpData.reduce((s, f) => s + f.lostPackets, 0);
  const maxDuration = Math.max(...tcpData.map((f) => f.durationS), 0);

  const aggThroughput =
    maxDuration > 0 ? (totalRxBytes * 8) / maxDuration / 1e6 : 0;
  const aggDelay =
    totalRxPackets > 0
      ? tcpData.reduce((s, f) => s + f.avgDelayUs * f.rxPackets, 0) /
        totalRxPackets
      : 0;
  const aggJitter =
    totalRxPackets > 0
      ? tcpData.reduce((s, f) => s + f.avgJitterUs * f.rxPackets, 0) /
        totalRxPackets
      : 0;
  const aggLoss = totalTxPackets > 0 ? totalLost / totalTxPackets : 0;

  return {
    flows: classified,
    summary: {
      throughputMbps: aggThroughput,
      avgDelayUs: aggDelay,
      avgJitterUs: aggJitter,
      lossRate: aggLoss,
      totalRxGB: totalRxBytes / 1e9,
      tcpFlowCount: tcpData.length,
      durationS: maxDuration,
    },
  };
}

mkdirSync(OUT_DIR, { recursive: true });

const dirs = readdirSync(LOGS_DIR).filter((d) => d.startsWith("comparison"));

const /**
@type {Record<string, {
  scenario: string;
  dataset: string;
  algorithms: Record<string, {
    flows: Flow[];
    summary: Summary;
  }>}>} */ allScenarios = {};
const scenarioSet = new Set();

for (const dir of dirs) {
  const dirPath = join(LOGS_DIR, dir);
  const files = readdirSync(dirPath).filter((f) => f.endsWith(".flowmonitor"));

  for (const file of files) {
    const name = basename(file, ".flowmonitor");
    let algo = null;
    let scenario = name;
    for (const a of ALGOS) {
      if (name.endsWith(a)) {
        algo = a;
        scenario = name.slice(0, -(a.length + 1));
        break;
      }
    }
    if (!algo) continue;

    scenarioSet.add(scenario);
    const key = `${dir}/${scenario}`;
    if (!allScenarios[key]) {
      allScenarios[key] = { scenario, dataset: dir, algorithms: {} };
    }

    const filePath = join(dirPath, file);
    try {
      allScenarios[key].algorithms[algo] = processFile(filePath);
    } catch (e) {
      console.error(
        `Error parsing ${filePath}: ${e instanceof Error ? e.message : String(e)}`,
      );
    }
  }
}

const scenarioList = Object.values(allScenarios).map((s) => ({
  scenario: s.scenario,
  dataset: s.dataset,
  algorithms: Object.keys(s.algorithms),
  summaries: Object.fromEntries(
    Object.entries(s.algorithms).map(([a, d]) => [a, d.summary]),
  ),
}));

writeFileSync(
  join(OUT_DIR, "index.json"),
  JSON.stringify(
    {
      scenarios: scenarioList,
      algorithms: ALGOS,
      generatedAt: new Date().toISOString(),
    },
    null,
    2,
  ),
);

for (const [key, data] of Object.entries(allScenarios)) {
  const safeName = key.replace(/\//g, "__");
  writeFileSync(
    join(OUT_DIR, `${safeName}.json`),
    JSON.stringify(data, null, 2),
  );
}

console.log(
  `Parsed ${Object.keys(allScenarios).length} scenario-algorithm sets from ${dirs.length} directories`,
);
console.log(`Scenarios: ${scenarioSet.size}`);
console.log(`Output: ${OUT_DIR}`);
