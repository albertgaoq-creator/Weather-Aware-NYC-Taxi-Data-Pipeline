# Dashboard Specification

## Page 1: Hourly Demand Dashboard

### Goal

Show how trip demand changes by hour, day, and peak period.

### Visuals

- Line chart: `dim_date_time[hour_ts]` vs `Trip Count`
- Heatmap or matrix: `weekday_name` by `hour_of_day` with `Trip Count`
- Clustered column chart: `Peak Hour Trip Count` vs `Off Peak Trip Count`
- KPI cards: `Trip Count`, `Average Fare`, `Average Trip Duration Min`

### Filters

- Date range
- Borough
- Weather severity

## Page 2: Location-Based Mobility Trends

### Goal

Show where demand and revenue concentrate.

### Visuals

- Bar chart: top 15 pickup zones by `Trip Count`
- Bar chart: top 15 pickup zones by `Total Revenue`
- Filled map or shape map: borough or zone-level `Trip Count`
- Table: `zone`, `Trip Count`, `Average Fare`, `Total Revenue`

### Filters

- Date range
- Borough
- Payment type

## Page 3: Weather Impact Analysis

### Goal

Show how weather changes demand, fares, and trip behavior.

### Visuals

- Combo chart: `Trip Count` with `Average Precipitation` by hour
- Column chart: `weather_severity` vs `Trip Count`
- Column chart: `weather_severity` vs `Average Fare`
- Scatter chart: `Average Precipitation` vs `Trip Count`, color by borough
- Matrix: borough by weather severity with `Trip Count` and `Average Trip Duration Min`

### Filters

- Date range
- Hour of day
- Borough
- Weather group

## Field Mapping Guidance

- Use `fct_hourly_demand` for trend and hourly visuals.
- Use `fct_fare_revenue` for revenue and fare visuals.
- Use `fct_weather_impact` for weather comparison visuals.
- Use `dim_location` to slice by borough and zone.
- Use `dim_date_time` for all calendar and hourly filters.
- Use `dim_weather` for rain, snow, clear, and severity filters.
