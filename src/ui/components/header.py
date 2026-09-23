import flet as ft
from utils.formatters import format_fcfa

class Header(ft.Container):
    def __init__(self, on_pin_click):
        self.on_pin_click = on_pin_click
        self.txt_total_dettes = ft.Text("0 FCFA", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
        self.txt_total_remboursements = ft.Text("0 FCFA", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)

        card_dettes = ft.Container(
            expand=True,
            bgcolor=ft.Colors.RED_50,
            border_radius=10,
            padding=12,
            content=ft.Column([
                ft.Text("Total Dettes", size=13, color=ft.Colors.RED_900,weight=ft.FontWeight.W_500),
                self.txt_total_dettes
            ], spacing=4)
        )

        card_remboursements = ft.Container(
            expand=True,
            bgcolor=ft.Colors.GREEN_50,
            border_radius=10,
            padding=12,
            content=ft.Column([
                ft.Text("Total Remboursé", size=13, color=ft.Colors.GREEN_900, weight=ft.FontWeight.W_500),
                self.txt_total_remboursements
            ], spacing=4)
        )

        super().__init__(
            margin=ft.Margin.only(bottom=15),
            content=ft.Column([
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=30, color=ft.Colors.BLUE_600),
                            ft.Text("Carnet de Crédit", size=22, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.IconButton(
                            icon=ft.Icons.SECURITY,
                            icon_color=ft.Colors.BLUE_700,
                            tooltip="Code PIN de sécurité",
                            on_click=lambda e: self.on_pin_click()
                        )
                    ]
                ),
                ft.Row([card_dettes, card_remboursements], spacing=10)
            ], spacing=12)
        )

    def mettre_a_jour(self, total_dettes: int, total_remboursements: int):
        self.txt_total_dettes.value = format_fcfa(total_dettes)
        self.txt_total_remboursements.value = format_fcfa(total_remboursements)