"""
API REST renvoyant du JSON.

Elle expose les biens et l'estimation de prix. C'est ce qui permet une vraie
interaction client-serveur : un client (page web en JavaScript, application
mobile...) peut consommer ces routes sans passer par les pages HTML.
"""
from flask import Blueprint, jsonify, request
from dataclasses import asdict

from services import bien_service, analyse_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/biens")
def liste_biens():
    """GET /api/biens?ville=Lyon&type=appartement — renvoie les biens en vente."""
    filtres = {
        "ville": request.args.get("ville", ""),
        "type": request.args.get("type", ""),
        "prix_max": request.args.get("prix_max", ""),
    }
    biens = bien_service.rechercher(filtres)
    return jsonify([asdict(b) for b in biens])


@api_bp.route("/biens/<int:bien_id>")
def detail_bien(bien_id):
    try:
        bien = bien_service.detail(bien_id)
    except bien_service.ErreurBien:
        return jsonify({"erreur": "Bien introuvable"}), 404
    return jsonify(asdict(bien))


@api_bp.route("/estimation")
def estimation():
    """GET /api/estimation?type=maison&ville=Lyon&surface=90&nb_pieces=4"""
    try:
        prix = analyse_service.estimateur.estimer(
            surface=float(request.args["surface"]),
            type_bien=request.args["type"],
            ville=request.args["ville"],
            nb_pieces=request.args.get("nb_pieces", 0),
        )
    except (KeyError, ValueError):
        return jsonify({"erreur": "Paramètres invalides"}), 400
    return jsonify({"prix_estime": prix})
