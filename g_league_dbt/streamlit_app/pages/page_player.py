import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google.cloud import bigquery
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Player Profiles - G-League",
    page_icon="👤",
    layout="wide"
)

# Reuse BigQuery connection function
@st.cache_resource
def init_bigquery_client():
    """Initialize BigQuery client"""
    try:
        project_id = 'carbide-bonsai-466217-v2'
        client = bigquery.Client(project=project_id)
        client.query("SELECT 1").result()
        return client
    except Exception as e:
        st.error(f"BigQuery error: {e}")
        return None

# Data loading function
@st.cache_data(ttl=3600)
def load_player_data():
    """Load player data from BigQuery"""
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
        st.error(f"Loading error: {e}")
        return pd.DataFrame()

def create_radar_chart(player_stats, league_avg_stats, player_name):
    """Create a radar chart to compare a player to league averages"""
    
    categories = ['Points/Game', 'Rebounds/Game', 'Assists/Game', 
                 'Efficiency', 'Overall Impact']
    
    # Calculate efficiency and impact
    player_efficiency = (player_stats['points_per_game'] + 
                        player_stats['rebounds_per_game'] + 
                        player_stats['assists_per_game']) / player_stats['games_played'].mean()
    
    league_efficiency = (league_avg_stats['points_per_game'] + 
                        league_avg_stats['rebounds_per_game'] + 
                        league_avg_stats['assists_per_game']) / league_avg_stats['games_played']
    
    player_impact = player_stats['total_points'] / 1000  # Normalize
    league_impact = league_avg_stats['total_points'] / 1000
    
    # Player values
    player_values = [
        player_stats['points_per_game'],
        player_stats['rebounds_per_game'],
        player_stats['assists_per_game'],
        player_efficiency,
        player_impact
    ]
    
    # League averages
    league_values = [
        league_avg_stats['points_per_game'],
        league_avg_stats['rebounds_per_game'],
        league_avg_stats['assists_per_game'],
        league_efficiency,
        league_impact
    ]
    
    # Create radar chart
    fig = go.Figure()
    
    # Add player data
    fig.add_trace(go.Scatterpolar(
        r=player_values,
        theta=categories,
        fill='toself',
        name=player_name,
        line_color='rgb(255, 99, 71)',
        fillcolor='rgba(255, 99, 71, 0.3)'
    ))
    
    # Add league averages
    fig.add_trace(go.Scatterpolar(
        r=league_values,
        theta=categories,
        fill='toself',
        name='League Average',
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
        title=f"Performance Profile - {player_name}",
        height=500
    )
    
    return fig

def create_performance_timeline(player_history_df):
    """Create a timeline chart of player performance"""
    
    fig = go.Figure()
    
    # Points per game
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['points_per_game'],
        mode='lines+markers',
        name='Points/Game',
        line=dict(color='rgb(255, 99, 71)', width=3),
        marker=dict(size=8)
    ))
    
    # Rebounds per game
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['rebounds_per_game'],
        mode='lines+markers',
        name='Rebounds/Game',
        line=dict(color='rgb(50, 205, 50)', width=3),
        marker=dict(size=8)
    ))
    
    # Assists per game
    fig.add_trace(go.Scatter(
        x=player_history_df['season'],
        y=player_history_df['assists_per_game'],
        mode='lines+markers',
        name='Assists/Game',
        line=dict(color='rgb(100, 149, 237)', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Performance Evolution by Season",
        xaxis_title="Season",
        yaxis_title="Per Game Statistics",
        hovermode='x unified',
        height=400
    )
    
    return fig

def calculate_advanced_metrics(player_stats, league_stats):
    """Calculate advanced metrics for a player"""
    
    # Offensive efficiency
    offensive_rating = (player_stats['points_per_game'] * 100) / league_stats['points_per_game'].mean()
    
    # Versatility (based on balanced distribution of stats)
    stats_std = np.std([player_stats['points_per_game'], 
                       player_stats['rebounds_per_game'], 
                       player_stats['assists_per_game']])
    versatility = 100 - (stats_std * 10)  # More balanced = higher score
    
    # Total impact
    total_impact = (player_stats['total_points'] + 
                   player_stats['total_rebounds'] + 
                   player_stats['total_assists']) / player_stats['games_played']
    
    # Consistency (based on games played)
    consistency = (player_stats['games_played'] / league_stats['games_played'].max()) * 100
    
    return {
        'Offensive Efficiency': f"{offensive_rating:.1f}",
        'Versatility': f"{versatility:.1f}",
        'Total Impact/Game': f"{total_impact:.1f}",
        'Consistency': f"{consistency:.1f}%",
        'Games Played': player_stats['games_played'],
        'Total Minutes (est.)': player_stats['games_played'] * 25  # Estimation
    }

def main():
    st.title("👤 Detailed Player Profiles")
    st.markdown("In-depth analysis of individual performances with advanced visualizations")
    
    # Load data
    with st.spinner("Loading data..."):
        df = load_player_data()
    
    if df.empty:
        st.error("Unable to load data")
        return
    
    # Player selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        players = sorted(df['player'].unique())
        selected_player = st.selectbox(
            "Select a player:",
            players,
            help="Choose a player to view their detailed profile"
        )
    
    with col2:
        # Season filter for comparison
        seasons = sorted(df['season'].unique(), reverse=True)
        selected_season = st.selectbox(
            "Reference season:",
            seasons,
            help="Season used for comparisons"
        )
    
    with col3:
        # Comparison option
        compare_player = st.selectbox(
            "Compare with:",
            ['None'] + [p for p in players if p != selected_player]
        )
    
    # Selected player data
    player_data = df[df['player'] == selected_player]
    player_current_season = player_data[player_data['season'] == selected_season].iloc[0] if not player_data[player_data['season'] == selected_season].empty else player_data.iloc[0]
    
    # League statistics for the season
    league_stats = df[df['season'] == selected_season]
    league_avg = league_stats.mean(numeric_only=True)
    
    # Header with player information
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Team", player_current_season['team'])
    with col2:
        st.metric("Position", player_current_season['pos'] if pd.notna(player_current_season['pos']) else "N/A")
    with col3:
        st.metric("Seasons played", len(player_data))
    with col4:
        st.metric("Games (season)", player_current_season['games_played'])
    
    # Main statistics
    st.markdown("### 📊 Main Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Points per Game",
            f"{player_current_season['points_per_game']:.1f}",
            f"{player_current_season['points_per_game'] - league_avg['points_per_game']:.1f} vs avg",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Rebounds per Game",
            f"{player_current_season['rebounds_per_game']:.1f}",
            f"{player_current_season['rebounds_per_game'] - league_avg['rebounds_per_game']:.1f} vs avg",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Assists per Game",
            f"{player_current_season['assists_per_game']:.1f}",
            f"{player_current_season['assists_per_game'] - league_avg['assists_per_game']:.1f} vs avg",
            delta_color="normal"
        )
    
    # Charts
    st.markdown("### 📈 Visualizations")
    
    # Tabs to organize visualizations
    tab1, tab2, tab3 = st.tabs(["Radar Chart", "Time Evolution", "Player Comparison"])
    
    with tab1:
        # Radar chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            radar_fig = create_radar_chart(player_current_season, league_avg, selected_player)
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 💡 Chart Reading")
            st.info("""
            The radar chart compares player performance (red) 
            to league averages (blue) across 5 key dimensions.
            
            The larger the red area, the more the player 
            outperforms compared to the average.
            """)
    
    with tab2:
        # Timeline chart
        if len(player_data) > 1:
            timeline_fig = create_performance_timeline(player_data.sort_values('season'))
            st.plotly_chart(timeline_fig, use_container_width=True)
            
            # Summary table
            st.markdown("#### 📋 Season by Season Details")
            season_summary = player_data[['season', 'team', 'games_played', 
                                         'points_per_game', 'rebounds_per_game', 
                                         'assists_per_game']].sort_values('season', ascending=False)
            st.dataframe(season_summary, hide_index=True, use_container_width=True)
        else:
            st.info("History not available (only one season of data)")
    
    with tab3:
        # Comparison with another player
        if compare_player != 'None':
            compare_data = df[(df['player'] == compare_player) & (df['season'] == selected_season)]
            
            if not compare_data.empty:
                compare_current = compare_data.iloc[0]
                
                # Create comparison chart
                comparison_data = pd.DataFrame({
                    'Statistic': ['Points/Game', 'Rebounds/Game', 'Assists/Game', 'Games played'],
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
                    comparison_data.melt(id_vars='Statistic', var_name='Player', value_name='Value'),
                    x='Statistic',
                    y='Value',
                    color='Player',
                    barmode='group',
                    title=f"Comparison: {selected_player} vs {compare_player}",
                    color_discrete_map={selected_player: 'rgb(255, 99, 71)', compare_player: 'rgb(100, 149, 237)'}
                )
                
                st.plotly_chart(fig_compare, use_container_width=True)
            else:
                st.warning(f"No data for {compare_player} in {selected_season}")
        else:
            st.info("Select a player from the dropdown to compare")
    
    # Advanced metrics
    st.markdown("### 🎯 Advanced Metrics")
    
    advanced_metrics = calculate_advanced_metrics(player_current_season, league_stats)
    
    col1, col2, col3 = st.columns(3)
    metrics_items = list(advanced_metrics.items())
    
    for i, (metric_name, metric_value) in enumerate(metrics_items):
        col = [col1, col2, col3][i % 3]
        with col:
            st.metric(metric_name, metric_value)
    
    # Rankings
    st.markdown("### 🏆 League Rankings")
    
    # Calculate ranks
    season_stats = df[df['season'] == selected_season].copy()
    season_stats['rank_points'] = season_stats['points_per_game'].rank(ascending=False)
    season_stats['rank_rebounds'] = season_stats['rebounds_per_game'].rank(ascending=False)
    season_stats['rank_assists'] = season_stats['assists_per_game'].rank(ascending=False)
    
    player_ranks = season_stats[season_stats['player'] == selected_player].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Points Ranking",
            f"#{int(player_ranks['rank_points'])}",
            f"out of {len(season_stats)} players"
        )
    
    with col2:
        st.metric(
            "Rebounds Ranking", 
            f"#{int(player_ranks['rank_rebounds'])}",
            f"out of {len(season_stats)} players"
        )
    
    with col3:
        st.metric(
            "Assists Ranking",
            f"#{int(player_ranks['rank_assists'])}",
            f"out of {len(season_stats)} players"
        )
    
    # Profile export
    st.markdown("### 💾 Profile Export")
    
    if st.button("📄 Generate PDF report"):
        st.info("Coming soon: complete player profile PDF export")
    
    # Notes and observations
    with st.expander("📝 Add notes about this player"):
        notes = st.text_area(
            "Observation notes:",
            placeholder="Add your observations about the player's strengths, weaknesses, potential...",
            height=150
        )
        if st.button("Save notes"):
            st.success("Notes saved (feature to be implemented with database)")

if __name__ == "__main__":
    main()