#!/usr/bin/env bash
# Extract -> dataset -> tokenizer -> (smoke|full) training.  Usage: scripts/run_pipeline.sh [smoke|full]
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
MODE="${1:-smoke}"
python -m zomi_nlp.build_all
python -m zomi_nlp.train_tokenizer
python -m zomi_nlp.train_lm --config configs/gpt2_scratch.yaml --mode "$MODE"
