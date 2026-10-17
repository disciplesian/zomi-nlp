---
language:
- ctd
license: other
pretty_name: Zomi (Tedim Chin) Bible
task_categories:
- text-generation
- fill-mask
- translation
---

# Zomi (Tedim Chin) Bible dataset

Verse-level Bible text in Zomi / Tedim Chin (ISO 639-3 `ctd`), extracted from the
`TC*STv-OL` Word files in the `disciplesian/zomi-nlp` repository.

- Verses: 27349
- Whitespace tokens: 744913
- Characters: 3818103

## Fields

`book` (code), `book_num` (1-66), `chapter`, `verse`, `text`.

## Splits

Deterministic 90/5/5 train/validation/test split by (book, chapter) with a fixed seed,
so no chapter (and hence no verse) appears in more than one split.

## Source and license / copyright caveat

The text comes from a Bible translation supplied by the repository owner. Bible translations
are usually copyrighted. **Confirm redistribution rights with the copyright holder before making
this dataset public.** The pipeline pushes to a PRIVATE Hugging Face repository by default.

## Limitations

Bible-only data is strongly domain-biased (archaic/religious register). Add other domains
(news, conversation, education) before using models for general-purpose applications.

Load with: `datasets.load_dataset("<username>/zomi-bible")`.
