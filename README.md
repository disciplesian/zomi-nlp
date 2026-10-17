# zomi-nlp

Automated, reproducible pipeline that turns the Zomi (Tedim Chin, ISO 639-3 `ctd`) Bible Word
files into clean datasets and trains Zomi language models with GitHub Actions and Hugging Face.

## Data provenance

`data/raw/` holds the Bible books as supplied (`NN- TC<CODE>STv-OL.doc[x]`, NN = canonical book
number, 01 = Genesis ... 66 = Revelation; currently 33 books, a mix of legacy `.doc` and `.docx`).
The files use Word styles such as `Beginning verse 1`, `ST verse number`, `Scripture Title`,
`Section title` and `Footnote`, which the parser uses to separate verse text from verse numbers,
headings, footnotes and cross references.

> **Copyright:** Bible translations are normally copyrighted. Confirm with the copyright holder
> that the text may be redistributed **before** making any dataset or model public. Everything
> pushed to Hugging Face is **private by default**.

## Pipeline

```
data/raw/*.doc|docx
   │  extract.py   (python-docx; LibreOffice headless for .doc)  -> data/interim/*.jsonl (styled paragraphs)
   ▼
 parse.py          (book map, chapter/verse records, NFC + quote/apostrophe/whitespace normalisation)
   │                                                            -> reports/extraction_report.md
   ▼
 build_dataset.py  (jsonl/csv/parquet, corpus.txt, 90/5/5 split by book+chapter, DatasetDict, card)
   │                                                            -> data/processed/, reports/dataset_stats.md, DATASET_CARD.md
   ▼
 train_tokenizer.py (SentencePiece unigram, train split only)   -> models/tokenizer
   ▼
 train_lm.py        (MLM fine-tuning of xlm-roberta-base, or small GPT-2 from scratch)
   │                                                            -> models/..., reports/metrics.json
   ▼
 push_to_hub.py     (dataset / tokenizer / model + model card, private)
```

## Setup and local run

Requires Python 3.10+ and LibreOffice (`soffice`) for the legacy `.doc` files.

```bash
python -m venv .venv && source .venv/bin/activate
make install-train          # or: pip install -r requirements-train.txt
make dataset                # python -m zomi_nlp.build_all
make tokenizer              # python -m zomi_nlp.train_tokenizer
make smoke                  # tiny CPU training run (also what CI uses)
make train                  # full GPT-2-style run (GPU recommended)
python -m zomi_nlp.train_lm --config configs/mlm_xlmr.yaml --mode full   # xlm-roberta-base MLM
make lint test
```

`scripts/run_pipeline.sh [smoke|full]` runs the whole chain. Check `reports/extraction_report.md`
after every build: it lists files that failed and chapters/verses that are missing or duplicated
in the source (the source files have a few styling inconsistencies and verse-numbering gaps; the
parser reports them rather than guessing).

## GitHub Actions

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push / PR | ruff, pytest, extraction + parsing on sample `.docx` and `.doc` files |
| `build-dataset.yml` | push to `data/raw/**`, manual | LibreOffice, extract, build dataset, upload artifacts, commit reports, optional HF push |
| `train.yml` | manual (`mode`, config, `model_name`, `epochs`, `push_to_hub`, `runner`) | tokenizer, train, evaluate, upload artifacts, optional HF push |

GitHub-hosted runners are CPU-only, so use `smoke` mode there. For `full` runs use a
self-hosted GPU runner (set the `runner` input to its label), or Hugging Face Spaces /
AutoTrain, or Colab, using the same `configs/*.yaml`.

### Secrets

Add in *Settings → Secrets and variables → Actions*; they are never stored in the repo:

- `HF_TOKEN` – Hugging Face access token with write permission
- `HF_USERNAME` – user/org that owns the repos (`<user>/zomi-bible`, `zomi-tokenizer`, `zomi-lm`)

## Roadmap

1. **English ↔ Zomi machine translation** – recommended next step. Align a public-domain English
   Bible with the Zomi verses by (book, chapter, verse) and fine-tune NLLB/mT5; see the stub
   `configs/translation.yaml` (split by chapter to avoid leakage).
2. Add non-Bible domains (news, conversation, education). Bible-only data causes strong domain
   bias, so evaluate on non-Bible text as well.
3. Evaluation with FLORES-style sets (chrF++/BLEU) for Zomi.
4. POS / NER tagging, then ASR / TTS.

## License

See `LICENSE` for the code. The Bible text is subject to its own copyright (see above).
