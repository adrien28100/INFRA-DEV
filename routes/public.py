"""Routes accessibles à tout le monde : accueil, recherche et fiche d'un bien."""
from flask import Blueprint, render_template, request, session, flash, redirect, url_for

from services import bien_service
from repositories import bien_repo, user_repo

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def accueil():
    # On affiche les derniers biens disponibles + les villes pour le filtre
    derniers = bien_repo.lister({"statut": "a_vendre"})[:6]
    villes = bien_repo.villes_disponibles()
    return render_template("index.html", biens=derniers, villes=villes)


@public_bp.route("/recherche")
def recherche():
    filtres = {
        "ville": request.args.get("ville", ""),
        "type": request.args.get("type", ""),
        "prix_min": request.args.get("prix_min", ""),
        "prix_max": request.args.get("prix_max", ""),
        "surface_min": request.args.get("surface_min", ""),
    }
    resultats = bien_service.rechercher(filtres)
    villes = bien_repo.villes_disponibles()
    return render_template("recherche.html", biens=resultats,
                           villes=villes, filtres=filtres)


@public_bp.route("/bien/<int:bien_id>")
def detail_bien(bien_id):
    try:
        bien = bien_service.detail(bien_id)
    except bien_service.ErreurBien:
        flash("Ce bien n'existe pas ou a été retiré.", "info")
        return redirect(url_for("public.recherche"))
    photos = bien_repo.photos(bien_id)
    # Pour savoir si l'utilisateur connecté a déjà mis ce bien en favori
    en_favori = False
    if "user" in session:
        en_favori = bien_id in user_repo.ids_favoris(session["user"]["id"])
    return render_template("bien.html", bien=bien, photos=photos, en_favori=en_favori)
