{{ config(materialized='table') }}

SELECT *
FROM {{ ref('bronze_kaggle_game') }}
WHERE season_id = 2023
