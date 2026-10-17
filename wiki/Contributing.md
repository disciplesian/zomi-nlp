# Contributing

🤝 Thank you for helping build **Zomi-NLP**. Contributions to code, documentation, data quality, testing, and research all help strengthen Zomi language technology.

## 💡 Ways to contribute

- 🐛 Report reproducible bugs or suggest improvements through GitHub Issues.
- 📝 Improve documentation or clarify setup and workflow steps.
- 🧹 Improve extraction, parsing, dataset validation, or tests.
- 🤖 Contribute to tokenizer and model workflows.
- 📊 Add carefully documented evaluation methods or analysis.
- 🌍 Identify appropriately licensed Zomi resources and document their provenance.

## 🛠️ A simple contribution workflow

1. Check existing issues and discussions before starting substantial work.
2. Create a focused branch and make a small, clearly scoped change.
3. Run the relevant checks:

   ```bash
   make lint test
   ```

4. Update documentation when behavior or instructions change.
5. Open a pull request describing what changed, why, and how it was tested.

The CI workflow also extracts and parses sample `.docx` and `.doc` files. Changes to those paths should preserve both formats where possible.

## 📚 Data contributions need extra care

Before adding or publishing data, document:

- The source and any permission or license details.
- The format, language variety, and intended use.
- Preprocessing or filtering applied.
- Known gaps, bias, and other limitations.

Do not commit copyrighted source material without appropriate permission. Bible text in particular is commonly copyrighted; confirm redistribution and model-use rights with its copyright holder. Avoid personal, private, or confidential data.

## 🧪 Experiment contributions

When proposing training or evaluation results, include the model and configuration, dataset version and split, preprocessing, key settings, measured metrics, and limitations. Keep generated datasets, model weights, and checkpoints out of source control unless a project maintainer explicitly requests them.

## 🌱 Be welcoming

Please communicate respectfully, make review feedback constructive, and remember that language work benefits from the knowledge and perspectives of Zomi speakers and community members.

🙏 Every careful contribution helps make language technology more useful and accessible.
