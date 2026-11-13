# ClimateWatch — laboratório de dados climáticos

Projeto experimental local para coletar dados históricos abertos, preservar proveniência e validar um pipeline com Apache Spark Declarative Pipelines (SDP). Não é um alerta oficial nem uma previsão de enchentes.

## Estado

Fase 1 implementada e testada localmente. A Fase 2 ainda não foi iniciada. Consulte [contratos de dados](docs/data-contracts.md), [fontes e licenças](docs/sources-and-licenses.md) e [evidências da Fase 1](docs/evidence/F1-09.md).

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

A imagem usa PySpark 4.1.0 com o extra oficial `pipelines`. A configuração do smoke está em `spark-pipeline.yml`. O runtime executou `dry-run`, `run` e uma leitura do Parquet sintético nesta fase.

## Coleta real

```bash
poetry run climatewatch-download \
  --location-id br-sp-sao-paulo \
  --start 2024-01-01 --end 2024-01-01 \
  --variables temperature_2m,precipitation \
  --output /tmp/climatewatch-raw
```

O serviço gratuito da Open-Meteo tem termos de uso não comercial e atribuição CC BY 4.0; confira [termos atuais](https://open-meteo.com/en/terms) antes de usar/publicar. As fixtures em `data/fixtures` são sintéticas. Dados reais baixados não são versionados por padrão neste repositório.
