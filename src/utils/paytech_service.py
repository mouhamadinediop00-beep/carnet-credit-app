import requests

# Remplacez par vos vraies clés PayTech
PAYTECH_API_KEY = "e896cec3fbf7d97814f5b692b75a1326bb4139c69c2044b1a0ecfc02ba468398"
PAYTECH_API_SECRET = "8db68c706e9f84888c1ca7d9b76d02eec961d2e870f9c24fe69916d94ed89bc0"

# URL de l'Edge Function créée à l'Étape 1
SUPABASE_WEBHOOK_URL = "https://ofmigkoamxqvfmthxcpa.supabase.co/functions/v1/paytech-webhook"

def generer_lien_paiement_paytech(user_id: str) -> str | None:
    """
    Initié une demande de paiement sur PayTech et retourne le lien de paiement.
    """
    url = "https://paytech.sn/api/payment/request-payment"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api_key": PAYTECH_API_KEY,
        "api_secret": PAYTECH_API_SECRET
    }

    payload = {
        "item_name": "Abonnement Carnet de Crédit (1 Mois)",
        "item_price": "2000",
        "currency": "XOF",
        "ref_command": f"SUB_{user_id[:8]}",
        "command_name": "Renouvellement Abonnement",
        "ipn_url": SUPABASE_WEBHOOK_URL,
        "success_url": "https://paytech.sn",
        "cancel_url": "https://paytech.sn",
        "custom_field": user_id,  # Permet d'identifier le client dans Supabase
        "env": "test"  # Utilisez "test" si vous testez avec un compte PayTech de démonstration
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        if data.get("success") == 1:
            return data.get("redirect_url")
        else:
            print(f"Erreur PayTech : {data}")
            return None
    except Exception as e:
        print(f"Erreur d'appel API PayTech : {e}")
        return None