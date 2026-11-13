"""Leitor limitado para as tabelas Gold materializadas pelo SDP."""

from datetime import date, datetime, time, timedelta
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit

GOLD_DAILY = "spark_catalog.climatewatch_f3.gold_daily"
GOLD_INDICATORS = "spark_catalog.climatewatch_f3.gold_indicators"
MAX_ROWS = 10_000


class GoldReader:
    """Consulta exclusivamente Gold, aplicando filtros antes do limite."""

    def __init__(self, spark: SparkSession, max_rows: int = MAX_ROWS) -> None:
        if not 1 <= max_rows <= MAX_ROWS:
            raise ValueError(f"max_rows deve estar entre 1 e {MAX_ROWS}")
        self._spark = spark
        self._max_rows = max_rows

    def daily(
        self, location_id: str, start: date, end: date
    ) -> list[dict[str, Any]]:
        """Retorna agregados diários locais em ordem, limitados a max_rows."""
        _validate_query(location_id, start, end)
        frame = self._table(GOLD_DAILY)
        if frame is None:
            return []
        rows = (
            frame.where(
                (col("location_id") == lit(location_id))
                & (col("local_date") >= lit(start))
                & (col("local_date") <= lit(end))
            )
            .orderBy("local_date", "source", "model")
            .limit(self._max_rows)
            .collect()
        )
        return [row.asDict(recursive=True) for row in rows]

    def indicators(
        self, location_id: str, start: date, end: date
    ) -> list[dict[str, Any]]:
        """Retorna indicadores Gold no período UTC, limitados a max_rows."""
        _validate_query(location_id, start, end)
        frame = self._table(GOLD_INDICATORS)
        if frame is None:
            return []
        start_at = datetime.combine(start, time.min)
        end_at = datetime.combine(end + timedelta(days=1), time.min)
        rows = (
            frame.where(
                (col("location_id") == lit(location_id))
                & (col("observed_at_utc") >= lit(start_at))
                & (col("observed_at_utc") < lit(end_at))
            )
            .orderBy("observed_at_utc", "source", "model")
            .limit(self._max_rows)
            .collect()
        )
        return [row.asDict(recursive=True) for row in rows]

    def _table(self, table: str) -> DataFrame | None:
        if not self._spark.catalog.tableExists(table):
            return None
        return self._spark.table(table)


def _validate_query(location_id: str, start: date, end: date) -> None:
    if not location_id.strip():
        raise ValueError("location_id não pode ser vazio")
    if end < start:
        raise ValueError("end deve ser igual ou posterior a start")
