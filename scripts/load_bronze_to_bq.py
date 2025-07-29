from google.cloud import bigquery
from google.cloud import storage
import re

# === Config ===
project_id = "carbide-bonsai-466217-v2"
dataset_id = "bronze"
bucket_name = "league-scouting-platform_bronze"
prefix = "bronze/"

# === Init clients ===
print("🚀 Initialisation des clients GCP...")
bq_client = bigquery.Client(project=project_id)
gcs_client = storage.Client(project=project_id)
bucket = gcs_client.bucket(bucket_name)

# === Liste des fichiers CSV dans le bucket ===
print("📦 Recherche des fichiers CSV dans GCS...")
blobs = bucket.list_blobs(prefix=prefix)

for blob in blobs:
    if not blob.name.endswith(".csv"):
        continue

    # 🧼 Nettoyage du nom de fichier pour faire un nom de table valide
    file_name = blob.name.split("/")[-1].replace(".csv", "")
    table_name = re.sub(r"[^a-zA-Z0-9_]", "_", file_name).lower()
    gcs_uri = f"gs://{bucket_name}/{blob.name}"
    table_id = f"{project_id}.{dataset_id}.{table_name}"

    print(f"\n🔄 Chargement de `{gcs_uri}` dans `{table_id}`...")

    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    try:
        load_job = bq_client.load_table_from_uri(
            gcs_uri, table_id, job_config=job_config
        )
        load_job.result()
        print(f"✅ Terminé : {table_id}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {table_id} : {e}")
