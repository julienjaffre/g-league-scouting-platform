{{ config(materialized='table') }}

SELECT *
FROM {{ source('bronze', 'team_stats_regular_clean') }}
