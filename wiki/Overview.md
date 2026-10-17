# Overview

🌿 **Welcome to Zomi-NLP** — an open, reproducible project for building natural language processing resources and models for **Zomi (Tedim Chin, ISO 639-3 `ctd`)**.

The repository turns source Bible documents into structured text datasets, trains tokenizers and language models, and provides workflows for checking and sharing experiment outputs. It is a foundation for language technology work, not a claim that current models are suitable for every domain.

---

## 🎯 Project goals

- Build useful, well-documented digital resources for Zomi.
- Make dataset preparation and model experiments reproducible.
- Encourage research and community contributions while respecting data rights.
- Create a foundation for future language tools and broader-domain resources.

## 🧩 What’s in the repository?

| Area | What it does |
| --- | --- |
| 📚 Source data | Word documents in `data/raw/` containing Zomi Bible text |
| 🧹 Extraction and parsing | Extracts styled paragraphs, then organizes and normalizes text by book, chapter, and verse |
| 🗃️ Dataset building | Writes structured dataset formats and text splits, with dataset statistics and extraction reports |
| 🔤 Tokenization | Trains a SentencePiece unigram tokenizer using the training split |
| 🤖 Language modeling | Supports a small GPT-2-style model trained from scratch and masked-language-model fine-tuning |
| ⚙️ Automation | Make targets and GitHub Actions for CI, dataset builds, and training |

The pipeline is:

```text
Word files → extraction → verse parsing and normalization → dataset and splits
          → tokenizer → model training → evaluation reports
```

## ⚠️ Data and responsible use

The current corpus is Bible text and has a religious, potentially archaic register. That makes it useful for experimentation, but not representative of everyday Zomi. Expand and evaluate with appropriately licensed material from other domains before drawing broader conclusions.

Bible translations are commonly copyrighted. **Confirm redistribution and model-use rights with the copyright holder before publishing data or models.** The Hugging Face workflow defaults to private repositories.

## 🚀 Find your next step

- ⚙️ [Setup](Setup) — prepare a local environment
- 📚 [Data](Data) — understand sources, processing, and data care
- 🤖 [Training](Training) — run tokenizer and model workflows
- 📊 [Evaluation](Evaluation) — interpret evaluation outputs and limitations
- 🤝 [Contributing](Contributing) — help improve the project

---

✨ Zomi-NLP welcomes thoughtful collaboration to make Zomi language technology more accessible, useful, and sustainable.
