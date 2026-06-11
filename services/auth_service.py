"""
Logique d'authentification : inscription et connexion.

On ne stocke jamais le mot de passe en clair, seulement son hash
(generate_password_hash / check_password_hash de Werkzeug).
"""
from werkzeug.security import generate_password_hash, check_password_hash

from repositories import user_repo
from models.bien import Utilisateur


class ErreurAuth(Exception):
    """Levée quand l'inscription ou la connexion échoue."""


def inscrire(nom, prenom, email, mot_de_passe):
    if not all([nom, prenom, email, mot_de_passe]):
        raise ErreurAuth("Tous les champs sont obligatoires.")
    if len(mot_de_passe) < 6:
        raise ErreurAuth("Le mot de passe doit faire au moins 6 caractères.")
    if user_repo.trouver_par_email(email):
        raise ErreurAuth("Un compte existe déjà avec cet email.")

    user_id = user_repo.creer(nom, prenom, email, generate_password_hash(mot_de_passe))
    return user_id


def connecter(email, mot_de_passe):
    row = user_repo.trouver_par_email(email)
    if row is None or not check_password_hash(row["mot_de_passe"], mot_de_passe):
        # même message dans les deux cas pour ne pas révéler si l'email existe
        raise ErreurAuth("Email ou mot de passe incorrect.")
    return Utilisateur.from_row(row)
