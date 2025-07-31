from google.cloud import bigquery
import os
import re

# === Config ===
project_id = "carbide-bonsai-466217-v2"
dataset_id = "bronze"
local_folder = "data/bronze_scrapping"

# === Initialisation client BigQuery ===
print("🚀 Connexion à BigQuery...")
bq_client = bigquery.Client(project=project_id)

# === Parcours des fichiers dans le dossier ===
print(f"📁 Lecture des fichiers dans `{local_folder}`...")
for filename in os.listdir(local_folder):
    if not filename.endswith(".csv"):
        continue

    file_path = os.path.join(local_folder, filename)
    table_name = re.sub(r"[^a-zA-Z0-9_]", "_", filename.replace(".csv", "")).lower()
    table_id = f"{project_id}.{dataset_id}.{table_name}"

    print(f"\n🔄 Chargement de `{file_path}` dans `{table_id}`...")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    try:
        with open(file_path, "rb") as file:
            load_job = bq_client.load_table_from_file(
                file, table_id, job_config=job_config
            )
            load_job.result()
        print(f"✅ Terminé : {table_id}")
    except Exception as e:
        print(f"❌ Erreur pour {table_id} : {e}")
