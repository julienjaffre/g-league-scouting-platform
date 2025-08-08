import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google.cloud import bigquery
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
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

def create_radar_chart(player_stats, league_stats, player_name):
    """Create a min-max normalized radar chart"""

    categories = ['Scoring', 'Rebounding', 'Playmaking', 'Availability', 'Production']

    def normalize_to_scale(player_val, min_val, avg_val, max_val):
        """Normalize value to 0-100 scale where 50 = average"""
        if max_val == min_val:
            return 50

        if player_val <= avg_val:
            # Scale from 0-50 (min to average)
            return 50 * (player_val - min_val) / (avg_val - min_val) if avg_val != min_val else 50
        else:
            # Scale from 50-100 (average to max)
            return 50 + 50 * (player_val - avg_val) / (max_val - avg_val) if max_val != avg_val else 50

    # Get league stats for normalization
    scoring_norm = normalize_to_scale(
        player_stats['points_per_game'],
        league_stats['points_per_game'].min(),
        league_stats['points_per_game'].mean(),
        league_stats['points_per_game'].max()
    )

    rebounding_norm = normalize_to_scale(
        player_stats['rebounds_per_game'],
        league_stats['rebounds_per_game'].min(),
        league_stats['rebounds_per_game'].mean(),
        league_stats['rebounds_per_game'].max()
    )

    playmaking_norm = normalize_to_scale(
        player_stats['assists_per_game'],
        league_stats['assists_per_game'].min(),
        league_stats['assists_per_game'].mean(),
        league_stats['assists_per_game'].max()
    )

    availability_norm = normalize_to_scale(
        player_stats['games_played'],
        league_stats['games_played'].min(),
        league_stats['games_played'].mean(),
        min(league_stats['games_played'].max(), 82)  # Cap at 82 games
    )

    # Total production
    player_production = player_stats['total_points'] + player_stats['total_rebounds'] + player_stats['total_assists']
    league_production = league_stats['total_points'] + league_stats['total_rebounds'] + league_stats['total_assists']

    production_norm = normalize_to_scale(
        player_production,
        league_production.min(),
        league_production.mean(),
        league_production.max()
    )

    player_values = [scoring_norm, rebounding_norm, playmaking_norm, availability_norm, production_norm]
    league_values = [50, 50, 50, 50, 50]  # Average baseline

    fig = go.Figure()

    # Player trace
    fig.add_trace(go.Scatterpolar(
        r=player_values,
        theta=categories,
        fill='toself',
        name=player_name,
        line=dict(color='rgb(255, 99, 71)', width=3),
        fillcolor='rgba(255, 99, 71, 0.25)',
        marker=dict(size=8)
    ))

    # League average reference
    fig.add_trace(go.Scatterpolar(
        r=league_values,
        theta=categories,
        fill='toself',
        name='League Average',
        line=dict(color='rgb(100, 149, 237)', width=2, dash='dash'),
        fillcolor='rgba(100, 149, 237, 0.1)',
        marker=dict(size=6)
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[0, 25, 50, 75, 100],
                ticktext=['Min', 'Below Avg', 'Average', 'Above Avg', 'Max'],
                gridcolor='lightgray'
            )
        ),
        showlegend=True,
        title=f"Performance Profile - {player_name}",
        height=500,
        font=dict(size=12)
    )

    return fig

def create_performance_timeline(player_history_df):
    # Convert season to integer to avoid decimals
    player_history_df = player_history_df.copy()
    player_history_df['season_clean'] = player_history_df['season'].astype(int)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=player_history_df['season_clean'],  # Use clean season values
        y=player_history_df['points_per_game'],
        mode='lines+markers',
        name='Points/Game',
        line=dict(color='rgb(255, 99, 71)', width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=player_history_df['season_clean'],  # Use clean season values
        y=player_history_df['rebounds_per_game'],
        mode='lines+markers',
        name='Rebounds/Game',
        line=dict(color='rgb(50, 205, 50)', width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=player_history_df['season_clean'],  # Use clean season values
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
        height=400,
        xaxis=dict(
            tickmode='array',
            tickvals=[2022, 2023, 2024],  # Force specific tick values
            ticktext=['2022', '2023', '2024']  # Clean labels
        )
    )
    return fig

def calculate_advanced_metrics(player_stats, league_stats):
    """Calculate metrics based on actually available data"""

    # Games availability (health/reliability)
    max_games = league_stats['games_played'].max() if len(league_stats) > 0 else 82
    availability = (player_stats['games_played'] / max_games) * 100

    # Per-game efficiency (points per minute estimate)
    # Assuming ~25 minutes per game average
    estimated_minutes_total = player_stats['games_played'] * 25
    points_per_minute = player_stats['total_points'] / estimated_minutes_total if estimated_minutes_total > 0 else 0

    # Total production
    total_production = player_stats['total_points'] + player_stats['total_rebounds'] + player_stats['total_assists']
    production_per_game = total_production / player_stats['games_played'] if player_stats['games_played'] > 0 else 0

    # League percentile rankings
    points_percentile = (league_stats['points_per_game'] < player_stats['points_per_game']).mean() * 100
    rebounds_percentile = (league_stats['rebounds_per_game'] < player_stats['rebounds_per_game']).mean() * 100
    assists_percentile = (league_stats['assists_per_game'] < player_stats['assists_per_game']).mean() * 100

    return {
        'Games Played': player_stats['games_played'],
        'Availability': f"{availability:.1f}%",
        'Total Production/Game': f"{production_per_game:.1f}",
        'Points Percentile': f"{points_percentile:.0f}th",
        'Rebounds Percentile': f"{rebounds_percentile:.0f}th",
        'Assists Percentile': f"{assists_percentile:.0f}th"
    }

def main():
    st.title("👤 Player Profiles - G-League")
    st.markdown("Deep dive into individual performances with advanced visualizations.")

    with st.spinner("Loading data..."):
        df = load_player_data()

    if df.empty:
        st.error("Failed to load data.")
        return

    # SIDEBAR with simplified filters and glossary
    st.sidebar.header("👤 Season")

    with st.spinner("Loading data..."):
        df = load_player_data()

    if df.empty:
        st.error("Failed to load data.")
        return

    # SIDEBAR FILTERS - Only season filter
    st.sidebar.subheader("Data Settings")

    # Season filter only
    seasons = sorted(df['season'].unique(), reverse=True)
    season_filter = st.sidebar.selectbox(
        "Available Seasons",
        options=seasons,
        help="Choose which seasons of data to include in the analysis"
    )

    # Filter dataframe by season only
    filtered_df = df[df['season'] == season_filter]

    # SIDEBAR GLOSSARY (updated to match current implementation)
    st.sidebar.markdown("---")
    with st.sidebar.expander("📚 Player Profile Glossary"):
        st.markdown("""
        **Core Statistics:**
        - **Points/Game** = Average points scored per game
        - **Rebounds/Game** = Average rebounds per game (offensive + defensive)
        - **Assists/Game** = Average assists per game (playmaking ability)
        - **Games Played** = Total games participated in during season

        **Radar Chart Dimensions:**
        - **Scoring** = Points per game vs league min/max/average
        - **Rebounding** = Rebounds per game vs league min/max/average
        - **Playmaking** = Assists per game vs league min/max/average
        - **Availability** = Games played vs league min/max/average (capped at 82)
        - **Production** = Total production vs league min/max/average

        **Radar Chart Scale:**
        - **0-25 = Min to Below Average** (Red zone - needs improvement)
        - **25-50 = Below Average to Average** (Yellow zone - developing)
        - **50 = League Average** (Blue dashed line baseline)
        - **50-75 = Average to Above Average** (Green zone - solid)
        - **75-100 = Above Average to Maximum** (Elite zone - outstanding)

        **Visualizations:**
        - **Radar Chart** = 5-dimension performance profile with min-max scaling
        - **Timeline** = Performance trends across seasons (2022, 2023, 2024)
        - **Player Comparison** = Head-to-head statistical comparison

        **Advanced Metrics:**
        - **Games Played** = Total games in selected season
        - **Availability** = Games played as % of maximum possible games (health indicator)
        - **Total Production/Game** = Combined stats per game (points + rebounds + assists)
        - **Points/Rebounds/Assists Percentile** = Performance rank vs all players (higher = better)

        **League Rankings:**
        - **Points/Rebounds/Assists Rank** = Position among all players in category
        - **Lower rank number = better performance** (Rank #1 = best in league)

        **How to Use:**
        - **Season filter** controls all data displayed
        - **Radar chart** shows relative strengths/weaknesses at a glance
        - **Timeline** reveals development/decline patterns
        - **Percentiles** show how player compares to entire league
        - **PDF export** generates comprehensive player report
        """)

    # Update the player selection to use filtered data
    # Update the player selection to use filtered data
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        available_players = sorted(filtered_df['player'].unique())
        if not available_players:
            st.warning("No players match your filters. Try broadening your criteria.")
            return

        # Check if a player was selected from the search page
        default_player_index = 0
        if 'selected_player_from_search' in st.session_state:
            if st.session_state.selected_player_from_search in available_players:
                default_player_index = available_players.index(st.session_state.selected_player_from_search)
                # Clear the session state after use
                del st.session_state.selected_player_from_search

        selected_player = st.selectbox(
            "Select a player",
            available_players,
            index=default_player_index,
            key="main_player_select"
        )

    with col2:
        seasons = sorted(filtered_df['season'].unique(), reverse=True)
        selected_season = st.selectbox("Reference season", seasons, key="reference_season_select")

    with col3:
        compare_player = st.selectbox(
            "Compare with",
            ['None'] + [p for p in available_players if p != selected_player],
            key="compare_player_select"
        )

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
        st.plotly_chart(create_radar_chart(player_current, league_stats, selected_player), use_container_width=True)

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
        try:
            pdf_buffer = generate_pdf_report(player_current, selected_player, selected_season, metrics)
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer,
                file_name=f"{selected_player}_profile_{selected_season}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")

def generate_pdf_report(player_data, player_name, season, advanced_metrics):
    """Generate PDF report for a player"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph(f"Player Profile: {player_name}", title_style))
    story.append(Spacer(1, 12))

    # Basic Info
    basic_info = [
        ['Team:', player_data.get('team', 'N/A')],
        ['Position:', player_data.get('pos', 'N/A')],
        ['Season:', str(season)],
        ['Games Played:', str(player_data.get('games_played', 'N/A'))]
    ]

    basic_table = Table(basic_info, colWidths=[2*inch, 2*inch])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("Basic Information", styles['Heading2']))
    story.append(basic_table)
    story.append(Spacer(1, 12))

    # Performance Stats
    perf_data = [
        ['Statistic', 'Value'],
        ['Points/Game', f"{player_data.get('points_per_game', 0):.1f}"],
        ['Rebounds/Game', f"{player_data.get('rebounds_per_game', 0):.1f}"],
        ['Assists/Game', f"{player_data.get('assists_per_game', 0):.1f}"]
    ]

    perf_table = Table(perf_data, colWidths=[2*inch, 2*inch])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("Performance Statistics", styles['Heading2']))
    story.append(perf_table)
    story.append(Spacer(1, 12))

    # Advanced Metrics
    adv_data = [['Metric', 'Value']]
    for key, value in advanced_metrics.items():
        adv_data.append([key, str(value)])

    adv_table = Table(adv_data, colWidths=[2*inch, 2*inch])
    adv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("Advanced Metrics", styles['Heading2']))
    story.append(adv_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    main()
