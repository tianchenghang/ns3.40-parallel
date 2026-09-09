#!/usr/bin/env python3

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import sys
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parent


def log(message: str) -> None:
    return print(f"[BUILD] {message}")


def warn(message: str) -> None:
    return print(f"[WARN] {message}")


def err(message: str) -> None:
    return print(f"[ERROR] {message}", file=sys.stderr)


def run_command(command: list[str], cwd: Path, ignore_failure: bool = False) -> bool:
    try:
        subprocess.run(
            command,
            cwd=cwd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError:
        err(f"Command not found: {command[0]}")
        if ignore_failure:
            return False
        raise
    except subprocess.CalledProcessError:
        if ignore_failure:
            return False
        raise


def clean_trash(directory: Path | None = None) -> None:
    target_dir = directory or Path(".")
    suffixes = {".aux", ".bbl", ".blg", ".lof", ".log", ".lot", ".toc", ".out"}

    for item in target_dir.iterdir():
        if item.is_file() and any(item.name.endswith(suffix) for suffix in suffixes):
            item.unlink(missing_ok=True)

    for item in target_dir.rglob("*.aux"):
        try:
            if len(item.relative_to(target_dir).parts) <= 2:
                item.unlink()
        except FileNotFoundError:
            pass


def build_simple(tex: str, compiler: str = "xelatex") -> None:
    name = tex.removesuffix(".tex")
    log(f"Compiling {tex} ...")
    try:
        run_command(
            [compiler, "-interaction=nonstopmode", "-halt-on-error", tex], DOCS_DIR
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        err(f"Pass 1 failed for {tex}. Please check {name}.log for details.")
        raise SystemExit(1)

    try:
        run_command(
            [compiler, "-interaction=nonstopmode", "-halt-on-error", tex], DOCS_DIR
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        err(f"Pass 2 failed for {tex}. Please check {name}.log for details.")
        raise SystemExit(1)

    log(f"{name}.pdf successfully generated ✓")


def build_with_bib(tex: str) -> None:
    name = tex.removesuffix(".tex")
    target_dir = DOCS_DIR / "NJUPT_Professional_Thesis_draft1"
    log(f"Compiling {tex} (with BibTeX)...")

    try:
        run_command(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex], target_dir
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        err(f"Pass 1 failed for {tex}.")
        raise SystemExit(1)

    if not run_command(["bibtex", name], target_dir, ignore_failure=True):
        warn(f"bibtex generated warnings for {name}.")

    try:
        run_command(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex], target_dir
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        err(f"Pass 2 failed for {tex}.")
        raise SystemExit(1)

    try:
        run_command(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex], target_dir
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        err(f"Pass 3 failed for {tex}.")
        raise SystemExit(1)

    log(f"{name}.pdf successfully generated ✓")


def usage() -> None:
    print(f"Usage: {Path(sys.argv[0]).name} <target...>")
    print("")
    print("  njupt    Compile NJUPT master's thesis (with BibTeX)")
    print("  thesis   Compile Chinese conference paper (thesis.tex)")
    print("  all      Compile all targets above")
    print("  clean    Clean compilation auxiliary files")


def clean_all() -> None:
    log("Cleaning auxiliary files...")
    clean_trash(DOCS_DIR)
    clean_trash(DOCS_DIR / "NJUPT_Professional_Thesis_draft1")
    clean_trash(DOCS_DIR / "NJUPT_Professional_Thesis_draft1" / "chapters")
    log("Cleanup complete ✓")


def build_all_parallel() -> None:
    targets = ("njupt", "thesis")
    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        future_to_target = {
            executor.submit(do_build, target): target for target in targets
        }
        for future in as_completed(future_to_target):
            target = future_to_target[future]
            try:
                future.result()
            except BaseException as exc:
                err(f"Parallel build failed for target: {target}")
                raise exc


def do_build(target: str) -> None:
    if target == "njupt":
        build_with_bib("NJUPT_Professional_Thesis_d1.tex")
        return

    if target == "thesis":
        build_simple("thesis.tex", "xelatex")
        return

    if target == "all":
        build_all_parallel()
        return

    if target == "clean":
        clean_all()
        return

    err(f"Unknown target: {target}")
    usage()
    raise SystemExit(1)


def main() -> int:
    auto_clean_targets = {"njupt", "thesis", "all"}

    if len(sys.argv) == 1:
        usage()
        return 0

    for target in sys.argv[1:]:
        do_build(target)
        if target in auto_clean_targets:
            clean_all()

    log("All tasks completed successfully ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
