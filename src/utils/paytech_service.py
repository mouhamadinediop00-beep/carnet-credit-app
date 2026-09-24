import requests

# Ces deux valeurs peuvent être publiques (l'URL du projet et la clé "anon" de Supabase).
# Les clés secrètes PayTech, elles, restent UNIQUEMENT côté Supabase (voir create-payment/index.ts).
SUPABASE_URL = "https://ofmigkoamxqvfmthxcpa.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mbWlna29hbXhxdmZtdGh4Y3BhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAwMzU4ODEsImV4cCI6MjEwNTYxMTg4MX0._3DhPB2WoKbivBJmgUTercoiO-C222qmY3C9DfpUZHs"

CREATE_PAYMENT_URL = f"{SUPABASE_URL}/functions/v1/create-payment"


def generer_lien_paiement_paytech(user_id: str) -> str | None:
    """
    Demande à la fonction Supabase 'create-payment' de créer le paiement PayTech
    et retourne le lien de paiement (ou None en cas d'erreur).
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "apikey": SUPABASE_ANON_KEY,
    }

    try:
        response = requests.post(
            CREATE_PAYMENT_URL,
            json={"user_id": user_id},
            headers=headers,
            timeout=15,
        )
        data = response.json()
        lien = data.get("redirect_url")
        if response.ok and lien:
            return lien
        print(f"Erreur création paiement : {data}")
        return None
    except Exception as e:
        print(f"Erreur d'appel create-payment : {e}")
        return None
