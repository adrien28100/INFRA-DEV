"""Inscription, connexion et déconnexion."""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)

from services import auth_service
from services.auth_service import ErreurAuth

auth_bp = Blueprint("auth", __name__)


def _sauver_session(utilisateur):
    """Stocke les infos utiles de l'utilisateur en session (pas le mot de passe)."""
    session["user"] = {
        "id": utilisateur.id,
        "nom_complet": utilisateur.nom_complet,
        "role": utilisateur.role,
        "agence_id": utilisateur.agence_id,
    }


@auth_bp.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        try:
            auth_service.inscrire(
                request.form.get("nom"), request.form.get("prenom"),
                request.form.get("email"), request.form.get("mot_de_passe"),
            )
            utilisateur = auth_service.connecter(
                request.form.get("email"), request.form.get("mot_de_passe"))
            _sauver_session(utilisateur)
            flash("Bienvenue ! Votre compte a été créé.", "succes")
            return redirect(url_for("public.accueil"))
        except ErreurAuth as e:
            flash(str(e), "erreur")
    return render_template("inscription.html")


@auth_bp.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        try:
            utilisateur = auth_service.connecter(
                request.form.get("email"), request.form.get("mot_de_passe"))
            _sauver_session(utilisateur)
            flash(f"Bonjour {utilisateur.prenom} !", "succes")
            return redirect(url_for("public.accueil"))
        except ErreurAuth as e:
            flash(str(e), "erreur")
    return render_template("connexion.html")


@auth_bp.route("/deconnexion")
def deconnexion():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("public.accueil"))
