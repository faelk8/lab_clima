"""Bronze pipeline: cópia imutável dos objetos raw com proveniência."""

from pyspark import pipelines as dp
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, get_json_object, regexp_extract, struct, to_json

RAW_PATH = "/app/data/raw/*/*.json"
SIDECAR_PATH = "/app/data/raw/*/*.manifest.json"


@dp.materialized_view
def bronze_raw() -> DataFrame:
    """Materializa bytes raw e campos de linhagem; nenhuma chamada HTTP é feita."""
    spark = SparkSession.active()
    raw = (
        spark.read.format("binaryFile")
        .load(RAW_PATH)
        .where(~col("path").endswith(".manifest.json"))
        .select(
            regexp_extract(col("path"), r"([^/]+)\.json$", 1).alias("sha256"),
            col("path").alias("raw_path"),
            col("content").alias("payload"),
        )
    )
    sidecars = (
        spark.read.format("binaryFile")
        .load(SIDECAR_PATH)
        .select(col("content").cast("string").alias("manifest_json"))
        .select(
            get_json_object("manifest_json", "$.sha256").alias("sha256"),
            get_json_object("manifest_json", "$.source").alias("source"),
            get_json_object("manifest_json", "$.batch_id").alias("batch_id"),
            get_json_object("manifest_json", "$.location_id").alias("location_id"),
            get_json_object("manifest_json", "$.timezone_name").alias("timezone_name"),
            get_json_object("manifest_json", "$.latitude").cast("double").alias("latitude"),
            get_json_object("manifest_json", "$.longitude").cast("double").alias("longitude"),
            get_json_object("manifest_json", "$.variables").alias("variables_json"),
            to_json(
                struct(
                    get_json_object("manifest_json", "$.location_id").alias("location_id"),
                    get_json_object("manifest_json", "$.start").alias("start"),
                    get_json_object("manifest_json", "$.end").alias("end"),
                    get_json_object("manifest_json", "$.timezone_name").alias("timezone_name"),
                    get_json_object("manifest_json", "$.variables").alias("variables"),
                )
            ).alias("params_json"),
            get_json_object("manifest_json", "$.ingested_at").alias("ingested_at"),
        )
    )
    return (
        raw.join(sidecars, on="sha256", how="inner")
        .select(
            "payload",
            "sha256",
            "source",
            "batch_id",
            "location_id",
            "timezone_name",
            "latitude",
            "longitude",
            "variables_json",
            "params_json",
            "ingested_at",
            "raw_path",
        )
    )
