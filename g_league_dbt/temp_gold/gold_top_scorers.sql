{{ config(materialized="table") }}

SELECT
  player,
  season,
  team,
  SUM(pts) AS total_points,
  SUM(mp) AS total_minutes,
  ROUND(SUM(pts) / SUM(mp), 2) AS pts_per_min,
  ROUND(AVG(fg_percent), 3) AS avg_fg_percent,
  COUNT(*) AS lines
FROM {{ ref("bronze_player_totals") }}
GROUP BY player, season, team
ORDER BY total_points DESC
