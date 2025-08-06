from google.cloud import bigquery
import os

# Authentification (modifie si besoin)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials/streamlit-access-key.json"

# Initialisation client
client = bigquery.Client()

# Paramètres
dataset_id = "g_league"  # à adapter si différent
table_id = "team_stats_regular"  # nom de la table cible
table_ref = f"{client.project}.{dataset_id}.{table_id}"

# Chemin local du fichier
file_path = "data/bronze_scrapping/team_stats_regular.csv"

# Config du job
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    autodetect=True,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE  # ⬅️ ⚠️ Remplace la table
)

# Chargement
with open(file_path, "rb") as source_file:
    load_job = client.load_table_from_file(source_file, table_ref, job_config=job_config)

load_job.result()  # Attente de la fin du job

print(f"✅ Table '{table_id}' mise à jour dans BigQuery ({dataset_id})")
