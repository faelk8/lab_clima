.PHONY: setup lint type test
setup:
	poetry install
lint:
	poetry run ruff check src tests
type:
	poetry run mypy src
test:
	poetry run pytest
