import flet as ft
from utils.formatters import parse_montant

class DialogAjout(ft.AlertDialog):
    def __init__(self, on_ajouter, db_ref):
        self.db = db_ref
        self.on_ajouter_callback = on_ajouter

        self.champ_nom = ft.TextField(
            label="Nom du client",
            prefix_icon=ft.Icons.PERSON,
            autofocus=True
        )
        self.champ_dette_initiale = ft.TextField(
            label="Dette initiale (FCFA)",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=""
        )

        super().__init__(
            title=ft.Text("Ajouter un Client"),
            content=ft.Column(
                controls=[self.champ_nom, self.champ_dette_initiale],
                tight=True
            ),
            actions=[
                ft.TextButton("Annuler", on_click=self.fermer),
                ft.ElevatedButton(
                    "Enregistrer",
                    icon=ft.Icons.CHECK,
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    on_click=self.enregistrer
                ),
            ],
        )

    def ouvrir(self, page):
        self.champ_nom.value = ""
        self.champ_nom.error_text = None
        self.champ_dette_initiale.value = ""
        self.champ_dette_initiale.error_text = None
        
        if self not in page.overlay:
            page.overlay.append(self)
        self.open = True
        page.update()

    def fermer(self, e):
        self.open = False
        e.page.update()

    def enregistrer(self, e):
        nom = (self.champ_nom.value or "").strip()
        texte_dette = (self.champ_dette_initiale.value or "").strip()
        erreur = False

        if not nom:
            self.champ_nom.error_text = "Le nom est obligatoire"
            erreur = True
        elif self.db.nom_existe(nom):
            self.champ_nom.error_text = "Ce client existe déjà"
            erreur = True
        else:
            self.champ_nom.error_text = None

        dette = 0 if texte_dette == "" else parse_montant(texte_dette)
        if dette is None:
            self.champ_dette_initiale.error_text = "Montant valide attendu (ex: 5000)"
            erreur = True
        else:
            self.champ_dette_initiale.error_text = None

        if erreur:
            self.update()
            return

        self.on_ajouter_callback(nom, dette)
        self.open = False
        e.page.update()