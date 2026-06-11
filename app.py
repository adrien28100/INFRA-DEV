"""
Point d'entrée de l'application Ymmo.

On crée l'application Flask, on enregistre les blueprints (chaque blueprint
regroupe les routes d'une partie du site) et on expose quelques fonctions
utiles aux templates.

Lancer : python app.py  puis ouvrir http://localhost:5000
"""
from flask import Flask, session

from routes.public import public_bp
from routes.auth import auth_bp
from routes.espace import espace_bp
from routes.analyse import analyse_bp
from routes.api import api_bp


def creer_app():
    app = Flask(__name__)
    app.secret_key = "ymmo-cle-secrete-a-changer-en-production"

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(espace_bp)
    app.register_blueprint(analyse_bp)
    app.register_blueprint(api_bp)

    # Rend l'utilisateur connecté disponible dans tous les templates
    @app.context_processor
    def injecter_utilisateur():
        return {
            "utilisateur_connecte": session.get("user"),
        }

    return app


app = creer_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
