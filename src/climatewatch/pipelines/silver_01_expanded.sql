CREATE MATERIALIZED VIEW silver_expanded AS
WITH decoded AS (
  SELECT
    payload, sha256, source, batch_id, location_id, timezone_name,
    variables_json, ingested_at,
    from_json(CAST(payload AS STRING), 'STRUCT<model:STRING,hourly_units:STRUCT<temperature_2m:STRING,precipitation:STRING,relative_humidity_2m:STRING,wind_speed_10m:STRING>,hourly:STRUCT<time:ARRAY<STRING>,temperature_2m:ARRAY<DOUBLE>,precipitation:ARRAY<DOUBLE>,relative_humidity_2m:ARRAY<DOUBLE>,wind_speed_10m:ARRAY<DOUBLE>>>') AS body,
    from_json(variables_json, 'ARRAY<STRING>') AS requested
  FROM bronze_raw
), arrays AS (
  SELECT *, body.hourly.time AS time_arr,
    CASE WHEN array_contains(requested, 'temperature_2m') THEN coalesce(body.hourly.temperature_2m, transform(body.hourly.time, x -> CAST(NULL AS DOUBLE))) ELSE transform(body.hourly.time, x -> CAST(NULL AS DOUBLE)) END AS temperature_arr,
    CASE WHEN array_contains(requested, 'precipitation') THEN coalesce(body.hourly.precipitation, transform(body.hourly.time, x -> CAST(NULL AS DOUBLE))) ELSE transform(body.hourly.time, x -> CAST(NULL AS DOUBLE)) END AS precipitation_arr,
    CASE WHEN array_contains(requested, 'relative_humidity_2m') THEN coalesce(body.hourly.relative_humidity_2m, transform(body.hourly.time, x -> CAST(NULL AS DOUBLE))) ELSE transform(body.hourly.time, x -> CAST(NULL AS DOUBLE)) END AS humidity_arr,
    CASE WHEN array_contains(requested, 'wind_speed_10m') THEN coalesce(body.hourly.wind_speed_10m, transform(body.hourly.time, x -> CAST(NULL AS DOUBLE))) ELSE transform(body.hourly.time, x -> CAST(NULL AS DOUBLE)) END AS wind_arr
  FROM decoded
), normalized AS (
  SELECT *, arrays_zip(time_arr, temperature_arr, precipitation_arr, humidity_arr, wind_arr) AS zipped
  FROM arrays
)
SELECT
  location_id, source, coalesce(body.model, 'unspecified') AS model,
  sha256, batch_id, ingested_at, timezone_name, requested,
  size(body.hourly.time) AS time_count,
  size(body.hourly.temperature_2m) AS temperature_count,
  size(body.hourly.precipitation) AS precipitation_count,
  size(body.hourly.relative_humidity_2m) AS humidity_count,
  size(body.hourly.wind_speed_10m) AS wind_count,
  body.hourly_units.temperature_2m AS temperature_unit,
  body.hourly_units.precipitation AS precipitation_unit,
  body.hourly_units.relative_humidity_2m AS humidity_unit,
  body.hourly_units.wind_speed_10m AS wind_unit,
  item.time_arr AS local_time,
  to_utc_timestamp(try_to_timestamp(item.time_arr), timezone_name) AS observed_at_utc,
  item.temperature_arr AS temperature_c,
  item.precipitation_arr AS precipitation_mm,
  item.humidity_arr AS humidity_pct,
  item.wind_arr AS wind_speed_kmh,
  body IS NULL OR body.hourly IS NULL AS malformed_payload
FROM normalized
LATERAL VIEW OUTER explode(zipped) exploded AS item;
