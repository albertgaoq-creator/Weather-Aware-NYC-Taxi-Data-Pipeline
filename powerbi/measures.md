# Recommended DAX Measures

```DAX
Trip Count =
SUM ( fct_hourly_demand[trip_count] )

Total Revenue =
SUM ( fct_fare_revenue[total_revenue_amount] )

Gross Fare =
SUM ( fct_fare_revenue[gross_fare_amount] )

Average Fare =
DIVIDE ( [Gross Fare], SUM ( fct_fare_revenue[trip_count] ) )

Average Revenue Per Trip =
DIVIDE ( [Total Revenue], SUM ( fct_fare_revenue[trip_count] ) )

Average Trip Distance =
AVERAGE ( fct_hourly_demand[avg_trip_distance] )

Average Trip Duration Min =
AVERAGE ( fct_hourly_demand[avg_trip_duration_min] )

Rush Hour Trip Count =
SUM ( fct_weather_impact[rush_hour_trip_count] )

Average Precipitation =
AVERAGE ( fct_weather_impact[avg_precipitation_mm] )

Average Temperature =
AVERAGE ( fct_weather_impact[avg_temperature_2m] )

Rain Trip Share =
DIVIDE (
    CALCULATE ( [Trip Count], dim_weather[weather_group] = "rain" ),
    [Trip Count]
)

Snow Trip Share =
DIVIDE (
    CALCULATE ( [Trip Count], dim_weather[weather_group] = "snow" ),
    [Trip Count]
)

Peak Hour Trip Count =
CALCULATE (
    [Trip Count],
    KEEPFILTERS ( dim_date_time[hour_of_day] IN { 7, 8, 9, 16, 17, 18, 19 } )
)

Off Peak Trip Count =
[Trip Count] - [Peak Hour Trip Count]
```

## KPI Cards

- Trip Count
- Total Revenue
- Average Fare
- Average Trip Duration Min
- Average Precipitation
- Rain Trip Share
