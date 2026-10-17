"""Config-driven language-model training (MLM fine-tuning or small causal LM from scratch)."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import yaml

from . import PROCESSED_DIR, REPORTS_DIR, ROOT


def load_config(path: Path, mode: str, overrides: dict | None = None) -> dict:
    """Merge the ``full``/``smoke`` section into the top-level config."""
    cfg = yaml.safe_load(Path(path).read_text())
    if mode not in {"smoke", "full"}:
        raise ValueError("mode must be 'smoke' or 'full'")
    section = cfg.get(mode, {}) or {}
    for key, value in section.items():
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            cfg[key] = {**cfg[key], **value}
        else:
            cfg[key] = value
    for key, value in (overrides or {}).items():
        if value is not None:
            cfg[key] = value
    cfg["mode"] = mode
    return cfg


def read_lines(path: Path, limit: int | None = None) -> list[str]:
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return lines[:limit] if limit else lines


class _Blocks:
    """Fixed-length token blocks for causal LM training."""

    def __init__(self, ids: list[int], block: int):
        self.blocks = [ids[i : i + block] for i in range(0, len(ids) - block + 1, block)]

    def __len__(self) -> int:
        return len(self.blocks)

    def __getitem__(self, i: int) -> dict:
        return {"input_ids": self.blocks[i], "labels": self.blocks[i]}


class _Encoded:
    """Tokenised, variable-length examples for MLM."""

    def __init__(self, enc: dict):
        self.ids = enc["input_ids"]

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, i: int) -> dict:
        return {"input_ids": self.ids[i]}


def _spm_ids(sp, lines: list[str]) -> list[int]:
    ids: list[int] = []
    for line in lines:
        ids.extend([sp.bos_id(), *sp.encode(line), sp.eos_id()])
    return ids


def run(cfg: dict, data_dir: Path = PROCESSED_DIR, metrics_path: Path | None = None) -> dict:
    from transformers import (
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    set_seed(cfg.get("seed", 42))
    max_train = cfg.get("max_train_samples")
    max_eval = cfg.get("max_eval_samples")
    train_lines = read_lines(data_dir / "train.txt", max_train)
    val_lines = read_lines(data_dir / "validation.txt", max_eval)
    test_lines = read_lines(data_dir / "test.txt", max_eval)
    out_dir = ROOT / cfg["output_dir"]
    max_len = cfg["max_length"]

    if cfg["task"] == "clm":
        import sentencepiece as spm
        from transformers import GPT2Config, GPT2LMHeadModel

        tok_dir = ROOT / cfg["tokenizer"]
        sp = spm.SentencePieceProcessor(model_file=str(tok_dir / "spm.model"))
        arch = cfg["architecture"]
        model = GPT2LMHeadModel(
            GPT2Config(
                vocab_size=sp.get_piece_size(),
                n_positions=max_len,
                n_ctx=max_len,
                n_layer=arch["n_layer"],
                n_head=arch["n_head"],
                n_embd=arch["n_embd"],
                bos_token_id=sp.bos_id(),
                eos_token_id=sp.eos_id(),
            )
        )
        train_ds, val_ds, test_ds = (
            _Blocks(_spm_ids(sp, lines), max_len) for lines in (train_lines, val_lines, test_lines)
        )
        collator = None
        save_tokenizer = lambda: _copy_tokenizer(tok_dir, out_dir)  # noqa: E731
    elif cfg["task"] == "mlm":
        from transformers import AutoModelForMaskedLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"])
        model = AutoModelForMaskedLM.from_pretrained(cfg["model_name"])

        def encode(lines: list[str]) -> _Encoded:
            return _Encoded(tokenizer(lines, truncation=True, max_length=max_len))

        train_ds, val_ds, test_ds = (encode(x) for x in (train_lines, val_lines, test_lines))
        collator = DataCollatorForLanguageModeling(
            tokenizer, mlm=True, mlm_probability=cfg.get("mlm_probability", 0.15)
        )
        save_tokenizer = lambda: tokenizer.save_pretrained(out_dir)  # noqa: E731
    else:
        raise ValueError(f"Unsupported task: {cfg['task']}")

    if len(train_ds) == 0 or len(val_ds) == 0:
        raise RuntimeError(
            "Not enough data to train/evaluate (increase samples or reduce max_length)"
        )

    total_steps = math.ceil(len(train_ds) / cfg["batch_size"]) * cfg["epochs"]
    args = TrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        num_train_epochs=cfg["epochs"],
        per_device_train_batch_size=cfg["batch_size"],
        per_device_eval_batch_size=cfg["batch_size"],
        learning_rate=float(cfg["learning_rate"]) if "learning_rate" in cfg else 5e-5,
        warmup_steps=int(cfg.get("warmup_ratio", 0.0) * total_steps),
        weight_decay=cfg.get("weight_decay", 0.0),
        save_strategy="no",
        logging_steps=50,
        report_to="none",
        seed=cfg.get("seed", 42),
    )
    trainer = Trainer(
        model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds, data_collator=collator
    )
    start = time.time()
    trainer.train()
    val = trainer.evaluate(val_ds, metric_key_prefix="val")
    test = trainer.evaluate(test_ds, metric_key_prefix="test") if len(test_ds) else {}

    out_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(out_dir))
    save_tokenizer()

    metrics = {
        "run": f"{cfg['task']}-{cfg.get('model_name', 'custom')}",
        "mode": cfg["mode"],
        "epochs": cfg["epochs"],
        "train_examples": len(train_ds),
        "val_loss": val["val_loss"],
        "val_perplexity": math.exp(min(val["val_loss"], 50)),
        "train_seconds": round(time.time() - start, 1),
    }
    if "test_loss" in test:
        metrics["test_loss"] = test["test_loss"]
        metrics["test_perplexity"] = math.exp(min(test["test_loss"], 50))
    metrics_path = metrics_path or REPORTS_DIR / "metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def _copy_tokenizer(src: Path, dst: Path) -> None:
    import shutil

    dst.mkdir(parents=True, exist_ok=True)
    for name in ("spm.model", "spm.vocab"):
        shutil.copy(src / name, dst / name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "gpt2_scratch.yaml")
    parser.add_argument("--mode", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--model-name", help="override the pretrained model (MLM configs)")
    parser.add_argument("--epochs", type=float)
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    cfg = load_config(
        args.config,
        args.mode,
        {"model_name": args.model_name, "epochs": args.epochs, "output_dir": args.output_dir},
    )
    print(json.dumps(run(cfg), indent=2))


if __name__ == "__main__":
    main()
