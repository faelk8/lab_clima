"""Pipeline mínimo para validar o runtime SDP sem dados externos."""

from pyspark import pipelines as dp
from pyspark.sql import SparkSession


@dp.materialized_view
def smoke_values():
    """Publica valores fixos para smoke test de execução e persistência."""
    spark = SparkSession.builder.getOrCreate()
    return spark.createDataFrame([(1, "ok")], ["id", "status"])
