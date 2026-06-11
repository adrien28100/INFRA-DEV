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

TYPES = ["appartement", "maison", "terrain", "local"]
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

    if type_bien == "terrain":
        surface = random.randint(300, 2000)
        pieces, chambres = None, None
    elif type_bien == "local":
        surface = random.randint(40, 400)
        pieces, chambres = None, None
    else:
        surface = random.randint(25, 180)
        pieces = max(1, round(surface / 22))
        chambres = max(0, pieces - 2)

    prix = round(prix_au_m2(ville, type_bien, annee) * surface, -3)

    titre = {
        "appartement": f"Appartement T{pieces or 2} - {ville}",
        "maison": f"Maison {surface} m² - {ville}",
        "terrain": f"Terrain constructible {surface} m² - {ville}",
        "local": f"Local commercial {surface} m² - {ville}",
    }[type_bien]

    return {
        "titre": titre,
        "description": f"Beau {type_bien} situé à {ville}, proche commerces et transports.",
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

    # --- Biens + ventes sur 3 ans ---
    debut = datetime(2022, 1, 1)
    for _ in range(800):
        ville_info = random.choice(VILLES)
        type_bien = random.choices(TYPES, weights=[50, 35, 8, 7])[0]
        jours = random.randint(0, 365 * 3 + 150)
        date_creation = debut + timedelta(days=jours)
        if date_creation > datetime.now():
            date_creation = datetime.now() - timedelta(days=random.randint(1, 60))

        bien = creer_bien(ville_info, type_bien, date_creation)
        # on rattache le bien à une agence de la même ville si elle existe, sinon au siège
        ag_id = agence_ids[VILLES.index(ville_info)]
        com_id = random.choice([c[0] for c in commerciaux if c[1] == ag_id])

        cur.execute(
            """INSERT INTO bien (titre, description, type, prix, surface, nb_pieces,
                                 nb_chambres, ville, code_postal, adresse, dpe,
                                 agence_id, commercial_id, date_creation)
               VALUES (:titre, :description, :type, :prix, :surface, :nb_pieces,
                       :nb_chambres, :ville, :code_postal, :adresse, :dpe,
                       :agence_id, :commercial_id, :date_creation)""",
            {**bien, "agence_id": ag_id, "commercial_id": com_id},
        )
        bien_id = cur.lastrowid

        cur.execute("INSERT INTO photo (bien_id, url, ordre) VALUES (?, ?, 0)",
                    (bien_id, f"https://picsum.photos/seed/{bien_id}/800/600"))

        # ~55% des biens créés ont été vendus. Le prix de vente est négocié à la baisse.
        if random.random() < 0.55:
            negociation = random.uniform(0.92, 1.0)
            prix_vente = round(bien["prix"] * negociation, -2)
            delai = random.randint(20, 180)
            date_vente = date_creation + timedelta(days=delai)
            if date_vente <= datetime.now():
                cur.execute("UPDATE bien SET statut = 'vendu' WHERE id = ?", (bien_id,))
                cur.execute(
                    """INSERT INTO vente (bien_id, client_id, commercial_id, prix_vente, date_vente)
                       VALUES (?, ?, ?, ?, ?)""",
                    (bien_id, random.choice(clients), com_id, prix_vente,
                     date_vente.strftime("%Y-%m-%d %H:%M:%S")),
                )

    conn.commit()

    # Petit récap
    for table in ("agence", "utilisateur", "bien", "vente"):
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:12} : {n}")
    conn.close()
    print("Base générée :", CHEMIN_DB)


if __name__ == "__main__":
    main()
