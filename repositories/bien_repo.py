"""
Couche d'accès aux données pour les biens.

Tout le SQL lié aux biens est regroupé ici. Les services appellent ces méthodes
sans savoir comment les données sont stockées (séparation des responsabilités).
"""
from database.db import get_connexion
from models.bien import Bien
import media

# Colonnes du bien + sa première photo, réutilisé dans plusieurs requêtes
SELECT_BIEN = """
    SELECT b.*, p.url AS photo
    FROM bien b
    LEFT JOIN photo p ON p.bien_id = b.id AND p.ordre = 0
"""


def lister(filtres=None):
    """
    Renvoie les biens correspondant aux filtres.
    filtres : dict optionnel (ville, type, prix_min, prix_max, surface_min, statut).
    On construit la clause WHERE dynamiquement en utilisant des paramètres liés
    pour éviter les injections SQL.
    """
    filtres = filtres or {}
    conditions, params = [], []

    if filtres.get("statut"):
        conditions.append("b.statut = ?")
        params.append(filtres["statut"])
    if filtres.get("ville"):
        conditions.append("b.ville = ?")
        params.append(filtres["ville"])
    if filtres.get("type"):
        conditions.append("b.type = ?")
        params.append(filtres["type"])
    if filtres.get("prix_min"):
        conditions.append("b.prix >= ?")
        params.append(filtres["prix_min"])
    if filtres.get("prix_max"):
        conditions.append("b.prix <= ?")
        params.append(filtres["prix_max"])
    if filtres.get("surface_min"):
        conditions.append("b.surface >= ?")
        params.append(filtres["surface_min"])

    sql = SELECT_BIEN
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY b.date_creation DESC"

    with get_connexion() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [Bien.from_row(r) for r in rows]


def trouver(bien_id):
    with get_connexion() as conn:
        row = conn.execute(SELECT_BIEN + " WHERE b.id = ?", (bien_id,)).fetchone()
    return Bien.from_row(row) if row else None


def villes_disponibles():
    """Liste des villes ayant au moins un bien, pour alimenter le filtre de recherche."""
    with get_connexion() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ville FROM bien ORDER BY ville"
        ).fetchall()
    return [r["ville"] for r in rows]


def creer(donnees, agence_id, commercial_id):
    with get_connexion() as conn:
        cur = conn.execute(
            """INSERT INTO bien (titre, description, type, prix, surface, nb_pieces,
                                 nb_chambres, ville, code_postal, adresse, dpe,
                                 agence_id, commercial_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (donnees["titre"], donnees.get("description"), donnees["type"],
             donnees["prix"], donnees["surface"], donnees.get("nb_pieces"),
             donnees.get("nb_chambres"), donnees["ville"], donnees["code_postal"],
             donnees.get("adresse"), donnees.get("dpe"), agence_id, commercial_id),
        )
        bien_id = cur.lastrowid
        photo = donnees.get("photo") or media.image_pour(donnees["type"], bien_id)
        conn.execute("INSERT INTO photo (bien_id, url, ordre) VALUES (?, ?, 0)",
                     (bien_id, photo))
    return bien_id


def photos(bien_id):
    """Toutes les photos d'un bien, ordonnées (pour la galerie de la fiche)."""
    with get_connexion() as conn:
        rows = conn.execute(
            "SELECT url FROM photo WHERE bien_id = ? ORDER BY ordre", (bien_id,)
        ).fetchall()
    return [r["url"] for r in rows]


def changer_statut(bien_id, statut):
    with get_connexion() as conn:
        conn.execute("UPDATE bien SET statut = ? WHERE id = ?", (statut, bien_id))


def supprimer(bien_id):
    with get_connexion() as conn:
        conn.execute("DELETE FROM bien WHERE id = ?", (bien_id,))
