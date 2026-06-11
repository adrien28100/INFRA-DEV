"""
Analyse de données du marché immobilier Ymmo.

Ce module lit les ventes et les biens depuis la base, les charge dans des
DataFrames pandas et produit :
  - des rapports de ventes (par mois, par ville, par type)
  - des statistiques de marché (prix moyen au m², types populaires)
  - un repérage des zones intéressantes pour acheter
  - une estimation du prix d'un bien par régression linéaire

Les résultats sont renvoyés sous forme de structures Python simples
(listes/dictionnaires) pour être facilement affichés dans les pages web.
"""
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from database.db import get_connexion


def _charger_ventes():
    """Charge l'historique des ventes avec les infos du bien associé."""
    with get_connexion() as conn:
        df = pd.read_sql_query(
            """SELECT v.prix_vente, v.date_vente,
                      b.type, b.surface, b.ville, b.nb_pieces, b.prix AS prix_affiche
               FROM vente v
               JOIN bien b ON b.id = v.bien_id""",
            conn,
        )
    df["date_vente"] = pd.to_datetime(df["date_vente"])
    df["prix_m2"] = df["prix_vente"] / df["surface"]
    return df


def _charger_biens():
    with get_connexion() as conn:
        return pd.read_sql_query("SELECT type, surface, ville, prix, statut FROM bien", conn)


# --- Rapports de ventes ---

def ventes_par_mois():
    """Chiffre d'affaires et nombre de ventes par mois (pour un graphique)."""
    df = _charger_ventes()
    df["mois"] = df["date_vente"].dt.to_period("M").astype(str)
    grp = df.groupby("mois").agg(
        nb_ventes=("prix_vente", "count"),
        chiffre_affaires=("prix_vente", "sum"),
    ).reset_index().sort_values("mois")
    return grp.to_dict("records")


def ventes_par_ville():
    df = _charger_ventes()
    grp = df.groupby("ville").agg(
        nb_ventes=("prix_vente", "count"),
        prix_moyen=("prix_vente", "mean"),
        prix_m2_moyen=("prix_m2", "mean"),
    ).reset_index().sort_values("nb_ventes", ascending=False)
    grp = grp.round(0)
    return grp.to_dict("records")


def repartition_par_pieces():
    """Répartition des ventes par nombre de pièces (T1, T2... T5+)."""
    df = _charger_ventes()
    df = df.dropna(subset=["nb_pieces"])
    df["categorie"] = df["nb_pieces"].apply(
        lambda n: f"T{int(n)}" if n < 5 else "T5+"
    )
    counts = df["categorie"].value_counts()
    total = counts.sum()
    ordre = ["T1", "T2", "T3", "T4", "T5+"]
    return [
        {"categorie": cat, "nb": int(counts[cat]), "part": round(float(counts[cat]) / float(total) * 100, 1)}
        for cat in ordre if cat in counts
    ]


# --- Indicateurs de marché ---

def indicateurs_globaux():
    df = _charger_ventes()
    biens = _charger_biens()
    return {
        "nb_ventes": int(len(df)),
        "chiffre_affaires": float(df["prix_vente"].sum()),
        "prix_moyen": float(df["prix_vente"].mean()),
        "prix_m2_moyen": float(df["prix_m2"].mean()),
        "biens_disponibles": int((biens["statut"] == "a_vendre").sum()),
    }


def zones_interessantes():
    """
    Repère les villes où il peut être intéressant d'acheter.

    Idée simple : une ville est intéressante si son prix au m² est sous la moyenne
    nationale (donc un investissement plus accessible) tout en ayant un bon volume
    de transactions (donc une demande réelle, le bien se revendra). On combine les
    deux en un score, puis on garde les meilleures villes.
    """
    df = _charger_ventes()
    stats = df.groupby("ville").agg(
        prix_m2_moyen=("prix_m2", "mean"),
        nb_ventes=("prix_vente", "count"),
    ).reset_index()

    prix_moyen_national = df["prix_m2"].mean()

    # On normalise entre 0 et 1 pour pouvoir additionner deux grandeurs d'échelles différentes
    stats["score_prix"] = 1 - (stats["prix_m2_moyen"] / stats["prix_m2_moyen"].max())
    stats["score_demande"] = stats["nb_ventes"] / stats["nb_ventes"].max()
    stats["score"] = (stats["score_prix"] + stats["score_demande"]) / 2

    stats = stats.sort_values("score", ascending=False)
    resultat = []
    for _, r in stats.head(5).iterrows():
        resultat.append({
            "ville": r["ville"],
            "prix_m2_moyen": round(r["prix_m2_moyen"]),
            "nb_ventes": int(r["nb_ventes"]),
            "score": round(r["score"], 2),
            "sous_moyenne": bool(r["prix_m2_moyen"] < prix_moyen_national),
        })
    return resultat


# --- Prédiction de prix ---

class EstimateurPrix:
    """
    Estime le prix d'un bien à partir de la surface, du type, de la ville et du
    nombre de pièces, en se basant sur l'historique des ventes.

    On utilise une régression linéaire avec encodage one-hot des variables
    catégorielles (ville, type). Le modèle est entraîné une fois puis réutilisé.
    """

    def __init__(self):
        self.modele = None
        self.score = None

    def entrainer(self):
        df = _charger_ventes().dropna(subset=["surface", "prix_vente"])
        df["nb_pieces"] = df["nb_pieces"].fillna(0)

        X = df[["surface", "nb_pieces", "type", "ville"]]
        y = df["prix_vente"]

        # OneHotEncoder transforme "type" et "ville" en colonnes numériques 0/1
        pretraitement = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["type", "ville"]),
        ], remainder="passthrough")

        self.modele = Pipeline([
            ("prep", pretraitement),
            ("reg", LinearRegression()),
        ])
        self.modele.fit(X, y)
        self.score = round(self.modele.score(X, y), 3)  # R² sur les données d'entraînement
        return self

    def estimer(self, surface, type_bien, ville, nb_pieces=0):
        if self.modele is None:
            self.entrainer()
        X = pd.DataFrame([{
            "surface": float(surface),
            "nb_pieces": float(nb_pieces or 0),
            "type": type_bien,
            "ville": ville,
        }])
        prix = float(self.modele.predict(X)[0])
        return max(0, round(prix, -3))  # arrondi au millier, jamais négatif


# Instance partagée pour ne pas réentraîner le modèle à chaque requête
estimateur = EstimateurPrix()


if __name__ == "__main__":
    # Petit test rapide en ligne de commande
    print("Indicateurs :", indicateurs_globaux())
    print("Zones intéressantes :", zones_interessantes())
    estimateur.entrainer()
    print("R² du modèle :", estimateur.score)
    print("Estimation appart 65m² 3 pièces à Lyon :",
          estimateur.estimer(65, "appartement", "Lyon", 3), "€")
