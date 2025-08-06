import os
from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
import json

def get_bigquery_client():
    """
    Initialize BigQuery client with flexible authentication
    Works for multiple developers and production deployment
    """
    try:
        # Method 1: Try environment variable for service account key path
        key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if key_path and os.path.exists(key_path):
            credentials = service_account.Credentials.from_service_account_file(key_path)
            client = bigquery.Client(credentials=credentials, location="US")
            return client

        # Method 2: Try service account key from environment variable (JSON string)
        key_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
        if key_json:
            key_dict = json.loads(key_json)
            credentials = service_account.Credentials.from_service_account_info(key_dict)
            client = bigquery.Client(credentials=credentials, location="US")
            return client

        # Method 3: Try default credentials (works in Cloud Run)
        client = bigquery.Client(location="US")
        return client

    except Exception as e:
        st.error(f"❌ BigQuery authentication failed: {str(e)}")
        st.error("Please check your authentication setup")
        return None

def test_bigquery_connection(client):
    """Test if BigQuery client is working"""
    if not client:
        return False

    try:
        # Simple test query
        query = "SELECT 1 as test"
        result = client.query(query).result()
        return True
    except Exception as e:
        st.error(f"BigQuery connection test failed: {e}")
        return False
