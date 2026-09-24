import os
import sqlite3
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

    # --- CODE PIN & SESSION ---
    def get_pin(self):
        return self.get_parametre("code_pin")

    def set_pin(self, nouveau_pin: str):
        self.set_parametre("code_pin", nouveau_pin)

    def get_user_session(self):
        with self.get_connection() as conn:
            cur = conn.execute(
                "SELECT cle, valeur FROM parametres WHERE cle IN ('user_id', 'user_email')"
            )
            rows = {row["cle"]: row["valeur"] for row in cur.fetchall()}
            return {"user_id": rows.get("user_id"), "email": rows.get("user_email")}

    def save_user_session(self, user_id: str, email: str, stay_logged_in: bool = True):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES ('user_id', ?)", (user_id,))
            conn.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES ('user_email', ?)", (email,))
