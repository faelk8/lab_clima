# ClimateWatch — laboratório de dados climáticos

Projeto experimental local para coletar dados históricos abertos, preservar proveniência e validar um pipeline com Apache Spark Declarative Pipelines (SDP). Não é um alerta oficial nem uma previsão de enchentes.

## Estado

Fases 1, 2 e 3 implementadas e testadas localmente. A Fase 3 acrescenta o DAG Bronze → Silver → Gold. Consulte [arquitetura](docs/architecture.md), [contratos de dados](docs/data-contracts.md) e [fontes e licenças](docs/sources-and-licenses.md).

## Requisitos e comandos

Python 3.12, Poetry e Java 17 ou 21. Para Spark no container, Docker e Docker Compose.

```bash
poetry install
poetry run pytest -q
poetry run ruff check src tests pipelines
poetry run mypy src
poetry run climatewatch-download --help
docker compose run --rm climatewatch python -m climatewatch.interfaces.cli --help
```

A imagem usa PySpark 4.1.0 com o extra oficial `pipelines`. A configuração do smoke está em `spark-pipeline.yml`. O runtime executou `dry-run`, `run` e uma leitura do Parquet sintético.

## Pipeline declarativo

```bash
docker compose run --build --rm climatewatch spark-pipelines dry-run --spec /app/spark-pipeline.yml
docker compose run --build --rm climatewatch spark-pipelines run --spec /app/spark-pipeline.yml
CLIMATEWATCH_SILVER_FIXTURES=1 poetry run pytest -q tests/integration/test_silver_sql_fixtures.py
CLIMATEWATCH_F3_REPLAY=1 poetry run pytest -q tests/integration/test_pipeline_replay.py
```

O catálogo persistente fica em `data/warehouse/f3`. Consulte [arquitetura](docs/architecture.md) para o DAG, schemas, cobertura e consultas de inspeção. Os testes opt-in precisam de Docker.

## Backfill e retomada

```bash
poetry run python scripts/backfill_weather.py --start 2026-10-01 --end 2026-10-30
poetry run python scripts/resume_batches.py
```

O pipeline limita as janelas e requests, mantém cache/manifests/raw em diretórios locais ignorados pelo Git e registra cobertura no relatório configurado. Consulte `docs/runbook.md` para falhas e recuperação.

## Coleta real

```bash
poetry run climatewatch-download \
  --location-id br-sp-sao-paulo \
  --start 2024-01-01 --end 2024-01-01 \
  --variables temperature_2m,precipitation \
  --output /tmp/climatewatch-raw
```

O serviço gratuito da Open-Meteo tem termos de uso não comercial e atribuição CC BY 4.0; confira [termos atuais](https://open-meteo.com/en/terms) antes de usar/publicar. As fixtures em `data/fixtures` são sintéticas. Dados reais baixados não são versionados por padrão neste repositório.
