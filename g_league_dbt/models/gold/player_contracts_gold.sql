WITH stats_raw AS (
    SELECT
        player,
        season,
        team,
        pos,
        age,
        g,
        CASE
            WHEN (fga_per_game + 0.44 * fta_per_game) > 0
            THEN pts_per_game / (2 * (fga_per_game + 0.44 * fta_per_game))
            ELSE NULL
        END AS ts_pct,
        pts_per_game AS pts,
        trb_per_game AS trb,
        ast_per_game AS ast,
        stl_per_game AS stl,
        blk_per_game AS blk,
        ROW_NUMBER() OVER (
            PARTITION BY player
            ORDER BY
                g DESC,
                pts_per_game DESC,
                CASE WHEN team LIKE '%TM' THEN 1 ELSE 0 END
        ) as rn
    FROM {{ source('raw_nba_data', 'player_per_game_2022_2024') }}
    WHERE season = 2024
),

stats AS (
    SELECT
        player AS Player,
        season AS Season,
        team AS Team,
        pos AS Pos,
        age AS Age,
        ts_pct,
        pts,
        trb,
        ast,
        stl,
        blk
    FROM stats_raw
    WHERE rn = 1
),

contracts AS (
    SELECT
        player,
        team,
        `202526`, `202627`, `202728`, `202829`, `202930`, `203031`,
        guaranteed,
        uncontracted
    FROM {{ source('raw_nba_data', 'nba_contracts_complete') }}
),

joined AS (
    SELECT
        s.*,
        c.`202526`, c.`202627`, c.`202728`, c.`202829`, c.`202930`, c.`203031`,
        c.guaranteed,
        c.uncontracted,
        CASE
            WHEN c.player IS NULL THEN 'Free Agent / No Contract Data'
            WHEN c.uncontracted = TRUE THEN 'Uncontracted'
            WHEN COALESCE(c.`202526`, 0) = 0 AND COALESCE(c.`202627`, 0) = 0 THEN 'Free Agent'
            WHEN COALESCE(c.`202627`, 0) = 0 AND COALESCE(c.`202526`, 0) > 0 THEN 'Expiring Contract'
            WHEN COALESCE(c.`202627`, 0) > 0 AND COALESCE(c.`202728`, 0) = 0 THEN '1 Year Left'
            ELSE 'Multi-Year Contract'
        END AS contract_status
    FROM stats s
    LEFT JOIN contracts c ON (
        LOWER(TRIM(s.Player)) = LOWER(TRIM(c.player))
        OR LOWER(REGEXP_REPLACE(TRIM(s.Player), r'[.\s]+', ' ')) =
           LOWER(REGEXP_REPLACE(TRIM(c.player), r'[.\s]+', ' '))
        OR LOWER(REGEXP_REPLACE(NORMALIZE(TRIM(s.Player), NFD), r'[^\w\s]', '')) =
           LOWER(REGEXP_REPLACE(NORMALIZE(TRIM(c.player), NFD), r'[^\w\s]', ''))
    )
),

player_percentiles AS (
    SELECT
        *,
        -- Position-adjusted percentiles
        NTILE(100) OVER (PARTITION BY Pos ORDER BY pts) AS pts_percentile,
        NTILE(100) OVER (PARTITION BY Pos ORDER BY trb) AS trb_percentile,
        NTILE(100) OVER (PARTITION BY Pos ORDER BY ast) AS ast_percentile,
        NTILE(100) OVER (PARTITION BY Pos ORDER BY stl) AS stl_percentile,
        NTILE(100) OVER (PARTITION BY Pos ORDER BY blk) AS blk_percentile,
        -- Overall efficiency
        NTILE(100) OVER (ORDER BY ts_pct) AS ts_percentile
    FROM joined
    WHERE ts_pct IS NOT NULL
),

final_classification AS (
    SELECT *,
        CASE
            WHEN (pts_percentile BETWEEN 0 AND 25
                  OR trb_percentile BETWEEN 0 AND 25
                  OR ast_percentile BETWEEN 0 AND 25)
                 AND contract_status IN ('Free Agent / No Contract Data', 'Expiring Contract', 'Uncontracted', 'Free Agent')
                 AND age <= 28
            THEN 'NBA Struggling / G-League Potential'

            WHEN (pts_percentile BETWEEN 25 AND 75
                  AND trb_percentile BETWEEN 25 AND 75
                  AND ast_percentile BETWEEN 25 AND 75
                  AND ts_percentile BETWEEN 25 AND 75)
                 AND contract_status IN ('Free Agent / No Contract Data', 'Expiring Contract', 'Uncontracted', 'Free Agent')
                 AND age <= 28
            THEN 'Well-Rounded Average'

            ELSE 'Not G-League Target'
        END AS g_league_category
    FROM player_percentiles
)

SELECT *
FROM final_classification
WHERE g_league_category != 'Not G-League Target'
