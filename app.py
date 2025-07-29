# app.py

import streamlit as st
from google.cloud import bigquery
import pandas as pd

# === Configuration de la page ===
st.set_page_config(page_title="G-League Dashboard", layout="wide")

# === Titre ===
st.title("🔥 G-League - Meilleurs Scoreurs")

# === Connexion à BigQuery avec région explicite ===
client = bigquery.Client(location="US")  # Remplace "US" si ta table est ailleurs (ex: "europe-west1")

# === Requête vers la table gold ===
QUERY = """
    SELECT *
    FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.gold_top_scorers`
    LIMIT 100
"""

@st.cache_data
def load_data():
    return client.query(QUERY).to_dataframe()

# === Chargement des données ===
df = load_data()

# === Affichage dans Streamlit ===
st.subheader("🏀 Top 100 Scoreurs G-League (2022–2024)")
st.dataframe(df, use_container_width=True)
