.PHONY: tests

tests:
	pipenv run pytest

check:
	pipenv run flake8 .
	pipenv run mypy .
