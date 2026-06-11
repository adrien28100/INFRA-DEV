# Ymmo — Plateforme web immobilière (partie DEV)

Projet UF B2 INFRA & DEV — Ynov Informatique.
Partie **Développement** : site web pour l'achat et la vente de biens immobiliers,
avec une API REST et un module d'analyse de données.

> La partie INFRA (réseau, serveurs, sécurité) est traitée séparément par le reste de l'équipe.

## Stack technique

- **Python 3.12** / **Flask** (backend + rendu des pages)
- **SQLite** (base de données relationnelle)
- **pandas** + **scikit-learn** (analyse de données et estimation de prix)
- **HTML / CSS** (front responsive, sans framework lourd pour rester léger)
- **Chart.js** (graphique côté client, chargé via CDN)

## Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Générer la base de données + les données de test
python -m database.seed

# 3. Lancer l'application
python app.py
```

Le site est ensuite accessible sur **http://localhost:5000**.

## Comptes de test

| Rôle       | Email            | Mot de passe |
|------------|------------------|--------------|
| Client     | demo@ymmo.fr     | demo123      |
| Admin      | admin@ymmo.fr    | admin123     |

(Les commerciaux générés ont le mot de passe `test123`.)

## Structure du projet

```
ymmo/
├── app.py                # Point d'entrée Flask
├── database/             # Schéma SQL, connexion, génération des données
│   ├── schema.sql
│   ├── db.py
│   └── seed.py
├── models/               # Entités du domaine (POO)
├── repositories/         # Accès aux données (SQL)
├── services/             # Logique métier + analyse de données
├── routes/               # Routes web (blueprints Flask)
├── templates/            # Pages HTML (Jinja2)
├── static/css/           # Styles
└── docs/                 # Documentation fonctionnelle et technique
```

Voir `docs/DOCUMENTATION.md` pour le détail fonctionnel et technique.
