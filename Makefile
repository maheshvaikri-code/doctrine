# One-command truth (skills/repo-devops.md): same entry points local and CI.
.PHONY: test lint verify

test:
	python -m unittest discover -s tests

lint:
	python tools/doctrine_lint.py

verify: lint test
