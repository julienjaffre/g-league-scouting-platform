-- models/gold/dim_player_career_stats.sql
{{ config(materialized='table') }}

SELECT 
    player,
    player_id,
    COUNT(DISTINCT season) as seasons_played,
    COUNT(DISTINCT team) as teams_played_for,
    SUM(g) as total_games,
    SUM(gs) as total_games_started,
    ROUND(AVG(pts), 1) as avg_points_per_game,
    ROUND(AVG(trb), 1) as avg_rebounds_per_game,
    ROUND(AVG(ast), 1) as avg_assists_per_game,
    ROUND(AVG(fg_percent), 3) as avg_field_goal_pct,
    ROUND(AVG(x3p_percent), 3) as avg_three_point_pct,
    ROUND(AVG(ft_percent), 3) as avg_free_throw_pct,
    SUM(trp_dbl) as total_triple_doubles,
    MIN(age) as age_first_season,
    MAX(age) as age_last_season
FROM {{ source('bronze', 'player_totals_2022_2024') }}
GROUP BY player, player_id