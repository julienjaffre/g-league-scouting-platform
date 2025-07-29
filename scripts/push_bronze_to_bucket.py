from google.cloud import storage
from pathlib import Path

# === Config ===
BUCKET_NAME = "league-scouting-platform_bronze"
LOCAL_DIR = Path("data/bronze")
DEST_PREFIX = "bronze/"  # Chemin GCS cible

# === Initialisation client GCS ===
print("🚀 Initialisation du client GCS...")
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)

# === Parcours des fichiers et upload ===
print(f"📂 Parcours des fichiers dans {LOCAL_DIR}...\n")

csv_files = list(LOCAL_DIR.glob("*.csv"))
if not csv_files:
    print("❌ Aucun fichier CSV trouvé à uploader.")
else:
    for file_path in csv_files:
        destination = f"{DEST_PREFIX}{file_path.name}"
        blob = bucket.blob(destination)
        blob.upload_from_filename(file_path.as_posix())
        print(f"✅ Upload : {file_path.name} → gs://{BUCKET_NAME}/{destination}")

print("\n🎉 Tous les fichiers ont été uploadés avec succès.")
