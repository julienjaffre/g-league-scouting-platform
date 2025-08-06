# pages/vue_equipes.py

import streamlit as st
from google.cloud import bigquery
import pandas as pd

# === Configuration de la page ===
st.set_page_config(page_title="Vue d'Ensemble des Équipes G-League", layout="wide")

# === Connexion BigQuery ===
client = bigquery.Client(location="US")  # Modifie si ta table est ailleurs

# === Requête : saisons et types de compétition ===
@st.cache_data
def get_seasons_competitions():
    query = """
        SELECT DISTINCT season, competition_type
        FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.gold_team_stats_all`
        ORDER BY season DESC, competition_type
    """
    df = client.query(query).to_dataframe()
    seasons = df['season'].unique()
    competitions = df['competition_type'].unique()
    return seasons, competitions

# === Requête : stats par équipe pour une saison/type compétition ===
@st.cache_data
def get_team_stats(season, competition_type):
    query = f"""
        SELECT *
        FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.gold_team_stats_all`
        WHERE season = @season AND competition_type = @competition_type
        ORDER BY win DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("season", "STRING", season),
            bigquery.ScalarQueryParameter("competition_type", "STRING", competition_type),
        ]
    )
    return client.query(query, job_config=job_config).to_dataframe()

# === UI Filtres ===
st.title("🏆 Vue d’Ensemble des Équipes G-League")

seasons, competitions = get_seasons_competitions()
col1, col2 = st.columns(2)
with col1:
    selected_season = st.selectbox("Saison", seasons)
with col2:
    selected_comp = st.selectbox("Type de compétition", competitions)

# === Chargement des données filtrées ===
df = get_team_stats(selected_season, selected_comp)

# === Tableau principal ===
st.subheader(f"📊 Statistiques par équipe – {selected_season} ({selected_comp})")
st.dataframe(df, use_container_width=True)

# === Comparaison visuelle ===
st.subheader("📈 Comparaison visuelle entre équipes")
# Liste des colonnes numériques (hors gp, si pas pertinent)
cols_to_plot = st.multiselect(
    "Choisissez les stats à comparer",
    [col for col in df.columns if df[col].dtype in ['float64', 'int64'] and col not in ['gp']],
    default=["win", "pts", "ast", "reb"]
)
teams_selected = st.multiselect(
    "Filtrer par équipes",
    options=df["team"].unique(),
    default=list(df["team"].unique())
)

df_comp = df[df["team"].isin(teams_selected)]
if not df_comp.empty and cols_to_plot:
    st.bar_chart(df_comp.set_index("team")[cols_to_plot])
else:
    st.info("Sélectionnez au moins une équipe et une statistique.")

# (Optionnel) Tu peux rajouter des visualisations supplémentaires ici si tu veux !
