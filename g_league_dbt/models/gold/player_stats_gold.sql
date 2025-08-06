{{ config(
    materialized='table'
) }}

SELECT 
    player,
    player_id,
    season,
    team,
    pos,
    g as games_played,
    pts as total_points,
    ROUND(pts/g, 1) as points_per_game,
    trb as total_rebounds,
    ROUND(trb/g, 1) as rebounds_per_game,
    ast as total_assists,
    ROUND(ast/g, 1) as assists_per_game
FROM {{ ref('bronze_player_totals') }} 
WHERE g > 0