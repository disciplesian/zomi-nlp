"""Parse extracted paragraphs into (book, chapter, verse, text) records."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import INTERIM_DIR, RAW_DIR, REPORTS_DIR

# number -> (code, English name, chapter count)
BOOKS: dict[int, tuple[str, str, int]] = {
    1: ("GE", "Genesis", 50), 2: ("EX", "Exodus", 40), 3: ("LE", "Leviticus", 27),
    4: ("NU", "Numbers", 36), 5: ("DT", "Deuteronomy", 34), 6: ("JOS", "Joshua", 24),
    7: ("JDG", "Judges", 21), 8: ("RU", "Ruth", 4), 9: ("SA1", "1 Samuel", 31),
    10: ("SA2", "2 Samuel", 24), 11: ("KI1", "1 Kings", 22), 12: ("KI2", "2 Kings", 25),
    13: ("CH1", "1 Chronicles", 29), 14: ("CH2", "2 Chronicles", 36), 15: ("EZR", "Ezra", 10),
    16: ("NE", "Nehemiah", 13), 17: ("ES", "Esther", 10), 18: ("JOB", "Job", 42),
    19: ("PS", "Psalms", 150), 20: ("PR", "Proverbs", 31), 21: ("ECC", "Ecclesiastes", 12),
    22: ("SS", "Song of Solomon", 8), 23: ("ISA", "Isaiah", 66), 24: ("JER", "Jeremiah", 52),
    25: ("LA", "Lamentations", 5), 26: ("EZE", "Ezekiel", 48), 27: ("DA", "Daniel", 12),
    28: ("HOS", "Hosea", 14), 29: ("JOE", "Joel", 3), 30: ("AM", "Amos", 9),
    31: ("OB", "Obadiah", 1), 32: ("JON", "Jonah", 4), 33: ("MIC", "Micah", 7),
    34: ("NAH", "Nahum", 3), 35: ("HAB", "Habakkuk", 3), 36: ("ZEP", "Zephaniah", 3),
    37: ("HAG", "Haggai", 2), 38: ("ZEC", "Zechariah", 14), 39: ("MAL", "Malachi", 4),
    40: ("MT", "Matthew", 28), 41: ("MK", "Mark", 16), 42: ("LK", "Luke", 24),
    43: ("JN", "John", 21), 44: ("AC", "Acts", 28), 45: ("RO", "Romans", 16),
    46: ("CO1", "1 Corinthians", 16), 47: ("CO2", "2 Corinthians", 13), 48: ("GAL", "Galatians", 6),
    49: ("EPH", "Ephesians", 6), 50: ("PHP", "Philippians", 4), 51: ("COL", "Colossians", 4),
    52: ("TH1", "1 Thessalonians", 5), 53: ("TH2", "2 Thessalonians", 3),
    54: ("TI1", "1 Timothy", 6), 55: ("TI2", "2 Timothy", 4), 56: ("TIT", "Titus", 3),
    57: ("PHM", "Philemon", 1), 58: ("HEB", "Hebrews", 13), 59: ("JAS", "James", 5),
    60: ("PE1", "1 Peter", 5), 61: ("PE2", "2 Peter", 3), 62: ("JN1", "1 John", 5),
    63: ("JN2", "2 John", 1), 64: ("JN3", "3 John", 1), 65: ("JUD", "Jude", 1),
    66: ("REV", "Revelation", 22),
}  # fmt: skip

CODE_TO_NUM = {code: num for num, (code, _, _) in BOOKS.items()}

FILENAME_RE = re.compile(r"^\s*(\d{1,2})\s*-\s*TC([A-Z0-9]+?)STv-OL", re.IGNORECASE)

HARD_SKIP_WORDS = (
    "footnote", "reference", "outline", "header", "footer", "caption", "toc", "contents",
    "section title",
)  # fmt: skip
TITLE_WORDS = ("title", "heading")

# file-name codes that differ from the canonical 2-3 letter code
CODE_ALIASES = {"LEV": "LE"}

VERSE_NUM_RE = re.compile(r"^\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?\s*$")
LEADING_NUM_RE = re.compile(r"^\s*(\d{1,3})(?=\D|$)")


def parse_filename(name: str) -> tuple[int, str]:
    """Return (book_num, book_code) from e.g. ``'01- TCGESTv-OL.docx'``."""
    m = FILENAME_RE.match(Path(name).stem)
    if not m:
        raise ValueError(f"Unrecognised file name: {name}")
    num, code = int(m.group(1)), m.group(2).upper()
    if num not in BOOKS:
        raise ValueError(f"Unknown book number {num} in {name}")
    code = CODE_ALIASES.get(code, code)
    if BOOKS[num][0] != code:
        raise ValueError(f"Book code {code} does not match number {num} ({BOOKS[num][0]})")
    return num, code


def book_mapping_from_files(raw_dir: Path = RAW_DIR) -> dict[str, dict]:
    """Derive code -> {num, name} for the book files present."""
    out = {}
    for p in sorted(raw_dir.iterdir()):
        try:
            num, code = parse_filename(p.name)
        except ValueError:
            continue
        out[code] = {"num": num, "name": BOOKS[num][1], "file": p.name}
    return out


_APOS = "\u2019\u2018\u02bc\u02b9\u2032\u0060\u00b4\u02bb\u02c8\uff07"
_DQUOTE = "\u201c\u201d\u201e\u201f\u00ab\u00bb\u2033\uff02"
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"))
_TRANS = {**{ord(c): "'" for c in _APOS}, **{ord(c): '"' for c in _DQUOTE}, **_INVISIBLE}


def normalize_text(text: str) -> str:
    """NFC-normalise, unify apostrophes/quotes/whitespace; keep diacritics."""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_TRANS)
    text = re.sub(r"\s+", " ", text.replace("\u00a0", " "))
    return text.strip()


@dataclass
class ParseResult:
    records: list[dict] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def _style_kind(style: str) -> str:
    """Classify a paragraph style as 'skip', 'title' (only kept if numbered) or 'text'."""
    s = (style or "").lower()
    if any(w in s for w in HARD_SKIP_WORDS):
        return "skip"
    if any(w in s for w in TITLE_WORDS):
        return "title"
    return "text"


def _is_verse_number_run(run: dict) -> bool:
    style = (run.get("style") or "").lower()
    return "verse number" in style and bool(VERSE_NUM_RE.match(run["text"]))


def parse_paragraphs(paragraphs: list[dict], book_code: str) -> ParseResult:
    """Turn styled paragraphs into verse records for one book."""
    num = CODE_TO_NUM[book_code]
    name = BOOKS[num][1]
    res = ParseResult()
    verses: dict[tuple[int, int], list[str]] = {}
    ends: dict[tuple[int, int], int] = {}
    max_ch = BOOKS[num][2]
    chapter, verse = None, None

    def add(text: str) -> None:
        if chapter is None or verse is None or not text:
            return
        verses.setdefault((chapter, verse), []).append(text)

    for para in paragraphs:
        style = para.get("style") or ""
        kind = _style_kind(style)
        if kind == "skip":
            continue
        runs = [r for r in para.get("runs", []) if r["text"]]
        while runs and not runs[0]["text"].strip():
            runs.pop(0)
        if not runs:
            continue
        first = runs[0]
        m = LEADING_NUM_RE.match(first["text"])
        n = int(m.group(1)) if m else 0
        only_num = m is not None and not first["text"].strip().lstrip("0123456789")
        plain_num = only_num and not _is_verse_number_run(first)
        after_num = first["text"][m.end() : m.end() + 1] if m else ""
        beginning = style.lower().startswith("beginning verse")
        is_chapter = (
            m is not None
            and (plain_num or (beginning and (only_num or after_num.isspace())))
            and n == (chapter or 0) + 1
            and n <= max_ch
        )
        has_verse_num = any(_is_verse_number_run(r) for r in runs)
        if kind == "title" and not (is_chapter or has_verse_num):
            continue
        if kind == "text" and chapter is None and not is_chapter:
            continue
        if is_chapter:
            chapter, verse = n, 1
            runs = [{**first, "text": first["text"][m.end() :], "style": None}, *runs[1:]]
        buf: list[str] = []
        for i, run in enumerate(runs):
            text = run["text"]
            if run.get("superscript") or "footnote" in (run.get("style") or "").lower():
                continue
            if _is_verse_number_run(run):
                add("".join(buf))
                buf = []
                m = VERSE_NUM_RE.match(text)
                verse, verse_end = int(m.group(1)), int(m.group(2) or m.group(1))
                if (chapter, verse) in verses:
                    res.problems.append(f"{book_code} {chapter}:{verse} duplicate verse number")
                    verse = None
                    continue
                ends[(chapter, verse)] = verse_end
                continue
            # unstyled verse number at paragraph start that continues the sequence
            if i == 0 and verse is not None and chapter is not None:
                m = LEADING_NUM_RE.match(text)
                if m and int(m.group(1)) == verse + 1:
                    add("".join(buf))
                    buf = []
                    verse += 1
                    text = text[m.end() :]
            buf.append(text)
        add("".join(buf))
    for (ch, vs), parts in sorted(verses.items()):
        text = normalize_text(" ".join(parts))
        if text:
            res.records.append(
                {"book": book_code, "book_num": num, "book_name": name,
                 "chapter": ch, "verse": vs, "verse_end": ends.get((ch, vs), vs), "text": text}
            )  # fmt: skip
    res.problems.extend(check_completeness(res.records, book_code))
    return res


def check_completeness(records: list[dict], book_code: str) -> list[str]:
    """Report missing chapters/verses (gaps) for one book."""
    problems = []
    if not records:
        return [f"{book_code}: no verses parsed"]
    expected = BOOKS[CODE_TO_NUM[book_code]][2]
    by_ch: dict[int, set[int]] = {}
    for r in records:
        by_ch.setdefault(r["chapter"], set()).update(
            range(r["verse"], r.get("verse_end", r["verse"]) + 1)
        )
    missing = [c for c in range(1, expected + 1) if c not in by_ch]
    if missing:
        problems.append(f"{book_code}: missing chapters {missing}")
    extra = [c for c in by_ch if c > expected]
    if extra:
        problems.append(f"{book_code}: unexpected chapters {extra}")
    for ch, covered in sorted(by_ch.items()):
        gaps = [v for v in range(1, max(covered) + 1) if v not in covered]
        if gaps:
            problems.append(f"{book_code} ch {ch}: missing verses {gaps}")
    return problems


def read_interim(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def parse_all(
    raw_dir: Path = RAW_DIR, interim_dir: Path = INTERIM_DIR
) -> tuple[list[dict], dict[str, list[str]]]:
    """Parse every raw book from interim JSONL; returns (records, {file: [problems]})."""
    records: list[dict] = []
    problems: dict[str, list[str]] = {}
    for src in sorted(raw_dir.iterdir()):
        if src.suffix.lower() not in {".doc", ".docx"}:
            continue
        try:
            _, code = parse_filename(src.name)
        except ValueError as exc:
            problems[src.name] = [str(exc)]
            continue
        interim = interim_dir / (src.stem.replace(" ", "") + ".jsonl")
        if not interim.exists():
            problems[src.name] = ["no interim extraction found"]
            continue
        try:
            res = parse_paragraphs(read_interim(interim), code)
        except Exception as exc:  # noqa: BLE001
            problems[src.name] = [f"parsing failed: {exc}"]
            continue
        records.extend(res.records)
        issues = list(res.problems)
        if issues:
            problems[src.name] = issues
    return records, problems


def write_extraction_report(
    problems: dict[str, list[str]], n_files: int, n_verses: int,
    path: Path = REPORTS_DIR / "extraction_report.md",
) -> None:  # fmt: skip
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Extraction report", "",
        f"- Files processed: {n_files}",
        f"- Verses parsed: {n_verses}",
        f"- Files with problems: {len(problems)}", "",
    ]  # fmt: skip
    if problems:
        lines.append("## Problems")
        for name, issues in sorted(problems.items()):
            lines.append(f"### {name}")
            lines.extend(f"- {i}" for i in issues[:50])
            if len(issues) > 50:
                lines.append(f"- ... and {len(issues) - 50} more")
            lines.append("")
    else:
        lines.append("No problems found.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--interim-dir", type=Path, default=INTERIM_DIR)
    args = parser.parse_args()
    records, problems = parse_all(args.raw_dir, args.interim_dir)
    write_extraction_report(problems, len(list(args.raw_dir.glob("*.doc*"))), len(records))
    print(f"parsed {len(records)} verses; {len(problems)} files with problems")


if __name__ == "__main__":
    main()
