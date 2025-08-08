import streamlit as st

# Page configuration
st.set_page_config(
    page_title="G-League Scouting Platform",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("🏀 G-League Scouting Platform")
st.markdown("### A Data-Driven Approach to NBA Player Scouting")

# Hero section
st.markdown("""
---
**Welcome to the G-League Scouting Analytics Platform**

This platform leverages advanced analytics to identify undervalued NBA players using G-League performance data,
helping scouts and analysts make data-driven decisions.
""")

# Navigation guide
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📊 **Navigation**

    **📋 Presentation**
    Project overview, methodology, and key insights

    **🏀 Team Overview**
    Team statistics, performance analysis, and comparisons
    """)

with col2:
    st.markdown("""
    #### 🔍 **Player Analytics**

    **🔍 Player Search**
    Advanced filtering and search capabilities

    **👤 Player Profiles**
    Detailed individual player analytics and projections
    """)

# Key features
st.markdown("---")
st.markdown("#### 🎯 **Key Features**")

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.markdown("""
    **📈 Advanced Analytics**
    - Performance metrics
    - Statistical modeling
    - Trend analysis
    """)

with feature_col2:
    st.markdown("""
    **🎯 Player Identification**
    - Undervalued talent detection
    - Potential assessment
    - Comparison tools
    """)

with feature_col3:
    st.markdown("""
    **📊 Data Integration**
    - G-League statistics
    - NBA performance data
    - Contract information
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with dbt, Google BigQuery, and Streamlit | Deployed on Cloud Run</p>
</div>
""", unsafe_allow_html=True)

# Sidebar info
st.sidebar.markdown("## 🏀 G-League Scouting")
