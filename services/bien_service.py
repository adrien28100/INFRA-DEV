"""
Logique métier autour des biens.

Le service valide les données et applique les règles métier avant d'appeler
le repository. Les routes ne touchent jamais directement à la base.
"""
from repositories import bien_repo

TYPES_VALIDES = {"appartement"}


class ErreurBien(Exception):
    pass


def rechercher(filtres):
    """Recherche de biens à vendre. Nettoie les filtres vides venant du formulaire."""
    propres = {"statut": "a_vendre"}
    for cle in ("ville", "type"):
        if filtres.get(cle):
            propres[cle] = filtres[cle]
    for cle in ("prix_min", "prix_max", "surface_min"):
        valeur = filtres.get(cle)
        if valeur:
            try:
                propres[cle] = float(valeur)
            except ValueError:
                pass  # on ignore une valeur non numérique plutôt que de planter
    return bien_repo.lister(propres)


def detail(bien_id):
    bien = bien_repo.trouver(bien_id)
    if bien is None:
        raise ErreurBien("Ce bien n'existe pas ou a été retiré.")
    return bien


def publier(donnees, agence_id, commercial_id):
    """Crée un nouveau bien après validation."""
    if donnees.get("type") not in TYPES_VALIDES:
        raise ErreurBien("Type de bien invalide.")
    try:
        donnees["prix"] = float(donnees["prix"])
        donnees["surface"] = float(donnees["surface"])
    except (KeyError, ValueError):
        raise ErreurBien("Le prix et la surface doivent être des nombres.")
    if donnees["prix"] <= 0 or donnees["surface"] <= 0:
        raise ErreurBien("Le prix et la surface doivent être positifs.")
    if not donnees.get("titre"):
        raise ErreurBien("Le titre est obligatoire.")

    return bien_repo.creer(donnees, agence_id, commercial_id)


def marquer_vendu(bien_id):
    bien_repo.changer_statut(bien_id, "vendu")
