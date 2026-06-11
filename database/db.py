"""Connexion à la base de données SQLite."""
import sqlite3
import os

CHEMIN_DB = os.path.join(os.path.dirname(__file__), "ymmo.db")


def get_connexion():
    """Ouvre une connexion. row_factory permet d'accéder aux colonnes par leur nom."""
    conn = sqlite3.connect(CHEMIN_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Crée les tables à partir du schéma si la base n'existe pas encore."""
    schema = os.path.join(os.path.dirname(__file__), "schema.sql")
    with get_connexion() as conn, open(schema, encoding="utf-8") as f:
        conn.executescript(f.read())
