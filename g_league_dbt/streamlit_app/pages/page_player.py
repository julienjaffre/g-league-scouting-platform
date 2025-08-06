import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google.cloud import bigquery
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Profils des Joueurs - G-League",
    page_icon="👤",
    layout="wide"
)

# Réutiliser la fonction de connexion BigQuery
@st.cache_resource
def init_bigquery_client():
    """Initialise le client BigQuery"""
    try:
        project_id = 'carbide-bonsai-466217-v2'
        client = bigquery.Client(project=project_id)
        client.query("SELECT 1").result()
        return client
    except Exception as e:
        st.error(f"Erreur BigQuery: {e}")
        return None

# Fonction de chargement des données
@st.cache_data(ttl=3600)
def load_player_data():
    """Charge les données des joueurs depuis BigQuery"""
    client = init_bigquery_client()
    if client is None:
        return pd.DataFrame()
    
    query = """
    SELECT *
    FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.player_stats_gold`
    ORDER BY season DESC, player
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement: {e}")
        return pd.DataFrame()

def create_radar_chart(player_stats, league_avg_stats, player_name):
    """Crée un graphique radar pour comparer un joueur aux moyennes de la ligue"""
    
    categories = ['Points/Match', 'Rebonds/Match', 'Passes/Match', 
                 'Efficacité', 'Impact Global']
    
    # Calculer l'efficacité et l'impact
    player_efficiency = (player_stats['points_per_game'] + 
                        player_stats['rebounds_per_game'] + 
                        player_stats['assists_per_game']) / player_stats['games_played'].mean()
    
    league_efficiency = (league_avg_stats['points_per_game'] + 
                        league_avg_stats['rebounds_per_game'] + 
                        league_avg_stats['assists_per_game']) / league_avg_stats['games_played']
    
    player_impact = player_stats['total_points'] / 1000  # Normaliser
    league_impact = league_avg_stats['total_points'] / 1000
    
    # Valeurs du joueur
    player_values = [
        player_stats['points_per_game'],
        player_stats['rebounds_per_game'],
        player_stats['assists_per_game'],
        player_efficiency,
        player_impact
    ]
    
    # Moyennes de la ligue
    league_values = [
        league_avg_stats['points_per_game'],
        league_avg_stats['rebounds_per_game'],
        league_avg_stats['assists_per_game'],
        league_efficiency,
        league_impact
    ]
    
    # Créer le graphique radar
    fig = go.Figure()
    
    # Ajouter les données du joueur
    fig.add_trace(go.Scatterpolar(
        r=player_values,
        theta=categories,
        fill='toself',
        name=player_name,
        line_color='rgb(255, 99, 71)',
        fillcolor='rgba(255, 99, 71, 0.3)'
    ))
    
    # Ajouter les moyennes de la ligue
    fig.add_trace(go.Scatterpolar(
        r=league_values,
        theta=categories,
        fill='toself',
        name='Moyenne Ligue',
        line_color='rgb(100, 149, 237)',
        fillcolor='rgba(100, 149, 237, 0.1)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(player_values), max(league_values)) * 1.2]
            )),
        showlegend=True,
        title=f"Profil Performance - {player_name}",
        height=500
    )
    
    return fig

def create_performance_timeline(player_history_df):
    """Crée un graphique temporel des performances du joueur"""
    
    fig = go.Figure()
    
    # Points par match
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['points_per_game'],
        mode='lines+markers',
        name='Points/Match',
        line=dict(color='rgb(255, 99, 71)', width=3),
        marker=dict(size=8)
    ))
    
    # Rebonds par match
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['rebounds_per_game'],
        mode='lines+markers',
        name='Rebonds/Match',
        line=dict(color='rgb(50, 205, 50)', width=3),
        marker=dict(size=8)
    ))
    
    # Passes par match
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['assists_per_game'],
        mode='lines+markers',
        name='Passes/Match',
        line=dict(color='rgb(100, 149, 237)', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Évolution des Performances par Saison",
        xaxis_title="Saison",
        yaxis_title="Statistiques par Match",
        hovermode='x unified',
        height=400
    )
    
    return fig

def calculate_advanced_metrics(player_stats, league_stats):
    """Calcule des métriques avancées pour un joueur"""
    
    # Efficacité offensive
    offensive_rating = (player_stats['points_per_game'] * 100) / league_stats['points_per_game'].mean()
    
    # Polyvalence (basée sur la distribution équilibrée des stats)
    stats_std = np.std([player_stats['points_per_game'], 
                       player_stats['rebounds_per_game'], 
                       player_stats['assists_per_game']])
    versatility = 100 - (stats_std * 10)  # Plus c'est équilibré, plus le score est élevé
    
    # Impact total
    total_impact = (player_stats['total_points'] + 
                   player_stats['total_rebounds'] + 
                   player_stats['total_assists']) / player_stats['games_played']
    
    # Régularité (basée sur les matchs joués)
    consistency = (player_stats['games_played'] / league_stats['games_played'].max()) * 100
    
    return {
        'Efficacité Offensive': f"{offensive_rating:.1f}",
        'Polyvalence': f"{versatility:.1f}",
        'Impact Total/Match': f"{total_impact:.1f}",
        'Régularité': f"{consistency:.1f}%",
        'Matchs Joués': player_stats['games_played'],
        'Minutes Totales (est.)': player_stats['games_played'] * 25  # Estimation
    }

def main():
    st.title("👤 Profils Détaillés des Joueurs")
    st.markdown("Analyse approfondie des performances individuelles avec visualisations avancées")
    
    # Chargement des données
    with st.spinner("Chargement des données..."):
        df = load_player_data()
    
    if df.empty:
        st.error("Impossible de charger les données")
        return
    
    # Sélection du joueur
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        players = sorted(df['player'].unique())
        selected_player = st.selectbox(
            "Sélectionner un joueur:",
            players,
            help="Choisissez un joueur pour voir son profil détaillé"
        )
    
    with col2:
        # Filtre par saison pour la comparaison
        seasons = sorted(df['season'].unique(), reverse=True)
        selected_season = st.selectbox(
            "Saison de référence:",
            seasons,
            help="Saison utilisée pour les comparaisons"
        )
    
    with col3:
        # Option de comparaison
        compare_player = st.selectbox(
            "Comparer avec:",
            ['Aucun'] + [p for p in players if p != selected_player]
        )
    
    # Données du joueur sélectionné
    player_data = df[df['player'] == selected_player]
    player_current_season = player_data[player_data['season'] == selected_season].iloc[0] if not player_data[player_data['season'] == selected_season].empty else player_data.iloc[0]
    
    # Statistiques de la ligue pour la saison
    league_stats = df[df['season'] == selected_season]
    league_avg = league_stats.mean(numeric_only=True)
    
    # En-tête avec informations du joueur
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Équipe", player_current_season['team'])
    with col2:
        st.metric("Position", player_current_season['pos'] if pd.notna(player_current_season['pos']) else "N/A")
    with col3:
        st.metric("Saisons jouées", len(player_data))
    with col4:
        st.metric("Matchs (saison)", player_current_season['games_played'])
    
    # Statistiques principales
    st.markdown("### 📊 Statistiques Principales")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Points par Match",
            f"{player_current_season['points_per_game']:.1f}",
            f"{player_current_season['points_per_game'] - league_avg['points_per_game']:.1f} vs moy",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Rebonds par Match",
            f"{player_current_season['rebounds_per_game']:.1f}",
            f"{player_current_season['rebounds_per_game'] - league_avg['rebounds_per_game']:.1f} vs moy",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Passes par Match",
            f"{player_current_season['assists_per_game']:.1f}",
            f"{player_current_season['assists_per_game'] - league_avg['assists_per_game']:.1f} vs moy",
            delta_color="normal"
        )
    
    # Graphiques
    st.markdown("### 📈 Visualisations")
    
    # Tabs pour organiser les visualisations
    tab1, tab2, tab3 = st.tabs(["Graphique Radar", "Évolution Temporelle", "Comparaison Joueurs"])
    
    with tab1:
        # Graphique radar
        col1, col2 = st.columns([2, 1])
        
        with col1:
            radar_fig = create_radar_chart(player_current_season, league_avg, selected_player)
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 💡 Lecture du graphique")
            st.info("""
            Le graphique radar compare les performances du joueur (rouge) 
            aux moyennes de la ligue (bleu) sur 5 dimensions clés.
            
            Plus la surface rouge est grande, plus le joueur 
            surperforme par rapport à la moyenne.
            """)
    
    with tab2:
        # Graphique temporel
        if len(player_data) > 1:
            timeline_fig = create_performance_timeline(player_data.sort_values('season'))
            st.plotly_chart(timeline_fig, use_container_width=True)
            
            # Tableau récapitulatif
            st.markdown("#### 📋 Détail par saison")
            season_summary = player_data[['season', 'team', 'games_played', 
                                         'points_per_game', 'rebounds_per_game', 
                                         'assists_per_game']].sort_values('season', ascending=False)
            st.dataframe(season_summary, hide_index=True, use_container_width=True)
        else:
            st.info("Historique non disponible (une seule saison de données)")
    
    with tab3:
        # Comparaison avec un autre joueur
        if compare_player != 'Aucun':
            compare_data = df[(df['player'] == compare_player) & (df['season'] == selected_season)]
            
            if not compare_data.empty:
                compare_current = compare_data.iloc[0]
                
                # Créer un graphique de comparaison
                comparison_data = pd.DataFrame({
                    'Statistique': ['Points/Match', 'Rebonds/Match', 'Passes/Match', 'Matchs joués'],
                    selected_player: [
                        player_current_season['points_per_game'],
                        player_current_season['rebounds_per_game'],
                        player_current_season['assists_per_game'],
                        player_current_season['games_played']
                    ],
                    compare_player: [
                        compare_current['points_per_game'],
                        compare_current['rebounds_per_game'],
                        compare_current['assists_per_game'],
                        compare_current['games_played']
                    ]
                })
                
                fig_compare = px.bar(
                    comparison_data.melt(id_vars='Statistique', var_name='Joueur', value_name='Valeur'),
                    x='Statistique',
                    y='Valeur',
                    color='Joueur',
                    barmode='group',
                    title=f"Comparaison: {selected_player} vs {compare_player}",
                    color_discrete_map={selected_player: 'rgb(255, 99, 71)', compare_player: 'rgb(100, 149, 237)'}
                )
                
                st.plotly_chart(fig_compare, use_container_width=True)
            else:
                st.warning(f"Pas de données pour {compare_player} en {selected_season}")
        else:
            st.info("Sélectionnez un joueur dans le menu déroulant pour comparer")
    
    # Métriques avancées
    st.markdown("### 🎯 Métriques Avancées")
    
    advanced_metrics = calculate_advanced_metrics(player_current_season, league_stats)
    
    col1, col2, col3 = st.columns(3)
    metrics_items = list(advanced_metrics.items())
    
    for i, (metric_name, metric_value) in enumerate(metrics_items):
        col = [col1, col2, col3][i % 3]
        with col:
            st.metric(metric_name, metric_value)
    
    # Classements
    st.markdown("### 🏆 Classements dans la Ligue")
    
    # Calculer les rangs
    season_stats = df[df['season'] == selected_season].copy()
    season_stats['rank_points'] = season_stats['points_per_game'].rank(ascending=False)
    season_stats['rank_rebounds'] = season_stats['rebounds_per_game'].rank(ascending=False)
    season_stats['rank_assists'] = season_stats['assists_per_game'].rank(ascending=False)
    
    player_ranks = season_stats[season_stats['player'] == selected_player].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Classement Points",
            f"#{int(player_ranks['rank_points'])}",
            f"sur {len(season_stats)} joueurs"
        )
    
    with col2:
        st.metric(
            "Classement Rebonds", 
            f"#{int(player_ranks['rank_rebounds'])}",
            f"sur {len(season_stats)} joueurs"
        )
    
    with col3:
        st.metric(
            "Classement Passes",
            f"#{int(player_ranks['rank_assists'])}",
            f"sur {len(season_stats)} joueurs"
        )
    
    # Export du profil
    st.markdown("### 💾 Export du Profil")
    
    if st.button("📄 Générer rapport PDF"):
        st.info("Fonctionnalité à venir : export PDF du profil complet du joueur")
    
    # Notes et observations
    with st.expander("📝 Ajouter des notes sur ce joueur"):
        notes = st.text_area(
            "Notes d'observation:",
            placeholder="Ajoutez vos observations sur les forces, faiblesses, potentiel du joueur...",
            height=150
        )
        if st.button("Sauvegarder les notes"):
            st.success("Notes sauvegardées (fonctionnalité à implémenter avec une base de données)")

if __name__ == "__main__":
    main()