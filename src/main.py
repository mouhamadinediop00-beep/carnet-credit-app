import webbrowser
import flet as ft

from database.db_manager import Database
from ui.auth_view import AuthView
from ui.components.pin_view import PinView
from ui.components.header import Header
from ui.components.client_tile import ClientTile
from ui.dialogs.ajout_client import DialogAjout
from ui.dialogs.dialogue_operation import DialogOperation
from ui.dialogs.pin_settings import DialogPinSettings
from utils.subscription_checker import verifier_statut_abonnement
from utils.updater import verifier_mise_a_jour
from utils.paytech_service import generer_lien_paiement_paytech

def main(page: ft.Page):
    page.title = "Carnet de Crédit"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16

    db = Database()

    # --- 1. BOÎTE DE DIALOGUE : PAIEMENT D'ABONNEMENT ---
    def afficher_dialogue_abonnement():
        session = db.get_user_session()
        user_id = session.get("user_id")

        txt_status = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        progress_bar = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2)

        def fermer_dialogue(e=None):
            dlg.open = False
            page.update()

        def aller_au_paiement(e):
            txt_status.value = "Génération du lien de paiement..."
            txt_status.color = ft.Colors.BLUE_700
            page.update()

            lien_paiement = generer_lien_paiement_paytech(user_id)
            if lien_paiement:
                txt_status.value = "Redirection vers PayTech..."
                page.update()
                webbrowser.open(lien_paiement)
            else:
                txt_status.value = "Erreur de connexion à PayTech."
                txt_status.color = ft.Colors.RED_600
                page.update()

        def reverifier_paiement(e):
            progress_bar.visible = True
            txt_status.value = "Vérification en cours sur Supabase..."
            txt_status.color = ft.Colors.BLUE_700
            page.update()

            est_actif, raison = verifier_statut_abonnement(db, forcer_verification=True)
            progress_bar.visible = False
            
            if est_actif:
                fermer_dialogue()
                page.snack_bar = ft.SnackBar(ft.Text("Abonnement activé avec succès !"), bgcolor=ft.Colors.GREEN_600)
                page.snack_bar.open = True
                page.update()
                charger_application_principale()
            else:
                txt_status.value = f"Non activé : {raison}"
                txt_status.color = ft.Colors.RED_600
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.LOCK, color=ft.Colors.RED_600),
                ft.Text("Abonnement requis", weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Column([
                ft.Text(
                    "Votre abonnement mensuel est arrivé à échéance.\n"
                    "Renouvelez votre abonnement pour continuer à utiliser l'application.",
                    size=14
                ),
                ft.Container(height=8),
                ft.Text("Tarif : 2 000 FCFA / mois", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                ft.Text("Disponible via Wave, Orange Money, Free Money ou Carte.", size=12, color=ft.Colors.GREY_700),
                ft.Row([progress_bar, txt_status], spacing=8)
            ], tight=True, spacing=8),
            actions=[
                ft.TextButton("Vérifier le paiement", on_click=reverifier_paiement),
                ft.ElevatedButton(
                    "Payer (2 000 FCFA)",
                    icon=ft.Icons.PAYMENT,
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    on_click=aller_au_paiement
                )
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # --- 2. GESTION DES OPÉRATIONS (DETTE / REMBOURSEMENT) ---
    def gerer_operation(client, is_dette: bool):
        est_autorise, raison = verifier_statut_abonnement(db)
        if not est_autorise:
            afficher_dialogue_abonnement()
            return

        def valider_op(client_id, type_op, montant):
            db.add_transaction(client_id, type_op, montant, "Endettement" if type_op == "dette" else "Remboursement")
            charger_application_principale()

        dialogue_op = DialogOperation(on_valider=valider_op)
        dialogue_op.ouvrir(
            page,
            client["id"],
            "dette" if is_dette else "remboursement",
            dette_actuelle=client["dette"]
        )

    # --- 3. GESTION DE LA SUPPRESSION CLIENT ---
    def confirmer_suppression(client):
        def supprimer(e):
            db.delete_client(client["id"])
            dlg.open = False
            page.update()
            charger_application_principale()

        def fermer(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Supprimer le client"),
            content=ft.Text(f"Voulez-vous vraiment supprimer {client['nom']} et son historique ?"),
            actions=[
                ft.TextButton("Annuler", on_click=fermer),
                ft.ElevatedButton("Supprimer", bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE, on_click=supprimer)
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # --- 4. GESTION D'AJOUT DE CLIENT ---
    def au_clic_ajouter_client(e):
        est_autorise, raison = verifier_statut_abonnement(db)
        if est_autorise:
            def valider_ajout(nom, dette):
                db.add_client(nom, dette)
                charger_application_principale()

            dialogue_ajout = DialogAjout(on_ajouter=valider_ajout, db_ref=db)
            dialogue_ajout.ouvrir(page)
        else:
            afficher_dialogue_abonnement()

    # --- 5. INTERFACE PRINCIPALE ---
    def charger_application_principale():
        page.controls.clear()

        def ouvrir_parametres_pin():
            dlg_pin = DialogPinSettings(db_ref=db, on_pin_changed=lambda new_pin: None)
            dlg_pin.ouvrir(page)

        header = Header(on_pin_click=ouvrir_parametres_pin)
        header.mettre_a_jour(db.get_total_dettes(), db.get_total_remboursements())

        txt_recherche = ft.TextField(
            hint_text="Rechercher un client...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            on_change=lambda e: rafraichir_liste_clients(e.control.value)
        )

        liste_view = ft.ListView(expand=True, spacing=8)

        def rafraichir_liste_clients(filtre=""):
            liste_view.controls.clear()
            clients = db.get_all_clients(filtre)
            if not clients:
                liste_view.controls.append(
                    ft.Container(
                        content=ft.Text("Aucun client trouvé", color=ft.Colors.GREY_500),
                        alignment=ft.alignment.Alignment(0, 0),
                        padding=20
                    )
                )
            else:
                for c in clients:
                    tile = ClientTile(
                        client=c,
                        db=db,
                        on_op_click=gerer_operation,
                        on_delete_click=confirmer_suppression
                    )
                    liste_view.controls.append(tile)
            page.update()

        rafraichir_liste_clients()

        btn_fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.BLUE_700,
            on_click=au_clic_ajouter_client
        )

        page.add(header, txt_recherche, liste_view)
        page.floating_action_button = btn_fab
        page.update()

        verifier_mise_a_jour(page)

    # --- 6. ÉCRAN DU CODE PIN ---
    def ouvrir_ecran_code_pin():
        pin_actuel = db.get_pin()
        if not pin_actuel:
            charger_application_principale()
        else:
            page.controls.clear()
            pin_view = PinView(pin_correct=pin_actuel, on_success=charger_application_principale)
            page.add(pin_view)
            page.update()

    # --- 7. INITIALISATION DU FLUX D'ACCÈS ---
    session = db.get_user_session()

    if not session["user_id"]:
        def au_succes_authentification(user_id):
            db.save_user_session(user_id, "", False)
            verifier_statut_abonnement(db)
            ouvrir_ecran_code_pin()

        page.controls.clear()
        page.add(AuthView(on_auth_success=au_succes_authentification))
        page.update()
    else:
        ouvrir_ecran_code_pin()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="../assets")