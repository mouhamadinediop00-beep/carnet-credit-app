import flet_secure_storage as fss


ACCESS_TOKEN_KEY = "carnet_credit.access_token"
REFRESH_TOKEN_KEY = "carnet_credit.refresh_token"


class SecureSessionStorage:
    """
    Stockage sécurisé des tokens Supabase.
    """

    def __init__(self):
        self.storage = fss.SecureStorage(
            android_options=fss.AndroidOptions(
                reset_on_error=True,
                migrate_on_algorithm_change=True,
            )
        )


    async def sauvegarder_tokens(
        self,
        access_token: str,
        refresh_token: str
    ):
        if not access_token or not refresh_token:
            return False

        try:
            await self.storage.set(
                ACCESS_TOKEN_KEY,
                access_token
            )

            await self.storage.set(
                REFRESH_TOKEN_KEY,
                refresh_token
            )

            return True

        except Exception as e:
            print(
                f"Erreur sauvegarde sécurisée : {e}"
            )
            return False


    async def recuperer_tokens(self):
        try:
            access_token = await self.storage.get(
                ACCESS_TOKEN_KEY
            )

            refresh_token = await self.storage.get(
                REFRESH_TOKEN_KEY
            )

            return access_token, refresh_token

        except Exception as e:
            print(
                f"Erreur lecture stockage sécurisé : {e}"
            )

            return None, None


    async def supprimer_tokens(self):
        try:
            await self.storage.remove(
                ACCESS_TOKEN_KEY
            )

            await self.storage.remove(
                REFRESH_TOKEN_KEY
            )

            return True

        except Exception as e:
            print(
                f"Erreur suppression tokens : {e}"
            )

            return False