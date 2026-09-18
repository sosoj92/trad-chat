"""
Évaluation honnête d'un classifieur de miaulements.

Fournit : prédictions sur un lot, rapport (accuracy + F1 par classe),
matrice de confusion (image), et export des exemples mal classés avec leur
chemin audio — pour pouvoir *écouter* ce que le modèle rate.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'affichage interactif, on sauvegarde des images
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from training.dataset_catmeows import Exemple


@torch.no_grad()
def predire_lot(
    modele: torch.nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Renvoie ``(y_vrai, y_predit, probabilites)`` sur tout le loader."""
    modele.eval()
    vrais, predits, probas = [], [], []
    for x, y in loader:
        x = x.to(device)
        logits = modele(x)
        p = torch.softmax(logits, dim=1).cpu().numpy()
        probas.append(p)
        predits.append(p.argmax(axis=1))
        vrais.append(y.numpy())
    return (
        np.concatenate(vrais),
        np.concatenate(predits),
        np.concatenate(probas),
    )


def rapport_texte(y_vrai: np.ndarray, y_predit: np.ndarray, classes: list[str]) -> str:
    """Rapport lisible : accuracy, F1 macro, et détail par classe."""
    acc = accuracy_score(y_vrai, y_predit)
    f1m = f1_score(y_vrai, y_predit, average="macro", zero_division=0)
    detail = classification_report(
        y_vrai, y_predit, labels=list(range(len(classes))),
        target_names=classes, zero_division=0,
    )
    return (
        f"Accuracy globale : {acc:.1%}\n"
        f"F1 macro         : {f1m:.1%}\n\n"
        f"{detail}"
    )


def sauver_matrice_confusion(
    y_vrai: np.ndarray,
    y_predit: np.ndarray,
    classes: list[str],
    chemin: str | Path,
    titre: str = "Matrice de confusion (test)",
) -> Path:
    """Sauvegarde la matrice de confusion (comptes + %) en image PNG."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    cm = confusion_matrix(y_vrai, y_predit, labels=list(range(len(classes))))
    cm_norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)

    fig, ax = plt.subplots(figsize=(1.6 * len(classes) + 2, 1.6 * len(classes) + 2))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    ax.set_xlabel("Prédit")
    ax.set_ylabel("Vrai")
    ax.set_title(titre)
    for i in range(len(classes)):
        for j in range(len(classes)):
            couleur = "white" if cm_norm[i, j] > 0.5 else "black"
            ax.text(j, i, f"{cm[i, j]}\n{cm_norm[i, j]:.0%}",
                    ha="center", va="center", color=couleur, fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(chemin, dpi=120)
    plt.close(fig)
    return chemin


def exporter_mal_classes(
    exemples: list[Exemple],
    y_vrai: np.ndarray,
    y_predit: np.ndarray,
    probas: np.ndarray,
    classes: list[str],
    chemin: str | Path,
) -> tuple[Path, int]:
    """Exporte en CSV les exemples mal classés (avec chemin audio à écouter)."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    lignes = []
    for ex, vrai, predit, p in zip(exemples, y_vrai, y_predit, probas):
        if vrai != predit:
            lignes.append({
                "fichier": str(ex.chemin),
                "chat": ex.chat,
                "vrai": classes[vrai],
                "predit": classes[predit],
                "confiance": f"{p[predit]:.2f}",
            })
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fichier", "chat", "vrai", "predit", "confiance"])
        w.writeheader()
        w.writerows(lignes)
    return chemin, len(lignes)
