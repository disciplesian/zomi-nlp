"""Upload dataset, tokenizer and model to the Hugging Face Hub (private by default).

Requires the ``HF_TOKEN`` environment variable. Repo ids come from ``--*-repo`` flags or
``HF_USERNAME`` (``<user>/zomi-bible``, ``<user>/zomi-tokenizer``, ``<user>/zomi-lm``).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from . import MODELS_DIR, PROCESSED_DIR, REPORTS_DIR


def default_repo_id(name: str, username: str | None = None) -> str:
    username = username or os.environ.get("HF_USERNAME")
    if not username:
        raise SystemExit("Set HF_USERNAME or pass an explicit repo id")
    return f"{username}/{name}"


def model_card(repo_id: str, metrics: dict | None) -> str:
    metric_lines = ""
    if metrics:
        metric_lines = "\n## Evaluation\n\n" + "\n".join(
            f"- {k}: {v}" for k, v in metrics.items() if isinstance(v, int | float | str)
        )
    return f"""---
language:
- ctd
license: other
tags:
- zomi
- tedim-chin
---

# {repo_id}

Language model for Zomi (Tedim Chin, ISO 639-3 `ctd`) trained with
[disciplesian/zomi-nlp](https://github.com/disciplesian/zomi-nlp) on Bible text only.
{metric_lines}

## Intended use and limitations

Research and experimentation. Training data is a single Bible translation, so the model is
biased toward religious/archaic register and should not be used for general-purpose
applications. The source translation is copyrighted; confirm redistribution rights before
making this repository public.
"""


def push(
    dataset_repo: str | None,
    tokenizer_repo: str | None,
    model_repo: str | None,
    private: bool = True,
    token: str | None = None,
    processed_dir: Path = PROCESSED_DIR,
    models_dir: Path = MODELS_DIR,
    model_dir: Path | None = None,
) -> None:
    from huggingface_hub import HfApi

    token = token or os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is not set; refusing to push")
    api = HfApi(token=token)

    if dataset_repo:
        api.create_repo(dataset_repo, repo_type="dataset", private=private, exist_ok=True)
        for name in ("zomi_bible.jsonl", "zomi_bible.csv", "zomi_bible.parquet", "corpus.txt",
                     "train.jsonl", "validation.jsonl", "test.jsonl"):  # fmt: skip
            f = processed_dir / name
            if f.exists():
                api.upload_file(path_or_fileobj=str(f), path_in_repo=f"data/{name}",
                                repo_id=dataset_repo, repo_type="dataset")  # fmt: skip
        card = processed_dir / "DATASET_CARD.md"
        if card.exists():
            api.upload_file(path_or_fileobj=str(card), path_in_repo="README.md",
                            repo_id=dataset_repo, repo_type="dataset")  # fmt: skip
        print(f"pushed dataset to {dataset_repo} (private={private})")

    if tokenizer_repo:
        tok_dir = models_dir / "tokenizer"
        api.create_repo(tokenizer_repo, repo_type="model", private=private, exist_ok=True)
        api.upload_folder(folder_path=str(tok_dir), repo_id=tokenizer_repo, repo_type="model")
        print(f"pushed tokenizer to {tokenizer_repo} (private={private})")

    if model_repo:
        model_dir = model_dir or models_dir / "gpt2-zomi"
        metrics_file = REPORTS_DIR / "metrics.json"
        metrics = json.loads(metrics_file.read_text()) if metrics_file.exists() else None
        api.create_repo(model_repo, repo_type="model", private=private, exist_ok=True)
        (model_dir / "README.md").write_text(model_card(model_repo, metrics), encoding="utf-8")
        api.upload_folder(folder_path=str(model_dir), repo_id=model_repo, repo_type="model",
                          ignore_patterns=["checkpoints/*"])  # fmt: skip
        print(f"pushed model to {model_repo} (private={private})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--what", nargs="+", choices=["dataset", "tokenizer", "model"],
                        default=["dataset", "tokenizer", "model"])  # fmt: skip
    parser.add_argument("--dataset-repo")
    parser.add_argument("--tokenizer-repo")
    parser.add_argument("--model-repo")
    parser.add_argument("--model-dir", type=Path, help="trained model directory")
    parser.add_argument(
        "--public",
        action="store_true",
        help="make repos public (only after confirming redistribution rights!)",
    )
    args = parser.parse_args()
    push(
        (args.dataset_repo or default_repo_id("zomi-bible")) if "dataset" in args.what else None,
        (args.tokenizer_repo or default_repo_id("zomi-tokenizer"))
        if "tokenizer" in args.what else None,
        (args.model_repo or default_repo_id("zomi-lm")) if "model" in args.what else None,
        private=not args.public,
        model_dir=args.model_dir,
    )  # fmt: skip


if __name__ == "__main__":
    main()
