# app.py

import streamlit as st
from google.cloud import bigquery
import pandas as pd

# Configure the page
st.set_page_config(
    page_title="G-League Scouting Platform",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page content
def main():
    st.title("🏀 G-League Scouting Platform")
    st.markdown("**Professional NBA player analysis for G-League recruitment**")

    st.markdown("---")

    # Navigation instructions
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📊 Team Overview")
        st.markdown("Analyze team performance and league standings")
        st.info("Navigate using the sidebar ➡️")

    with col2:
        st.markdown("### 🔍 Player Search")
        st.markdown("Find G-League target players with advanced filtering")
        st.success("✅ 152 target players available")

    with col3:
        st.markdown("### 👤 Player Profiles")
        st.markdown("Detailed individual player analysis and comparisons")
        st.info("Coming soon...")

    st.markdown("---")

    # Quick stats
    st.subheader("🎯 Platform Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Target Players", "152")
    with col2:
        st.metric("NBA Struggling", "68%")
    with col3:
        st.metric("Well-Rounded", "32%")
    with col4:
        st.metric("Available Players", "~70%")

if __name__ == "__main__":
    main()
