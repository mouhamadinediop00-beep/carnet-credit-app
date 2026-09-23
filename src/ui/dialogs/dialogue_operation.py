import flet as ft

class DialogOperation:
    def __init__(self, on_valider):
        self.on_valider = on_valider
        self.dlg = None
        self.txt_montant = None
        self.client_id = None
        self.type_op = None
        self.dette_actuelle = 0

    def ouvrir(self, page: ft.Page, client_id: int, type_op: str, dette_actuelle: int = 0):
        self.client_id = client_id
        self.type_op = type_op
        self.dette_actuelle = dette_actuelle

        titre = "Ajouter une dette" if type_op == "dette" else "Enregistrer un remboursement"
        couleur_btn = ft.Colors.RED_600 if type_op == "dette" else ft.Colors.GREEN_600

        self.txt_montant = ft.TextField(
            label="Montant (FCFA)",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True
        )

        def valider(e):
            val = self.txt_montant.value.strip() if self.txt_montant.value else ""
            if not val or not val.isdigit() or int(val) <= 0:
                self.txt_montant.error_text = "Veuillez entrer un montant valide"
                self.txt_montant.update()
                return

            montant = int(val)

            # CONTRAINTE : Le remboursement ne peut pas dépasser la dette actuelle
            if self.type_op != "dette":
                if self.dette_actuelle == 0:
                    self.txt_montant.error_text = "Ce client n'a aucune dette à rembourser"
                    self.txt_montant.update()
                    return
                if montant > self.dette_actuelle:
                    self.txt_montant.error_text = f"Le remboursement ne peut pas dépasser la dette ({self.dette_actuelle} FCFA)"
                    self.txt_montant.update()
                    return

            self.dlg.open = False
            page.update()
            self.on_valider(self.client_id, self.type_op, montant)

        def fermer(e):
            self.dlg.open = False
            page.update()

        contenu_dialogue = [self.txt_montant]
        if type_op != "dette":
            contenu_dialogue.insert(0, ft.Text(f"Dette actuelle : {self.dette_actuelle} FCFA", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD))

        self.dlg = ft.AlertDialog(
            title=ft.Text(titre),
            content=ft.Column(contenu_dialogue, tight=True, spacing=10),
            actions=[
                ft.TextButton("Annuler", on_click=fermer),
                ft.ElevatedButton("Valider", bgcolor=couleur_btn, color=ft.Colors.WHITE, on_click=valider)
            ]
        )

        page.overlay.append(self.dlg)
        self.dlg.open = True
        page.update()