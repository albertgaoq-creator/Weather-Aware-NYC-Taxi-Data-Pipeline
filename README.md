# Weather-Aware NYC Taxi Data Pipeline

This project builds on the original Uber/Taxi ETL tutorial and turns it into something more useful: a practical analytics pipeline for understanding how weather changes taxi behavior in New York City.

Instead of only tracking trip counts, fares, and pickup/dropoff patterns, we focus on questions like:

- How much do rain and snow change trip demand?
- Do bad weather conditions increase average fare or trip duration?
- Are some boroughs more weather-sensitive than others?
- How does weather interact with rush-hour demand?

---

## Project Goal

Move from a basic ETL demo to an analysis-ready pipeline that supports real business questions with clear metrics and reproducible data modeling.

---

## Data Sources

### 1) NYC Taxi Trips

Use TLC Yellow Taxi monthly parquet files first (Green/FHV can be added later).

Typical fields:
- `pickup_datetime`
- `dropoff_datetime`
- `PULocationID`
- `DOLocationID`
- `trip_distance`
- `fare_amount`
- `tip_amount`
- `total_amount`
- `passenger_count`

### 2) Historical Weather (Open-Meteo Archive API)

Weather data comes from `archive-api.open-meteo.com`.

Key query parameters:
- `latitude`, `longitude`
- `start_date`, `end_date`
- `hourly=temperature_2m,precipitation,rain,snowfall,windspeed_10m,weathercode`
- `timezone=America/New_York`

Example request:

```bash
curl "https://archive-api.open-meteo.com/v1/archive?latitude=40.7831&longitude=-73.9712&start_date=2023-01-01&end_date=2023-01-31&hourly=temperature_2m,precipitation,rain,snowfall,windspeed_10m,weathercode&timezone=America/New_York"
```

Tip: request weather by borough anchor points and cache responses locally so reruns do not hammer the API.

---

## Pipeline Design

### 1) Ingestion

- `taxi_ingest`: load NYC taxi monthly data (partition by `year/month`)
- `weather_ingest`: call Open-Meteo Archive API at hourly grain (partition by `date/borough`)
- Save untouched source payloads in raw storage (`data/raw/` or object storage bucket)

### 2) Staging (Cleaning + Standardization)

#### Taxi staging
- Convert timestamps to `America/New_York`
- Remove obvious bad records:
  - `trip_duration <= 0`
  - `fare_amount < 0`
  - extreme outliers (for example, cap at P99/P99.5)
- Add derived columns:
  - `trip_duration_min`
  - `pickup_hour`
  - `pickup_date`
  - `day_of_week`
  - `is_weekend`

#### Weather staging
- Standardized hourly columns:
  - `weather_ts_hour`
  - `temperature_2m`
  - `precipitation_mm`
  - `rain_mm`
  - `snowfall_cm`
  - `wind_speed`
- Add weather flags:
  - `is_rain` (`rain_mm > 0`)
  - `is_snow` (`snowfall_cm > 0`)
  - `weather_severity` (`clear/light/moderate/severe`)

### 3) Integration (Join Taxi + Weather)

Suggested join keys:
- Time key: align `pickup_ts` to hourly `pickup_hour`
- Location key: map `PULocationID -> borough`
- Weather key: `borough + weather_ts_hour`

Output table:
- `fact_trip_weather_hourly`

Depending on use case, either:
- keep trip-level rows with matched weather, or
- pre-aggregate to `hour x borough` for BI/dashboard speed

---

## Recommended Data Model (Star Schema)

- `fact_trip_weather`
- `dim_datetime`
- `dim_location` (borough, zone)
- `dim_weather_condition` (weathercode + severity)

Core metrics:
- `trip_count`
- `avg_fare`
- `avg_trip_duration_min`
- `avg_speed` (optional, distance / duration)
- `surge_proxy` (optional, e.g., fare per mile or high-percentile fare)

---

## Analysis Questions to Implement in SQL

### Q1. Rain/Snow impact on trip volume
- Grain: `borough x hour` or `borough x day`
- Compare: clear vs rain vs snow
- Output: `trip_count_diff_pct`

### Q2. Does severe weather raise fare/duration?
- Group by: `weather_severity`
- Metrics: `avg_fare`, `avg_trip_duration_min`
- Controls: `hour_of_day`, `borough`, `weekday/weekend`

### Q3. Borough-level weather sensitivity
- Model idea:
  - `demand ~ precipitation + snowfall + temperature + fixed_effects`
- Output: `sensitivity_rank`

### Q4. Rush hour × weather interaction
- Rush-hour windows: `7-10`, `16-20`
- Interaction terms:
  - `is_rush_hour * is_rain`
  - `is_rush_hour * is_snow`
- Check whether interaction effects are meaningful

---

## Dashboard Suggestions

1. **Weather vs Demand Timeline**
   - Show `trip_count` and `precipitation` together (single or dual axis)
2. **Borough Sensitivity Heatmap**
   - Rows: borough
   - Columns: weather category
   - Values: demand change rate
3. **Rush-Hour Interaction Chart**
   - Compare peak-hour demand under clear/rain/snow
4. **Fare & Duration Box Plots**
   - Show distribution shifts across weather conditions

---

## Suggested Repository Layout

```text
.
├── data/
│   ├── raw/
│   │   ├── taxi/
│   │   └── weather/
│   └── curated/
├── pipelines/
│   ├── ingest_taxi.py
│   ├── ingest_weather_open_meteo.py
│   ├── transform_trip_weather.py
│   └── build_marts.py
├── sql/
│   ├── marts/
│   └── analysis/
└── dashboard/
```

---

## Orchestration and Data Quality

Example DAG flow:
- `DAG 1`: `taxi_ingest -> taxi_stage`
- `DAG 2`: `weather_ingest -> weather_stage`
- `DAG 3`: `join_trip_weather -> marts -> BI refresh`

Suggested quality checks:
- `not_null` on time and location keys
- `accepted_range` for fare, duration, temperature
- weather data freshness threshold
- daily trip-count anomaly detection

---

## Rollout Plan

### Phase 1 (1-2 days)
- Integrate Open-Meteo Archive API
- Build `hour x borough` joined dataset
- Deliver one working dashboard page

### Phase 2 (3-5 days)
- Add borough weather-sensitivity analysis
- Add rush-hour interaction metrics
- Add monitoring and quality gates

### Phase 3 (optional)
- Add weather forecast source for short-term demand forecasting
- Add extreme-weather event analysis (snowstorms, heavy rain)

---

## Fastest Way to Start

1. Run one month first (for example: `2023-01`)
2. Limit scope to Manhattan + Brooklyn for the PoC
3. Build three charts first:
   - `trip_count vs precipitation`
   - `avg_fare by weather_type`
   - `rush_hour interaction`

This is usually enough to validate whether weather adds real analytical value beyond a standard ETL tutorial.
