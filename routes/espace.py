"""Espace connecté : favoris et demandes de visite (clients), publication (commerciaux)."""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)

from repositories import user_repo
from services import bien_service
from services.bien_service import ErreurBien
from routes.auth_utils import connexion_requise, commercial_requis

espace_bp = Blueprint("espace", __name__)


@espace_bp.route("/favoris")
@connexion_requise
def favoris():
    biens = user_repo.lister_favoris(session["user"]["id"])
    return render_template("favoris.html", biens=biens)


@espace_bp.route("/favoris/ajouter/<int:bien_id>", methods=["POST"])
@connexion_requise
def ajouter_favori(bien_id):
    user_repo.ajouter_favori(session["user"]["id"], bien_id)
    return redirect(request.referrer or url_for("public.detail_bien", bien_id=bien_id))


@espace_bp.route("/favoris/retirer/<int:bien_id>", methods=["POST"])
@connexion_requise
def retirer_favori(bien_id):
    user_repo.retirer_favori(session["user"]["id"], bien_id)
    return redirect(request.referrer or url_for("espace.favoris"))


@espace_bp.route("/bien/<int:bien_id>/visite", methods=["POST"])
@connexion_requise
def demander_visite(bien_id):
    user_repo.demander_visite(
        bien_id, session["user"]["id"],
        request.form.get("date_visite"), request.form.get("message"),
    )
    flash("Votre demande de visite a été envoyée à l'agence.", "succes")
    return redirect(url_for("public.detail_bien", bien_id=bien_id))


@espace_bp.route("/publier", methods=["GET", "POST"])
@commercial_requis
def publier():
    if request.method == "POST":
        try:
            bien_id = bien_service.publier(
                request.form.to_dict(),
                session["user"]["agence_id"],
                session["user"]["id"],
            )
            flash("Le bien a été publié.", "succes")
            return redirect(url_for("public.detail_bien", bien_id=bien_id))
        except ErreurBien as e:
            flash(str(e), "erreur")
    return render_template("publier.html")
