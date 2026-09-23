from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

# --- CLÉS SUPABASE ---
SUPABASE_URL = "https://ofmigkoamxqvfmthxcpa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mbWlna29hbXhxdmZtdGh4Y3BhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAwMzU4ODEsImV4cCI6MjEwNTYxMTg4MX0._3DhPB2WoKbivBJmgUTercoiO-C222qmY3C9DfpUZHs"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def _nettoyer_telephone(phone: str) -> str:
    clean_num = "".join(filter(str.isdigit, phone))
    return f"{clean_num}@carnet.app"

class SupabaseManager:

    @staticmethod
    def s_inscrire(telephone: str, password: str):
        try:
            if len(password) < 6:
                return False, "Le mot de passe doit faire au moins 6 caractères."

            email_fake = _nettoyer_telephone(telephone)
            res = supabase.auth.sign_up({"email": email_fake, "password": password})
            
            if res.user:
                user_id = res.user.id
                # Offrir 30 jours d'essai gratuit automatiquement
                exp_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                try:
                    supabase.table("profiles").upsert({
                        "id": user_id,
                        "expiration_date": exp_date,
                        "is_vip": False
                    }).execute()
                except Exception:
                    pass
                return True, user_id
            return False, "Impossible de créer le compte."
        except Exception as e:
            msg = str(e)
            if "rate limit exceeded" in msg.lower():
                return False, "Trop de tentatives. Veuillez patienter 10 à 15 minutes."
            if "User already registered" in msg:
                return False, "Ce numéro est déjà inscrit. Choisissez 'Se connecter'."
            return False, msg

    @staticmethod
    def se_connecter(telephone: str, password: str):
        try:
            email_fake = _nettoyer_telephone(telephone)
            res = supabase.auth.sign_in_with_password({"email": email_fake, "password": password})
            if res.user:
                return True, res.user.id
            return False, "Numéro ou mot de passe incorrect."
        except Exception as e:
            msg = str(e)
            if "rate limit exceeded" in msg.lower():
                return False, "Trop de tentatives de connexion. Patientez 10 minutes."
            if "Invalid login credentials" in msg:
                return False, "Numéro ou mot de passe incorrect."
            return False, msg

    @staticmethod
    def verifier_abonnement_en_ligne(user_id: str):
        try:
            res = supabase.table("profiles").select("expiration_date, is_vip").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                profile = res.data[0]
                is_vip = profile.get("is_vip", False)
                exp_str = profile.get("expiration_date", "")

                if is_vip:
                    return True, "2099-12-31T23:59:59+00:00", True

                if exp_str:
                    exp_date = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    est_valide = exp_date > now
                    return est_valide, exp_str, False
            else:
                # Si aucun profil n'existe encore, lui offrir 30 jours d'essai
                exp_date_obj = datetime.now(timezone.utc) + timedelta(days=30)
                exp_str = exp_date_obj.isoformat()
                try:
                    supabase.table("profiles").upsert({
                        "id": user_id,
                        "expiration_date": exp_str,
                        "is_vip": False
                    }).execute()
                except Exception:
                    pass
                return True, exp_str, False

            return False, "", False
        except Exception:
            return None, "", False