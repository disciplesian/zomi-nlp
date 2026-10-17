import json
import unicodedata

import pytest

from zomi_nlp.build_dataset import make_splits, split_units
from zomi_nlp.parse import (
    BOOKS,
    CODE_TO_NUM,
    check_completeness,
    normalize_text,
    parse_filename,
    parse_paragraphs,
)


def run(text, style=None):
    return {"text": text, "style": style, "superscript": False}


def para(style, *runs):
    return {"style": style, "text": "".join(r["text"] for r in runs), "runs": list(runs)}


V = "ST verse number"


def sample_paragraphs():
    return [
        para("Section title", run("PIANCILNA")),
        para("Scripture Text", run("(Genesis)")),
        para("Scripture Title before chapter", run("Heading")),
        para(
            "Beginning verse 1",
            run("1"),
            run(" A kipat"),
            run("2", V),
            run("Leitung in"),
            run("Topa"),
            run(" in"),
        ),  # fmt: skip
        para("Scripture Text", run("3", V), run("Pasian in")),
        para("Scripture Text", run("continues here")),
        para("Beginning verse 1", run("2 "), run("Tua ahih"), run("2", V), run("Ni sagih")),
        para("Footnote", run("1 note")),
    ]


def test_book_mapping():
    assert len(BOOKS) == 66
    assert BOOKS[1][:2] == ("GE", "Genesis") and BOOKS[66][:2] == ("REV", "Revelation")
    assert len(CODE_TO_NUM) == 66
    assert parse_filename("01- TCGESTv-OL.docx") == (1, "GE")
    assert parse_filename("58-TCHEBSTv-OL.doc") == (58, "HEB")
    assert parse_filename("03- TCLEVSTv-OL.doc") == (3, "LE")
    with pytest.raises(ValueError):
        parse_filename("readme.docx")
    with pytest.raises(ValueError):
        parse_filename("01- TCEXSTv-OL.docx")


def test_parse_strips_numbers_headings_and_footnotes():
    res = parse_paragraphs(sample_paragraphs(), "GE")
    got = {(r["chapter"], r["verse"]): r["text"] for r in res.records}
    assert got[(1, 1)] == "A kipat"
    assert got[(1, 2)] == "Leitung inTopa in"
    assert got[(1, 3)] == "Pasian in continues here"
    assert got[(2, 1)] == "Tua ahih"
    assert got[(2, 2)] == "Ni sagih"
    assert all(not any(c.isdigit() for c in t) for t in got.values())
    assert not any("Heading" in t or "PIANCILNA" in t or "note" in t for t in got.values())


def test_verse_bridge_and_completeness():
    paras = [para("Beginning verse 1", run("1"), run(" a"), run("2-3", V), run("b"), run("4", V),
                  run("c"))]  # fmt: skip
    res = parse_paragraphs(paras, "OB")
    assert [(r["verse"], r["verse_end"]) for r in res.records] == [(1, 1), (2, 3), (4, 4)]
    assert not any("missing verses" in p for p in res.problems)
    gap = [{"chapter": 1, "verse": 1, "verse_end": 1}, {"chapter": 1, "verse": 3, "verse_end": 3}]
    assert "missing verses [2]" in check_completeness(gap, "OB")[0]


def test_missing_chapters_reported():
    problems = check_completeness([{"chapter": 1, "verse": 1}], "RU")
    assert any("missing chapters [2, 3, 4]" in p for p in problems)


def test_normalize_text():
    out = normalize_text("Tuite\u2019  laizang\u00a0\u2018x\u2019 \u201cHi\u201d\u200b\n")
    assert out == "Tuite' laizang 'x' \"Hi\""
    decomposed = unicodedata.normalize("NFD", "ngâk")
    assert normalize_text(decomposed) == unicodedata.normalize("NFC", "ngâk")
    assert "â" in normalize_text("ngâk")


def make_records():
    return [
        {"book": b, "book_num": n, "chapter": c, "verse": v, "text": f"{b} {c} {v}"}
        for n, b in enumerate(["GE", "EX", "LE"], 1)
        for c in range(1, 21)
        for v in range(1, 6)
    ]


def test_splits_no_leakage_and_deterministic():
    recs = make_records()
    a, b = make_splits(recs, seed=1), make_splits(recs, seed=1)
    assert json.dumps(a) == json.dumps(b)
    assert sum(len(v) for v in a.values()) == len(recs)
    seen = {}
    for name, rows in a.items():
        for r in rows:
            assert seen.setdefault((r["book"], r["chapter"]), name) == name
    assert all(len(rows) > 0 for rows in a.values())
    assert split_units(recs, seed=1) != split_units(recs, seed=2)
    assert len(a["train"]) > 0.8 * len(recs)
