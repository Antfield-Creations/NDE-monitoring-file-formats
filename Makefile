.PHONY: tests check

tests:
	pipenv run python -m pytest

check:
	pipenv run flake8 .
	pipenv run mypy . --strict
