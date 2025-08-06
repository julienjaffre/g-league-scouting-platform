# streamlit_app/utils/bigquery_client.py
import streamlit as st
from google.cloud import bigquery
import pandas as pd

@st.cache_resource
def get_bigquery_client():
    """Client BigQuery réutilisable"""
    return bigquery.Client()

@st.cache_data(ttl=3600)
def load_data_from_bq(query: str) -> pd.DataFrame:
    """Charge des données depuis BigQuery avec cache"""
    client = get_bigquery_client()
    return client.query(query).to_dataframe()