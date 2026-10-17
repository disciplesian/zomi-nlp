# Evaluation

📊 Evaluation helps determine whether a Zomi-NLP experiment learned useful patterns and where it still falls short.

## 🔍 What the current pipeline reports

The training pipeline evaluates on the validation split during training and evaluates the held-out test split after training. It writes `reports/metrics.json`, including applicable fields such as:

- `val_loss` and `val_perplexity`
- `test_loss` and `test_perplexity` when test examples are available
- run mode, epoch count, training example count, and elapsed time

Perplexity is derived from language-model loss. Compare it only across compatible tasks, tokenization, data, and evaluation setups; a lower score alone does not establish that a model is useful in real-world Zomi applications.

## 🧪 Suggested workflow

1. Build the dataset and review `reports/extraction_report.md`.
2. Train with the intended configuration and retain the generated `reports/metrics.json`.
3. Compare validation metrics while developing; use the test split for final comparisons rather than repeated tuning.
4. Inspect model outputs with fluent Zomi speakers and record representative successes and errors.
5. Document the dataset, preprocessing, model configuration, metrics, and limitations.

The chapter-based split is designed to reduce leakage between splits, but it does not remove domain bias: the present corpus is Bible text. Evaluate on suitable, separately sourced data before claiming performance beyond that domain.

## 📝 Report results clearly

For each experiment, record:

| Detail | Example |
| --- | --- |
| Task and model | Causal LM or masked LM; model/config name |
| Data | Dataset version, source, and split |
| Setup | Tokenizer, preprocessing, mode, and hyperparameters |
| Results | Validation/test loss and perplexity, where applicable |
| Interpretation | Error patterns, limitations, and next steps |

Only report metrics that are actually measured. Classification or translation scores such as accuracy, BLEU, or chrF++ require task-specific labeled or parallel evaluation data and are not produced by the current language-model training script.

## ⚠️ Interpret results with care

- A smoke run checks the pipeline; it is not a performance benchmark.
- Small or domain-specific test sets can give misleading results.
- Include qualitative review and note who reviewed outputs when appropriate.
- Do not publish evaluation text or model outputs unless their source rights allow it.

➡️ Use evaluation findings to guide data improvements and future experiments.
