import flet as ft
from utils.formatters import format_fcfa, format_datetime

class ClientTile(ft.Card):
    def __init__(self, client, db, on_op_click, on_delete_click):
        self.client = client
        self.db = db
        self.on_op_click = on_op_click
        self.on_delete_click = on_delete_click

        dette = client["dette"]
        a_une_dette = dette > 0
        couleur_statut = ft.Colors.RED_600 if a_une_dette else ft.Colors.GREEN_600

        # Récupération des transactions avec repli de sécurité si le nom varie
        if hasattr(self.db, "get_transactions"):
            historique = self.db.get_transactions(client["id"])
        elif hasattr(self.db, "get_historique_client"):
            historique = self.db.get_historique_client(client["id"])
        else:
            historique = []

        journal_controls = []
        if not historique:
            journal_controls.append(
                ft.Text("Aucune opération enregistrée", italic=True, color=ft.Colors.GREY_500, size=12)
            )
        else:
            journal_controls.append(
                ft.Text("Historique des transactions :", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.GREY_700)
            )
            for op in historique:
                type_op = op.get("type") or op.get("type_op")
                est_remboursement = type_op in ("rembourser", "remboursement")
                couleur_op = ft.Colors.GREEN_600 if est_remboursement else ft.Colors.RED_600
                prefixe = "- " if est_remboursement else "+ "
                libelle = op.get("note") or ("Remboursement" if est_remboursement else "Nouveau crédit")
                date_str = op.get("created_at") or op.get("date_op") or ""

                journal_controls.append(
                    ft.Container(
                        margin=ft.Margin.only(top=6),
                        padding=8,
                        bgcolor=ft.Colors.GREY_100,
                        border_radius=8,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column([
                                    ft.Text(libelle, weight=ft.FontWeight.W_500, size=13),
                                    ft.Text(format_datetime(date_str), size=11, color=ft.Colors.GREY_600),
                                ], spacing=2),
                                ft.Text(
                                    f"{prefixe}{format_fcfa(op['montant'])}",
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color=couleur_op
                                )
                            ]
                        )
                    )
                )

        actions_bar = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_400,
                    tooltip="Supprimer",
                    on_click=lambda e: self.on_delete_click(self.client)
                ),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                        icon_color=ft.Colors.GREEN_600,
                        tooltip="Rembourser (-)",
                        icon_size=28,
                        on_click=lambda e: self.on_op_click(self.client, False)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                        icon_color=ft.Colors.RED_600,
                        tooltip="Ajouter dette (+)",
                        icon_size=28,
                        on_click=lambda e: self.on_op_click(self.client, True)
                    ),
                ])
            ]
        )

        expansion = ft.ExpansionTile(
            title=ft.Text(client["nom"], size=18, weight=ft.FontWeight.BOLD),
            subtitle=ft.Text(
                format_fcfa(dette),
                size=15,
                weight=ft.FontWeight.BOLD,
                color=couleur_statut
            ),
            leading=ft.Icon(ft.Icons.PERSON, size=28, color=ft.Colors.GREY_700),
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=15, bottom=15),
                    content=ft.Column(
                        controls=[
                            ft.Divider(height=10, color=ft.Colors.GREY_300),
                            actions_bar,
                            ft.Divider(height=10, color=ft.Colors.GREY_300),
                            ft.Column(controls=journal_controls, spacing=4)
                        ]
                    )
                )
            ]
        )

        super().__init__(elevation=2, content=expansion)