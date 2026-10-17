.PHONY: install install-train extract dataset tokenizer smoke train lint test clean

PY ?= python
export PYTHONPATH := src

install:
	$(PY) -m pip install -r requirements.txt

install-train:
	$(PY) -m pip install -r requirements-train.txt

extract:
	$(PY) -m zomi_nlp.extract

dataset:
	$(PY) -m zomi_nlp.build_all

tokenizer:
	$(PY) -m zomi_nlp.train_tokenizer

smoke: tokenizer
	$(PY) -m zomi_nlp.train_lm --config configs/gpt2_scratch.yaml --mode smoke

train: tokenizer
	$(PY) -m zomi_nlp.train_lm --config configs/gpt2_scratch.yaml --mode full

lint:
	ruff check .

test:
	$(PY) -m pytest

clean:
	rm -rf data/interim data/processed models
