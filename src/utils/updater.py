import requests
import flet as ft

VERSION_ACTUELLE = "1.0.0"
GITHUB_REPO = "mouhamadinediop00-beep/carnet-credit-app"

def verifier_mise_a_jour():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5).json()
        
        version_distante = response.get("tag_name", "").replace("v", "")
        
        if version_distante and version_distante > VERSION_ACTUELLE:
            # Chercher le lien du fichier .apk dans les assets de la release
            assets = response.get("assets", [])
            for asset in assets:
                if asset["name"].endswith(".apk"):
                    return True, asset["browser_download_url"]
                    
        return False, None
    except Exception as e:
        print(f"[UPDATER] Erreur de vérification : {e}")
        return False, None