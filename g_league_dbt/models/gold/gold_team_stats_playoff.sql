{{ config(materialized='table') }}

SELECT *
FROM {{ ref('bronze_team_stats_playoff') }}
WHERE season IS NOT NULL
