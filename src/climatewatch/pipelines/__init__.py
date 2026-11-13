"""Declarative pipeline entry points for ClimateWatch.

The configured SDP graph is deliberately local: pipeline definitions must not
perform HTTP requests. External collection remains in the downloader layer.
"""

from pyspark import pipelines as dp
from pyspark.sql import DataFrame, SparkSession


@dp.materialized_view
def smoke_values() -> DataFrame:
    """Fixed values used to validate the pinned SDP runtime without HTTP."""
    spark = SparkSession.builder.getOrCreate()
    return spark.createDataFrame([(1, "ok")], ["id", "status"])
