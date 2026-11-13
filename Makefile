.PHONY: setup lint type test sdp-dry-run sdp-run dashboard
setup:
	poetry install
lint:
	poetry run ruff check src tests
type:
	poetry run mypy src
test:
	poetry run pytest
sdp-dry-run:
	docker compose run --build --rm climatewatch spark-pipelines dry-run --spec /app/spark-pipeline.yml
sdp-run:
	docker compose run --build --rm climatewatch spark-pipelines run --spec /app/spark-pipeline.yml
dashboard:
	poetry run climatewatch-dashboard
