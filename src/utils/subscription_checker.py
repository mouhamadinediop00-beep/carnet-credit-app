import os
import json
import requests
from datetime import datetime, timezone

import database.supabase_client as sp_client


# ============================================================
# CONFIGURATION
# ============================================================

SUPABASE_URL = "https://ofmigkoamxqvfmthxcpa.supabase.co"

CACHE_FILE = "subscription_cache.json"

# Nombre maximum de jours sans nouvelle vérification serveur.
CACHE_DURATION_DAYS = 3


# ============================================================
# CHEMIN DU CACHE
# ============================================================

def _get_cache_path():
    """
    Retourne le chemin du fichier de cache.

    Sur Android/Flet, FLET_APP_STORAGE_DATA permet de conserver
    le fichier entre les lancements de l'application.
    """

    storage_dir = os.environ.get(
        "FLET_APP_STORAGE_DATA",
        "."
    )

    return os.path.join(
        storage_dir,
        CACHE_FILE
    )


# ============================================================
# LECTURE DU CACHE
# ============================================================

def _lire_cache():
    try:
        cache_path = _get_cache_path()

        if not os.path.exists(cache_path):
            return None

        with open(
            cache_path,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        return data

    except Exception as e:
        print(
            f"Erreur lecture cache abonnement : {e}"
        )
        return None


# ============================================================
# SAUVEGARDE DU CACHE
# ============================================================

def _sauvegarder_cache(
    expires_at=None,
    is_vip=False
):
    """
    Sauvegarde le dernier état confirmé par Supabase.

    expires_at :
        date réelle d'expiration de l'abonnement.

    is_vip :
        True = accès permanent.

    last_check :
        dernière vérification réussie auprès du serveur.
    """

    try:
        cache_path = _get_cache_path()

        data = {
            "expires_at": expires_at,
            "is_vip": bool(is_vip),
            "last_check": datetime.now(
                timezone.utc
            ).isoformat()
        }

        with open(
            cache_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False
            )

    except Exception as e:
        print(
            f"Erreur sauvegarde cache abonnement : {e}"
        )


# ============================================================
# CONVERSION DES DATES
# ============================================================

def _parser_date(date_str):
    if not date_str:
        return None

    try:
        date_obj = datetime.fromisoformat(
            str(date_str).replace(
                "Z",
                "+00:00"
            )
        )

        # Si Supabase renvoie exceptionnellement une date
        # sans timezone, on considère UTC.
        if date_obj.tzinfo is None:
            date_obj = date_obj.replace(
                tzinfo=timezone.utc
            )

        return date_obj

    except Exception as e:
        print(
            f"Erreur conversion date abonnement : {e}"
        )
        return None


# ============================================================
# VÉRIFICATION DATE D'ABONNEMENT
# ============================================================

def _abonnement_non_expire(expires_at):
    date_expiration = _parser_date(
        expires_at
    )

    if date_expiration is None:
        return False

    return (
        date_expiration
        > datetime.now(timezone.utc)
    )


# ============================================================
# VALIDITÉ DU CACHE HORS LIGNE
# ============================================================

def _cache_encore_utilisable(cache):
    """
    Vérifie si le serveur a été contacté avec succès
    il y a moins de CACHE_DURATION_DAYS.

    Attention :
    cela ne signifie PAS que l'abonnement est valide.
    La date d'expiration est contrôlée séparément.
    """

    if not cache:
        return False

    last_check = cache.get(
        "last_check"
    )

    if not last_check:
        return False

    date_verification = _parser_date(
        last_check
    )

    if date_verification is None:
        return False

    maintenant = datetime.now(
        timezone.utc
    )

    age = (
        maintenant
        - date_verification
    )

    return age.total_seconds() < (
        CACHE_DURATION_DAYS
        * 24
        * 60
        * 60
    )


# ============================================================
# LECTURE DU CACHE POUR LE MODE HORS LIGNE
# ============================================================

def _verifier_cache_local(cache):
    """
    Retourne :
        True, "VIP"
        True, date_expiration
        False, message
    """

    if not cache:
        return False, "Aucune vérification locale disponible"

    # Le cache doit provenir d'une vérification serveur
    # suffisamment récente.
    if not _cache_encore_utilisable(cache):
        return (
            False,
            "Connexion Internet requise pour vérifier l'abonnement"
        )

    is_vip = bool(
        cache.get(
            "is_vip",
            False
        )
    )

    # Un VIP reste autorisé pendant la fenêtre hors ligne.
    if is_vip:
        return True, "VIP"

    expires_at = cache.get(
        "expires_at"
    )

    if not expires_at:
        return (
            False,
            "Aucun abonnement actif"
        )

    # Même avec un cache de moins de 3 jours,
    # on vérifie la vraie date d'expiration.
    if _abonnement_non_expire(
        expires_at
    ):
        return True, expires_at

    return (
        False,
        "Abonnement expiré"
    )


# ============================================================
# RÉCUPÉRATION DE LA SESSION SUPABASE
# ============================================================

def _get_access_token():
    """
    Récupère le JWT de l'utilisateur actuellement connecté.
    """

    try:
        session = (
            sp_client.supabase
            .auth
            .get_session()
        )

        if (
            session
            and getattr(
                session,
                "access_token",
                None
            )
        ):
            return session.access_token

    except Exception as e:
        print(
            f"Erreur récupération session Supabase : {e}"
        )

    return None


# ============================================================
# APPEL DE L'EDGE FUNCTION
# ============================================================

def _obtenir_abonnement_distant():
    """
    Interroge l'Edge Function sécurisée get-subscription.

    L'identité de l'utilisateur provient du JWT.
    Aucun user_id n'est envoyé manuellement.
    """

    access_token = _get_access_token()

    if not access_token:
        print(
            "Aucune session Supabase disponible."
        )

        return None, "session"

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "apikey": sp_client.SUPABASE_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            (
                f"{SUPABASE_URL}"
                "/functions/v1/get-subscription"
            ),
            headers=headers,
            timeout=10
        )

    except requests.RequestException as e:
        print(
            f"Connexion Supabase impossible : {e}"
        )

        return None, "network"

    except Exception as e:
        print(
            f"Erreur appel Edge Function : {e}"
        )

        return None, "network"

    # --------------------------------------------
    # Session expirée / JWT invalide
    # --------------------------------------------

    if response.status_code == 401:

        print(
            "Session Supabase invalide ou expirée."
        )

        return None, "session"

    # --------------------------------------------
    # Profil introuvable
    # --------------------------------------------

    if response.status_code == 404:

        print(
            "Profil Supabase introuvable."
        )

        return None, "profile"

    # --------------------------------------------
    # Autre erreur serveur
    # --------------------------------------------

    if response.status_code != 200:

        print(
            "Erreur Edge Function :",
            response.status_code,
            response.text
        )

        return None, "server"

    # --------------------------------------------
    # Lecture JSON
    # --------------------------------------------

    try:
        data = response.json()

    except Exception as e:

        print(
            f"Réponse Supabase invalide : {e}"
        )

        return None, "server"

    if not isinstance(data, dict):
        return None, "server"

    return data, None


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def verifier_statut_abonnement(
    db=None,
    forcer_verification=False
):
    """
    Fonction appelée par main.py.

    Compatible avec :

        verifier_statut_abonnement(db)

    et :

        verifier_statut_abonnement(
            db,
            forcer_verification=True
        )

    Fonctionnement :

    1. Si le cache est récent et qu'aucune vérification
       forcée n'est demandée :
       -> utilisation locale.

    2. Sinon :
       -> vérification auprès de l'Edge Function.

    3. Si Internet est indisponible :
       -> fallback sur le cache local.

    4. VIP :
       -> accès autorisé.

    5. Utilisateur normal :
       -> accès uniquement si expires_at est encore valide.
    """

    cache = _lire_cache()

    # ========================================================
    # 1. CACHE LOCAL
    # ========================================================

    if (
        not forcer_verification
        and _cache_encore_utilisable(cache)
    ):
        return _verifier_cache_local(
            cache
        )

    # ========================================================
    # 2. VÉRIFICATION SERVEUR
    # ========================================================

    data, erreur = (
        _obtenir_abonnement_distant()
    )

    if data is not None:

        is_vip = bool(
            data.get(
                "is_vip",
                False
            )
        )

        expires_at = data.get(
            "expires_at"
        )

        # --------------------------------------------
        # VIP / ADMIN
        # --------------------------------------------

        if is_vip:

            _sauvegarder_cache(
                expires_at=expires_at,
                is_vip=True
            )

            return True, "VIP"

        # --------------------------------------------
        # UTILISATEUR NORMAL
        # --------------------------------------------

        if expires_at:

            # Sauvegarde l'état serveur même si
            # l'abonnement vient d'expirer.
            _sauvegarder_cache(
                expires_at=expires_at,
                is_vip=False
            )

            if _abonnement_non_expire(
                expires_at
            ):
                return (
                    True,
                    expires_at
                )

            return (
                False,
                "Abonnement expiré"
            )

        # Le serveur a répondu correctement mais
        # aucun abonnement n'existe.
        _sauvegarder_cache(
            expires_at=None,
            is_vip=False
        )

        return (
            False,
            "Aucun abonnement actif"
        )

    # ========================================================
    # 3. PAS DE RÉPONSE SERVEUR
    # ========================================================

    # Si le réseau est indisponible, on autorise
    # éventuellement le mode hors ligne.
    if erreur in (
        "network",
        "server"
    ):

        est_actif, raison = (
            _verifier_cache_local(
                cache
            )
        )

        if est_actif:
            return (
                est_actif,
                raison
            )

        return (
            False,
            raison
        )

    # ========================================================
    # 4. SESSION SUPABASE ABSENTE
    # ========================================================

    if erreur == "session":

        # TEMPORAIREMENT :
        # on accepte le cache valide afin de conserver
        # le fonctionnement hors ligne.
        #
        # Une fois la restauration automatique du JWT
        # mise en place, cette situation deviendra rare.

        est_actif, raison = (
            _verifier_cache_local(
                cache
            )
        )

        if est_actif:
            return (
                est_actif,
                raison
            )

        return (
            False,
            "Veuillez vous reconnecter à votre compte"
        )

    # ========================================================
    # 5. PROFIL INTROUVABLE
    # ========================================================

    if erreur == "profile":
        return (
            False,
            "Profil d'abonnement introuvable"
        )

    # ========================================================
    # 6. SÉCURITÉ PAR DÉFAUT
    # ========================================================

    return (
        False,
        "Impossible de vérifier l'abonnement"
    )