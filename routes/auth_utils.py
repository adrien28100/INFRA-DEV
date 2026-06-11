"""Petits décorateurs pour protéger les routes selon le rôle."""
from functools import wraps
from flask import session, redirect, url_for, flash


def connexion_requise(vue):
    @wraps(vue)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Connectez-vous pour accéder à cette page.", "info")
            return redirect(url_for("auth.connexion"))
        return vue(*args, **kwargs)
    return wrapper


def commercial_requis(vue):
    @wraps(vue)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user or user["role"] not in ("commercial", "admin"):
            flash("Accès réservé aux commerciaux.", "erreur")
            return redirect(url_for("public.accueil"))
        return vue(*args, **kwargs)
    return wrapper


def admin_requis(vue):
    @wraps(vue)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user or user["role"] != "admin":
            flash("Accès réservé à l'administrateur.", "erreur")
            return redirect(url_for("public.accueil"))
        return vue(*args, **kwargs)
    return wrapper
