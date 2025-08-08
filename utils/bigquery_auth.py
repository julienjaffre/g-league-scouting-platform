import os
from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st  # ← ADD THIS LINE
import json

def get_bigquery_client():
    """
    Initialize BigQuery client for Cloud Run deployment
    """
    try:
        # Method 1: Service account key from environment variable (Cloud Run)
        key_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
        if key_json:
            key_dict = json.loads(key_json)
            credentials = service_account.Credentials.from_service_account_info(key_dict)
            client = bigquery.Client(credentials=credentials, project='carbide-bonsai-466217-v2', location="US")
            return client

        # Method 2: Default Cloud Run service account
        client = bigquery.Client(project='carbide-bonsai-466217-v2', location="US")
        return client

    except Exception as e:
        st.error(f"❌ BigQuery authentication failed: {str(e)}")
        return None

def test_bigquery_connection(client):
    """Test if BigQuery client is working"""
    if not client:
        return False

    try:
        query = "SELECT 1 as test"
        result = client.query(query).result()
        return True
    except Exception as e:
        st.error(f"❌ BigQuery connection test failed: {e}")
        return False
