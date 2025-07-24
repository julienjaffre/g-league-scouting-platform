{{ config(materialized='table') }}

SELECT *
FROM {{ source('bronze', 'kaggle_game_2021_2024') }}
