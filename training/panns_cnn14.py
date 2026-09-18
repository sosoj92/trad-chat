"""
CNN14 (PANNs) — backbone audio pré-entraîné sur AudioSet, vendorisé.

Architecture reprise de PANNs (Kong et al., « PANNs: Large-Scale Pretrained
Audio Neural Networks for Audio Pattern Recognition », 2020 — MIT license,
https://github.com/qiuqiangkong/audioset_tagging_cnn). On la recopie ici pour
NE PAS dépendre du package `panns_inference` (qui, à l'import, tente un `wget`
et télécharge un CSV externe — fragile sous Windows). Seul `torchlibrosa` est
utilisé, pour le frontend spectrogramme → log-mel, exactement comme à
l'entraînement d'origine (sinon les poids ne correspondraient pas).

On s'en sert en **extracteur de features** : chaque miaulement → embedding
2048-D. Poids : models/panns/Cnn14_mAP=0.431.pth (téléchargés depuis Zenodo).
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn
from torchlibrosa.augmentation import SpecAugmentation
from torchlibrosa.stft import LogmelFilterBank, Spectrogram

# Hyperparamètres du frontend, identiques au checkpoint AudioSet.
SR_PANNS = 32000
WINDOW = 1024
HOP = 320
MELS = 64
FMIN = 50
FMAX = 14000
CLASSES_AUDIOSET = 527
DIM_EMBEDDING = 2048


class _BlocConv(nn.Module):
    """Deux convolutions 3×3 + BatchNorm + pooling (bloc PANNs)."""

    def __init__(self, entree: int, sortie: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(entree, sortie, 3, 1, 1, bias=False)
        self.conv2 = nn.Conv2d(sortie, sortie, 3, 1, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(sortie)
        self.bn2 = nn.BatchNorm2d(sortie)

    def forward(self, x: torch.Tensor, pool_size=(2, 2)) -> torch.Tensor:
        x = F.relu_(self.bn1(self.conv1(x)))
        x = F.relu_(self.bn2(self.conv2(x)))
        return F.avg_pool2d(x, kernel_size=pool_size)


class Cnn14(nn.Module):
    """CNN14 PANNs. ``forward`` renvoie l'embedding 2048-D (avant tête AudioSet)."""

    def __init__(self, classes_num: int = CLASSES_AUDIOSET) -> None:
        super().__init__()
        self.spectrogram_extractor = Spectrogram(
            n_fft=WINDOW, hop_length=HOP, win_length=WINDOW,
            window="hann", center=True, pad_mode="reflect", freeze_parameters=True)
        self.logmel_extractor = LogmelFilterBank(
            sr=SR_PANNS, n_fft=WINDOW, n_mels=MELS, fmin=FMIN, fmax=FMAX,
            ref=1.0, amin=1e-10, top_db=None, freeze_parameters=True)
        self.spec_augmenter = SpecAugmentation(
            time_drop_width=64, time_stripes_num=2, freq_drop_width=8, freq_stripes_num=2)

        self.bn0 = nn.BatchNorm2d(64)
        self.conv_block1 = _BlocConv(1, 64)
        self.conv_block2 = _BlocConv(64, 128)
        self.conv_block3 = _BlocConv(128, 256)
        self.conv_block4 = _BlocConv(256, 512)
        self.conv_block5 = _BlocConv(512, 1024)
        self.conv_block6 = _BlocConv(1024, 2048)
        self.fc1 = nn.Linear(2048, 2048, bias=True)
        self.fc_audioset = nn.Linear(2048, classes_num, bias=True)

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        # waveform : (batch, échantillons) @ 32 kHz
        x = self.spectrogram_extractor(waveform)   # (b, 1, temps, freq)
        x = self.logmel_extractor(x)               # (b, 1, temps, mel)
        x = x.transpose(1, 3)
        x = self.bn0(x)
        x = x.transpose(1, 3)

        x = self.conv_block1(x, pool_size=(2, 2))
        x = self.conv_block2(x, pool_size=(2, 2))
        x = self.conv_block3(x, pool_size=(2, 2))
        x = self.conv_block4(x, pool_size=(2, 2))
        x = self.conv_block5(x, pool_size=(2, 2))
        x = self.conv_block6(x, pool_size=(1, 1))
        x = torch.mean(x, dim=3)                   # moyenne sur les fréquences
        x1, _ = torch.max(x, dim=2)
        x2 = torch.mean(x, dim=2)
        x = x1 + x2                                # pooling temporel (max+moyenne)
        embedding = F.relu_(self.fc1(x))           # (b, 2048)
        return embedding


def charger_cnn14(chemin_poids: str | Path, device: torch.device) -> Cnn14:
    """Instancie CNN14 et charge les poids AudioSet. Modèle gelé, en eval."""
    modele = Cnn14()
    paquet = torch.load(str(chemin_poids), map_location=device, weights_only=False)
    etat = paquet["model"] if isinstance(paquet, dict) and "model" in paquet else paquet
    modele.load_state_dict(etat, strict=True)
    modele.to(device).eval()
    for p in modele.parameters():
        p.requires_grad = False
    return modele
