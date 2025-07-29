{{ config(materialized='table') }}

SELECT *
FROM {{ source('bronze', 'player_totals_2022_2024') }}
