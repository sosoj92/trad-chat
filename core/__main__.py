"""
Point d'entrée de diagnostic : ``uv run python -m core``.

Affiche un résumé de la configuration (labels détectés, chemins, réglages
audio) — pratique pour vérifier d'un coup que les fondations tiennent.
"""

import sys

from core.config import _resume

# La console Windows est souvent en cp1252 : on force l'UTF-8 pour éviter
# un plantage sur les accents / flèches du résumé.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_resume()
