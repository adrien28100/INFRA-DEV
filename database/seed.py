"""
Génère un jeu de données réaliste pour Ymmo.
On crée le siège + 12 agences, des commerciaux, des clients, des biens
et un historique de ventes sur ~3 ans pour pouvoir faire l'analyse de données.

Lancer une seule fois : python -m database.seed
"""
import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from database.db import get_connexion, init_db, CHEMIN_DB
import media

random.seed(42)  # pour avoir toujours le même jeu de données

# Villes des agences avec leur code postal et un niveau de prix moyen au m²
VILLES = [
    ("Aix-en-Provence", "13100", 5200),
    ("Marseille", "13001", 3600),
    ("Lyon", "69001", 4900),
    ("Paris", "75011", 10500),
    ("Bordeaux", "33000", 4700),
    ("Toulouse", "31000", 3600),
    ("Nantes", "44000", 3900),
    ("Lille", "59000", 3400),
    ("Nice", "06000", 4800),
    ("Montpellier", "34000", 3500),
    ("Rennes", "35000", 3700),
    ("Strasbourg", "67000", 3300),
    ("Grenoble", "38000", 3000),
]

TYPES = ["appartement"]
DPE = ["A", "B", "C", "D", "E", "F", "G"]

PRENOMS = ["Lucas", "Emma", "Hugo", "Léa", "Nathan", "Chloé", "Théo", "Manon",
           "Enzo", "Camille", "Louis", "Sarah", "Jules", "Inès", "Adam", "Jade"]
NOMS = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Petit", "Durand",
        "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Garcia", "Roux"]

RUES = ["rue de la République", "avenue Victor Hugo", "boulevard Gambetta",
        "rue Pasteur", "cours Mirabeau", "allée des Tilleuls", "impasse des Lilas"]


def prix_au_m2(ville, type_bien, annee):
    """Calcule un prix au m² avec une variation par type, par année et un peu d'aléa."""
    base = dict((v[0], v[2]) for v in VILLES)[ville]
    coef_type = {"appartement": 1.0, "maison": 0.9, "terrain": 0.4, "local": 0.8}[type_bien]
    # le marché a augmenté d'environ 3% par an depuis 2022
    inflation = 1.03 ** (annee - 2022)
    alea = random.uniform(0.85, 1.15)
    return base * coef_type * inflation * alea


def creer_bien(ville_info, type_bien, date_creation):
    ville, cp, _ = ville_info
    annee = date_creation.year

    # On ne gère que des appartements
    surface = random.randint(20, 120)
    pieces = max(1, round(surface / 24))      # ~1 pièce toutes les 24 m²
    chambres = max(0, pieces - 1)

    prix = round(prix_au_m2(ville, type_bien, annee) * surface, -3)

    titre = f"Appartement T{pieces} - {ville}"

    return {
        "titre": titre,
        "description": media.description_pour(type_bien, ville, surface, pieces),
        "type": type_bien,
        "prix": prix,
        "surface": surface,
        "nb_pieces": pieces,
        "nb_chambres": chambres,
        "ville": ville,
        "code_postal": cp,
        "adresse": f"{random.randint(1, 90)} {random.choice(RUES)}",
        "dpe": random.choice(DPE),
        "date_creation": date_creation.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main():
    if os.path.exists(CHEMIN_DB):
        os.remove(CHEMIN_DB)
    init_db()

    conn = get_connexion()
    cur = conn.cursor()

    # --- Agences (la première est le siège à Aix) ---
    agence_ids = []
    for i, (ville, cp, _) in enumerate(VILLES):
        est_siege = 1 if i == 0 else 0
        nom = "Ymmo Siège" if est_siege else f"Ymmo {ville}"
        cur.execute(
            """INSERT INTO agence (nom, ville, code_postal, adresse, telephone, email, est_siege)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nom, ville, cp, f"{random.randint(1, 50)} {random.choice(RUES)}",
             "04 42 00 00 0" + str(i % 10), f"contact.{ville.lower().replace(' ', '')}@ymmo.fr", est_siege),
        )
        agence_ids.append(cur.lastrowid)

    # --- Admin du siège ---
    cur.execute(
        """INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role, agence_id)
           VALUES (?, ?, ?, ?, 'admin', ?)""",
        ("Admin", "Ymmo", "admin@ymmo.fr", generate_password_hash("admin123"), agence_ids[0]),
    )

    # --- Commerciaux (5 par agence) ---
    commerciaux = []
    for ag_id in agence_ids:
        for _ in range(5):
            prenom, nom = random.choice(PRENOMS), random.choice(NOMS)
            email = f"{prenom.lower()}.{nom.lower()}{random.randint(1, 999)}@ymmo.fr"
            cur.execute(
                """INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role, agence_id)
                   VALUES (?, ?, ?, ?, 'commercial', ?)""",
                (nom, prenom, email, generate_password_hash("test123"), ag_id),
            )
            commerciaux.append((cur.lastrowid, ag_id))

    # --- Clients ---
    clients = []
    for _ in range(150):
        prenom, nom = random.choice(PRENOMS), random.choice(NOMS)
        email = f"{prenom.lower()}.{nom.lower()}{random.randint(1, 9999)}@email.fr"
        cur.execute(
            """INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role)
               VALUES (?, ?, ?, ?, 'client')""",
            (nom, prenom, email, generate_password_hash("test123")),
        )
        clients.append(cur.lastrowid)

    # Un compte de démo facile à retenir pour l'oral
    cur.execute(
        """INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role)
           VALUES (?, ?, ?, ?, 'client')""",
        ("Demo", "Client", "demo@ymmo.fr", generate_password_hash("demo123")),
    )
    clients.append(cur.lastrowid)

    # --- Historique de ventes (pour l'analyse) ---
    # Appartements déjà vendus sur ~3 ans. Ils n'apparaissent pas dans les annonces
    # (statut "vendu") mais alimentent le tableau de bord et l'estimation de prix.
    debut = datetime(2022, 1, 1)
    NB_VENDUS = 250
    for _ in range(NB_VENDUS):
        ville_info = random.choice(VILLES)
        date_creation = debut + timedelta(days=random.randint(0, 365 * 3 + 150))
        if date_creation > datetime.now():
            date_creation = datetime.now() - timedelta(days=random.randint(1, 60))

        bien = creer_bien(ville_info, "appartement", date_creation)
        ag_id = agence_ids[VILLES.index(ville_info)]
        com_id = random.choice([c[0] for c in commerciaux if c[1] == ag_id])

        cur.execute(
            """INSERT INTO bien (titre, description, type, statut, prix, surface, nb_pieces,
                                 nb_chambres, ville, code_postal, adresse, dpe,
                                 agence_id, commercial_id, date_creation)
               VALUES (:titre, :description, :type, 'vendu', :prix, :surface, :nb_pieces,
                       :nb_chambres, :ville, :code_postal, :adresse, :dpe,
                       :agence_id, :commercial_id, :date_creation)""",
            {**bien, "agence_id": ag_id, "commercial_id": com_id},
        )
        bien_id = cur.lastrowid
        for ordre, url in enumerate(media.galerie_pour("appartement", bien_id)):
            cur.execute("INSERT INTO photo (bien_id, url, ordre) VALUES (?, ?, ?)",
                        (bien_id, url, ordre))

        prix_vente = round(bien["prix"] * random.uniform(0.92, 1.0), -2)
        date_vente = min(date_creation + timedelta(days=random.randint(20, 180)), datetime.now())
        cur.execute(
            """INSERT INTO vente (bien_id, client_id, commercial_id, prix_vente, date_vente)
               VALUES (?, ?, ?, ?, ?)""",
            (bien_id, random.choice(clients), com_id, prix_vente,
             date_vente.strftime("%Y-%m-%d %H:%M:%S")),
        )

    # --- Annonces à vendre (affichées sur le site) ---
    # 20 appartements disponibles, chacun avec 3 photos et une photo principale unique.
    for k in range(20):
        ville_info = random.choice(VILLES)
        date_creation = datetime.now() - timedelta(days=random.randint(1, 90))
        bien = creer_bien(ville_info, "appartement", date_creation)
        ag_id = agence_ids[VILLES.index(ville_info)]
        com_id = random.choice([c[0] for c in commerciaux if c[1] == ag_id])

        cur.execute(
            """INSERT INTO bien (titre, description, type, statut, prix, surface, nb_pieces,
                                 nb_chambres, ville, code_postal, adresse, dpe,
                                 agence_id, commercial_id, date_creation)
               VALUES (:titre, :description, :type, 'a_vendre', :prix, :surface, :nb_pieces,
                       :nb_chambres, :ville, :code_postal, :adresse, :dpe,
                       :agence_id, :commercial_id, :date_creation)""",
            {**bien, "agence_id": ag_id, "commercial_id": com_id},
        )
        bien_id = cur.lastrowid
        # 3 photos distinctes : principale unique (k), une photo "extra", un autre intérieur
        photos = [
            f"/static/img/biens/appartement_{k}.jpg",
            f"/static/img/biens/appartement_{20 + (k % 4)}.jpg",
            f"/static/img/biens/appartement_{(k + 1) % 20}.jpg",
        ]
        for ordre, url in enumerate(photos):
            cur.execute("INSERT INTO photo (bien_id, url, ordre) VALUES (?, ?, ?)",
                        (bien_id, url, ordre))

    conn.commit()

    # Petit récap
    for table in ("agence", "utilisateur", "bien", "vente"):
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:12} : {n}")
    conn.close()
    print("Base générée :", CHEMIN_DB)


if __name__ == "__main__":
    main()
