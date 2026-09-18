"""
Journalisation propre et partagée.

Un seul point d'entrée : :func:`configurer_journalisation` (à appeler une
fois au démarrage d'un programme), puis :func:`obtenir_logger` partout
ailleurs. Sortie simultanée console + fichier tournant dans ``logs/``.

Le niveau et le nom du fichier viennent de ``config.yaml`` (section
``journalisation``), donc rien de figé dans le code.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from core.config import RACINE, charger_config

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE = "%H:%M:%S"

# Pour éviter d'empiler les handlers si on appelle la fonction deux fois.
_deja_configure = False


def configurer_journalisation(
    config: dict[str, Any] | None = None,
    niveau: str | None = None,
) -> logging.Logger:
    """Configure la journalisation racine (console + fichier tournant).

    À appeler une fois, au lancement d'un script. Idempotent : un second
    appel ne duplique pas les handlers.

    Args:
        config: config déjà chargée (sinon lue automatiquement).
        niveau: force un niveau (``"DEBUG"``…), sinon celui de la config.

    Returns:
        Le logger racine configuré.
    """
    global _deja_configure

    config = config or charger_config()
    reglages = config.get("journalisation", {})
    niveau_txt = (niveau or reglages.get("niveau", "INFO")).upper()
    niveau_num = getattr(logging, niveau_txt, logging.INFO)

    racine = logging.getLogger()
    racine.setLevel(niveau_num)

    if _deja_configure:
        racine.setLevel(niveau_num)
        return racine

    formateur = logging.Formatter(_FORMAT, datefmt=_DATE)

    # --- Console ---
    console = logging.StreamHandler()
    console.setFormatter(formateur)
    racine.addHandler(console)

    # --- Fichier tournant (5 Mo × 3) ---
    dossier_logs = (RACINE / config.get("chemins", {}).get("logs", "logs")).resolve()
    dossier_logs.mkdir(parents=True, exist_ok=True)
    fichier = dossier_logs / reglages.get("fichier", "chat-traducteur.log")

    fichier_handler = RotatingFileHandler(
        fichier, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    fichier_handler.setFormatter(formateur)
    racine.addHandler(fichier_handler)

    _deja_configure = True
    racine.debug("Journalisation configurée (niveau=%s, fichier=%s)", niveau_txt, fichier)
    return racine


def obtenir_logger(nom: str) -> logging.Logger:
    """Renvoie un logger nommé (généralement ``__name__`` de l'appelant)."""
    return logging.getLogger(nom)
