from google.cloud import bigquery
import pandas as pd

def load_data_from_bq(query: str, credentials_path: str = "credentials/streamlit-access-key.json") -> pd.DataFrame:
    client = bigquery.Client.from_service_account_json(credentials_path)
    df = client.query(query).to_dataframe()
    return df
