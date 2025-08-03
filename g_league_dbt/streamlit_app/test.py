# -*- coding: utf-8 -*-
"""
G-League Scouting Platform - Simple Data Viewer
Affichage des données player_stats_gold
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery

# Configuration de la page
st.set_page_config(
    page_title="G-League Data Viewer",
    page_icon="📊",
    layout="wide"
)

# Fonction de connexion BigQuery
@st.cache_resource
def init_bigquery_client():
    """Initialise le client BigQuery"""
    try:
        client = bigquery.Client(project='carbide-bonsai-466217-v2')
        return client
    except Exception as e:
        st.error(f"Erreur BigQuery: {e}")
        return None

# Fonction de chargement des données
@st.cache_data(ttl=3600)
def load_data():
    """Charge les données depuis BigQuery"""
    client = init_bigquery_client()
    if client is None:
        return pd.DataFrame()
    
    query = """
    SELECT *
    FROM `carbide-bonsai-466217-v2.scouting_dbt_bronze_scouting_dbt_bronze_gold.player_stats_gold`
    ORDER BY game_date DESC
    LIMIT 1000
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement: {e}")
        return pd.DataFrame()

def main():
    # En-tête
    st.title("📊 G-League Scouting Platform")
    st.header("🏀 Données Player Stats Gold")
    
    # Chargement des données
    with st.spinner("Chargement des données..."):
        df = load_data()
    
    if df.empty:
        st.warning("⚠️ Aucune donnée disponible")
        st.info("""
        **Vérifications à faire :**
        1. Permissions BigQuery configurées ?
        2. Table `player_stats_gold` existe ?
        3. Connexion réseau OK ?
        """)
        return
    
    # Statistiques générales
    st.success(f"✅ {len(df)} enregistrements chargés")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Joueurs uniques", df['player_name'].nunique())
    with col2:
        st.metric("Équipes", df['team'].nunique())
    with col3:
        st.metric("Matchs", len(df))
    with col4:
        st.metric("Période", f"{df['game_date'].min().strftime('%d/%m')} - {df['game_date'].max().strftime('%d/%m')}")
    
    # Filtres
    st.subheader("🔍 Filtres")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        players = ['Tous'] + sorted(df['player_name'].unique())
        selected_player = st.selectbox("Joueur:", players)
    
    with col2:
        teams = ['Toutes'] + sorted(df['team'].unique())
        selected_team = st.selectbox("Équipe:", teams)
    
    with col3:
        date_range = st.date_input(
            "Période:",
            value=(df['game_date'].min(), df['game_date'].max()),
            min_value=df['game_date'].min(),
            max_value=df['game_date'].max()
        )
    
    # Appliquer les filtres
    filtered_df = df.copy()
    
    if selected_player != 'Tous':
        filtered_df = filtered_df[filtered_df['player_name'] == selected_player]
    
    if selected_team != 'Toutes':
        filtered_df = filtered_df[filtered_df['team'] == selected_team]
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['game_date'] >= pd.to_datetime(date_range[0])) &
            (filtered_df['game_date'] <= pd.to_datetime(date_range[1]))
        ]
    
    # Affichage des données filtrées
    st.subheader(f"📋 Données filtrées ({len(filtered_df)} enregistrements)")
    
    if not filtered_df.empty:
        # Tableau principal
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "game_date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                "player_name": st.column_config.TextColumn("Joueur", width="medium"),
                "team": st.column_config.TextColumn("Équipe", width="small"),
                "points": st.column_config.NumberColumn("Points", format="%d"),
                "rebounds": st.column_config.NumberColumn("Rebonds", format="%d"),
                "assists": st.column_config.NumberColumn("Passes", format="%d"),
                "minutes_played": st.column_config.NumberColumn("Minutes", format="%d")
            }
        )
        
        # Statistiques des données filtrées
        st.subheader("📈 Statistiques")
        
        numeric_cols = ['points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'minutes_played']
        stats_df = filtered_df[numeric_cols].describe().round(2)
        
        st.dataframe(
            stats_df,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(col.title(), format="%.2f") for col in numeric_cols}
        )
        
        # Top 10 des performances
        st.subheader("🏆 Top 10 Points")
        top_performances = filtered_df.nlargest(10, 'points')[['player_name', 'team', 'game_date', 'points', 'rebounds', 'assists']]
        st.dataframe(top_performances, hide_index=True, use_container_width=True)
        
        # Export des données
        st.subheader("💾 Export")
        if st.button("📥 Télécharger les données filtrées"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📄 Télécharger CSV",
                data=csv,
                file_name=f"player_stats_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("Aucune donnée ne correspond aux filtres sélectionnés")
    
    # Informations techniques
    with st.expander("🔧 Informations techniques"):
        st.write("**Colonnes disponibles:**")
        st.write(df.columns.tolist())
        st.write("**Types de données:**")
        st.write(df.dtypes)

if __name__ == "__main__":
    main()