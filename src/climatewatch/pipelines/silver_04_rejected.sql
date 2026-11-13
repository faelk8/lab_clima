CREATE MATERIALIZED VIEW silver_rejected AS
SELECT location_id, source, model, sha256, batch_id, ingested_at, timezone_name,
       local_time, observed_at_utc, temperature_c, precipitation_mm, humidity_pct,
       wind_speed_kmh, quality_flags
FROM silver_quality
WHERE size(quality_flags) > 0;
