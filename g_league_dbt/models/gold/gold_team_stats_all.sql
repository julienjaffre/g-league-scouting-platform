{{ config(materialized='table') }}

-- Partie saison régulière (pas de rank)
SELECT
  'regular' AS competition_type,
  season,
  NULL AS rank,  -- <--- ICI
  team,
  url,
  gp,
  w,
  l,
  win,
  min,
  pts,
  fgm,
  fga,
  fg,
  col_0_625,
  `3pa`,
  `3p`,
  ftm,
  fta,
  ft,
  oreb,
  dreb,
  reb,
  ast,
  tov,
  stl,
  blk,
  blka,
  pf,
  pfd
FROM {{ ref('gold_team_stats_regular') }}

UNION ALL

-- Partie playoffs (avec rank)
SELECT
  'playoff' AS competition_type,
  season,
  rank,
  team,
  url,
  gp,
  w,
  l,
  win,
  min,
  pts,
  fgm,
  fga,
  fg,
  col_0_625,
  `3pa`,
  `3p`,
  ftm,
  fta,
  ft,
  oreb,
  dreb,
  reb,
  ast,
  tov,
  stl,
  blk,
  blka,
  pf,
  pfd
FROM {{ ref('gold_team_stats_playoff') }}
