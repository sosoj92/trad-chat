"""
Lecture de la configuration centrale (``config.yaml``).

Principe : un seul fichier de config, non versionné, chargé une fois et
partagé partout. Aucun réglage ni secret n'est écrit en dur dans le code —
tout vit dans ``config.yaml`` (modèle : ``config.example.yaml``).

Les labels (catégories d'intentions) sont lus ici : le nombre de classes
est donc *dynamique*. Ajouter/retirer un label dans le YAML suffit, le reste
du pipeline s'y adapte via :func:`labels` et :func:`index_des_labels`.

Usage rapide pour vérifier que tout est en place :
    uv run python -m core
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import yaml

# Racine du projet = dossier parent de « core/ ». Sert à résoudre tous les
# chemins relatifs de la config en chemins absolus, quel que soit le cwd.
RACINE = Path(__file__).resolve().parent.parent

_CONFIG = RACINE / "config.yaml"
_EXEMPLE = RACINE / "config.example.yaml"


class ErreurConfig(RuntimeError):
    """Config manquante ou invalide — message clair pour s'en sortir vite."""


@lru_cache(maxsize=1)
def charger_config(chemin: str | Path | None = None) -> dict[str, Any]:
    """Charge et met en cache la configuration.

    Args:
        chemin: fichier YAML à lire. Par défaut ``config.yaml`` à la racine.

    Returns:
        Le contenu du YAML sous forme de dictionnaire.

    Raises:
        ErreurConfig: si le fichier est absent ou mal formé.
    """
    fichier = Path(chemin) if chemin is not None else _CONFIG

    if not fichier.exists():
        raise ErreurConfig(
            f"Config introuvable : {fichier}\n"
            "→ Lance : uv run --no-sync python -m core.initialiser --nom-chat Moka"
        )

    try:
        with fichier.open("r", encoding="utf-8") as f:
            donnees = yaml.safe_load(f)
    except yaml.YAMLError:
        # Les messages du parseur peuvent reproduire la ligne contenant la clé.
        raise ErreurConfig("YAML invalide : vérifier l'indentation de config.yaml (valeurs masquées).") from None

    if not isinstance(donnees, dict):
        raise ErreurConfig(f"Config vide ou mal formée : {fichier}")

    return donnees


def token_sur(token: object) -> bool:
    """Refuse la clé publique d'exemple ; ne renvoie et ne journalise aucun secret."""
    return (isinstance(token, str) and token == token.strip()
            and len(token) >= 16 and token != "CHANGE-MOI-token-secret")


def valider_collecte(config: dict) -> None:
    """Contrôles utiles pour une première installation et des catégories personnelles."""
    if not isinstance(config, dict):
        raise ErreurConfig("La configuration doit être un dictionnaire YAML.")
    categories = config.get("labels", [])
    if not isinstance(categories, list) or not categories or any(
        not isinstance(l, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", l) for l in categories
    ):
        raise ErreurConfig("Labels : utiliser des identifiants courts en minuscules, sans accent (ex. porte).")
    if len(set(categories)) != len(categories):
        raise ErreurConfig("Labels : une catégorie est répétée.")
    if not {"autre", "incertain"}.issubset(categories):
        raise ErreurConfig("Conserver les catégories autre et incertain.")
    collecte = config.get("collecte", {})
    if not isinstance(collecte, dict) or not token_sur(collecte.get("token")):
        raise ErreurConfig("Clé absente, trop courte ou d'exemple. Voir docs/installation.md ; ne pas publier cette clé.")
    port = collecte.get("port", 8771)
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ErreurConfig("Le port de collecte doit être un entier entre 1024 et 65535.")
    chat = config.get("chat", {})
    nom = chat.get("nom", "Mon chat") if isinstance(chat, dict) else None
    if not isinstance(nom, str) or not 1 <= len(nom.strip()) <= 60:
        raise ErreurConfig("chat.nom doit contenir entre 1 et 60 caractères.")
    chemins = config.get("chemins", {})
    if not isinstance(chemins, dict) or any(not isinstance(chemins.get(c), str) or not chemins[c].strip()
        for c in ("data_mon_chat", "data_catmeows", "models", "logs")):
        raise ErreurConfig("Les quatre chemins de données, modèles et journaux doivent être renseignés.")


def chemin_absolu(cle: str, config: dict[str, Any] | None = None) -> Path:
    """Résout un chemin de la section ``chemins`` en chemin absolu.

    Args:
        cle: nom de l'entrée, ex. ``"data_catmeows"``.
        config: config déjà chargée (sinon chargée automatiquement).

    Returns:
        Le chemin absolu correspondant, ancré sur la racine du projet.
    """
    config = config or charger_config()
    chemins = config.get("chemins", {})
    if cle not in chemins:
        raise ErreurConfig(
            f"Chemin '{cle}' absent de la section 'chemins' de la config."
        )
    return (RACINE / chemins[cle]).resolve()


def labels(config: dict[str, Any] | None = None) -> list[str]:
    """Renvoie la liste des labels (catégories d'intentions).

    C'est la source de vérité pour le nombre de classes du pipeline.
    """
    config = config or charger_config()
    valeurs = config.get("labels")
    if not valeurs or not isinstance(valeurs, list):
        raise ErreurConfig("La section 'labels' doit être une liste non vide.")
    return list(valeurs)


def labels_exclus(config: dict[str, Any] | None = None) -> list[str]:
    """Labels mis en quarantaine, exclus de l'entraînement (ex. ``incertain``).

    Source de vérité : ``entrainement.labels_exclus`` dans la config.
    """
    config = config or charger_config()
    valeurs = config.get("entrainement", {}).get("labels_exclus", [])
    return sorted(set(valeurs if isinstance(valeurs, list) else []) | {"incertain"})


def labels_entrainement(config: dict[str, Any] | None = None) -> list[str]:
    """Labels réellement utilisés à l'entraînement = tous SAUF les exclus.

    À utiliser partout où l'on entraîne (Phase 3), pour garantir que la
    quarantaine (``incertain``) ne pollue jamais le modèle.
    """
    config = config or charger_config()
    exclus = set(labels_exclus(config))
    return [nom for nom in labels(config) if nom not in exclus]


def index_des_labels(
    config: dict[str, Any] | None = None,
) -> tuple[dict[str, int], dict[int, str]]:
    """Renvoie les tables de correspondance label ⇄ indice.

    Returns:
        ``(label_vers_indice, indice_vers_label)`` — pratique pour encoder
        les cibles d'entraînement et décoder les prédictions du modèle.
    """
    noms = labels(config)
    label_vers_indice = {nom: i for i, nom in enumerate(noms)}
    indice_vers_label = {i: nom for i, nom in enumerate(noms)}
    return label_vers_indice, indice_vers_label


def _resume() -> None:
    """Affiche un résumé de la config — sert de test rapide à la Phase 0."""
    config = charger_config()
    noms = labels(config)
    print(f"Projet    : {config.get('projet', {}).get('nom', '?')} "
          f"v{config.get('projet', {}).get('version', '?')}")
    print(f"Racine    : {RACINE}")
    print(f"Labels    : {len(noms)} classes → {', '.join(noms)}")
    print("Chemins   :")
    for cle in config.get("chemins", {}):
        print(f"  - {cle:15} → {chemin_absolu(cle, config)}")
    sr = config.get("audio", {}).get("sample_rate", "?")
    print(f"Audio     : {sr} Hz mono, {config.get('audio', {}).get('n_mels', '?')} mels")
    print("\nConfig chargee sans erreur. [OK]")


if __name__ == "__main__":
    # La console Windows est souvent en cp1252 : on force l'UTF-8 pour que
    # les accents et flèches s'affichent sans planter.
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    _resume()
