import flet as ft


class PinView(ft.Container):
    def __init__(self, db_ref, on_success):
        self.db = db_ref
        self.on_success = on_success

        self.champ_code = ft.TextField(
            label="Entrez votre code PIN",
            password=True,
            can_reveal_password=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=6,
            text_align=ft.TextAlign.CENTER,
            width=220,
            autofocus=True,
            on_submit=self.valider,
        )

        self.txt_erreur = ft.Text(
            "",
            color=ft.Colors.RED_600,
            size=13,
        )

        super().__init__(
            alignment=ft.alignment.Alignment(0, 0),
            padding=30,
            expand=True,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.LOCK_OUTLINED,
                        size=60,
                        color=ft.Colors.BLUE_600,
                    ),
                    ft.Text(
                        "Carnet verrouillé",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Veuillez saisir votre code à 6 chiffres",
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Container(height=10),
                    self.champ_code,
                    self.txt_erreur,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Déverrouiller",
                        icon=ft.Icons.LOCK_OPEN,
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE,
                        on_click=self.valider,
                    ),
                ],
            ),
        )

    def valider(self, e):
        saisie = (self.champ_code.value or "").strip()

        if not saisie:
            self.txt_erreur.value = "Veuillez saisir votre code PIN."
            self.update()
            return

        if not saisie.isdigit():
            self.txt_erreur.value = "Le code PIN doit contenir uniquement des chiffres."
            self.champ_code.value = ""
            self.update()
            return

        if self.db.verifier_pin(saisie):
            self.txt_erreur.value = ""
            self.champ_code.value = ""
            self.update()
            self.on_success()
        else:
            self.txt_erreur.value = "Code PIN incorrect"
            self.champ_code.value = ""
            self.update()
