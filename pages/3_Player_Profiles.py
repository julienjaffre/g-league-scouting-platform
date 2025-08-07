import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google.cloud import bigquery
import numpy as np
import sys
import os

# Add the project root to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.bigquery_auth import get_bigquery_client, test_bigquery_connection

# === Page Configuration ===
st.set_page_config(
    page_title="Player Profiles - G-League",
    page_icon="👤",
    layout="wide"
)

# === BigQuery Client ===
@st.cache_resource
def get_client():
    return get_bigquery_client()

client = get_client()
if client:
    if test_bigquery_connection(client):
        st.success("✅ BigQuery connection successful!")
    else:
        st.error("❌ BigQuery connection test failed")

@st.cache_data(ttl=3600)
def load_player_data():
    client = get_client()
    if client is None:
        st.error("❌ Cannot connect to BigQuery. Please check authentication.")
        return pd.DataFrame()

    query = """
    SELECT *
    FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.player_stats_gold`
    ORDER BY season DESC, player
    """

    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"❌ Error while loading: {e}")
        return pd.DataFrame()

def create_radar_chart(player_stats, league_avg_stats, player_name):
    categories = ['Points/Game', 'Rebounds/Game', 'Assists/Game', 'Efficiency', 'Total Impact']

    player_efficiency = (
        player_stats['points_per_game'] +
        player_stats['rebounds_per_game'] +
        player_stats['assists_per_game']
    ) / player_stats['games_played'].mean()

    league_efficiency = (
        league_avg_stats['points_per_game'] +
        league_avg_stats['rebounds_per_game'] +
        league_avg_stats['assists_per_game']
    ) / league_avg_stats['games_played']

    player_impact = player_stats['total_points'] / 1000
    league_impact = league_avg_stats['total_points'] / 1000

    player_values = [
        player_stats['points_per_game'],
        player_stats['rebounds_per_game'],
        player_stats['assists_per_game'],
        player_efficiency,
        player_impact
    ]

    league_values = [
        league_avg_stats['points_per_game'],
        league_avg_stats['rebounds_per_game'],
        league_avg_stats['assists_per_game'],
        league_efficiency,
        league_impact
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=player_values,
        theta=categories,
        fill='toself',
        name=player_name,
        line_color='rgb(255, 99, 71)',
        fillcolor='rgba(255, 99, 71, 0.3)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=league_values,
        theta=categories,
        fill='toself',
        name='League Average',
        line_color='rgb(100, 149, 237)',
        fillcolor='rgba(100, 149, 237, 0.1)'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(max(player_values), max(league_values)) * 1.2])),
        showlegend=True,
        title=f"Performance Profile - {player_name}",
        height=500
    )
    return fig

def create_performance_timeline(player_history_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['points_per_game'],
        mode='lines+markers',
        name='Points/Game',
        line=dict(color='rgb(255, 99, 71)', width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['rebounds_per_game'],
        mode='lines+markers',
        name='Rebounds/Game',
        line=dict(color='rgb(50, 205, 50)', width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['assists_per_game'],
        mode='lines+markers',
        name='Assists/Game',
        line=dict(color='rgb(100, 149, 237)', width=3),
        marker=dict(size=8)
    ))
    fig.update_layout(
        title="Performance Over Time",
        xaxis_title="Season",
        yaxis_title="Stats per Game",
        hovermode='x unified',
        height=400
    )
    return fig

def calculate_advanced_metrics(player_stats, league_stats):
    offensive_rating = (player_stats['points_per_game'] * 100) / league_stats['points_per_game'].mean()
    stats_std = np.std([
        player_stats['points_per_game'],
        player_stats['rebounds_per_game'],
        player_stats['assists_per_game']
    ])
    versatility = 100 - (stats_std * 10)
    total_impact = (player_stats['total_points'] + player_stats['total_rebounds'] + player_stats['total_assists']) / player_stats['games_played']
    consistency = (player_stats['games_played'] / league_stats['games_played'].max()) * 100

    return {
        'Offensive Efficiency': f"{offensive_rating:.1f}",
        'Versatility': f"{versatility:.1f}",
        'Total Impact/Game': f"{total_impact:.1f}",
        'Consistency': f"{consistency:.1f}%",
        'Games Played': player_stats['games_played'],
        'Estimated Minutes': player_stats['games_played'] * 25
    }

def main():
    st.title("👤 Player Profiles - G-League")
    st.markdown("Deep dive into individual performances with advanced visualizations.")

    with st.spinner("Loading data..."):
        df = load_player_data()

    if df.empty:
        st.error("Failed to load data.")
        return

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        players = sorted(df['player'].unique())
        selected_player = st.selectbox("Select a player", players)

    with col2:
        seasons = sorted(df['season'].unique(), reverse=True)
        selected_season = st.selectbox("Reference season", seasons)

    with col3:
        compare_player = st.selectbox("Compare with", ['None'] + [p for p in players if p != selected_player])

    player_data = df[df['player'] == selected_player]
    player_current = player_data[player_data['season'] == selected_season].iloc[0] if not player_data[player_data['season'] == selected_season].empty else player_data.iloc[0]
    league_stats = df[df['season'] == selected_season]
    league_avg = league_stats.mean(numeric_only=True)

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Team", player_current['team'])
    col2.metric("Position", player_current['pos'] if pd.notna(player_current['pos']) else "N/A")
    col3.metric("Seasons Played", len(player_data))
    col4.metric("Games (season)", player_current['games_played'])

    st.markdown("### 📊 Key Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Points/Game", f"{player_current['points_per_game']:.1f}", f"{player_current['points_per_game'] - league_avg['points_per_game']:.1f} vs avg")
    col2.metric("Rebounds/Game", f"{player_current['rebounds_per_game']:.1f}", f"{player_current['rebounds_per_game'] - league_avg['rebounds_per_game']:.1f} vs avg")
    col3.metric("Assists/Game", f"{player_current['assists_per_game']:.1f}", f"{player_current['assists_per_game'] - league_avg['assists_per_game']:.1f} vs avg")

    st.markdown("### 📈 Visualizations")
    tab1, tab2, tab3 = st.tabs(["Radar Chart", "Timeline", "Player Comparison"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(create_radar_chart(player_current, league_avg, selected_player), use_container_width=True)
        with col2:
            st.markdown("#### ℹ️ Chart Reading Guide")
            st.info("This radar chart compares the player's performance (red) to the league average (blue) across 5 key dimensions.")

    with tab2:
        if len(player_data) > 1:
            st.plotly_chart(create_performance_timeline(player_data.sort_values('season')), use_container_width=True)
            st.markdown("#### 📋 Season Breakdown")
            st.dataframe(player_data[['season', 'team', 'games_played', 'points_per_game', 'rebounds_per_game', 'assists_per_game']].sort_values('season', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No historical data (only one season).")

    with tab3:
        if compare_player != 'None':
            compare_data = df[(df['player'] == compare_player) & (df['season'] == selected_season)]
            if not compare_data.empty:
                compare_current = compare_data.iloc[0]
                comparison_df = pd.DataFrame({
                    'Stat': ['Points/Game', 'Rebounds/Game', 'Assists/Game', 'Games Played'],
                    selected_player: [
                        player_current['points_per_game'],
                        player_current['rebounds_per_game'],
                        player_current['assists_per_game'],
                        player_current['games_played']
                    ],
                    compare_player: [
                        compare_current['points_per_game'],
                        compare_current['rebounds_per_game'],
                        compare_current['assists_per_game'],
                        compare_current['games_played']
                    ]
                })
                fig = px.bar(
                    comparison_df.melt(id_vars='Stat', var_name='Player', value_name='Value'),
                    x='Stat',
                    y='Value',
                    color='Player',
                    barmode='group',
                    title=f"{selected_player} vs {compare_player}",
                    color_discrete_map={selected_player: 'rgb(255, 99, 71)', compare_player: 'rgb(100, 149, 237)'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No data for {compare_player} in {selected_season}")
        else:
            st.info("Select a player to compare.")

    st.markdown("### 🎯 Advanced Metrics")
    metrics = calculate_advanced_metrics(player_current, league_stats)
    col1, col2, col3 = st.columns(3)
    for i, (name, value) in enumerate(metrics.items()):
        [col1, col2, col3][i % 3].metric(name, value)

    st.markdown("### 🏆 League Rankings")
    season_stats = df[df['season'] == selected_season].copy()
    season_stats['rank_points'] = season_stats['points_per_game'].rank(ascending=False)
    season_stats['rank_rebounds'] = season_stats['rebounds_per_game'].rank(ascending=False)
    season_stats['rank_assists'] = season_stats['assists_per_game'].rank(ascending=False)
    ranks = season_stats[season_stats['player'] == selected_player].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Points Rank", f"#{int(ranks['rank_points'])}", f"out of {len(season_stats)}")
    col2.metric("Rebounds Rank", f"#{int(ranks['rank_rebounds'])}", f"out of {len(season_stats)}")
    col3.metric("Assists Rank", f"#{int(ranks['rank_assists'])}", f"out of {len(season_stats)}")

    st.markdown("### 💾 Export Player Profile")
    if st.button("📄 Generate PDF Report"):
        st.info("Coming soon: PDF export of the full player profile.")

    with st.expander("📝 Add notes about this player"):
        notes = st.text_area("Observation notes", placeholder="Strengths, weaknesses, potential...", height=150)
        if st.button("Save notes"):
            st.success("Notes saved (functionality to be implemented).")

if __name__ == "__main__":
    main()
