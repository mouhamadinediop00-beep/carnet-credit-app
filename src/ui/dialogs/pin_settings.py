import flet as ft

class DialogPinSettings(ft.AlertDialog):
    def __init__(self, db_ref, on_pin_changed):
        self.db = db_ref
        self.on_pin_changed = on_pin_changed

        self.champ_pin = ft.TextField(
            label="Code PIN (6 chiffres)",
            password=True,
            can_reveal_password=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=6,
            autofocus=True
        )

        super().__init__(
            title=ft.Text("Sécurité PIN"),
            content=ft.Column([
                ft.Text("Définissez un code PIN à 6 chiffres pour protéger l'accès à votres carnet. Laissez vide pour désactiver le verrouillage.", size=13, color=ft.Colors.GREY_700),
                self.champ_pin
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Annuler", on_click=self.fermer),
                ft.ElevatedButton(
                    "Enregistrer",
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    on_click=self.enregistrer
                )
            ]
        )

    def ouvrir(self, page):
        pin_actuel = self.db.get_pin()
        self.champ_pin.value = ""

        self.champ_pin.error_text = None
        self.champ_pin.hint_text = "PIN déjà défini — laissez vide pour le garder" if pin_actuel else None
        if self not in page.overlay:
            page.overlay.append(self)
        self.open = True
        page.update()

    def fermer(self, e):
        self.open = False
        e.page.update()

    def enregistrer(self, e):
        val = (self.champ_pin.value or "").strip()

        if not val:
            self.db.set_parametre("code_pin", None)   # désactive le verrouillage
            self.open = False
            e.page.update()
            self.on_pin_changed(val)
            return

        if val and (not val.isdigit() or len(val) != 6):
            self.champ_pin.error_text = "Le PIN doit contenir exactement 6 chiffres"
            self.update()
            return

        self.db.set_pin(val)
        self.open = False
        e.page.update()
        self.on_pin_changed(val)
        