# Documentation — Ymmo (partie DEV)

Projet UF B2 INFRA & DEV — Ynov Informatique
Document couvrant la partie Développement uniquement.

---

# Partie 1 — Documentation fonctionnelle

## 1.1 Le besoin métier

Ymmo est un groupe immobilier (siège à Aix-en-Provence, 12 agences en France)
spécialisé dans l'achat et la vente de biens résidentiels et professionnels.

L'entreprise veut une **plateforme web centralisée** où :

- les **clients** peuvent chercher des biens, les consulter, les mettre en favori
  et demander une visite ;
- les **agences / commerciaux** peuvent publier et gérer leurs biens ;
- l'entreprise peut **exploiter les données du marché** (tendances, prix, zones
  intéressantes) pour aider ses décisions d'achat et de vente.

Notre périmètre est la partie DEV : le site web, l'API et l'analyse de données.

## 1.2 Les utilisateurs (rôles)

| Rôle        | Ce qu'il peut faire                                                       |
|-------------|--------------------------------------------------------------------------|
| Visiteur    | Parcourir et rechercher les biens, estimer un prix, voir l'analyse marché |
| Client      | + favoris, demandes de visite                                            |
| Commercial  | + publier un bien, le marquer comme vendu                                |
| Admin       | Commercial rattaché au siège                                             |

## 1.3 Les fonctionnalités

**Côté public / client**
- Page d'accueil avec recherche rapide et derniers biens.
- Recherche avec filtres (ville, type, prix min/max, surface min).
- Fiche détaillée d'un bien (photos, caractéristiques, DPE, prix au m²).
- Inscription / connexion sécurisées.
- Favoris (ajout / retrait).
- Demande de visite sur un bien.

**Côté commercial**
- Publication d'un bien (rattaché automatiquement à son agence).

**Analyse de données**
- Tableau de bord du marché : indicateurs clés, évolution des ventes par mois,
  ventes par ville, types de biens les plus vendus.
- Repérage des **zones intéressantes pour acheter**.
- **Estimation du prix** d'un bien à partir de ses caractéristiques.

**API REST** (`/api/...`) renvoyant du JSON, pour permettre à un futur client
(application mobile, autre service) de consommer les données.

## 1.4 Parcours utilisateur type

1. Un visiteur arrive sur l'accueil et lance une recherche « appartement à Lyon ».
2. Il consulte une fiche, crée un compte, l'ajoute en favori.
3. Il demande une visite en choisissant une date.
4. Avant d'acheter, il utilise l'outil d'estimation pour vérifier si le prix est cohérent.

---

# Partie 2 — Documentation technique

## 2.1 Architecture générale

L'application suit une **architecture en couches**, ce qui sépare clairement les
responsabilités (principe de responsabilité unique) :

```
Navigateur (HTML/CSS/JS)
        │  requêtes HTTP
        ▼
routes/        ← reçoit les requêtes, appelle les services (aucun SQL ici)
        ▼
services/      ← logique métier + validation (auth, biens, analyse)
        ▼
repositories/  ← seul endroit qui écrit du SQL
        ▼
database/      ← SQLite
```

Les `models/` (entités du domaine) circulent entre les couches.

Cette organisation correspond à une **architecture backend orientée services** :
chaque service (authentification, biens, analyse) est responsable d'un domaine
fonctionnel et peut évoluer indépendamment.

**Interactions client-serveur** : le navigateur dialogue avec le serveur Flask
de deux manières — par les pages HTML (formulaires) et par l'API REST JSON.

## 2.2 Choix techniques (justification)

- **Python / Flask** : la partie analyse de données impose Python (pandas).
  Utiliser Python pour tout le backend évite de jongler entre deux langages et
  reste cohérent. Flask est léger et adapté à la taille du projet (vs Django, plus lourd).
- **SQLite** : base relationnelle sans serveur à installer, suffisante pour une
  démonstration. Le code passe par une couche `repositories`, donc migrer vers
  PostgreSQL/MySQL plus tard ne toucherait que cette couche.
- **Pas de framework front lourd** : HTML/CSS + un peu de JS. Cela garde le site
  rapide à charger (critère de performance) et facile à rendre accessible.

## 2.3 Programmation orientée objet (POO)

Les entités métier sont modélisées par des classes dans `models/bien.py` :
`Agence`, `Utilisateur`, `Bien`.

Exemples de logique encapsulée dans les objets :

- `Bien.prix_m2` : calcule le prix au m² (propriété calculée).
- `Bien.prix_formate()` : met en forme le prix (`250000 €`).
- `Utilisateur.nom_complet` et `Utilisateur.est_commercial`.

Chaque classe sait se construire depuis une ligne de la base via `from_row()`,
ce qui évite de manipuler des dictionnaires bruts dans tout le code.

La classe `EstimateurPrix` (dans `services/analyse_service.py`) encapsule
l'entraînement et l'utilisation du modèle de prédiction.

## 2.4 Bonnes pratiques (SOLID, DRY, KISS)

- **Responsabilité unique (S de SOLID)** : routes ≠ logique métier ≠ accès BDD.
- **DRY** : la requête de sélection des biens (`SELECT_BIEN`) et la carte d'un
  bien (macro Jinja `carte_bien`) sont écrites une seule fois et réutilisées.
- **KISS** : on reste simple (SQLite, pas de couche inutile), on ne code que ce
  dont le projet a besoin.
- **Sécurité** : mots de passe stockés en **hash** (jamais en clair), requêtes
  SQL **paramétrées** (protection contre les injections SQL).
- **Git** : code versionné, une branche par fonctionnalité, commits réguliers,
  pull requests pour la revue (travail d'équipe).

## 2.5 Modèle de données relationnel

Tables principales et relations :

- `agence` (1) ──< `utilisateur` (un commercial appartient à une agence)
- `agence` (1) ──< `bien` ; `utilisateur` (commercial) (1) ──< `bien`
- `bien` (1) ──< `photo`
- `bien` (1) ──< `vente` >── (1) `utilisateur` (client)
- `favori` : table d'association **N-N** entre `utilisateur` et `bien`
- `visite` : demandes de visite (`bien` ↔ `client`)

Le modèle respecte les règles de **normalisation** : pas de données dupliquées
(une ville d'agence n'est pas recopiée dans chaque bien), clés étrangères pour
relier les tables, clés primaires sur chaque table. La table `favori` utilise une
clé primaire composite `(utilisateur_id, bien_id)` pour éviter les doublons.

Des **index** sont posés sur les colonnes les plus filtrées (`ville`, `type`,
`statut`, `prix`, `date_vente`) pour accélérer les recherches.

Schéma complet : `database/schema.sql`.

## 2.6 Requêtes SQL

Tout le SQL est centralisé dans `repositories/`. Quelques exemples représentatifs :

**Recherche avec filtres dynamiques et jointure** (la clause WHERE se construit
selon les filtres choisis, avec des paramètres liés) :

```sql
SELECT b.*, p.url AS photo
FROM bien b
LEFT JOIN photo p ON p.bien_id = b.id AND p.ordre = 0
WHERE b.statut = ? AND b.ville = ? AND b.prix <= ?
ORDER BY b.date_creation DESC;
```

**Liste des favoris d'un utilisateur** (jointure sur la table d'association) :

```sql
SELECT b.*, p.url AS photo
FROM bien b
LEFT JOIN photo p ON p.bien_id = b.id AND p.ordre = 0
JOIN favori f ON f.bien_id = b.id
WHERE f.utilisateur_id = ?
ORDER BY f.date_ajout DESC;
```

**Agrégation pour l'analyse** (ventes par ville, utilisée par pandas) :

```sql
SELECT v.prix_vente, v.date_vente, b.type, b.surface, b.ville
FROM vente v
JOIN bien b ON b.id = v.bien_id;
```

## 2.7 Analyse et manipulation de données (Python)

Module `services/analyse_service.py`. Les données de la base sont chargées dans
des **DataFrames pandas**, nettoyées, puis agrégées pour produire :

- des **rapports de ventes** : par mois (chiffre d'affaires, nombre de ventes),
  par ville, et répartition par type de bien ;
- des **indicateurs de marché** : prix moyen, prix moyen au m², CA total ;
- les **zones intéressantes** : pour chaque ville on calcule un score combinant un
  prix au m² accessible et un volume de transactions élevé (demande réelle), puis
  on garde les meilleures.

**Estimation de prix (prédiction)** : une **régression linéaire** (scikit-learn)
est entraînée sur l'historique des ventes. Les variables catégorielles (ville,
type) sont transformées par un encodage **one-hot**. Le modèle prédit le prix à
partir de la surface, du type, de la ville et du nombre de pièces.
Le coefficient R² obtenu est d'environ **0,84** sur les données d'entraînement.

## 2.8 Interfaces : UX, responsive et accessibilité

**UX / interfaces intuitives**
- Recherche accessible dès l'accueil, filtres regroupés dans une colonne fixe.
- Cartes de biens lisibles (prix mis en avant, infos clés, photo).
- Messages de retour (« flash ») après chaque action (connexion, favori, visite).
- États vides explicites (« Aucun bien ne correspond... »).

**Responsive (mobile first)**
- Mise en page en CSS Grid avec `minmax`/`auto-fill` qui s'adapte à la largeur.
- Points de rupture (`@media`) : la recherche passe en une colonne, le menu se
  resserre sur petit écran.

**Accessibilité (WCAG / ARIA)**
- HTML sémantique (`header`, `nav`, `main`, `article`, `footer`).
- Lien d'évitement « Aller au contenu » pour la navigation au clavier.
- `alt` sur les images, `label` associés à chaque champ de formulaire.
- Focus visible (`:focus-visible`), respect de `prefers-reduced-motion`.
- Contrastes de couleurs suffisants entre le texte et le fond.

**Performance**
- Chargement différé des images (`loading="lazy"`).
- `preconnect` vers les polices, CSS unique et léger, pas de framework JS lourd.

## 2.9 API REST

| Méthode | Route                  | Description                          |
|---------|------------------------|--------------------------------------|
| GET     | `/api/biens`           | Liste des biens en vente (filtrable) |
| GET     | `/api/biens/<id>`      | Détail d'un bien (404 si absent)     |
| GET     | `/api/estimation`      | Estimation de prix (paramètres)      |

Exemple :
`GET /api/estimation?type=maison&ville=Lyon&surface=90&nb_pieces=4`
→ `{ "prix_estime": 381000.0 }`

## 2.10 Pistes d'amélioration

- Pagination des résultats de recherche.
- Upload réel des photos (actuellement une URL d'illustration).
- Espace commercial complet (suivi des visites, édition d'un bien).
- Tests automatisés (pytest) sur les services.
