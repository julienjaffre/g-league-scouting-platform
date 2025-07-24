{{ config(materialized='table') }}

SELECT
  team_id,
  COUNT(*) AS total_games
FROM (
  SELECT team_id_home AS team_id FROM {{ ref('silver_kaggle_game_filtered') }}
  UNION ALL
  SELECT team_id_away AS team_id FROM {{ ref('silver_kaggle_game_filtered') }}
)
GROUP BY team_id
ORDER BY total_games DESC
