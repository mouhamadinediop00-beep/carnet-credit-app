import os
import threading
import asyncio

import flet as ft

from database.db_manager import Database
from database.supabase_client import SupabaseManager
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
from utils.url_helper import ouvrir_url
from utils.secure_storage import SecureSessionStorage


async def main(page: ft.Page):
    page.title = "Carnet de Crédit"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16

    db = Database()
    secure_session = SecureSessionStorage()

    # La vérification de mise à jour ne se fait qu'une fois par lancement
    maj_deja_verifiee = {"fait": False}

    # --- 0. MISE À JOUR ---
    def afficher_dialogue_maj(url_apk: str):
        def fermer(e=None):
            dlg.open = False
            page.update()

        def telecharger(e):
            fermer()
            ouvrir_url(page, url_apk)

        dlg = ft.AlertDialog(
            title=ft.Text("Mise à jour disponible", weight=ft.FontWeight.BOLD),
            content=ft.Text(
                "Une nouvelle version de l'application est disponible.\n"
                "Le téléchargement s'ouvrira dans votre navigateur."
            ),
            actions=[
                ft.TextButton("Plus tard", on_click=fermer),
                ft.ElevatedButton("Télécharger", on_click=telecharger),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def controler_mise_a_jour():
        # Exécuté dans un thread pour ne pas bloquer l'interface
        disponible, url_apk = verifier_mise_a_jour()
        if disponible and url_apk:
            afficher_dialogue_maj(url_apk)

    def lancer_controle_maj_une_fois():
        if maj_deja_verifiee["fait"]:
            return
        maj_deja_verifiee["fait"] = True
        threading.Thread(target=controler_mise_a_jour, daemon=True).start()

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
            progress_bar.visible = True
            txt_status.value = "Génération du lien de paiement..."
            txt_status.color = ft.Colors.BLUE_700
            page.update()

            lien_paiement = generer_lien_paiement_paytech(user_id)
            progress_bar.visible = False
            if lien_paiement:
                txt_status.value = "Redirection vers PayTech..."
                page.update()
                ouvrir_url(page, lien_paiement)
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

    async def au_succes_authentification(user_id):
        
        # --------------------------------------------------------
        # 1. Récupération de la session créée par Supabase
        # --------------------------------------------------------
        
        session_supabase = (
            SupabaseManager.get_session()
        )
        
        if not session_supabase:
        
            page.snack_bar =(
                ft.SnackBar(
                    content=ft.Text(
                        "Impossible de récupérer la session."
                    )
                )
            )
            page.snack_bar.open = True
            page.update()
            return
    
        access_token = getattr(
            session_supabase,
            "access_token",
                None
        )
    
        refresh_token = getattr(
            session_supabase,
            "refresh_token",
            None
        )
    
        if not access_token or not refresh_token:
    
            page.snack_bar(
                ft.SnackBar(
                    content=ft.Text(
                        "Session Supabase incomplète."
                    )
                )
            )
            page.snack_bar.open = True
            page.update()
            return
    
        # --------------------------------------------------------
        # 2. Tokens -> stockage sécurisé
        # --------------------------------------------------------
    
        sauvegarde_ok = (
            await secure_session.sauvegarder_tokens(
                access_token,
                refresh_token
            )
        )
    
        if not sauvegarde_ok:
    
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(
                        "Impossible de sécuriser la session."
                    )
                )
            )
    
            return
        # --------------------------------------------------------
        # 3. SQLite -> uniquement user_id / email
        # --------------------------------------------------------

        db.save_user_session(
            user_id=user_id,
            email="",
            stay_logged_in=True
        )

        # --------------------------------------------------------
        # 4. Nettoyage des anciens tokens SQLite
        # --------------------------------------------------------

        db.supprimer_anciens_tokens()

        # --------------------------------------------------------
        # 5. Vérification initiale de l'abonnement
        # --------------------------------------------------------

        verifier_statut_abonnement(
            db,
            forcer_verification=True
        )
    
        # --------------------------------------------------------
        # 6. Ouverture du PIN
        # --------------------------------------------------------

        ouvrir_ecran_code_pin()

    async def deconnecter_utilisateur(e=None):
    
        # 1. Supabase
        SupabaseManager.se_deconnecter()
    
        # 2. Tokens sécurisés
        await secure_session.supprimer_tokens()
    
        # 3. Session locale SQLite
        db.clear_user_session()
    
        # 4. Anciennes traces éventuelles
        db.supprimer_anciens_tokens()
    
        # 5. Retour connexion
        page.controls.clear()
        page.floating_action_button = None
    
        page.add(
            AuthView(
                on_auth_success=au_succes_authentification
            )
        )
    
        page.update()
    

    # --- 5. INTERFACE PRINCIPALE ---
    def charger_application_principale():
        page.controls.clear()

        def ouvrir_parametres_pin():
            dlg_pin = DialogPinSettings(db_ref=db, on_pin_changed=lambda new_pin: None)
            dlg_pin.ouvrir(page)

        header = Header(
            on_pin_click=ouvrir_parametres_pin
        )

        btn_deconnexion = ft.IconButton(
            icon=ft.Icons.LOGOUT,
            tooltip="Se déconnecter",
            icon_color=ft.Colors.RED_600,
            on_click=deconnecter_utilisateur
        )

        barre_haut = ft.Row(
            controls=[
                ft.Container(
                    content=header,
                    expand=True
                ),
                btn_deconnexion
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        header.mettre_a_jour(
            db.get_total_dettes(),
            db.get_total_remboursements()
        )
    

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

        page.add(barre_haut,txt_recherche,liste_view)
        page.floating_action_button = btn_fab
        page.update()

        # Une seule vérification par lancement, en arrière-plan
        lancer_controle_maj_une_fois()

    # --- 6. ÉCRAN DU CODE PIN ---
    def ouvrir_ecran_code_pin():
        pin_existe = db.get_pin()
        if not pin_existe:
            charger_application_principale()
        else:
            page.controls.clear()
            pin_view = PinView(db_ref=db, on_success=charger_application_principale)
            page.add(pin_view)
            page.update()

    # ========================================================
    # DÉMARRAGE / RESTAURATION SESSION
    # ========================================================

    session_locale = db.get_user_session()

    user_id = session_locale.get(
        "user_id"
    )

    # ========================================================
    # AUCUN UTILISATEUR LOCAL
    # ========================================================

    if not user_id:

        def afficher_authentification():

            page.controls.clear()

            page.add(
                AuthView(
                    on_auth_success=
                    au_succes_authentification
                )
            )

            page.update()


        afficher_authentification()


    # ========================================================
    # UTILISATEUR DÉJÀ CONNU
    # ========================================================

    else:

        # ----------------------------------------------------
        # Migration :
        # suppression d'éventuels anciens tokens SQLite
        # ----------------------------------------------------

        db.supprimer_anciens_tokens()

        # ----------------------------------------------------
        # Lecture SecureStorage
        # ----------------------------------------------------

        access_token, refresh_token = (
            await secure_session.recuperer_tokens()
        )

        # ----------------------------------------------------
        # Tentative de restauration Supabase
        # ----------------------------------------------------

        if access_token and refresh_token:

            restauration_ok = (
                SupabaseManager.restaurer_session(
                    access_token,
                    refresh_token
                )
            )

            if restauration_ok:

                # Supabase peut avoir renouvelé le JWT.
                nouvelle_session = (
                    SupabaseManager.get_session()
                )

                if nouvelle_session:

                    nouveau_access = getattr(
                        nouvelle_session,
                        "access_token",
                        None
                    )

                    nouveau_refresh = getattr(
                        nouvelle_session,
                        "refresh_token",
                        None
                    )

                    if (
                        nouveau_access
                        and nouveau_refresh
                    ):

                        await (
                            secure_session
                            .sauvegarder_tokens(
                                nouveau_access,
                                nouveau_refresh
                            )
                        )

        ouvrir_ecran_code_pin()

    async def supprimer_compte_utilisateur(e=None):
        def confirmer(e):
            dlg.open = False
            page.update()

            succes, msg = SupabaseManager.supprimer_compte()
            if succes:
                db.clear_user_session()
                db.supprimer_anciens_tokens()
                asyncio.create_task(secure_session.supprimer_tokens())
                page.controls.clear()
                page.floating_action_button = None
                page.add(AuthView(on_auth_success=au_succes_authentification))
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erreur : {msg}"), bgcolor=ft.Colors.RED_600)
                page.snack_bar.open = True
            page.update()

        def annuler(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Supprimer le compte"),
            content=ft.Text(
                "Cette action est définitive. Votre compte, votre abonnement et vos accès seront "
                "supprimés. Vos clients et transactions locaux resteront sur cet appareil.",
                size=13
            ),
            actions=[
                ft.TextButton("Annuler", on_click=annuler),
                ft.ElevatedButton("Supprimer définitivement", bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE, on_click=confirmer)
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()



if __name__ == "__main__":
    # Le dossier "assets" doit être à côté de main.py ; on ne le déclare que s'il existe.
    dossier_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    options = {"assets_dir": "assets"} if os.path.isdir(dossier_assets) else {}

    lanceur = ft.app if hasattr(ft, "app") else ft.run
    lanceur(main, **options)
