import platform

import requests

VERSION_ACTUELLE = "1.0.0"
GITHUB_REPO = "mouhamadinediop00-beep/carnet-credit-app"


def _version_en_tuple(version: str) -> tuple:
    """'v1.10.2' -> (1, 10, 2). Evite l'erreur de la comparaison de chaines ("1.10" < "1.9")."""
    morceaux = []
    for partie in version.strip().lstrip("vV").split("."):
        chiffres = "".join(c for c in partie if c.isdigit())
        morceaux.append(int(chiffres) if chiffres else 0)
    return tuple(morceaux)


def _architecture() -> str:
    """Retourne 'arm64' (telephones 64 bits) ou 'armv7' (anciens telephones 32 bits)."""
    machine = platform.machine().lower()
    if machine in ("aarch64", "arm64", "x86_64", "amd64"):
        return "arm64"
    return "armv7"


def _choisir_apk(assets: list) -> str | None:
    """Choisit l'APK adapte au telephone parmi les fichiers de la release."""
    apks = [a for a in assets if a.get("name", "").endswith(".apk")]
    if not apks:
        return None

    archi = _architecture()
    for asset in apks:
        if archi in asset["name"].lower():
            return asset["browser_download_url"]

    # Repli : release avec un seul APK "universel" (ancien format)
    return apks[0]["browser_download_url"]


def verifier_mise_a_jour():
    """
    Retourne (True, url_apk) si une version plus recente existe sur GitHub,
    sinon (False, None). Ne leve jamais d'exception.
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
            lien = _choisir_apk(data.get("assets", []))
            if lien:
                return True, lien

        return False, None
    except Exception as e:
        print(f"[UPDATER] Erreur de verification : {e}")
        return False, None
