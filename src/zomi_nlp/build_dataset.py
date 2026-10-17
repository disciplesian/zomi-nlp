"""Build the processed dataset, deterministic splits, corpus and statistics."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from . import PROCESSED_DIR, REPORTS_DIR, ROOT

FIELDS = ["book", "book_num", "chapter", "verse", "text"]
SPLIT_NAMES = ("train", "validation", "test")
DEFAULT_RATIOS = (0.90, 0.05, 0.05)
DEFAULT_SEED = 42


def split_units(
    records: list[dict],
    ratios: tuple[float, float, float] = DEFAULT_RATIOS,
    seed: int = DEFAULT_SEED,
) -> dict[tuple[str, int], str]:
    """Assign every (book, chapter) unit to a split. Deterministic for a given seed.

    Splitting by chapter keeps all verses of a chapter together, so no verse can
    leak between splits.
    """
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError("ratios must sum to 1")
    units = sorted({(r["book"], r["chapter"]) for r in records})
    random.Random(seed).shuffle(units)
    n = len(units)
    n_val = max(1, round(n * ratios[1])) if n >= 3 and ratios[1] > 0 else 0
    n_test = max(1, round(n * ratios[2])) if n >= 3 and ratios[2] > 0 else 0
    assignment = {}
    for i, unit in enumerate(units):
        if i < n_val:
            assignment[unit] = "validation"
        elif i < n_val + n_test:
            assignment[unit] = "test"
        else:
            assignment[unit] = "train"
    return assignment


def make_splits(
    records: list[dict],
    ratios: tuple[float, float, float] = DEFAULT_RATIOS,
    seed: int = DEFAULT_SEED,
) -> dict[str, list[dict]]:
    assignment = split_units(records, ratios, seed)
    splits: dict[str, list[dict]] = {name: [] for name in SPLIT_NAMES}
    for r in sorted(records, key=lambda r: (r["book_num"], r["chapter"], r["verse"])):
        splits[assignment[(r["book"], r["chapter"])]].append(r)
    return splits


def compute_stats(records: list[dict]) -> dict:
    tokens = [t for r in records for t in r["text"].split()]
    return {
        "verses": len(records),
        "tokens": len(tokens),
        "vocab": len(set(t.lower() for t in tokens)),
        "chars": sum(len(r["text"]) for r in records),
    }


def write_stats_report(splits: dict[str, list[dict]], path: Path) -> None:
    all_records = [r for s in splits.values() for r in s]
    rows = {"all": compute_stats(all_records)} | {k: compute_stats(v) for k, v in splits.items()}
    lines = [
        "# Dataset statistics", "",
        "Tokens are whitespace-separated words; vocab is the number of distinct lower-cased words.",
        "", "| split | verses | tokens | vocab | chars |", "|---|---:|---:|---:|---:|",
    ]  # fmt: skip
    for name, s in rows.items():
        lines.append(f"| {name} | {s['verses']} | {s['tokens']} | {s['vocab']} | {s['chars']} |")
    books = sorted({(r["book_num"], r["book"]) for r in all_records})
    lines += ["", f"Books included: {len(books)} ({', '.join(b for _, b in books)})", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: r[k] for k in FIELDS}, ensure_ascii=False) + "\n")


def write_dataset_card(path: Path, stats: dict, hf_repo: str = "<username>/zomi-bible") -> None:
    path.write_text(
        f"""---
language:
- ctd
license: other
pretty_name: Zomi Bible
task_categories:
- text-generation
- fill-mask
- translation
---

# Zomi Bible dataset

Verse-level Bible text in Zomi (ISO 639-3 `ctd`), extracted from the
`TC*STv-OL` Word files in the `disciplesian/zomi-nlp` repository.

- Verses: {stats["verses"]}
- Whitespace tokens: {stats["tokens"]}
- Characters: {stats["chars"]}

## Fields

`book` (code), `book_num` (1-66), `chapter`, `verse`, `text`.

## Splits

Deterministic 90/5/5 train/validation/test split by (book, chapter) with a fixed seed,
so no chapter (and hence no verse) appears in more than one split.

## Source and license / copyright caveat

The text comes from a Bible translation supplied by the repository owner. Bible translations
are usually copyrighted. **Confirm redistribution rights with the copyright holder before making
this dataset public.** The pipeline pushes to a PRIVATE Hugging Face repository by default.

## Limitations

Bible-only data is strongly domain-biased (archaic/religious register). Add other domains
(news, conversation, education) before using models for general-purpose applications.

Load with: `datasets.load_dataset("{hf_repo}")`.
""",
        encoding="utf-8",
    )


def to_dataset_dict(splits: dict[str, list[dict]]):
    from datasets import Dataset, DatasetDict

    return DatasetDict(
        {
            name: Dataset.from_list([{k: r[k] for k in FIELDS} for r in rows])
            for name, rows in splits.items()
        }
    )


def build(
    records: list[dict],
    out_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
    seed: int = DEFAULT_SEED,
    hf_dataset: bool = True,
) -> dict[str, list[dict]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = sorted(records, key=lambda r: (r["book_num"], r["chapter"], r["verse"]))
    splits = make_splits(records, seed=seed)

    write_jsonl(out_dir / "zomi_bible.jsonl", records)
    import pandas as pd

    df = pd.DataFrame([{k: r[k] for k in FIELDS} for r in records], columns=FIELDS)
    df.to_csv(out_dir / "zomi_bible.csv", index=False)
    try:
        df.to_parquet(out_dir / "zomi_bible.parquet", index=False)
    except ImportError:
        print("pyarrow not installed; skipping parquet output")

    (out_dir / "corpus.txt").write_text(
        "\n".join(r["text"] for r in records) + "\n", encoding="utf-8"
    )
    for name, rows in splits.items():
        write_jsonl(out_dir / f"{name}.jsonl", rows)
        (out_dir / f"{name}.txt").write_text(
            "".join(r["text"] + "\n" for r in rows), encoding="utf-8"
        )

    write_stats_report(splits, reports_dir / "dataset_stats.md")
    write_dataset_card(out_dir / "DATASET_CARD.md", compute_stats(records))
    if out_dir == PROCESSED_DIR:
        write_dataset_card(ROOT / "DATASET_CARD.md", compute_stats(records))
    if hf_dataset:
        try:
            to_dataset_dict(splits).save_to_disk(str(out_dir / "hf_dataset"))
        except ImportError:
            print("`datasets` not installed; skipping DatasetDict")
    return splits


def main() -> None:
    from .parse import parse_all

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args()
    records, _ = parse_all()
    splits = build(records, args.out_dir, seed=args.seed)
    print({k: len(v) for k, v in splits.items()})


if __name__ == "__main__":
    main()
