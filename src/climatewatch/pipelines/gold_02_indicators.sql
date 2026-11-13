CREATE MATERIALIZED VIEW gold_indicators AS
WITH rolling AS (
  SELECT location_id, source, model, timezone_name, local_time, observed_at_utc,
    sum(precipitation_mm) OVER w AS precipitation_24h_mm,
    avg(temperature_c) OVER w AS temperature_avg_24h_c,
    count(*) OVER w AS observed_hours_24h,
    count(precipitation_mm) OVER w AS precipitation_hours_24h,
    count(temperature_c) OVER w AS temperature_hours_24h
  FROM silver_observations
  WINDOW w AS (PARTITION BY location_id, source, model ORDER BY unix_timestamp(observed_at_utc)
    RANGE BETWEEN 82800 PRECEDING AND CURRENT ROW)
)
SELECT *, observed_hours_24h = 24 AND precipitation_hours_24h = 24
  AND temperature_hours_24h = 24 AS complete_24h_window
FROM rolling;

CREATE MATERIALIZED VIEW gold_daily_ranking AS
WITH eligible AS (
  SELECT *, dense_rank() OVER (
    PARTITION BY source, model, local_date, expected_hours
    ORDER BY precipitation_mm DESC NULLS LAST
  ) AS precipitation_rank
  FROM gold_daily
  WHERE NOT incomplete_day AND precipitation_mm IS NOT NULL
)
SELECT location_id, source, model, timezone_name, local_date, expected_hours,
  observed_hours, precipitation_mm, precipitation_rank
FROM eligible;
