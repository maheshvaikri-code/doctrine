# One-command truth (skills/repo-devops.md): same entry points local and CI.
.PHONY: test lint ruff verify

test:
	python -m unittest discover -s tests

lint:
	python tools/doctrine_lint.py

ruff:
	python -m ruff check tools tests

verify: lint ruff test
