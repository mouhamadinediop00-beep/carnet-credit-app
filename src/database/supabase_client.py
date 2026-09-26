from supabase import create_client, Client


# ============================================================
# CONFIGURATION SUPABASE
# ============================================================

SUPABASE_URL = "https://ofmigkoamxqvfmthxcpa.supabase.co"

SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mbWlna29hbXhxdmZtdGh4Y3BhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAwMzU4ODEsImV4cCI6MjEwNTYxMTg4MX0._3DhPB2WoKbivBJmgUTercoiO-C222qmY3C9DfpUZHs"


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# CONVERSION DU NUMÉRO EN EMAIL INTERNE
# ============================================================

def _nettoyer_telephone(phone: str) -> str:
    clean_num = "".join(
        filter(str.isdigit, phone)
    )

    return f"{clean_num}@carnet.app"


# ============================================================
# GESTION SUPABASE
# ============================================================

class SupabaseManager:

    # --------------------------------------------------------
    # INSCRIPTION
    # --------------------------------------------------------

    @staticmethod
    def s_inscrire(
        telephone: str,
        password: str
    ):
        try:

            if len(password) < 6:
                return (
                    False,
                    "Le mot de passe doit faire au moins 6 caractères."
                )

            email_fake = _nettoyer_telephone(
                telephone
            )

            res = supabase.auth.sign_up({
                "email": email_fake,
                "password": password
            })

            if res.user:

                # Le trigger PostgreSQL handle_new_user()
                # crée automatiquement :
                # le profil


                return True, res.user.id

            return (
                False,
                "Impossible de créer le compte."
            )

        except Exception as e:

            msg = str(e)

            if "rate limit exceeded" in msg.lower():
                return (
                    False,
                    "Trop de tentatives. "
                    "Veuillez patienter 10 à 15 minutes."
                )

            if "User already registered" in msg:
                return (
                    False,
                    "Ce numéro est déjà inscrit. "
                    "Choisissez 'Se connecter'."
                )

            return False, msg


    # --------------------------------------------------------
    # CONNEXION
    # --------------------------------------------------------

    @staticmethod
    def se_connecter(
        telephone: str,
        password: str
    ):
        try:

            email_fake = _nettoyer_telephone(
                telephone
            )

            res = (
                supabase.auth
                .sign_in_with_password({
                    "email": email_fake,
                    "password": password
                })
            )

            if res.user:
                return True, res.user.id

            return (
                False,
                "Numéro ou mot de passe incorrect."
            )

        except Exception as e:

            msg = str(e)

            if "rate limit exceeded" in msg.lower():
                return (
                    False,
                    "Trop de tentatives de connexion. "
                    "Patientez 10 minutes."
                )

            if "Invalid login credentials" in msg:
                return (
                    False,
                    "Numéro ou mot de passe incorrect."
                )

            return False, msg


    # --------------------------------------------------------
    # SESSION SUPABASE ACTUELLE
    # --------------------------------------------------------

    @staticmethod
    def get_session():
        try:
            return supabase.auth.get_session()

        except Exception as e:
            print(
                f"Erreur récupération session Supabase : {e}"
            )
            return None


    # --------------------------------------------------------
    # ACCESS TOKEN
    # --------------------------------------------------------

    @staticmethod
    def get_access_token():

        session = SupabaseManager.get_session()

        if (
            session
            and getattr(
                session,
                "access_token",
                None
            )
        ):
            return session.access_token

        return None


    # --------------------------------------------------------
    # REFRESH TOKEN
    # --------------------------------------------------------

    @staticmethod
    def get_refresh_token():

        session = SupabaseManager.get_session()

        if (
            session
            and getattr(
                session,
                "refresh_token",
                None
            )
        ):
            return session.refresh_token

        return None


    # --------------------------------------------------------
    # RESTAURATION DE LA SESSION
    # --------------------------------------------------------

    @staticmethod
    def restaurer_session(
        access_token: str,
        refresh_token: str
    ):
        """
        Restaure la session Supabase enregistrée localement.

        Supabase pourra ensuite renouveler le JWT si nécessaire.
        """

        if not access_token or not refresh_token:
            return False

        try:

            res = supabase.auth.set_session(
                access_token,
                refresh_token
            )

            if (
                res
                and getattr(
                    res,
                    "session",
                    None
                )
            ):
                return True

            # Selon la version de supabase-py,
            # get_session() permet également de confirmer.
            session = supabase.auth.get_session()

            return bool(session)

        except Exception as e:

            print(
                f"Erreur restauration session Supabase : {e}"
            )

            return False


    # --------------------------------------------------------
    # DÉCONNEXION
    # --------------------------------------------------------

    @staticmethod
    def se_deconnecter():
        try:
            supabase.auth.sign_out()
            return True

        except Exception as e:
            print(
                f"Erreur déconnexion Supabase : {e}"
            )
            return False

    @staticmethod
    def supprimer_compte():
        try:
            session = supabase.auth.get_session()
            if not session:
                return False, "Session invalide."

            res = supabase.functions.invoke(
                "delete-account",
                invoke_options={
                    "headers": {
                        "Authorization": f"Bearer {session.access_token}"
                    }
                }
            )
            return True, "Compte supprimé."
        except Exception as e:
            return False, str(e)