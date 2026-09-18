"""
Modèles de classification.

Pour cette baseline (Phase 1), un **petit CNN from scratch** : léger, rapide
à entraîner sur un GPU 6 Go, et suffisant pour valider tout le pipeline. Il
sert de référence honnête. Le transfer learning (PANNs / AST / NatureLM),
plus puissant, viendra ensuite comme amélioration (voir docs/baseline.md).

Le nombre de classes est un paramètre : le modèle s'adapte à ``config.yaml``.
"""

from __future__ import annotations

import torch
from torch import nn


class BlocConv(nn.Module):
    """Conv 3×3 → BatchNorm → ReLU → MaxPool 2×2."""

    def __init__(self, entree: int, sortie: int) -> None:
        super().__init__()
        self.bloc = nn.Sequential(
            nn.Conv2d(entree, sortie, kernel_size=3, padding=1),
            nn.BatchNorm2d(sortie),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.bloc(x)


class PetitCNN(nn.Module):
    """CNN compact pour spectrogrammes mel ``(1, n_mels, T)``.

    Quatre blocs convolutifs, pooling global adaptatif, puis une tête
    linéaire. ~0,5 M paramètres : petit, donc peu enclin à surapprendre sur
    440 exemples, et confortable sur 6 Go de VRAM.
    """

    def __init__(self, n_classes: int, canaux: tuple[int, ...] = (32, 64, 128, 128)) -> None:
        super().__init__()
        blocs = []
        precedent = 1
        for c in canaux:
            blocs.append(BlocConv(precedent, c))
            precedent = c
        self.features = nn.Sequential(*blocs)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.tete = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.3),
            nn.Linear(precedent, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x : (batch, 1, n_mels, T)
        x = self.features(x)
        x = self.pool(x)
        return self.tete(x)


def construire_modele(nom: str, n_classes: int) -> nn.Module:
    """Fabrique un modèle par nom. Point d'extension pour le transfer learning."""
    nom = nom.lower()
    if nom in ("petit_cnn", "cnn", "baseline"):
        return PetitCNN(n_classes)
    raise ValueError(f"Modèle inconnu : {nom!r} (dispo : 'petit_cnn')")


def compter_parametres(modele: nn.Module) -> int:
    """Nombre de paramètres entraînables."""
    return sum(p.numel() for p in modele.parameters() if p.requires_grad)
