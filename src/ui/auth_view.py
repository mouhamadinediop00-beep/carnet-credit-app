import flet as ft
from database.supabase_client import SupabaseManager

class AuthView(ft.Container):
    def __init__(self, on_auth_success):
        super().__init__(expand=True, padding=20)
        self.on_auth_success = on_auth_success
        self.is_signup_mode = False

        self.txt_telephone = ft.TextField(
            label="Numéro de téléphone",
            hint_text="ex: 771234567",
            prefix_icon=ft.Icons.PHONE,
            border_radius=10,
            keyboard_type=ft.KeyboardType.PHONE
        )
        self.txt_password = ft.TextField(
            label="Mot de passe (6 caractères min.)",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10
        )
        self.lbl_erreur = ft.Text(
            "", 
            color=ft.Colors.RED_600, 
            size=13, 
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )

        # Radio / Boutons de bascule simples et très lisibles
        self.switch_mode = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="login", label="Se connecter"),
                ft.Radio(value="signup", label="S'inscrire (30j gratuits)"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            value="login",
            on_change=self._changer_mode
        )

        self.btn_action = ft.ElevatedButton(
            "Se connecter",
            bgcolor=ft.Colors.BLUE_700,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            width=320,
            height=45,
            on_click=self._soumettre
        )

        self.content = ft.Column([
            ft.Container(height=10),
            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=55, color=ft.Colors.BLUE_600),
            ft.Text("Carnet de Crédit", size=22, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            self.switch_mode,
            ft.Container(height=10),
            self.txt_telephone,
            self.txt_password,
            self.lbl_erreur,
            ft.Container(height=10),
            self.btn_action,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    def _changer_mode(self, e):
        self.lbl_erreur.value = ""
        self.is_signup_mode = (self.switch_mode.value == "signup")
        
        if self.is_signup_mode:
            self.btn_action.text = "Créer mon compte"
            self.btn_action.bgcolor = ft.Colors.GREEN_700
        else:
            self.btn_action.text = "Se connecter"
            self.btn_action.bgcolor = ft.Colors.BLUE_700
            
        self.update()

    def _soumettre(self, e):
        tel = self.txt_telephone.value.strip()
        pwd = self.txt_password.value.strip()

        if not tel or not pwd:
            self.lbl_erreur.value = "Veuillez remplir tous les champs."
            self.update()
            return

        if len("".join(filter(str.isdigit, tel))) < 8:
            self.lbl_erreur.value = "Numéro de téléphone invalide."
            self.update()
            return

        self.btn_action.disabled = True
        self.lbl_erreur.value = "Patientez..."
        self.update()

        if self.is_signup_mode:
            succes, res = SupabaseManager.s_inscrire(tel, pwd)
        else:
            succes, res = SupabaseManager.se_connecter(tel, pwd)

        if succes:
            self.on_auth_success(res)
        else:
            self.lbl_erreur.value = res
            self.btn_action.disabled = False
            self.update()