from google.cloud import storage
import pandas as pd
import re
import os

# === Config ===
project_id = "carbide-bonsai-466217-v2"
bucket_name = "league-scouting-platform_bronze"
local_output_folder = "data/bronze_scrapping"
os.makedirs(local_output_folder, exist_ok=True)

# === Connexion GCS ===
print("🚀 Connexion à GCS...")
storage_client = storage.Client(project=project_id)
bucket = storage_client.bucket(bucket_name)

# === Fonction de nettoyage des noms de colonnes ===
def clean_column_name(col):
    col = col.strip()
    if re.match(r"^\d+(\.\d+)?$", col):  # nom numérique (ex: "0.625")
        col = f"col_{col.replace('.', '_')}"
    col = re.sub(r"\s+", "_", col)
    col = re.sub(r"[^a-zA-Z0-9_]", "", col)
    return col.lower()

# === Traitement ===
print("📦 Recherche des fichiers CSV à la racine de GCS...")
blobs = bucket.list_blobs(prefix="")

for blob in blobs:
    if not blob.name.endswith(".csv") or "/" in blob.name.strip("/"):
        continue

    print(f"\n📥 Téléchargement de `{blob.name}`...")
    local_path = os.path.join(local_output_folder, os.path.basename(blob.name))
    blob.download_to_filename(local_path)
    print(f"✅ Fichier téléchargé : {local_path}")

    try:
        # Lecture et nettoyage des colonnes
        df = pd.read_csv(local_path)
        original_cols = list(df.columns)
        cleaned_cols = [clean_column_name(c) for c in original_cols]

        if original_cols != cleaned_cols:
            print("🧼 Colonnes modifiées pour compatibilité BQ.")
            df.columns = cleaned_cols
            df.to_csv(local_path, index=False)
            print(f"✅ Colonnes nettoyées et fichier réécrit : {local_path}")
        else:
            print("✅ Colonnes déjà valides. Pas de nettoyage nécessaire.")

    except Exception as e:
        print(f"❌ Erreur pendant le traitement de {blob.name} : {e}")
