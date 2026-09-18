"""
Utilitaires partagés du projet « traducteur de chat ».

Regroupe ce dont tous les modules ont besoin (collecte, training, inference) :
lecture de la config centrale et journalisation. Tout le reste s'appuie
là-dessus pour rester cohérent — et pour qu'aucun secret ne traîne en dur.
"""

from core.config import (
    RACINE,
    charger_config,
    chemin_absolu,
    index_des_labels,
    labels,
    labels_entrainement,
    labels_exclus,
)
from core.journalisation import configurer_journalisation, obtenir_logger

__all__ = [
    "RACINE",
    "charger_config",
    "chemin_absolu",
    "index_des_labels",
    "labels",
    "labels_entrainement",
    "labels_exclus",
    "configurer_journalisation",
    "obtenir_logger",
]
