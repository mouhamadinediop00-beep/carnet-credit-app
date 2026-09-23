import urllib.request
import json
import flet as ft

CURRENT_VERSION = "1.0.0"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/mouhamadinediop00-beep/carnet-credit-app/refs/heads/main/version.json"

def verifier_mise_a_jour(page: ft.Page):
    try:
        req = urllib.request.Request(
            VERSION_CHECK_URL,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        # Correction de 'reponse' -> 'response'
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        derniere_version = data.get("latest_version", CURRENT_VERSION)
        download_url = data.get("download_url", "")
        changelog = data.get("changelog", "Nouvelle version disponible.")

        if derniere_version > CURRENT_VERSION:
            afficher_dialogue_maj(page, derniere_version, download_url, changelog)

    except Exception:
        pass

def afficher_dialogue_maj(page: ft.Page, version: str, url: str, changelog: str):
    def telecharger(e):
        page.close(dlg)
        page.launch_url(url)
        
    dlg = ft.AlertDialog(
        title=ft.Text(f"Mise à jour disponible ({version})"),
        content=ft.Column([
            ft.Text("Une nouvelle version de votre carnet est disponible :", size=14),
            ft.Container(height=5),
            ft.Text(changelog, size=12, italic=True, color=ft.Colors.GREY_700),
        ], tight=True),
        actions=[
            ft.TextButton("Plus tard", on_click=lambda e: page.close(dlg)),
            ft.ElevatedButton(
                "Mettre à jour",
                icon=ft.Icons.DOWNLOAD,
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
                on_click=telecharger
            )
        ]
    )

    page.open(dlg)