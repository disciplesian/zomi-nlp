"""End-to-end data pipeline: extract -> parse -> build dataset (+ reports)."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import INTERIM_DIR, PROCESSED_DIR, RAW_DIR, REPORTS_DIR
from .build_dataset import DEFAULT_SEED, build
from .extract import extract_all
from .parse import parse_all, write_extraction_report


def run(
    raw_dir: Path = RAW_DIR,
    interim_dir: Path = INTERIM_DIR,
    out_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
    seed: int = DEFAULT_SEED,
    skip_extract: bool = False,
) -> int:
    problems: dict[str, list[str]] = {}
    if not skip_extract:
        _, errors = extract_all(raw_dir, interim_dir)
        problems.update({k: [v] for k, v in errors.items()})
    records, parse_problems = parse_all(raw_dir, interim_dir)
    for name, issues in parse_problems.items():
        problems.setdefault(name, []).extend(issues)
    n_files = len([p for p in raw_dir.iterdir() if p.suffix.lower() in {".doc", ".docx"}])
    write_extraction_report(problems, n_files, len(records), reports_dir / "extraction_report.md")
    if not records:
        print("No verses parsed; see reports/extraction_report.md")
        return 1
    build(records, out_dir, reports_dir, seed=seed)
    print(f"{len(records)} verses from {n_files} files; {len(problems)} files with problems")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--interim-dir", type=Path, default=INTERIM_DIR)
    parser.add_argument("--out-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--skip-extract", action="store_true", help="reuse data/interim")
    args = parser.parse_args()
    raise SystemExit(
        run(args.raw_dir, args.interim_dir, args.out_dir, seed=args.seed,
            skip_extract=args.skip_extract)
    )  # fmt: skip


if __name__ == "__main__":
    main()
