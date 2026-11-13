CREATE MATERIALIZED VIEW silver_observations AS
WITH accepted AS (
  SELECT
    location_id, source, model, sha256, batch_id, ingested_at, timezone_name,
    local_time, observed_at_utc,
    CASE temperature_unit WHEN '°F' THEN (temperature_c - 32.0) * 5.0 / 9.0 ELSE temperature_c END AS temperature_c,
    CASE precipitation_unit WHEN 'inch' THEN precipitation_mm * 25.4 ELSE precipitation_mm END AS precipitation_mm,
    humidity_pct,
    CASE wind_unit WHEN 'm/s' THEN wind_speed_kmh * 3.6 WHEN 'mph' THEN wind_speed_kmh * 1.609344 WHEN 'kn' THEN wind_speed_kmh * 1.852 ELSE wind_speed_kmh END AS wind_speed_kmh
  FROM silver_quality
  WHERE size(quality_flags) = 0
), ranked AS (
  SELECT *, row_number() OVER (
    PARTITION BY location_id, observed_at_utc, source, model
    ORDER BY ingested_at DESC NULLS LAST, sha256 DESC, batch_id DESC
  ) AS duplicate_rank
  FROM accepted
)
SELECT location_id, source, model, sha256, batch_id, ingested_at, timezone_name,
       local_time, observed_at_utc, temperature_c, precipitation_mm, humidity_pct, wind_speed_kmh
FROM ranked
WHERE duplicate_rank = 1;
