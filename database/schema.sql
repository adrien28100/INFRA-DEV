-- Base de données Ymmo
-- Modèle relationnel pour la gestion de l'achat / vente de biens immobiliers

PRAGMA foreign_keys = ON;

-- Les 12 agences + le siège
CREATE TABLE agence (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nom         TEXT NOT NULL,
    ville       TEXT NOT NULL,
    code_postal TEXT NOT NULL,
    adresse     TEXT,
    telephone   TEXT,
    email       TEXT,
    est_siege   INTEGER NOT NULL DEFAULT 0
);

-- Clients, commerciaux et administrateurs
-- role : client | commercial | admin
CREATE TABLE utilisateur (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nom             TEXT NOT NULL,
    prenom          TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    mot_de_passe    TEXT NOT NULL,           -- hash
    telephone       TEXT,
    role            TEXT NOT NULL DEFAULT 'client',
    agence_id       INTEGER,                 -- NULL pour les clients
    date_inscription TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (agence_id) REFERENCES agence(id)
);

-- Biens immobiliers
-- type   : maison | appartement | terrain | local
-- statut : a_vendre | sous_compromis | vendu
CREATE TABLE bien (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    titre         TEXT NOT NULL,
    description   TEXT,
    type          TEXT NOT NULL,
    statut        TEXT NOT NULL DEFAULT 'a_vendre',
    prix          REAL NOT NULL,
    surface       REAL NOT NULL,             -- m²
    nb_pieces     INTEGER,
    nb_chambres   INTEGER,
    ville         TEXT NOT NULL,
    code_postal   TEXT NOT NULL,
    adresse       TEXT,
    dpe           TEXT,                       -- classe énergie A à G
    agence_id     INTEGER NOT NULL,
    commercial_id INTEGER,
    date_creation TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (agence_id) REFERENCES agence(id),
    FOREIGN KEY (commercial_id) REFERENCES utilisateur(id)
);

CREATE TABLE photo (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    bien_id INTEGER NOT NULL,
    url     TEXT NOT NULL,
    ordre   INTEGER DEFAULT 0,
    FOREIGN KEY (bien_id) REFERENCES bien(id) ON DELETE CASCADE
);

-- Une vente conclue. On garde le prix de vente réel (qui peut différer du prix affiché)
-- pour pouvoir analyser la marge de négociation ensuite.
CREATE TABLE vente (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    bien_id       INTEGER NOT NULL,
    client_id     INTEGER NOT NULL,
    commercial_id INTEGER,
    prix_vente    REAL NOT NULL,
    date_vente    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (bien_id) REFERENCES bien(id),
    FOREIGN KEY (client_id) REFERENCES utilisateur(id),
    FOREIGN KEY (commercial_id) REFERENCES utilisateur(id)
);

-- Biens mis en favori par un client (relation N-N)
CREATE TABLE favori (
    utilisateur_id INTEGER NOT NULL,
    bien_id        INTEGER NOT NULL,
    date_ajout     TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (utilisateur_id, bien_id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE,
    FOREIGN KEY (bien_id) REFERENCES bien(id) ON DELETE CASCADE
);

-- Demandes de visite
-- statut : en_attente | confirmee | annulee
CREATE TABLE visite (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bien_id     INTEGER NOT NULL,
    client_id   INTEGER NOT NULL,
    date_visite TEXT NOT NULL,
    statut      TEXT NOT NULL DEFAULT 'en_attente',
    message     TEXT,
    FOREIGN KEY (bien_id) REFERENCES bien(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES utilisateur(id) ON DELETE CASCADE
);

-- Index sur les colonnes les plus utilisées pour les recherches et filtres
CREATE INDEX idx_bien_ville  ON bien(ville);
CREATE INDEX idx_bien_type   ON bien(type);
CREATE INDEX idx_bien_statut ON bien(statut);
CREATE INDEX idx_bien_prix   ON bien(prix);
CREATE INDEX idx_vente_date  ON vente(date_vente);
