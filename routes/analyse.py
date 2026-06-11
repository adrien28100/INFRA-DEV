"""Tableau de bord d'analyse du marché + outil d'estimation de prix."""
from flask import Blueprint, render_template, request

from services import analyse_service
from repositories import bien_repo

analyse_bp = Blueprint("analyse", __name__)


@analyse_bp.route("/analyse")
def tableau_de_bord():
    """Page d'analyse : indicateurs, ventes par ville/type et zones à surveiller."""
    return render_template(
        "analyse.html",
        indicateurs=analyse_service.indicateurs_globaux(),
        par_ville=analyse_service.ventes_par_ville(),
        par_type=analyse_service.repartition_par_type(),
        par_mois=analyse_service.ventes_par_mois(),
        zones=analyse_service.zones_interessantes(),
    )


@analyse_bp.route("/estimer", methods=["GET", "POST"])
def estimer():
    """Estime le prix d'un bien à partir de ses caractéristiques (modèle de prédiction)."""
    estimation = None
    formulaire = {}
    if request.method == "POST":
        formulaire = request.form.to_dict()
        try:
            estimation = analyse_service.estimateur.estimer(
                surface=float(formulaire["surface"]),
                type_bien=formulaire["type"],
                ville=formulaire["ville"],
                nb_pieces=formulaire.get("nb_pieces") or 0,
            )
        except (ValueError, KeyError):
            estimation = None

    villes = bien_repo.villes_disponibles()
    return render_template("estimer.html", villes=villes,
                           estimation=estimation, formulaire=formulaire)
