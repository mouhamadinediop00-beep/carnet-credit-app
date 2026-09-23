from datetime import datetime, timezone, timedelta
from supabase import create_client

SUPABASE_URL = "https://ofmigkoamxqvfmthxcpa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mbWlna29hbXhxdmZtdGh4Y3BhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAwMzU4ODEsImV4cCI6MjEwNTYxMTg4MX0._3DhPB2WoKbivBJmgUTercoiO-C222qmY3C9DfpUZHs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DELAI_SYNCHRO_JOURS = 3  # Intervalle de vérification en ligne (en jours)

def verifier_statut_abonnement(db, forcer_verification: bool = False) -> tuple[bool, str]:
    maintenant = datetime.now(timezone.utc)
    
    # --- A. LECTURE DU CACHE LOCAL (SQLite) ---
    expires_at_cache = db.get_parametre("subscription_expires_at")
    last_check_str = db.get_parametre("last_subscription_check")
    
    date_exp_cache = None
    if expires_at_cache:
        try:
            date_exp_cache = datetime.fromisoformat(expires_at_cache.replace("Z", "+00:00"))
        except Exception:
            pass

    derniere_verif = None
    if last_check_str:
        try:
            derniere_verif = datetime.fromisoformat(last_check_str.replace("Z", "+00:00"))
        except Exception:
            pass

    # --- B. VÉRIFICATION DU CACHE RECENT (Moins de 3 jours) ---
    cache_est_recent = derniere_verif and (maintenant - derniere_verif < timedelta(days=DELAI_SYNCHRO_JOURS))
    
    if not forcer_verification and cache_est_recent and date_exp_cache:
        if maintenant < date_exp_cache:
            print("[CHECKER] Accès accordé instantanément via le cache local (< 3 jours).")
            return True, "Abonnement actif (Cache local)"

    # --- C. VÉRIFICATION EN LIGNE (Si > 3 jours ou forcé) ---
    try:
        session = db.get_user_session()
        user_id = str(session.get("user_id", "")).strip()

        if not user_id:
            if date_exp_cache and maintenant < date_exp_cache:
                return True, "Abonnement valide (Hors-ligne)"
            return False, "Session introuvable"

        print(f"[CHECKER] Synchro Supabase en cours pour : {user_id}")
        response = supabase.table("profiles") \
            .select("subscription_expires_at, expiration_date") \
            .or_(f"id.eq.{user_id},email.ilike.%{user_id}%") \
            .execute()

        if response.data:
            profile = response.data[0]
            expires_at_str = profile.get("subscription_expires_at") or profile.get("expiration_date")

            if expires_at_str:
                date_exp_distante = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                
                # Mise à jour du cache SQLite local
                db.set_parametre("subscription_expires_at", expires_at_str)
                db.set_parametre("last_subscription_check", maintenant.isoformat())

                if maintenant < date_exp_distante:
                    return True, "Abonnement actif"
                else:
                    return False, "Abonnement expiré"

    except Exception as e:
        print(f"[CHECKER] Connexion réseau indisponible : {e}")
        # MODE HORS-LIGNE : Si Internet coupe, on se fie au dernier cache local disponible !
        if date_exp_cache and maintenant < date_exp_cache:
            print("[CHECKER] Mode hors-ligne : date locale valide. Accès débloqué.")
            return True, "Abonnement actif (Mode Hors-ligne)"

    return False, "Abonnement expiré ou pas d'accès"