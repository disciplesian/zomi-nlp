# Data

📚 Data quality, provenance, and careful handling are central to **Zomi-NLP**.

## 🗂️ Current source and outputs

The repository currently processes Zomi (Tedim Chin, ISO 639-3 `ctd`) Bible Word files stored under `data/raw/`. The source set includes legacy `.doc` and `.docx` files; the parser uses Word styles to distinguish verse text from headings, footnotes, and verse numbers.

The pipeline produces:

| Location | Contents |
| --- | --- |
| `data/interim/` | Extracted styled paragraphs |
| `data/processed/` | Structured records, text files, and train/validation/test splits |
| `reports/extraction_report.md` | Extraction issues and verse completeness checks |
| `reports/dataset_stats.md` | Dataset build statistics |
| `DATASET_CARD.md` | Dataset fields, split strategy, provenance, and caveats |

Build the dataset with:

```bash
make dataset
```

Generated directories are ignored by Git. Do not assume they will be present in a fresh clone; build them from authorized source data.

## 🔄 Processing and splits

Text is normalized to Unicode NFC, and quote, apostrophe, and whitespace variants are standardized. Records are organized by book, chapter, verse, and text. The dataset builder creates a deterministic **90/5/5 train/validation/test split by book and chapter**, so a chapter does not occur across multiple splits.

Check `reports/extraction_report.md` after each build. The parser reports source inconsistencies rather than silently guessing missing or duplicated verses.

## 🔐 Rights, privacy, and responsible use

Bible translations are usually copyrighted. **Before redistributing source text, datasets, or models, confirm the relevant permissions with the copyright holder.** Hugging Face uploads are private by default; keep them private unless you have permission to publish.

When adding any data:

- Record its source, license or permission, and intended use.
- Preserve raw inputs separately from derived data.
- Document transformations and known limitations.
- Avoid including personal or confidential information.
- Keep train, validation, and test examples separate to prevent leakage.

## 🧭 Known limitation

Bible-only text is strongly domain-biased and may contain a religious or archaic register. It is not a balanced sample of modern, everyday Zomi. General-purpose claims require additional appropriately licensed material from other domains and evaluation on that material.

➡️ See [Training](Training) for how the processed splits are used.
