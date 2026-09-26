import os
import sqlite3
import hashlib
import hmac
import secrets
from contextlib import contextmanager

# Sur Android, seul le dossier fourni par Flet est accessible en écriture
# et conservé entre les lancements. Sur PC, on retombe sur le dossier courant.
DATA_DIR = os.getenv("FLET_APP_STORAGE_DATA", ".")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "carnet.db")


class Database:
    def __init__(self, db_name: str = DB_PATH):
        self.db_name = db_name
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Ouvre une connexion, valide (commit) en cas de succès,
        annule (rollback) en cas d'erreur, et ferme toujours la connexion."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # --- PARAMÈTRES ---
    def get_parametre(self, cle: str):
        with self.get_connection() as conn:
            row = conn.execute("SELECT valeur FROM parametres WHERE cle = ?", (cle,)).fetchone()
            return row["valeur"] if row else None

    def set_parametre(self, cle: str, valeur: str):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES (?, ?)", (cle, valeur))

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    dette INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    type TEXT NOT NULL,
                    montant INTEGER NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS parametres (
                    cle TEXT PRIMARY KEY,
                    valeur TEXT
                )
            """)

            # Migration : ajoute la colonne 'note' sur les anciennes bases
            try:
                conn.execute("ALTER TABLE transactions ADD COLUMN note TEXT")
            except sqlite3.OperationalError:
                pass

    # --- CLIENTS ---
    def nom_existe(self, nom: str) -> bool:
        """Vérifie si un client avec ce nom existe déjà."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM clients WHERE LOWER(nom) = LOWER(?)", (nom.strip(),)
            ).fetchone()
            return row is not None

    def get_all_clients(self, filtre: str = ""):
        with self.get_connection() as conn:
            if filtre:
                cur = conn.execute(
                    "SELECT * FROM clients WHERE nom LIKE ? ORDER BY nom ASC", (f"%{filtre}%",)
                )
            else:
                cur = conn.execute("SELECT * FROM clients ORDER BY nom ASC")
            return [dict(row) for row in cur.fetchall()]

    def add_client(self, nom: str, dette: int = 0):
        with self.get_connection() as conn:
            cur = conn.execute("INSERT INTO clients (nom, dette) VALUES (?, ?)", (nom.strip(), dette))
            client_id = cur.lastrowid
            if dette > 0:
                conn.execute(
                    "INSERT INTO transactions (client_id, type, montant, note) VALUES (?, ?, ?, ?)",
                    (client_id, "dette", dette, "Dette initiale"),
                )

    def delete_client(self, client_id: int):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM transactions WHERE client_id = ?", (client_id,))
            conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))

    # --- TRANSACTIONS ---
    def get_transactions(self, client_id: int):
        with self.get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM transactions WHERE client_id = ? ORDER BY created_at DESC, id DESC",
                (client_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_historique_client(self, client_id: int):
        """Alias de compatibilité pour get_transactions."""
        return self.get_transactions(client_id)

    def add_transaction(self, client_id: int, type_op: str, montant: int, note: str = ""):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO transactions (client_id, type, montant, note) VALUES (?, ?, ?, ?)",
                (client_id, type_op, montant, note),
            )
            if type_op == "dette":
                conn.execute("UPDATE clients SET dette = dette + ? WHERE id = ?", (montant, client_id))
            else:
                conn.execute(
                    "UPDATE clients SET dette = MAX(0, dette - ?) WHERE id = ?", (montant, client_id)
                )

    def get_total_dettes(self):
        with self.get_connection() as conn:
            res = conn.execute("SELECT SUM(dette) FROM clients").fetchone()[0]
            return res if res else 0

    def get_total_remboursements(self):
        with self.get_connection() as conn:
            res = conn.execute(
                "SELECT SUM(montant) FROM transactions WHERE type IN ('rembourser', 'remboursement')"
            ).fetchone()[0]
            return res if res else 0

    # ========================================================
    # CODE PIN
    # ========================================================

    def get_pin(self):
        """
        Retourne la valeur enregistrée.
        Et non plus le PIN en clair.
        """

        return self.get_parametre(
            "code_pin"
        )


    def set_pin(self, nouveau_pin: str):
        """
        Hash le PIN avec PBKDF2-HMAC-SHA256
        avant stockage dans SQLite.
        """

        if not nouveau_pin:
            raise ValueError(
                "Le PIN ne peut pas être vide."
            )

        sel = secrets.token_hex(16)

        hash_pin = hashlib.pbkdf2_hmac(
            "sha256",
            nouveau_pin.encode("utf-8"),
            bytes.fromhex(sel),
            200_000
        ).hex()

        valeur_stockee = (
            f"pbkdf2${sel}${hash_pin}"
        )

        self.set_parametre(
            "code_pin",
            valeur_stockee
        )


    def verifier_pin(self, pin_saisi: str):
        """
        Vérifie le PIN sans jamais avoir besoin
        de connaître le PIN original.
        """

        valeur_stockee = self.get_pin()

        if not valeur_stockee:
            return False

        # ----------------------------------------------------
        # Si le PIN est correct, migration automatique
        # vers PBKDF2.
        # ----------------------------------------------------

        if not valeur_stockee.startswith(
            "pbkdf2$"
        ):

            if hmac.compare_digest(
                valeur_stockee,
                pin_saisi
            ):
                self.set_pin(pin_saisi)
                return True

            return False

        # ----------------------------------------------------
        # Nouveau format sécurisé
        # ----------------------------------------------------

        try:

            _, sel, hash_attendu = (
                valeur_stockee.split(
                    "$",
                    2
                )
            )

            hash_saisi = hashlib.pbkdf2_hmac(
                "sha256",
                pin_saisi.encode("utf-8"),
                bytes.fromhex(sel),
                200_000
            ).hex()

            return hmac.compare_digest(
                hash_saisi,
                hash_attendu
            )

        except Exception as e:

            print(
                f"Erreur vérification PIN : {e}"
            )

            return False

    def supprimer_pin(self):
        """
        Supprimer le code PIN enregistré pour désactiver la protection.
        """
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM parametres WHERE cle = 'code_pin'"
            )

    # ========================================================
    # SESSION UTILISATEUR
    # ========================================================

    def get_user_session(self):
        """
        SQLite ne contient plus aucun token Supabase.

        Il contient uniquement l'identité locale
        de l'utilisateur.
        """

        with self.get_connection() as conn:

            cur = conn.execute("""
                SELECT cle, valeur
                FROM parametres
                WHERE cle IN (
                    'user_id',
                    'user_email'
                )
            """)

            rows = {
                row["cle"]: row["valeur"]
                for row in cur.fetchall()
            }

            return {
                "user_id":
                    rows.get("user_id"),

                "email":
                    rows.get("user_email")
            }


    def save_user_session(
        self,
        user_id: str,
        email: str = "",
        stay_logged_in: bool = True
    ):
        """
        Enregistre uniquement les informations
        non sensibles.

        Les tokens Supabase sont enregistrés
        dans SecureStorage.
        """

        with self.get_connection() as conn:

            conn.execute(
                """
                INSERT OR REPLACE INTO parametres
                (cle, valeur)
                VALUES ('user_id', ?)
                """,
                (user_id,)
            )

            conn.execute(
                """
                INSERT OR REPLACE INTO parametres
                (cle, valeur)
                VALUES ('user_email', ?)
                """,
                (email or "",)
            )


    def supprimer_anciens_tokens(self):
        """
        Migration de sécurité.

        Supprime access_token et refresh_token
        des anciennes installations.
        """

        with self.get_connection() as conn:

            conn.execute("""
                DELETE FROM parametres
                WHERE cle IN (
                    'access_token',
                    'refresh_token'
                )
            """)


    def clear_user_session(self):
        """
        Supprime l'identité locale lors
        d'une déconnexion.
        """

        with self.get_connection() as conn:

            conn.execute("""
                DELETE FROM parametres
                WHERE cle IN (
                    'user_id',
                    'user_email',
                    'access_token',
                    'refresh_token'
                )
            """)