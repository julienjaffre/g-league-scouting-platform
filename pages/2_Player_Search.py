import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
import os

st.set_page_config(page_title="G-League Player Search", page_icon="🔍", layout="wide")

# BigQuery connection
@st.cache_resource
def init_bigquery():
    key_path = "/home/maxence.garnier/dbt-credentials/dbt-scounting-key.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    client = bigquery.Client()
    return client

@st.cache_data(ttl=3600)
def load_player_data():
    """Load G-League target players from BigQuery"""
    client = init_bigquery()
    query = """
    SELECT *
    FROM `carbide-bonsai-466217-v2.scouting_dbt_gold.player_contracts_gold`
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

    # Sidebar filters
    st.sidebar.header("🎯 Search Filters")

    # G-League category filter
    st.sidebar.subheader("G-League Category")
    selected_categories = st.sidebar.multiselect(
        "Player Type",
        options=df['g_league_category'].unique(),
        default=df['g_league_category'].unique(),
        help="NBA Struggling = Players with specific weaknesses\nWell-Rounded = Average players across all stats"
    )

    # Position filter
    st.sidebar.subheader("Position")
    selected_positions = st.sidebar.multiselect(
        "Positions",
        options=sorted(df['Pos'].unique()),
        default=sorted(df['Pos'].unique())
    )

    # Contract status filter
    st.sidebar.subheader("Contract Status")
    selected_contracts = st.sidebar.multiselect(
        "Availability",
        options=df['contract_status'].unique(),
        default=df['contract_status'].unique(),
        help="Free Agent = Available immediately\nExpiring = Available end of season"
    )

    # Performance filters
    st.sidebar.subheader("Performance")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        age_range = st.slider(
            "Age",
            min_value=int(df['Age'].min()),
            max_value=int(df['Age'].max()),
            value=(int(df['Age'].min()), int(df['Age'].max()))
        )

    with col2:
        pts_range = st.slider(
            "Points per game",
            min_value=float(df['pts'].min()),
            max_value=float(df['pts'].max()),
            value=(float(df['pts'].min()), float(df['pts'].max())),
            step=0.5
        )

    # Advanced filters (expandable)
    with st.sidebar.expander("🔧 Advanced Filters"):
        ts_range = st.slider(
            "True Shooting %",
            min_value=float(df['ts_pct'].min()),
            max_value=float(df['ts_pct'].max()),
            value=(float(df['ts_pct'].min()), float(df['ts_pct'].max())),
            step=0.01,
            format="%.3f"
        )

        reb_range = st.slider(
            "Rebounds per game",
            min_value=float(df['trb'].min()),
            max_value=float(df['trb'].max()),
            value=(float(df['trb'].min()), float(df['trb'].max())),
            step=0.1
        )

        ast_range = st.slider(
            "Assists per game",
            min_value=float(df['ast'].min()),
            max_value=float(df['ast'].max()),
            value=(float(df['ast'].min()), float(df['ast'].max())),
            step=0.1
        )

    # Apply filters
    filtered_df = df[
        (df['g_league_category'].isin(selected_categories)) &
        (df['Pos'].isin(selected_positions)) &
        (df['contract_status'].isin(selected_contracts)) &
        (df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1]) &
        (df['pts'] >= pts_range[0]) & (df['pts'] <= pts_range[1]) &
        (df['ts_pct'] >= ts_range[0]) & (df['ts_pct'] <= ts_range[1]) &
        (df['trb'] >= reb_range[0]) & (df['trb'] <= reb_range[1]) &
        (df['ast'] >= ast_range[0]) & (df['ast'] <= ast_range[1])
    ]

    # Main content
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🎯 Players Found", len(filtered_df))

    with col2:
        if len(filtered_df) > 0:
            avg_age = filtered_df['Age'].mean()
            st.metric("📅 Average Age", f"{avg_age:.1f} years")

    with col3:
        if len(filtered_df) > 0:
            available = len(filtered_df[filtered_df['contract_status'].str.contains('Free Agent|Uncontracted')])
            st.metric("✅ Available", f"{available}")

    with col4:
        if len(filtered_df) > 0:
            struggling = len(filtered_df[filtered_df['g_league_category'] == 'NBA Struggling / G-League Potential'])
            st.metric("🔧 Development Targets", f"{struggling}")

    if len(filtered_df) == 0:
        st.warning("🚫 No players match your criteria. Try broadening your filters.")
        return

    # Visualization tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Performance", "📋 Detailed List"])

    with tab1:
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

    with tab2:
        # Performance scatter plot
        fig3 = px.scatter(
            filtered_df,
            x='pts',
            y='ts_pct',
            color='g_league_category',
            size='Age',
            hover_data=['Player', 'Pos', 'Team', 'contract_status'],
            title="Performance: Points vs Shooting Efficiency",
            labels={'pts': 'Points per game', 'ts_pct': 'True Shooting %'}
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Performance comparison
        col1, col2 = st.columns(2)
        with col1:
            fig4 = px.box(
                filtered_df,
                x='g_league_category',
                y='pts',
                title="Points Distribution by Category"
            )
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            fig5 = px.box(
                filtered_df,
                x='Pos',
                y='trb',
                title="Rebounds Distribution by Position"
            )
            st.plotly_chart(fig5, use_container_width=True)

    with tab3:
        # Detailed player table
        st.subheader("📋 Detailed Player List")

        # Select columns to display
        display_columns = [
            'Player', 'Age', 'Pos', 'Team', 'g_league_category',
            'contract_status', 'pts', 'trb', 'ast', 'ts_pct',
            'pts_percentile', 'trb_percentile', 'ast_percentile'
        ]

        # Format the dataframe
        display_df = filtered_df[display_columns].copy()
        display_df = display_df.round({
            'pts': 1, 'trb': 1, 'ast': 1, 'ts_pct': 3,
            'pts_percentile': 0, 'trb_percentile': 0, 'ast_percentile': 0
        })

        # Add sorting options
        sort_col1, sort_col2 = st.columns(2)
        with sort_col1:
            sort_by = st.selectbox(
                "Sort by:",
                options=['Player', 'Age', 'pts', 'trb', 'ast', 'ts_pct'],
                index=2
            )
        with sort_col2:
            sort_order = st.selectbox("Order:", options=['Descending', 'Ascending'])

        ascending = sort_order == 'Ascending'
        display_df = display_df.sort_values(sort_by, ascending=ascending)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )

        # Export functionality
        if st.button("📥 Export Results (CSV)"):
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"g_league_targets_{len(display_df)}_players.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
