import requests

VERSION_ACTUELLE = "1.0.0"
GITHUB_REPO = "mouhamadinediop00-beep/carnet-credit-app"


def _version_en_tuple(version: str) -> tuple:
    """'v1.10.2' -> (1, 10, 2). Évite l'erreur de la comparaison de chaînes ("1.10" < "1.9")."""
    morceaux = []
    for partie in version.strip().lstrip("vV").split("."):
        chiffres = "".join(c for c in partie if c.isdigit())
        morceaux.append(int(chiffres) if chiffres else 0)
    return tuple(morceaux)


def verifier_mise_a_jour():
    """
    Retourne (True, url_apk) si une version plus récente existe sur GitHub,
    sinon (False, None). Ne lève jamais d'exception.
    """
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        version_distante = data.get("tag_name", "")
        if not version_distante:
            return False, None

        if _version_en_tuple(version_distante) > _version_en_tuple(VERSION_ACTUELLE):
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".apk"):
                    return True, asset["browser_download_url"]

        return False, None
    except Exception as e:
        print(f"[UPDATER] Erreur de vérification : {e}")
        return False, None
