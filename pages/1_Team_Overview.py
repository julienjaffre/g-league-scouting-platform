import streamlit as st
import pandas as pd
import sys
import os
from google.cloud import bigquery

# Add the project root to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.bigquery_auth import get_bigquery_client, test_bigquery_connection

# === Page configuration ===
st.set_page_config(page_title="🏆 G-League Team Overview", layout="wide")

# === BigQuery connection ===
@st.cache_resource
def get_client():
    """Get cached BigQuery client"""
    return get_bigquery_client()

client = get_client()
if client:
    if test_bigquery_connection(client):
        st.success("✅ BigQuery connection successful!")
    else:
        st.error("❌ BigQuery connection test failed")

# === Query: seasons and competition types ===
@st.cache_data
def get_seasons_competitions():
    client = get_client()
    if not client:
        st.error("❌ Cannot connect to BigQuery. Please check authentication.")
        return [], []

    query = """
        SELECT DISTINCT season, competition_type
        FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.gold_team_stats_all`
        ORDER BY season DESC, competition_type
    """

    try:
        df = client.query(query).to_dataframe()
        seasons = df['season'].unique()
        competitions = df['competition_type'].unique()
        return seasons, competitions
    except Exception as e:
        st.error(f"❌ Query failed: {str(e)}")
        return [], []

# === Query: team stats per season/competition ===
@st.cache_data
def get_team_stats(season, competition_type):
    client = get_client()
    if not client:
        st.error("❌ Cannot connect to BigQuery. Please check authentication.")
        return pd.DataFrame()

    query = f"""
        SELECT *
        FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.gold_team_stats_all`
        WHERE season = @season AND competition_type = @competition_type
        ORDER BY win DESC
    """

    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("season", "STRING", season),
                bigquery.ScalarQueryParameter("competition_type", "STRING", competition_type),
            ]
        )
        return client.query(query, job_config=job_config).to_dataframe()
    except Exception as e:
        st.error(f"❌ Query failed: {str(e)}")
        return pd.DataFrame()

# === UI Filters ===
st.title("🏆 G-League Team Overview")

# SIDEBAR with filters and glossary
st.sidebar.header("🏆 Team Filters")

# Add basic filters in sidebar instead of main area
seasons, competitions = get_seasons_competitions()

if len(seasons) > 0 and len(competitions) > 0:
    # Move season/competition selectors to sidebar
    st.sidebar.subheader("Season & Competition")
    selected_season = st.sidebar.selectbox(
        "Season",
        seasons,
        help="Select the season year to analyze team performance"
    )
    selected_comp = st.sidebar.selectbox(
        "Competition Type",
        competitions,
        help="Choose between regular season, playoffs, or other competition types"
    )

    # SIDEBAR GLOSSARY (adapted for team stats)
    st.sidebar.markdown("---")
    with st.sidebar.expander("📚 Team Stats Glossary"):
        st.markdown("""
        **Team Performance Stats:**
        - **WIN** = Total wins in the season
        - **GP** = Games played
        - **PTS** = Average points scored per game
        - **AST** = Average assists per game (team playmaking)
        - **REB** = Average rebounds per game (team rebounding)
        - **FG%** = Field goal percentage (shooting accuracy)
        - **3P%** = Three-point percentage
        - **FT%** = Free throw percentage

        **Advanced Team Metrics:**
        - **OFF RTG** = Offensive rating (points per 100 possessions)
        - **DEF RTG** = Defensive rating (points allowed per 100 possessions)
        - **NET RTG** = Net rating (offensive - defensive rating)
        - **PACE** = Possessions per 48 minutes (game tempo)

        **Competition Types:**
        - **Regular Season** = Standard league games
        - **Playoffs** = Post-season elimination games
        - **Tournament** = Special competition format

        **How to Use:**
        - Compare teams across different statistical categories
        - Higher offensive stats = better scoring teams
        - Lower defensive stats = better defensive teams
        - Net rating is often the best overall team metric
        """)

    # Remove the old column-based selectors and replace with sidebar versions
    # The rest of your code stays the same, but remove this section:
    # col1, col2 = st.columns(2)
    # with col1:
    #     selected_season = st.selectbox("Season", seasons)
    # with col2:
    #     selected_comp = st.selectbox("Competition Type", competitions)

    # === Load filtered data ===
    df = get_team_stats(selected_season, selected_comp)

    if not df.empty:
        # === Main table ===
        st.subheader(f"📊 Team Statistics – {selected_season} ({selected_comp})")
        st.dataframe(df, use_container_width=True)

        # === Visual comparison ===
        st.subheader("📈 Visual Comparison Between Teams")

        numeric_cols = [col for col in df.columns if df[col].dtype in ['float64', 'int64'] and col not in ['gp']]

        if len(numeric_cols) > 0:
            cols_to_plot = st.multiselect(
                "Choose stats to compare",
                numeric_cols,
                default=["win", "pts", "ast", "reb"] if all(col in numeric_cols for col in ["win", "pts", "ast", "reb"]) else numeric_cols[:4]
            )
            teams_selected = st.multiselect(
                "Filter by teams",
                options=df["team"].unique(),
                default=list(df["team"].unique())
            )

            df_comp = df[df["team"].isin(teams_selected)]
            if not df_comp.empty and cols_to_plot:
                st.bar_chart(df_comp.set_index("team")[cols_to_plot])
            else:
                st.info("Select at least one team and one statistic.")
        else:
            st.info("No numeric columns found for visualization.")
    else:
        st.warning("No data found for this season and competition type.")
else:
    st.error("Failed to load seasons and competition types.")
