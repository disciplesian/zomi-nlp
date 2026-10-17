"""Convert Word files (.doc/.docx) to per-book JSONL keeping paragraph/run styles."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import INTERIM_DIR, RAW_DIR


def doc_to_docx(src: Path, outdir: Path) -> Path:
    """Convert a legacy .doc to .docx with LibreOffice headless."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        raise RuntimeError(
            "LibreOffice (soffice) not found; install it to convert legacy .doc files"
        )
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            soffice,
            f"-env:UserInstallation={Path(profile).as_uri()}",
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            str(outdir),
            str(src),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    out = outdir / (src.stem + ".docx")
    if not out.exists():
        raise RuntimeError(f"LibreOffice produced no output for {src.name}")
    return out


def docx_paragraphs(path: Path) -> list[dict]:
    """Return paragraphs as dicts with style names and styled runs."""
    import docx

    document = docx.Document(str(path))
    paragraphs = []
    for para in document.paragraphs:
        runs = []
        for run in para.runs:
            style = run.style.name if run.style is not None else None
            runs.append(
                {"text": run.text, "style": style, "superscript": bool(run.font.superscript)}
            )
        paragraphs.append({"style": para.style.name, "text": para.text, "runs": runs})
    return paragraphs


def extract_file(src: Path, interim_dir: Path = INTERIM_DIR) -> Path:
    """Extract one Word file to ``interim_dir/<stem>.jsonl`` and return the output path."""
    interim_dir.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".docx":
        paragraphs = docx_paragraphs(src)
    elif src.suffix.lower() == ".doc":
        with tempfile.TemporaryDirectory() as tmp:
            paragraphs = docx_paragraphs(doc_to_docx(src, Path(tmp)))
    else:
        raise ValueError(f"Unsupported file type: {src}")
    out = interim_dir / (src.stem.replace(" ", "") + ".jsonl")
    with out.open("w", encoding="utf-8") as fh:
        for para in paragraphs:
            fh.write(json.dumps(para, ensure_ascii=False) + "\n")
    return out


def raw_files(raw_dir: Path = RAW_DIR) -> list[Path]:
    return sorted(p for p in raw_dir.iterdir() if p.suffix.lower() in {".doc", ".docx"})


def extract_all(
    raw_dir: Path = RAW_DIR, interim_dir: Path = INTERIM_DIR
) -> tuple[list[Path], dict[str, str]]:
    """Extract every file; returns (outputs, {filename: error})."""
    outputs, errors = [], {}
    for src in raw_files(raw_dir):
        try:
            outputs.append(extract_file(src, interim_dir))
        except Exception as exc:  # noqa: BLE001 - reported, not fatal
            errors[src.name] = f"extraction failed: {exc}"
    return outputs, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--interim-dir", type=Path, default=INTERIM_DIR)
    parser.add_argument("files", nargs="*", type=Path, help="optional subset of files")
    args = parser.parse_args()
    if args.files:
        outs, errs = [], {}
        for f in args.files:
            try:
                outs.append(extract_file(f, args.interim_dir))
            except Exception as exc:  # noqa: BLE001
                errs[f.name] = f"extraction failed: {exc}"
    else:
        outs, errs = extract_all(args.raw_dir, args.interim_dir)
    print(f"extracted {len(outs)} files; {len(errs)} errors")
    for name, err in errs.items():
        print(f"  {name}: {err}")


if __name__ == "__main__":
    main()
