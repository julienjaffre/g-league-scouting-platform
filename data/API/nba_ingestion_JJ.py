from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import os

def fetch_nba_player_stats(season="2023-24"):
    """
    Récupère les stats par match des joueurs NBA pour une saison donnée.
    Filtre ensuite les colonnes utiles.
    """
    print("🔁 Requête NBA API en cours...")
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable=season)
    games = gamefinder.get_data_frames()[0]

    # Colonnes utiles
    columns = ["PLAYER_NAME", "TEAM_NAME", "MIN", "PTS", "GAME_DATE"]
    games = games[columns]

    print(f"✅ {len(games)} lignes récupérées.")
    return games

def save_to_csv(df, output_path="data/nba_player_stats.csv"):
    """
    Sauvegarde le DataFrame dans le dossier local `data/`.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"📁 Données sauvegardées dans {output_path}")

if __name__ == "__main__":
    df = fetch_nba_player_stats(season="2023-24")
    save_to_csv(df)
