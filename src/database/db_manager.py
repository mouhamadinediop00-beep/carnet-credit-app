import sqlite3

class Database:
    def __init__(self, db_name="carnet.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def get_parametre(self, cle: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valeur FROM parametres WHERE cle = ?", (cle,))
            row = cursor.fetchone()
            return row["valeur"] if row else None

    def set_parametre(self, cle: str, valeur: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES (?, ?)", (cle, valeur))
            conn.commit()
            
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Table clients
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    dette INTEGER DEFAULT 0
                )
            """)
            
            # 2. Table transactions
            cursor.execute("""
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

            # 3. Table parametres
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parametres (
                    cle TEXT PRIMARY KEY,
                    valeur TEXT
                )
            """)

            # Migration automatique de la colonne 'note'
            try:
                cursor.execute("ALTER TABLE transactions ADD COLUMN note TEXT")
            except sqlite3.OperationalError:
                pass

            conn.commit()

    # --- MÉTHODES CLIENTS ---
    def nom_existe(self, nom: str) -> bool:
        """Vérifie si un client avec ce nom existe déjà dans la base de données."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM clients WHERE LOWER(nom) = LOWER(?)", (nom.strip(),))
            return cursor.fetchone() is not None

    def get_all_clients(self, filtre=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if filtre:
                cursor.execute("SELECT * FROM clients WHERE nom LIKE ? ORDER BY nom ASC", (f"%{filtre}%",))
            else:
                cursor.execute("SELECT * FROM clients ORDER BY nom ASC")
            return [dict(row) for row in cursor.fetchall()]

    def add_client(self, nom: str, dette: int = 0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO clients (nom, dette) VALUES (?, ?)", (nom.strip(), dette))
            client_id = cursor.lastrowid
            if dette > 0:
                cursor.execute(
                    "INSERT INTO transactions (client_id, type, montant, note) VALUES (?, ?, ?, ?)",
                    (client_id, "dette", dette, "Dette initiale")
                )
            conn.commit()

    def delete_client(self, client_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE client_id = ?", (client_id,))
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()

    # --- MÉTHODES TRANSACTIONS ---
    def get_transactions(self, client_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_historique_client(self, client_id: int):
        """Alias de compatibilité pour get_transactions"""
        return self.get_transactions(client_id)

    def add_transaction(self, client_id: int, type_op: str, montant: int, note: str = ""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (client_id, type, montant, note) VALUES (?, ?, ?, ?)",
                (client_id, type_op, montant, note)
            )
            if type_op == "dette":
                cursor.execute("UPDATE clients SET dette = dette + ? WHERE id = ?", (montant, client_id))
            else:
                cursor.execute("UPDATE clients SET dette = MAX(0, dette - ?) WHERE id = ?", (montant, client_id))
            conn.commit()

    def get_total_dettes(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(dette) FROM clients")
            res = cursor.fetchone()[0]
            return res if res else 0

    def get_total_remboursements(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(montant) FROM transactions WHERE type IN ('rembourser', 'remboursement')")
            res = cursor.fetchone()[0]
            return res if res else 0

    # --- MÉTHODES CODE PIN & SESSION ---
    def get_pin(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valeur FROM parametres WHERE cle = 'code_pin'")
            row = cursor.fetchone()
            return row["valeur"] if row else None

    def set_pin(self, nouveau_pin: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES ('code_pin', ?)", (nouveau_pin,))
            conn.commit()

    def get_user_session(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cle, valeur FROM parametres WHERE cle IN ('user_id', 'user_email')")
            rows = {row["cle"]: row["valeur"] for row in cursor.fetchall()}
            return {
                "user_id": rows.get("user_id"),
                "email": rows.get("user_email")
            }

    def save_user_session(self, user_id: str, email: str, stay_logged_in: bool = True):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES ('user_id', ?)", (user_id,))
            cursor.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES ('user_email', ?)", (email,))
            conn.commit()