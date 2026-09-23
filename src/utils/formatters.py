from datetime import datetime

def parse_montant(texte: str):
    """Convertit '5 000' ou '5000' en entier. Retourne None si invalide."""
    if not texte:
        return None
    propre = texte.replace(" ","").replace("\u00a0","").replace("\u202f","")
    if not propre.isdigit():
        return None
    return int(propre)
def format_fcfa(montant: int) -> str:
    """Format 5000 en '5 000 FCFA'."""
    return f"{montant:,}".replace(",", " ") + " FCFA"

def format_datetime(iso_str: str) -> str:
    """Convertit '2026-09-21T17:30:00' en '21/09/2026 à 17:30'."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y à %H:%M")
    except Exception:
        return iso_str