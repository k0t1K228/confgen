.RECIPEPREFIX := >

VENV := .venv
PYTHON := $(VENV)/bin/python

.PHONY: install test lint run clean

install:
> python -m venv $(VENV)
> $(PYTHON) -m pip install -r requirements.txt

test:
> $(PYTHON) -m pytest

lint:
> $(VENV)/bin/ruff check .

run:
> PYTHONPATH=src $(PYTHON) -m confgen

clean:
> find . -name "__pycache__" -type d -prune -exec rm -rf {} +
> rm -rf .pytest_cache .ruff_cache
