import inspect


def ouvrir_url(page, url: str):
    """
    Ouvre une URL dans le navigateur du téléphone.
    Remplace webbrowser.open(), qui ne fonctionne pas sur Android.
    Compatible avec les versions de Flet où launch_url est synchrone
    comme avec celles où il est asynchrone.
    """
    resultat = page.launch_url(url)
    if inspect.isawaitable(resultat):
        async def _attendre():
            await resultat

        page.run_task(_attendre)
