"""
Génération du visuel et du texte des annonces.

Les photos sont stockées en local dans static/img/biens/ (récupérées depuis un
jeu d'images libres + visuels générés pour les terrains). Chaque type de bien a
son propre lot d'images ; on choisit l'image selon l'identifiant du bien, ce qui
donne des photos variées d'une annonce à l'autre et cohérentes avec le type.

Tout étant local, le site fonctionne sans connexion internet (pratique pour une
démonstration à l'oral).
"""
import random

# Nombre d'images disponibles (fichiers static/img/biens/appartement_<n>.jpg)
NB_IMAGES = {
    "appartement": 8,
}

ATOUTS = [
    "proche des commerces et des transports",
    "dans un quartier calme et recherché",
    "à deux pas du centre-ville",
    "avec une belle luminosité toute la journée",
    "récemment rénové",
    "idéal pour un premier achat",
    "parfait pour un investissement locatif",
    "au cœur d'un secteur en plein développement",
]


def image_pour(type_bien, bien_id):
    """Renvoie le chemin d'une image locale cohérente avec le type de bien."""
    n = NB_IMAGES.get(type_bien, 0)
    if n == 0:
        return "/static/img/biens/appartement_0.jpg"
    return f"/static/img/biens/{type_bien}_{bien_id % n}.jpg"


def galerie_pour(type_bien, bien_id, nombre=3):
    """Renvoie plusieurs images différentes du même type pour la galerie."""
    n = NB_IMAGES.get(type_bien, 1)
    nombre = min(nombre, n)
    return [f"/static/img/biens/{type_bien}_{(bien_id + i) % n}.jpg" for i in range(nombre)]


def description_pour(type_bien, ville, surface, pieces=None):
    """Construit une description plus naturelle qu'un simple texte générique."""
    if type_bien == "appartement":
        intro = f"Bel appartement de {surface} m²"
        if pieces:
            intro += f" comprenant {pieces} pièces"
        intro += f", situé à {ville}"
    elif type_bien == "maison":
        intro = f"Charmante maison de {surface} m² à {ville}"
    elif type_bien == "terrain":
        intro = f"Terrain constructible de {surface} m² à {ville}"
    else:
        intro = f"Local de {surface} m² à {ville}, adapté à une activité commerciale"

    atouts = ", ".join(random.sample(ATOUTS, 2))
    return f"{intro}, {atouts}. Disponible immédiatement. Contactez l'agence pour organiser une visite."
