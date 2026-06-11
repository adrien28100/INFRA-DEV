"""Accès aux données pour les utilisateurs, favoris et demandes de visite."""
from database.db import get_connexion
from models.bien import Utilisateur, Bien
from repositories.bien_repo import SELECT_BIEN


# --- Utilisateurs ---

def trouver_par_email(email):
    """Renvoie la ligne complète (avec le hash) pour la connexion."""
    with get_connexion() as conn:
        return conn.execute(
            "SELECT * FROM utilisateur WHERE email = ?", (email,)
        ).fetchone()


def trouver(user_id):
    with get_connexion() as conn:
        row = conn.execute("SELECT * FROM utilisateur WHERE id = ?", (user_id,)).fetchone()
    return Utilisateur.from_row(row) if row else None


def creer(nom, prenom, email, mot_de_passe_hash):
    with get_connexion() as conn:
        cur = conn.execute(
            """INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role)
               VALUES (?, ?, ?, ?, 'client')""",
            (nom, prenom, email, mot_de_passe_hash),
        )
        return cur.lastrowid


# --- Favoris ---

def ajouter_favori(user_id, bien_id):
    with get_connexion() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO favori (utilisateur_id, bien_id) VALUES (?, ?)",
            (user_id, bien_id),
        )


def retirer_favori(user_id, bien_id):
    with get_connexion() as conn:
        conn.execute(
            "DELETE FROM favori WHERE utilisateur_id = ? AND bien_id = ?",
            (user_id, bien_id),
        )


def lister_favoris(user_id):
    with get_connexion() as conn:
        rows = conn.execute(
            SELECT_BIEN + """ JOIN favori f ON f.bien_id = b.id
                              WHERE f.utilisateur_id = ?
                              ORDER BY f.date_ajout DESC""",
            (user_id,),
        ).fetchall()
    return [Bien.from_row(r) for r in rows]


def ids_favoris(user_id):
    """Ensemble des ids favoris, pratique pour afficher le bon état du bouton cœur."""
    with get_connexion() as conn:
        rows = conn.execute(
            "SELECT bien_id FROM favori WHERE utilisateur_id = ?", (user_id,)
        ).fetchall()
    return {r["bien_id"] for r in rows}


# --- Visites ---

def demander_visite(bien_id, client_id, date_visite, message):
    with get_connexion() as conn:
        conn.execute(
            """INSERT INTO visite (bien_id, client_id, date_visite, message)
               VALUES (?, ?, ?, ?)""",
            (bien_id, client_id, date_visite, message),
        )


def visites_du_client(client_id):
    with get_connexion() as conn:
        return conn.execute(
            """SELECT v.*, b.titre FROM visite v
               JOIN bien b ON b.id = v.bien_id
               WHERE v.client_id = ? ORDER BY v.date_visite DESC""",
            (client_id,),
        ).fetchall()
