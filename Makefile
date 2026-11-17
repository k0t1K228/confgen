.RECIPEPREFIX := >

VENV := .venv
PYTHON := $(VENV)/bin/python

.PHONY: install test lint run examples clean

install:
> python -m venv $(VENV)
> $(PYTHON) -m pip install -r requirements.txt

test:
> $(PYTHON) -m pytest

lint:
> $(VENV)/bin/ruff check .

run:
> @PYTHONPATH=src $(PYTHON) -m confgen

examples:
> @for f in examples/*.conf; do \
>   echo "=== $$f ==="; \
>   PYTHONPATH=src $(PYTHON) -m confgen < $$f || exit 1; \
> done

clean:
> find . -name "__pycache__" -type d -prune -exec rm -rf {} +
> rm -rf .pytest_cache .ruff_cache
