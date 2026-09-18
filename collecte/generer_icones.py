"""
Génère les icônes de la PWA (tête de chat stylisée) dans static/.

Un seul dessin vectoriel rendu en PNG à plusieurs tailles. Utilise matplotlib
(déjà présent via le groupe training). À relancer si on change le visuel :
    uv run python -m collecte.generer_icones
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

STATIC = Path(__file__).parent / "static"
ACCENT = "#ff7a59"
FOND = "#12141c"


def _dessiner(taille_px: int, chemin: Path) -> None:
    dpi = 100
    fig = plt.figure(figsize=(taille_px / dpi, taille_px / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.patch.set_facecolor(FOND)

    # Oreilles
    ax.add_patch(Polygon([(0.28, 0.72), (0.40, 0.92), (0.46, 0.66)], color=ACCENT))
    ax.add_patch(Polygon([(0.72, 0.72), (0.60, 0.92), (0.54, 0.66)], color=ACCENT))
    # Tête
    ax.add_patch(Circle((0.5, 0.48), 0.30, color=ACCENT))
    # Yeux
    ax.add_patch(Circle((0.40, 0.52), 0.045, color=FOND))
    ax.add_patch(Circle((0.60, 0.52), 0.045, color=FOND))
    # Museau
    ax.add_patch(Polygon([(0.47, 0.40), (0.53, 0.40), (0.5, 0.35)], color=FOND))
    # Moustaches
    for dy in (0.0, 0.04, -0.04):
        ax.plot([0.20, 0.44], [0.40 + dy, 0.40], color=FOND, lw=max(1, taille_px / 200))
        ax.plot([0.80, 0.56], [0.40 + dy, 0.40], color=FOND, lw=max(1, taille_px / 200))

    fig.savefig(chemin, dpi=dpi, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    STATIC.mkdir(parents=True, exist_ok=True)
    for taille, nom in [(512, "icon-512.png"), (192, "icon-192.png"), (180, "icon-180.png")]:
        _dessiner(taille, STATIC / nom)
        print("écrit :", nom)


if __name__ == "__main__":
    main()
