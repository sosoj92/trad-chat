"""
Augmentation de données — cruciale vu la petite taille du dataset.

Deux niveaux :
  * sur la **waveform** (avant le spectrogramme) : décalage temporel,
    léger pitch shift, bruit de fond — simule des conditions variées ;
  * sur le **spectrogramme mel** (SpecAugment) : on masque des bandes de
    fréquences et des instants, ce qui force le modèle à ne pas dépendre
    d'un détail unique.

Tout est piloté par la section ``augmentation`` de ``config.yaml`` et
n'utilise que numpy/librosa (pas de torch) : appliqué à la volée à chaque
époque, uniquement sur le lot d'entraînement.
"""

from __future__ import annotations

from typing import Any

import librosa
import numpy as np


def augmenter_waveform(
    y: np.ndarray,
    sr: int,
    cfg: dict[str, Any],
    rng: np.random.Generator,
) -> np.ndarray:
    """Applique les augmentations de forme d'onde (aléatoires, in-place logique)."""
    if not cfg.get("active", True):
        return y

    y = y.copy()
    # Chaque augmentation ne s'applique qu'avec cette probabilité : sur un
    # dataset minuscule, tout augmenter à chaque fois empêche le modèle
    # d'apprendre (sous-apprentissage). On garde des exemples « propres ».
    proba = float(cfg.get("proba", 0.5))

    # Décalage temporel circulaire (le miaulement n'est pas toujours au même endroit).
    if cfg.get("time_shift", True) and rng.random() < proba:
        decalage = int(rng.uniform(-0.2, 0.2) * y.size)
        y = np.roll(y, decalage)

    # Léger pitch shift (un chat ne miaule jamais deux fois pareil).
    if cfg.get("pitch_shift", True) and rng.random() < proba:
        demi_tons = float(rng.uniform(-1, 1) * cfg.get("pitch_shift_demi_tons", 1.5))
        if abs(demi_tons) > 0.05:
            y = librosa.effects.pitch_shift(y, sr=sr, n_steps=demi_tons)

    # Bruit de fond gaussien.
    if cfg.get("bruit_de_fond", True) and rng.random() < proba:
        niveau = float(cfg.get("bruit_niveau", 0.005))
        y = y + rng.normal(0.0, niveau, size=y.shape).astype(np.float32)

    return y.astype(np.float32)


def spec_augment(
    mel: np.ndarray,
    rng: np.random.Generator,
    n_masques_freq: int = 2,
    largeur_freq: int = 8,
    n_masques_temps: int = 2,
    largeur_temps: int = 20,
    valeur: float = 0.0,
) -> np.ndarray:
    """Masque aléatoirement des bandes de fréquences et de temps (SpecAugment).

    ``valeur=0`` correspond à la moyenne d'un spectrogramme z-scoré.
    """
    mel = mel.copy()
    n_mels, n_temps = mel.shape

    for _ in range(n_masques_freq):
        f = int(rng.integers(0, max(1, largeur_freq)))
        f0 = int(rng.integers(0, max(1, n_mels - f)))
        mel[f0 : f0 + f, :] = valeur

    for _ in range(n_masques_temps):
        t = int(rng.integers(0, max(1, largeur_temps)))
        t0 = int(rng.integers(0, max(1, n_temps - t)))
        mel[:, t0 : t0 + t] = valeur

    return mel
