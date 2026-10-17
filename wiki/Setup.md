# Setup

⚙️ This guide prepares a local environment for working with **Zomi-NLP**. Commands below assume a Unix-like shell unless noted.

## ✅ Prerequisites

- Python **3.10 or newer**
- Git
- `make` (optional, for the repository’s shortcuts)
- LibreOffice Writer (`soffice`) to extract the legacy `.doc` source files; `.docx` files are also supported
- For full model training, suitable compute such as a GPU is recommended

## 📥 Clone and enter the repository

```bash
git clone https://github.com/disciplesian/zomi-nlp.git
cd zomi-nlp
```

## 🐍 Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

## 📦 Install dependencies

For the extraction and dataset pipeline:

```bash
python -m pip install -r requirements.txt
```

For tokenizer and model training, install the additional training dependencies:

```bash
make install-train
```

If `make` is unavailable, use:

```bash
python -m pip install -r requirements-train.txt
```

## 🧪 Check your installation

```bash
make lint test
```

To build the dataset locally (requires the source files and LibreOffice for `.doc` files):

```bash
make dataset
```

Review `reports/extraction_report.md` after a build for files that failed extraction and source gaps or duplicates. Generated datasets and models are local artifacts and are ignored by Git.

## 🛠️ Common setup issues

- **`soffice` not found:** install LibreOffice Writer and ensure `soffice` is available on your `PATH`.
- **Wrong Python version:** activate the intended virtual environment and confirm with `python --version`.
- **Training dependency errors:** install `requirements-train.txt` in the activated environment.
- **Insufficient compute or memory:** start with the CPU-friendly smoke configuration before attempting a full training run.

➡️ Continue with [Data](Data) to learn about source files, splits, and data handling.
