import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import math

# Configuration de la page
st.set_page_config(
    page_title="G-League Scouting - Profils Joueurs",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour se connecter à BigQuery
@st.cache_resource
def init_bigquery_client():
    """Initialise le client BigQuery"""
    try:
        client = bigquery.Client()
        return client
    except Exception as e:
        st.error(f"Erreur de connexion à BigQuery: {str(e)}")
        return None

# Fonction pour charger les données
@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def load_player_data():
    """Charge les données des joueurs depuis BigQuery"""
    client = init_bigquery_client()
    if client is None:
        return pd.DataFrame()
    
    query = """
    SELECT *
    FROM `scouting_dbt_bronze_scouting_dbt_bronze_gold.player_stats_gold`
    ORDER BY game_date DESC
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return pd.DataFrame()

# Fonction pour calculer les percentiles
def calculate_player_percentiles(df, player_name, metrics):
    """Calcule les percentiles d'un joueur pour les métriques données"""
    player_data = df[df['player_name'] == player_name]
    if player_data.empty:
        return {}
    
    percentiles = {}
    for metric in metrics:
        if metric in df.columns:
            player_avg = player_data[metric].mean()
            league_percentile = (df[metric] < player_avg).mean() * 100
            percentiles[metric] = min(100, max(0, league_percentile))
    
    return percentiles

# Fonction pour créer le graphique radar
def create_radar_chart(player_data, metrics_config):
    """Crée un graphique radar pour un joueur"""
    categories = list(metrics_config.keys())
    values = list(metrics_config.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=player_data['player_name'].iloc[0] if not player_data.empty else 'Joueur',
        line_color='#1f77b4',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode='linear',
                tick0=0,
                dtick=20
            )),
        showlegend=True,
        title="Profil Radar du Joueur (Percentiles)",
        font=dict(size=12),
        width=500,
        height=500
    )
    
    return fig

# Fonction pour créer l'historique de performance
def create_performance_timeline(player_data, metric):
    """Crée un graphique temporel de performance"""
    if player_data.empty:
        return go.Figure()
    
    # Trier par date
    player_data_sorted = player_data.sort_values('game_date')
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[f'{metric.replace("_", " ").title()} par Match', 'Moyenne Mobile (5 matchs)'],
        vertical_spacing=0.1
    )
    
    # Graphique principal
    fig.add_trace(
        go.Scatter(
            x=player_data_sorted['game_date'],
            y=player_data_sorted[metric],
            mode='lines+markers',
            name=f'{metric}',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    # Moyenne mobile
    if len(player_data_sorted) >= 5:
        rolling_avg = player_data_sorted[metric].rolling(window=5, min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=player_data_sorted['game_date'],
                y=rolling_avg,
                mode='lines',
                name='Moyenne Mobile',
                line=dict(color='#ff7f0e', width=3)
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        height=600,
        title_text=f"Évolution de {metric.replace('_', ' ').title()}",
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text=metric.replace('_', ' ').title(), row=1, col=1)
    fig.update_yaxes(title_text="Moyenne Mobile", row=2, col=1)
    
    return fig

# Fonction pour créer le tableau de métriques avancées
def create_advanced_metrics_table(player_data):
    """Crée un tableau de métriques avancées"""
    if player_data.empty:
        return pd.DataFrame()
    
    # Calculer les métriques avancées
    metrics = {
        'Matchs Joués': len(player_data),
        'Points/Match': player_data['points'].mean(),
        'Rebonds/Match': player_data['rebounds'].mean(),
        'Passes/Match': player_data['assists'].mean(),
        'Interceptions/Match': player_data['steals'].mean(),
        'Contres/Match': player_data['blocks'].mean(),
        'FG%': (player_data['field_goals_made'].sum() / player_data['field_goals_attempted'].sum() * 100) if player_data['field_goals_attempted'].sum() > 0 else 0,
        '3P%': (player_data['three_pointers_made'].sum() / player_data['three_pointers_attempted'].sum() * 100) if player_data['three_pointers_attempted'].sum() > 0 else 0,
        'FT%': (player_data['free_throws_made'].sum() / player_data['free_throws_attempted'].sum() * 100) if player_data['free_throws_attempted'].sum() > 0 else 0,
        'Minutes/Match': player_data['minutes_played'].mean(),
        'Efficacité': (player_data['points'] + player_data['rebounds'] + player_data['assists'] + player_data['steals'] + player_data['blocks'] - player_data['turnovers']).mean(),
        'Plus/Minus': player_data['plus_minus'].mean() if 'plus_minus' in player_data.columns else 0
    }
    
    # Créer le DataFrame
    df_metrics = pd.DataFrame({
        'Métrique': list(metrics.keys()),
        'Valeur': [round(v, 2) if isinstance(v, float) else v for v in metrics.values()]
    })
    
    return df_metrics

# Interface principale
def main():
    st.title("🏀 G-League Scouting Platform")
    st.header("📊 Profils Détaillés des Joueurs")
    
    # Charger les données
    with st.spinner("Chargement des données..."):
        df = load_player_data()
    
    if df.empty:
        st.error("Aucune donnée disponible. Vérifiez votre connexion BigQuery.")
        return
    
    # Sidebar pour la sélection
    st.sidebar.header("🎯 Sélection du Joueur")
    
    # Liste des joueurs
    players = sorted(df['player_name'].unique())
    selected_player = st.sidebar.selectbox(
        "Choisir un joueur:",
        players,
        index=0 if players else None
    )
    
    # Filtre par équipe
    teams = ['Toutes'] + sorted(df['team'].unique().tolist())
    selected_team = st.sidebar.selectbox("Filtrer par équipe:", teams)
    
    # Filtre par période
    date_range = st.sidebar.date_input(
        "Période d'analyse:",
        value=(df['game_date'].min(), df['game_date'].max()),
        min_value=df['game_date'].min(),
        max_value=df['game_date'].max()
    )
    
    # Filtrer les données
    filtered_df = df.copy()
    if selected_team != 'Toutes':
        filtered_df = filtered_df[filtered_df['team'] == selected_team]
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['game_date'] >= pd.to_datetime(date_range[0])) &
            (filtered_df['game_date'] <= pd.to_datetime(date_range[1]))
        ]
    
    # Données du joueur sélectionné
    player_data = filtered_df[filtered_df['player_name'] == selected_player]
    
    if player_data.empty:
        st.warning(f"Aucune donnée trouvée pour {selected_player} dans la période sélectionnée.")
        return
    
    # Affichage des informations générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Matchs Joués", len(player_data))
    with col2:
        st.metric("Points/Match", f"{player_data['points'].mean():.1f}")
    with col3:
        st.metric("Rebonds/Match", f"{player_data['rebounds'].mean():.1f}")
    with col4:
        st.metric("Passes/Match", f"{player_data['assists'].mean():.1f}")
    
    # Section 1: Graphique Radar
    st.header("🎯 Profil Radar Multi-dimensionnel")
    
    # Métriques pour le radar
    radar_metrics = {
        'Points': 'points',
        'Rebonds': 'rebounds',
        'Passes': 'assists',
        'Interceptions': 'steals',
        'Contres': 'blocks',
        'Précision TIR': 'field_goals_made'
    }
    
    # Calculer les percentiles pour le radar
    percentiles = calculate_player_percentiles(filtered_df, selected_player, list(radar_metrics.values()))
    
    radar_config = {}
    for label, metric in radar_metrics.items():
        if metric in percentiles:
            radar_config[label] = percentiles[metric]
    
    if radar_config:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            radar_fig = create_radar_chart(player_data, radar_config)
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Percentiles Liga")
            for label, value in radar_config.items():
                st.metric(
                    label,
                    f"{value:.0f}%",
                    delta=f"+{value-50:.0f}%" if value > 50 else f"{value-50:.0f}%"
                )
    
    # Section 2: Historique de Performance
    st.header("📈 Historique de Performance")
    
    # Sélection de la métrique à analyser
    metric_options = {
        'Points': 'points',
        'Rebonds': 'rebounds',
        'Passes': 'assists',
        'Minutes': 'minutes_played',
        'Field Goal %': 'field_goals_made',
        'Efficacité': 'points'  # Sera calculée
    }
    
    selected_metric = st.selectbox(
        "Choisir la métrique à analyser:",
        list(metric_options.keys())
    )
    
    if selected_metric == 'Efficacité':
        # Calculer l'efficacité
        player_data_copy = player_data.copy()
        player_data_copy['efficiency'] = (
            player_data_copy['points'] + 
            player_data_copy['rebounds'] + 
            player_data_copy['assists'] + 
            player_data_copy['steals'] + 
            player_data_copy['blocks'] - 
            player_data_copy['turnovers']
        )
        timeline_fig = create_performance_timeline(player_data_copy, 'efficiency')
    else:
        timeline_fig = create_performance_timeline(player_data, metric_options[selected_metric])
    
    st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Section 3: Métriques Avancées
    st.header("📊 Tableau de Bord - Métriques Avancées")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Tableau des métriques
        metrics_df = create_advanced_metrics_table(player_data)
        st.dataframe(
            metrics_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Métrique": st.column_config.TextColumn("Métrique", width="medium"),
                "Valeur": st.column_config.NumberColumn("Valeur", format="%.2f")
            }
        )
    
    with col2:
        # Graphique de répartition des points
        if len(player_data) > 1:
            st.subheader("📊 Distribution des Points")
            fig_hist = px.histogram(
                player_data,
                x='points',
                nbins=10,
                title="Distribution des Points par Match",
                color_discrete_sequence=['#1f77b4']
            )
            fig_hist.update_layout(height=300)
            st.plotly_chart(fig_hist, use_container_width=True)
    
    # Section 4: Comparaison avec la Liga
    st.header("⚖️ Comparaison avec la Liga")
    
    col1, col2, col3 = st.columns(3)
    
    # Calculer les moyennes de la ligue
    league_avg_points = filtered_df['points'].mean()
    league_avg_rebounds = filtered_df['rebounds'].mean()
    league_avg_assists = filtered_df['assists'].mean()
    
    player_avg_points = player_data['points'].mean()
    player_avg_rebounds = player_data['rebounds'].mean()
    player_avg_assists = player_data['assists'].mean()
    
    with col1:
        st.metric(
            "Points vs Liga",
            f"{player_avg_points:.1f}",
            delta=f"{player_avg_points - league_avg_points:.1f}"
        )
    
    with col2:
        st.metric(
            "Rebonds vs Liga",
            f"{player_avg_rebounds:.1f}",
            delta=f"{player_avg_rebounds - league_avg_rebounds:.1f}"
        )
    
    with col3:
        st.metric(
            "Passes vs Liga",
            f"{player_avg_assists:.1f}",
            delta=f"{player_avg_assists - league_avg_assists:.1f}"
        )
    
    # Section 5: Exportation des données
    st.header("💾 Exportation des Données")
    
    if st.button("📥 Télécharger le Profil Complet"):
        # Préparer les données pour l'export
        export_data = player_data.copy()
        export_data['efficiency'] = (
            export_data['points'] + export_data['rebounds'] + 
            export_data['assists'] + export_data['steals'] + 
            export_data['blocks'] - export_data['turnovers']
        )
        
        csv = export_data.to_csv(index=False)
        st.download_button(
            label="📄 Télécharger CSV",
            data=csv,
            file_name=f"profil_{selected_player}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()