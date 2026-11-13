CREATE MATERIALIZED VIEW silver_quality AS
WITH flagged AS (
  SELECT *, filter(array(
    CASE WHEN malformed_payload THEN 'invalid_json_or_hourly_schema' END,
    CASE WHEN location_id IS NULL THEN 'missing_location_id' END,
    CASE WHEN source IS NULL THEN 'missing_source' END,
    CASE WHEN requested IS NULL OR size(requested) = 0 THEN 'missing_requested_variables' END,
    CASE WHEN local_time IS NULL OR observed_at_utc IS NULL THEN 'invalid_measurement_time' END,
    CASE WHEN time_count IS NULL THEN 'missing_time_array' END,
    CASE WHEN array_contains(requested, 'temperature_2m') AND coalesce(temperature_count <> time_count, true) THEN 'misaligned_temperature_array' END,
    CASE WHEN array_contains(requested, 'precipitation') AND coalesce(precipitation_count <> time_count, true) THEN 'misaligned_precipitation_array' END,
    CASE WHEN array_contains(requested, 'relative_humidity_2m') AND coalesce(humidity_count <> time_count, true) THEN 'misaligned_humidity_array' END,
    CASE WHEN array_contains(requested, 'wind_speed_10m') AND coalesce(wind_count <> time_count, true) THEN 'misaligned_wind_array' END,
    CASE WHEN array_contains(requested, 'temperature_2m') AND coalesce(temperature_unit NOT IN ('°C', '°F'), true) THEN 'invalid_temperature_unit' END,
    CASE WHEN array_contains(requested, 'precipitation') AND coalesce(precipitation_unit NOT IN ('mm', 'inch'), true) THEN 'invalid_precipitation_unit' END,
    CASE WHEN array_contains(requested, 'relative_humidity_2m') AND coalesce(humidity_unit <> '%', true) THEN 'invalid_humidity_unit' END,
    CASE WHEN array_contains(requested, 'wind_speed_10m') AND coalesce(wind_unit NOT IN ('km/h', 'm/s', 'mph', 'kn'), true) THEN 'invalid_wind_unit' END,
    CASE WHEN array_contains(requested, 'temperature_2m') AND temperature_c IS NULL THEN 'missing_temperature' END,
    CASE WHEN array_contains(requested, 'precipitation') AND precipitation_mm IS NULL THEN 'missing_precipitation' END,
    CASE WHEN array_contains(requested, 'relative_humidity_2m') AND humidity_pct IS NULL THEN 'missing_humidity' END,
    CASE WHEN array_contains(requested, 'wind_speed_10m') AND wind_speed_kmh IS NULL THEN 'missing_wind_speed' END,
    CASE WHEN precipitation_mm < 0 THEN 'negative_precipitation' END,
    CASE WHEN humidity_pct < 0 OR humidity_pct > 100 THEN 'humidity_out_of_range' END
  ), flag -> flag IS NOT NULL) AS quality_flags
  FROM silver_expanded
)
SELECT * FROM flagged;
