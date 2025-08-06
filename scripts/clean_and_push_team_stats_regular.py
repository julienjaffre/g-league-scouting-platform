from google.cloud import bigquery
from google.cloud import storage
import pandas as pd

# === Config ===
project_id = "carbide-bonsai-466217-v2"
dataset_id = "bronze"
bucket_name = "league-scouting-platform_bronze"
gcs_path = "bronze/team_stats_regular_clean.csv"
local_path = "data/bronze_scrapping/team_stats_regular_clean.csv"
table_id = f"{project_id}.{dataset_id}.team_stats_regular_clean"

# === Nettoyage CSV ===
print("🧼 Lecture et nettoyage du fichier CSV...")
df = pd.read_csv("data/bronze_scrapping/team_stats_regular.csv")

# Supprimer les colonnes vides ou "unnamed"
df = df.loc[:, ~df.columns.str.contains("^unnamed", case=False)]
df = df.dropna(how='all', axis=1)

# Nettoyer et convertir la colonne 'gp' en int (en supprimant les lignes non convertibles)
df['gp'] = pd.to_numeric(df['gp'], errors='coerce')
df = df.dropna(subset=['gp'])
df['gp'] = df['gp'].astype(int)

# Tu peux ajouter ce nettoyage pour d'autres colonnes numériques si besoin, exemple :
# cols_to_clean = ['w', 'l', 'win', 'min', 'pts', 'fgm', 'fga', 'fg', 'col_0_625', '3pa', '3p', 'ftm', 'fta', 'ft', 'oreb', 'dreb', 'reb', 'ast', 'tov', 'stl', 'blk', 'blka', 'pf', 'pfd']
# for col in cols_to_clean:
#     df[col] = pd.to_numeric(df[col], errors='coerce')

#     # Si tu veux supprimer aussi les lignes où ces colonnes sont invalides, décommenter :
#     # df = df.dropna(subset=[col])

# Sauvegarder le fichier nettoyé
df.to_csv(local_path, index=False, encoding='utf-8')
print(f"✅ Fichier nettoyé sauvegardé : {local_path}")

# === Upload vers GCS ===
print("☁️ Upload du fichier dans GCS...")
storage_client = storage.Client(project=project_id)
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(gcs_path)
blob.upload_from_filename(local_path)
print(f"✅ Upload terminé : gs://{bucket_name}/{gcs_path}")

# === Définir le schéma manuellement ===
schema = [
    bigquery.SchemaField("season", "STRING"),
    bigquery.SchemaField("team", "STRING"),
    bigquery.SchemaField("url", "STRING"),
    bigquery.SchemaField("gp", "INTEGER"),
    bigquery.SchemaField("w", "INTEGER"),
    bigquery.SchemaField("l", "FLOAT"),
    bigquery.SchemaField("win", "FLOAT"),
    bigquery.SchemaField("min", "FLOAT"),
    bigquery.SchemaField("pts", "FLOAT"),
    bigquery.SchemaField("fgm", "FLOAT"),
    bigquery.SchemaField("fga", "FLOAT"),
    bigquery.SchemaField("fg", "FLOAT"),
    bigquery.SchemaField("col_0_625", "FLOAT"),
    bigquery.SchemaField("3pa", "FLOAT"),
    bigquery.SchemaField("3p", "FLOAT"),
    bigquery.SchemaField("ftm", "FLOAT"),
    bigquery.SchemaField("fta", "FLOAT"),
    bigquery.SchemaField("ft", "FLOAT"),
    bigquery.SchemaField("oreb", "FLOAT"),
    bigquery.SchemaField("dreb", "FLOAT"),
    bigquery.SchemaField("reb", "FLOAT"),
    bigquery.SchemaField("ast", "FLOAT"),
    bigquery.SchemaField("tov", "FLOAT"),
    bigquery.SchemaField("stl", "FLOAT"),
    bigquery.SchemaField("blk", "FLOAT"),
    bigquery.SchemaField("blka", "FLOAT"),
    bigquery.SchemaField("pf", "FLOAT"),
    bigquery.SchemaField("pfd", "FLOAT"),
]

# === Chargement dans BigQuery ===
print("📥 Chargement dans BigQuery...")
bq_client = bigquery.Client(project=project_id)
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    schema=schema,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)

uri = f"gs://{bucket_name}/{gcs_path}"
load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)
load_job.result()

print(f"✅ Chargement terminé dans BigQuery : {table_id}")
