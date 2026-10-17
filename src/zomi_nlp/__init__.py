"""Zomi (Tedim Chin) NLP pipeline."""

from pathlib import Path

__version__ = "0.1.0"

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
