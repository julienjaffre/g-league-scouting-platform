import streamlit as st
import pandas as pd
import sys
import os
from google.cloud import bigquery

# Add the project root to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.bigquery_auth import get_bigquery_client, test_bigquery_connection

# === Connexion BigQuery ===
@st.cache_resource
def get_client():
    """Get cached BigQuery client"""
    return get_bigquery_client()

# Update all your query functions to use:
def your_query_function():
    client = get_client()
    if not client:
        st.error("❌ Cannot connect to BigQuery. Please check authentication.")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_player_data():
    """Load G-League target players from BigQuery with minutes per game"""
    client = get_client()  # ← CHANGE THIS LINE
    if not client:
        st.error("❌ Cannot connect to BigQuery. Please check authentication.")
        return pd.DataFrame()
    query = """
    WITH stats_raw AS (
        SELECT
            player, season, team, pos, age, g, mp_per_game,
            CASE
                WHEN (fga_per_game + 0.44 * fta_per_game) > 0
                THEN pts_per_game / (2 * (fga_per_game + 0.44 * fta_per_game))
                ELSE NULL
            END AS ts_pct,
            pts_per_game AS pts, trb_per_game AS trb, ast_per_game AS ast,
            stl_per_game AS stl, blk_per_game AS blk,
            ROW_NUMBER() OVER (
                PARTITION BY player
                ORDER BY g DESC, pts_per_game DESC,
                CASE WHEN team LIKE '%TM' THEN 1 ELSE 0 END
            ) as rn
        FROM `carbide-bonsai-466217-v2.bronze.player_per_game_2022_2024`
        WHERE season = 2024
    ),

    stats AS (
        SELECT player AS Player, season AS Season, team AS Team, pos AS Pos,
               age AS Age, mp_per_game AS mp, ts_pct, pts, trb, ast, stl, blk
        FROM stats_raw WHERE rn = 1
    ),

    contracts AS (
        SELECT player, team, `202526`, `202627`, `202728`, `202829`, `202930`, `203031`,
               guaranteed, uncontracted
        FROM `carbide-bonsai-466217-v2.bronze.nba_contracts_complete`
    ),

    joined AS (
        SELECT s.*, c.`202526`, c.`202627`, c.`202728`, c.`202829`, c.`202930`, c.`203031`,
               c.guaranteed, c.uncontracted,
               CASE
                   WHEN c.player IS NULL THEN 'Free Agent / No Contract Data'
                   WHEN c.uncontracted = TRUE THEN 'Uncontracted'
                   WHEN COALESCE(c.`202526`, 0) = 0 AND COALESCE(c.`202627`, 0) = 0 THEN 'Free Agent'
                   WHEN COALESCE(c.`202627`, 0) = 0 AND COALESCE(c.`202526`, 0) > 0 THEN 'Expiring Contract'
                   WHEN COALESCE(c.`202627`, 0) > 0 AND COALESCE(c.`202728`, 0) = 0 THEN '1 Year Left'
                   ELSE 'Multi-Year Contract'
               END AS contract_status
        FROM stats s
        LEFT JOIN contracts c ON LOWER(TRIM(s.Player)) = LOWER(TRIM(c.player))
    ),

    player_percentiles AS (
        SELECT *,
            NTILE(100) OVER (PARTITION BY Pos ORDER BY pts) AS pts_percentile,
            NTILE(100) OVER (PARTITION BY Pos ORDER BY trb) AS trb_percentile,
            NTILE(100) OVER (PARTITION BY Pos ORDER BY ast) AS ast_percentile,
            NTILE(100) OVER (ORDER BY ts_pct) AS ts_percentile
        FROM joined WHERE ts_pct IS NOT NULL
    ),

    final_classification AS (
        SELECT *,
            CASE
                WHEN (pts_percentile BETWEEN 0 AND 25 OR trb_percentile BETWEEN 0 AND 25 OR ast_percentile BETWEEN 0 AND 25)
                     AND contract_status IN ('Free Agent / No Contract Data', 'Expiring Contract', 'Uncontracted', 'Free Agent')
                     AND age <= 28
                THEN 'NBA Struggling / G-League Potential'
                WHEN (pts_percentile BETWEEN 25 AND 75 AND trb_percentile BETWEEN 25 AND 75 AND ast_percentile BETWEEN 25 AND 75 AND ts_percentile BETWEEN 25 AND 75)
                     AND contract_status IN ('Free Agent / No Contract Data', 'Expiring Contract', 'Uncontracted', 'Free Agent')
                     AND age <= 28
                THEN 'Well-Rounded Average'
                ELSE 'Not G-League Target'
            END AS g_league_category
        FROM player_percentiles
    )

    SELECT * FROM final_classification
    WHERE g_league_category != 'Not G-League Target'
    ORDER BY Player
    """
    return client.query(query).to_dataframe()

def main():
    st.title("🔍 G-League Player Search")
    st.markdown("**Find the best NBA candidates for your G-League team**")

    # Load data
    with st.spinner("Loading player data..."):
        try:
            df = load_player_data()
            st.success(f"✅ {len(df)} target players loaded")
        except Exception as e:
            st.error(f"❌ Loading error: {str(e)}")
            st.stop()

    # Sidebar filters with help text
    st.sidebar.header("🎯 Search Filters")

    # G-League category filter with help
    st.sidebar.subheader("G-League Category")
    selected_categories = st.sidebar.multiselect(
        "Player Type",
        options=df['g_league_category'].unique(),
        default=df['g_league_category'].unique(),
        help="🔍 NBA Struggling = Players with specific weaknesses to develop\n🔍 Well-Rounded = Average players across all statistics"
    )

    # Position filter with help
    st.sidebar.subheader("Position")
    selected_positions = st.sidebar.multiselect(
        "Positions",
        options=sorted(df['Pos'].unique()),
        default=sorted(df['Pos'].unique()),
        help="Basketball positions: PG=Point Guard, SG=Shooting Guard, SF=Small Forward, PF=Power Forward, C=Center"
    )

    # Contract status filter with help
    st.sidebar.subheader("Contract Status")
    selected_contracts = st.sidebar.multiselect(
        "Availability",
        options=df['contract_status'].unique(),
        default=df['contract_status'].unique(),
        help="🟢 Free Agent = Available immediately\n🟡 Expiring = Available end of season\n🔴 Multi-Year = Less likely available"
    )

    # Performance filters with help
    st.sidebar.subheader("Performance")

    # Age filter (full width)
    age_range = st.sidebar.slider(
        "Age",
        min_value=int(df['Age'].min()),
        max_value=int(df['Age'].max()),
        value=(int(df['Age'].min()), int(df['Age'].max())),
        help="Player age in years (younger players typically have more development potential)"
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        mp_range = st.slider(
            "Minutes per game",
            min_value=float(df['mp'].min()),
            max_value=float(df['mp'].max()),
            value=(float(df['mp'].min()), float(df['mp'].max())),
            step=0.5,
            help="Minutes played per game. 30+ = starter, 15-25 = role player, <15 = limited opportunity/stuck behind stars"
        )

    with col2:
        pts_range = st.slider(
            "Points per game",
            min_value=float(df['pts'].min()),
            max_value=float(df['pts'].max()),
            value=(float(df['pts'].min()), float(df['pts'].max())),
            step=0.5,
            help="Average points scored per game (higher = better scorer)"
        )

    # Advanced filters (expandable) with help
    with st.sidebar.expander("🔧 Advanced Filters"):
        ts_range = st.slider(
            "True Shooting %",
            min_value=float(df['ts_pct'].min()),
            max_value=float(df['ts_pct'].max()),
            value=(float(df['ts_pct'].min()), float(df['ts_pct'].max())),
            step=0.01,
            format="%.3f",
            help="Overall shooting efficiency: accounts for 2-pointers, 3-pointers, and free throws. NBA average ≈ 0.570"
        )

        reb_range = st.slider(
            "Rebounds per game",
            min_value=float(df['trb'].min()),
            max_value=float(df['trb'].max()),
            value=(float(df['trb'].min()), float(df['trb'].max())),
            step=0.1,
            help="Total rebounds (offensive + defensive) per game. Centers typically 8-12, Guards 3-6"
        )

        ast_range = st.slider(
            "Assists per game",
            min_value=float(df['ast'].min()),
            max_value=float(df['ast'].max()),
            value=(float(df['ast'].min()), float(df['ast'].max())),
            step=0.1,
            help="Average assists per game (playmaking ability). Point guards typically 4-8, Centers 1-3"
        )

    # SIDEBAR GLOSSARY
    st.sidebar.markdown("---")
    with st.sidebar.expander("📚 Basketball Glossary"):
        st.markdown("""
        **Performance Stats:**
        - **PTS** = Points per game
        - **TRB** = Total rebounds per game
        - **AST** = Assists per game
        - **MP** = Minutes per game (playing time)
        - **STL** = Steals per game
        - **BLK** = Blocks per game
        - **TS%** = True Shooting % (overall shooting efficiency)

        **Contract Terms:**
        - **Free Agent** = No current contract, available immediately
        - **Expiring** = Contract ends this season
        - **Uncontracted** = Flagged as available by data source
        - **Multi-Year** = Under contract for multiple seasons

        **G-League Categories:**
        - **NBA Struggling** = Players with specific weaknesses to develop
        - **Well-Rounded** = Average across all stats, no major strengths/weaknesses

        **Percentiles:**
        - **Position-adjusted rankings** (0-100, where 50 = average for position)
        - **Higher number = better performance relative to position**

        **Positions:**
        - **PG** = Point Guard (playmaker, ball handler)
        - **SG** = Shooting Guard (scorer, perimeter shooter)
        - **SF** = Small Forward (versatile wing player)
        - **PF** = Power Forward (interior player, rebounder)
        - **C** = Center (rim protector, post player)
        """)

    # Apply filters
    filtered_df = df[
        (df['g_league_category'].isin(selected_categories)) &
        (df['Pos'].isin(selected_positions)) &
        (df['contract_status'].isin(selected_contracts)) &
        (df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1]) &
        (df['mp'] >= mp_range[0]) & (df['mp'] <= mp_range[1]) &
        (df['pts'] >= pts_range[0]) & (df['pts'] <= pts_range[1]) &
        (df['ts_pct'] >= ts_range[0]) & (df['ts_pct'] <= ts_range[1]) &
        (df['trb'] >= reb_range[0]) & (df['trb'] <= reb_range[1]) &
        (df['ast'] >= ast_range[0]) & (df['ast'] <= ast_range[1])
    ]

    # Main content with enhanced metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🎯 Players Found", len(filtered_df), help="Number of players matching your criteria")

    with col2:
        if len(filtered_df) > 0:
            avg_age = filtered_df['Age'].mean()
            st.metric("📅 Average Age", f"{avg_age:.1f} years", help="Average age of filtered players")

    with col3:
        if len(filtered_df) > 0:
            available = len(filtered_df[filtered_df['contract_status'].str.contains('Free Agent|Uncontracted')])
            st.metric("✅ Available Now", f"{available}", help="Players available for immediate signing")

    with col4:
        if len(filtered_df) > 0:
            struggling = len(filtered_df[filtered_df['g_league_category'] == 'NBA Struggling / G-League Potential'])
            st.metric("🔧 Development Targets", f"{struggling}", help="Players with specific areas to improve")

    if len(filtered_df) == 0:
        st.warning("🚫 No players match your criteria. Try broadening your filters.")
        return

    # Visualization tabs - REMOVED Performance tab
    tab1, tab2 = st.tabs(["📊 Overview", "📋 Detailed List"])

    with tab1:
    # Clean and simple: just the 2 original charts
        col1, col2 = st.columns(2)

        with col1:
            # Contract status distribution
            contract_counts = filtered_df['contract_status'].value_counts()
            fig1 = px.pie(
                values=contract_counts.values,
                names=contract_counts.index,
                title="Distribution by Contract Status"
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # G-League category distribution
            category_counts = filtered_df['g_league_category'].value_counts()
            fig2 = px.bar(
                x=category_counts.index,
                y=category_counts.values,
                title="Distribution by G-League Category",
                labels={'x': 'Category', 'y': 'Number of Players'}
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Row 2: New strategic visualizations
            col3, col4 = st.columns(2)


    with tab2:
        # Detailed player table with enhanced column config
        st.subheader("📋 Detailed Player List")

        # Select columns to display
        display_columns = [
            'Player', 'Age', 'Pos', 'Team', 'mp', 'g_league_category',
            'contract_status', 'pts', 'trb', 'ast', 'ts_pct',
            'pts_percentile', 'trb_percentile', 'ast_percentile'
        ]

        # Format the dataframe
        display_df = filtered_df[display_columns].copy()
        display_df = display_df.round({
            'mp': 1, 'pts': 1, 'trb': 1, 'ast': 1, 'ts_pct': 3,
            'pts_percentile': 0, 'trb_percentile': 0, 'ast_percentile': 0
        })

        # Add sorting options with user-friendly names
        sort_col1, sort_col2 = st.columns(2)
        with sort_col1:
            # Create a mapping of display names to actual column names
            sort_options = {
                'Player': 'Player',
                'Age': 'Age',
                'Points': 'pts',
                'Rebounds': 'trb',
                'Assists': 'ast',
                'Minutes': 'mp',
                'True Shooting %': 'ts_pct'
            }

            sort_display = st.selectbox(
                "Sort by:",
                options=list(sort_options.keys()),
                index=2,  # Default to "Points"
                help="Choose which column to sort the results by"
            )

            # Get the actual column name
            sort_by = sort_options[sort_display]

        with sort_col2:
            sort_order = st.selectbox(
                "Order:",
                options=['Descending', 'Ascending'],
                help="Sort from highest to lowest (Descending) or lowest to highest (Ascending)"
            )

        ascending = sort_order == 'Ascending'
        display_df = display_df.sort_values(sort_by, ascending=ascending)

        # Enhanced dataframe with column tooltips
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            column_config={
                'Player': st.column_config.TextColumn('Player', help='Player name'),
                'Age': st.column_config.NumberColumn('Age', help='Player age in years'),
                'Pos': st.column_config.TextColumn('Position', help='Primary playing position (PG/SG/SF/PF/C)'),
                'Team': st.column_config.TextColumn('Team', help='Last NBA team played for'),
                'mp': st.column_config.NumberColumn(
                    'Minutes/Game',
                    help='Average minutes played per game. 30+ = starter, 20-30 = key role player, 10-20 = bench, <10 = limited opportunity',
                    format="%.1f"
                ),
                'g_league_category': st.column_config.TextColumn(
                    'G-League Category',
                    help='NBA Struggling = specific weaknesses to develop; Well-Rounded = average across all stats'
                ),
                'contract_status': st.column_config.TextColumn(
                    'Contract Status',
                    help='Free Agent = available now; Expiring = available end of season; Multi-Year = under contract'
                ),
                'pts': st.column_config.NumberColumn(
                    'Points/Game',
                    help='Average points scored per game (NBA average ≈ 10-15 for role players)',
                    format="%.1f"
                ),
                'trb': st.column_config.NumberColumn(
                    'Rebounds/Game',
                    help='Total rebounds (offensive + defensive) per game. Centers: 8-12, Guards: 3-6',
                    format="%.1f"
                ),
                'ast': st.column_config.NumberColumn(
                    'Assists/Game',
                    help='Average assists per game (playmaking). Point guards: 4-8, Centers: 1-3',
                    format="%.1f"
                ),
                'ts_pct': st.column_config.NumberColumn(
                    'True Shooting %',
                    help='Overall shooting efficiency (2PT + 3PT + FT). NBA average ≈ 0.570, Good ≈ 0.600+',
                    format="%.3f"
                ),
                'pts_percentile': st.column_config.NumberColumn(
                    'Points Percentile',
                    help='Scoring rank vs other players at same position (0-100, 50=average, higher=better)',
                    format="%.0f"
                ),
                'trb_percentile': st.column_config.NumberColumn(
                    'Rebounds Percentile',
                    help='Rebounding rank vs other players at same position (0-100, 50=average, higher=better)',
                    format="%.0f"
                ),
                'ast_percentile': st.column_config.NumberColumn(
                    'Assists Percentile',
                    help='Playmaking rank vs other players at same position (0-100, 50=average, higher=better)',
                    format="%.0f"
                )
            }
        )

        # Export functionality with help
        if st.button("📥 Export Results (CSV)", help="Download filtered results as CSV file for further analysis"):
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"g_league_targets_{len(display_df)}_players.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
