{{ config(materialized='table') }}

SELECT
  season,
  SAFE_CAST(rank AS FLOAT64) AS rank,
  team,
  url,
  SAFE_CAST(gp AS INT64) AS gp,
  SAFE_CAST(w AS INT64) AS w,
  SAFE_CAST(l AS INT64) AS l,
  SAFE_CAST(win AS FLOAT64) AS win,
  SAFE_CAST(min AS FLOAT64) AS min,
  SAFE_CAST(pts AS FLOAT64) AS pts,
  SAFE_CAST(fgm AS FLOAT64) AS fgm,
  SAFE_CAST(fga AS FLOAT64) AS fga,
  SAFE_CAST(fg AS FLOAT64) AS fg,
  SAFE_CAST(col_0_625 AS FLOAT64) AS col_0_625,
  SAFE_CAST(`3pa` AS FLOAT64) AS `3pa`,
  SAFE_CAST(`3p` AS FLOAT64) AS `3p`,
  SAFE_CAST(ftm AS FLOAT64) AS ftm,
  SAFE_CAST(fta AS FLOAT64) AS fta,
  SAFE_CAST(ft AS FLOAT64) AS ft,
  SAFE_CAST(oreb AS FLOAT64) AS oreb,
  SAFE_CAST(dreb AS FLOAT64) AS dreb,
  SAFE_CAST(reb AS FLOAT64) AS reb,
  SAFE_CAST(ast AS FLOAT64) AS ast,
  SAFE_CAST(tov AS FLOAT64) AS tov,
  SAFE_CAST(stl AS FLOAT64) AS stl,
  SAFE_CAST(blk AS FLOAT64) AS blk,
  SAFE_CAST(blka AS FLOAT64) AS blka,
  SAFE_CAST(pf AS FLOAT64) AS pf,
  SAFE_CAST(pfd AS FLOAT64) AS pfd
FROM {{ source('bronze', 'team_stats_playoff') }}
WHERE team IS NOT NULL
