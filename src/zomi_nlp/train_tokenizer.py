"""Train a SentencePiece tokenizer on the TRAIN split only."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from . import ROOT


def train_tokenizer(
    train_file: Path,
    output_dir: Path,
    vocab_size: int = 8000,
    model_type: str = "unigram",
    character_coverage: float = 1.0,
) -> Path:
    import sentencepiece as spm

    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "spm"
    spm.SentencePieceTrainer.train(
        input=str(train_file),
        model_prefix=str(prefix),
        vocab_size=vocab_size,
        model_type=model_type,
        character_coverage=character_coverage,
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        hard_vocab_limit=False,
        normalization_rule_name="identity",  # text is already normalised; keep apostrophes
    )
    return prefix.with_suffix(".model")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "tokenizer.yaml")
    parser.add_argument("--vocab-size", type=int)
    parser.add_argument("--model-type", choices=["unigram", "bpe"])
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    model = train_tokenizer(
        ROOT / cfg["train_file"],
        ROOT / cfg["output_dir"],
        args.vocab_size or cfg["vocab_size"],
        args.model_type or cfg["model_type"],
        cfg.get("character_coverage", 1.0),
    )
    print(f"tokenizer saved to {model}")


if __name__ == "__main__":
    main()
