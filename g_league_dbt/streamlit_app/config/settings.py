# streamlit_app/config/settings.py
import os

# Configuration BigQuery
PROJECT_ID = "carbide-bonsai-466217-v2"
DATASET_ID = "scouting_dbt_bronze_scouting_dbt_bronze_gold"
TABLE_ID = "player_stats_gold"

# Configuration Streamlit
PAGE_CONFIG = {
    "page_title": "G-League Scouting Platform",
    "page_icon": "🏀",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}