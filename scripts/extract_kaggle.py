import pandas as pd
import os

# 📁 Chemins
SOURCE_DIR = "data/kaggle/csv"      # CSV extraits du zip
EXPORT_DIR = "data/bronze"          # Export filtré
SEASONS_TO_KEEP = ("2022", "2023", "2024")  # Saisons conservées

# 📂 Créer le dossier d’export s’il n’existe pas
os.makedirs(EXPORT_DIR, exist_ok=True)

# 🔁 Parcourir tous les fichiers CSV
print("🔍 Début de l'extraction Kaggle filtrée...")

for file in os.listdir(SOURCE_DIR):
    if file.endswith(".csv"):
        file_path = os.path.join(SOURCE_DIR, file)
        print(f"\n📄 Traitement : {file}")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {file} : {e}")
            continue

        # 🔍 Filtrage si colonne `season` présente
        if "season" in df.columns:
            df["season"] = df["season"].astype(str)
            df_filtered = df[df["season"].isin(SEASONS_TO_KEEP)]
            print(f"✅ {len(df_filtered)} lignes conservées sur {len(df)} (filtrées par saison)")
        else:
            df_filtered = df
            print("⚠️ Aucune colonne `season` détectée — export complet")

        # 📤 Export vers data/bronze/
        export_filename = (
            file.replace(".csv", "_2022_2024.csv")
                .replace(" ", "_")
                .lower()
        )
        export_path = os.path.join(EXPORT_DIR, export_filename)
        df_filtered.to_csv(export_path, index=False)
        print(f"📁 Exporté : {export_path}")

print("\n🎉 Extraction terminée avec succès.")
