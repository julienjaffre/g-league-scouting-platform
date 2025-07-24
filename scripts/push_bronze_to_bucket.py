from google.cloud import storage
from pathlib import Path

# === Config ===
BUCKET_NAME = "league-scouting-platform_bronze"
LOCAL_DIR = Path("data/bronze")
DEST_PREFIX = "bronze/"  # Chemin cible dans le bucket

# === Initialisation du client GCS ===
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)

# === Parcours des fichiers CSV et upload ===
for file_path in LOCAL_DIR.glob("*.csv"):
    blob = bucket.blob(f"{DEST_PREFIX}{file_path.name}")
    blob.upload_from_filename(file_path.as_posix())
    print(f"✅ Upload: {file_path.name} → gs://{BUCKET_NAME}/{DEST_PREFIX}{file_path.name}")
