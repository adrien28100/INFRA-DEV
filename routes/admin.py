"""
Espace administrateur.

Réservé au rôle 'admin'. Permet de voir tous les utilisateurs, de changer leur
rôle (donc de créer des commerciaux / admins à partir de comptes clients) et de
gérer les biens (marquer vendu, supprimer).
"""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session)

from repositories import user_repo, bien_repo
from routes.auth_utils import admin_requis

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_requis
def tableau():
    utilisateurs = user_repo.lister_tous()
    biens = bien_repo.lister()
    return render_template("admin.html", utilisateurs=utilisateurs, biens=biens)


@admin_bp.route("/role/<int:user_id>", methods=["POST"])
@admin_requis
def changer_role(user_id):
    role = request.form.get("role")
    # Un commercial/admin est rattaché au siège (agence 1) par défaut
    agence_id = session["user"]["agence_id"] if role in ("commercial", "admin") else None
    user_repo.changer_role(user_id, role, agence_id)
    flash("Rôle mis à jour.", "succes")
    return redirect(url_for("admin.tableau"))


@admin_bp.route("/bien/<int:bien_id>/vendu", methods=["POST"])
@admin_requis
def marquer_vendu(bien_id):
    bien_repo.changer_statut(bien_id, "vendu")
    flash("Bien marqué comme vendu.", "succes")
    return redirect(url_for("admin.tableau"))


@admin_bp.route("/bien/<int:bien_id>/supprimer", methods=["POST"])
@admin_requis
def supprimer_bien(bien_id):
    bien_repo.supprimer(bien_id)
    flash("Bien supprimé.", "info")
    return redirect(url_for("admin.tableau"))
