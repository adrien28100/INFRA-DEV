"""
Modèles du domaine.

On représente chaque entité métier par une classe. Les classes savent se
construire à partir d'une ligne de la base (from_row) pour éviter de manipuler
des dictionnaires bruts partout dans le code.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Agence:
    id: int
    nom: str
    ville: str
    code_postal: str
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    est_siege: bool = False

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"], nom=row["nom"], ville=row["ville"],
            code_postal=row["code_postal"], adresse=row["adresse"],
            telephone=row["telephone"], email=row["email"],
            est_siege=bool(row["est_siege"]),
        )


@dataclass
class Utilisateur:
    id: int
    nom: str
    prenom: str
    email: str
    role: str
    agence_id: Optional[int] = None

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def est_commercial(self):
        return self.role in ("commercial", "admin")

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"], nom=row["nom"], prenom=row["prenom"],
            email=row["email"], role=row["role"], agence_id=row["agence_id"],
        )


@dataclass
class Bien:
    id: int
    titre: str
    type: str
    statut: str
    prix: float
    surface: float
    ville: str
    code_postal: str
    description: Optional[str] = None
    nb_pieces: Optional[int] = None
    nb_chambres: Optional[int] = None
    adresse: Optional[str] = None
    dpe: Optional[str] = None
    agence_id: Optional[int] = None
    commercial_id: Optional[int] = None
    photo: Optional[str] = None

    @property
    def prix_m2(self):
        """Prix au m², utile pour comparer des biens de tailles différentes."""
        if self.surface:
            return round(self.prix / self.surface)
        return 0

    @property
    def est_disponible(self):
        return self.statut == "a_vendre"

    def prix_formate(self):
        # 250000.0 -> "250 000 €"
        return f"{self.prix:,.0f} €".replace(",", " ")

    @classmethod
    def from_row(cls, row):
        cols = row.keys()
        return cls(
            id=row["id"], titre=row["titre"], type=row["type"], statut=row["statut"],
            prix=row["prix"], surface=row["surface"], ville=row["ville"],
            code_postal=row["code_postal"], description=row["description"],
            nb_pieces=row["nb_pieces"], nb_chambres=row["nb_chambres"],
            adresse=row["adresse"], dpe=row["dpe"], agence_id=row["agence_id"],
            commercial_id=row["commercial_id"],
            photo=row["photo"] if "photo" in cols else None,
        )
