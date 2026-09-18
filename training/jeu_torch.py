"""
Adaptateur PyTorch : transforme une liste d'``Exemple`` en Dataset.

Les formes d'onde (durée fixe) sont préchargées en RAM une fois — le dataset
est minuscule — puis, à chaque accès :
  * (entraînement) augmentation waveform + SpecAugment, appliquées à la volée
    pour varier les exemples à chaque époque ;
  * calcul du spectrogramme mel → tenseur ``(1, n_mels, T)``.

Séparé de ``dataset_catmeows`` pour que ce dernier reste sans dépendance torch.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from torch.utils.data import Dataset

from core.audio import charger_audio, melspectrogramme, preparer_waveform
from training.augmentation import augmenter_waveform, spec_augment
from training.dataset_catmeows import Exemple


class JeuMiaulements(Dataset):
    """Dataset de miaulements → (spectrogramme mel, indice de classe)."""

    def __init__(
        self,
        exemples: list[Exemple],
        config: dict[str, Any],
        entrainement: bool = False,
        seed: int = 42,
    ) -> None:
        self.exemples = exemples
        self.config = config
        self.entrainement = entrainement
        self.sr = int(config.get("audio", {}).get("sample_rate", 16000))
        self.aug_cfg = config.get("augmentation", {})
        self.rng = np.random.default_rng(seed)

        # Préchargement des formes d'onde (durée fixe) — une seule fois.
        self.waveforms = [
            preparer_waveform(charger_audio(ex.chemin, self.sr), config)
            for ex in exemples
        ]

    def __len__(self) -> int:
        return len(self.exemples)

    def __getitem__(self, i: int) -> tuple[torch.Tensor, int]:
        y = self.waveforms[i]

        if self.entrainement and self.aug_cfg.get("active", True):
            y = augmenter_waveform(y, self.sr, self.aug_cfg, self.rng)

        mel = melspectrogramme(y, self.config)

        if self.entrainement and self.aug_cfg.get("active", True) \
                and self.aug_cfg.get("spec_augment", True) \
                and self.rng.random() < float(self.aug_cfg.get("proba", 0.5)):
            mel = spec_augment(mel, self.rng)

        x = torch.from_numpy(mel).unsqueeze(0)  # (1, n_mels, T)
        return x, self.exemples[i].indice
