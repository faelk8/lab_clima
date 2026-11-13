CREATE MATERIALIZED VIEW gold_daily AS
WITH local_rows AS (
  SELECT *, to_date(local_time) AS local_date
  FROM silver_observations
), grouped AS (
  SELECT location_id, source, model, timezone_name, local_date,
    count(*) AS observed_hours,
    count(DISTINCT observed_at_utc) AS distinct_hours,
    sum(precipitation_mm) AS precipitation_mm,
    avg(temperature_c) AS temperature_avg_c,
    max(temperature_c) AS temperature_max_c,
    min(observed_at_utc) AS first_observed_at_utc,
    max(observed_at_utc) AS last_observed_at_utc
  FROM local_rows
  GROUP BY location_id, source, model, timezone_name, local_date
)
SELECT *,
  CAST((unix_timestamp(to_utc_timestamp(CAST(date_add(local_date, 1) AS TIMESTAMP), timezone_name))
      - unix_timestamp(to_utc_timestamp(CAST(local_date AS TIMESTAMP), timezone_name))) / 3600 AS INT) AS expected_hours,
  distinct_hours < CAST((unix_timestamp(to_utc_timestamp(CAST(date_add(local_date, 1) AS TIMESTAMP), timezone_name))
      - unix_timestamp(to_utc_timestamp(CAST(local_date AS TIMESTAMP), timezone_name))) / 3600 AS INT) AS incomplete_day
FROM grouped;
