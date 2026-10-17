# Training

🤖 Zomi-NLP includes workflows for training a tokenizer and language models from the processed corpus. Start with a smoke run before scaling up.

## 🧱 Before you begin

1. Complete [Setup](Setup), including the training dependencies.
2. Build the dataset with `make dataset`.
3. Confirm the source data can be used for your intended training and sharing plans.
4. Choose a configuration under `configs/`.

## 🔤 Train the tokenizer

The pipeline trains a SentencePiece unigram tokenizer from the training split:

```bash
make tokenizer
```

The tokenizer is written to `models/tokenizer/` and is used by the GPT-2-style configuration.

## 🚀 Run a small CPU-friendly training check

```bash
make smoke
```

This uses `configs/gpt2_scratch.yaml` in `smoke` mode, with a small model and limited samples to check that the training path works. It is a pipeline check, not a meaningful benchmark.

## 🧠 Run a full training configuration

For the GPT-2-style causal language model:

```bash
make train
```

For masked-language-model fine-tuning of `xlm-roberta-base`:

```bash
python -m zomi_nlp.train_lm --config configs/mlm_xlmr.yaml --mode full
```

The available configurations define model and tokenizer choices, sequence length, architecture, and mode-specific settings such as epochs, batch size, and learning rate. Edit or copy a configuration for an experiment and record the changes.

Full runs can be compute-intensive; a GPU is recommended. GitHub-hosted runners are CPU-only, so use `smoke` for routine checks. The manually triggered training workflow supports configurable mode and config. Its runner choices may need to be updated to use an available self-hosted GPU.

## 📦 Outputs and reproducibility

Model files are saved beneath the configured `output_dir` in `models/`. Training writes evaluation metrics to `reports/metrics.json`.

For reproducible experiments:

- Keep the config and dataset version associated with each run.
- Record model, mode, hyperparameters, and any overrides.
- Set and retain the random seed where applicable.
- Do not commit large generated model artifacts or data files.

## 🔒 Sharing models

The optional Hugging Face upload workflow publishes to a **private** repository by default. Before sharing a model, verify the source-data rights and document the model’s data, intended use, domain bias, and limitations. Store access tokens as GitHub Actions secrets, never in source files.

➡️ See [Evaluation](Evaluation) for interpreting the validation and test results.
