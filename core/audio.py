"""
Prétraitement audio et extraction de features — partagé partout.

Chaîne : charger → (rogner les silences) → normaliser → durée fixe →
spectrogramme mel (en dB, standardisé). Tout est piloté par la section
``audio`` de ``config.yaml``, donc identique à l'entraînement et à
l'inférence (sinon le modèle verrait des features différentes en prod).

Tout est en numpy/librosa (CPU) : ce module ne dépend PAS de torch, ce qui
permet de valider le pipeline de données sans installer le framework ML.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import librosa
import numpy as np

from core.config import charger_config


def _audio_cfg(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return (config or charger_config()).get("audio", {})


def charger_audio(chemin: str | Path, sr: int) -> np.ndarray:
    """Charge un fichier audio en mono, ré-échantillonné à ``sr`` Hz."""
    y, _ = librosa.load(str(chemin), sr=sr, mono=True)
    return y.astype(np.float32)


def preparer_waveform(y: np.ndarray, config: dict[str, Any] | None = None) -> np.ndarray:
    """Rogne les silences, normalise en amplitude, force une durée fixe.

    Durée fixe = ``duree_max_s`` : les extraits courts sont complétés par du
    silence (padding), les longs sont tronqués. Indispensable pour empiler
    les exemples en batch.
    """
    cfg = _audio_cfg(config)
    sr = int(cfg.get("sample_rate", 16000))

    # Rogner les silences en début/fin (le miaulement ne dure qu'un instant).
    if cfg.get("trim_silence", True) and y.size > 0:
        y, _ = librosa.effects.trim(y, top_db=int(cfg.get("trim_top_db", 30)))

    # Normalisation en amplitude (indépendante du volume d'enregistrement).
    crete = float(np.max(np.abs(y))) if y.size else 0.0
    if crete > 1e-6:
        y = y / crete

    # Durée fixe.
    n_cible = int(float(cfg.get("duree_max_s", 4.0)) * sr)
    if y.size < n_cible:
        y = np.pad(y, (0, n_cible - y.size))
    else:
        y = y[:n_cible]
    return y.astype(np.float32)


def melspectrogramme(y: np.ndarray, config: dict[str, Any] | None = None) -> np.ndarray:
    """Spectrogramme mel en dB, standardisé (z-score).

    Returns:
        Tableau ``(n_mels, T)`` en float32. Le z-score par extrait rend le
        modèle robuste aux différences de niveau sonore.
    """
    cfg = _audio_cfg(config)
    sr = int(cfg.get("sample_rate", 16000))

    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=int(cfg.get("n_fft", 1024)),
        hop_length=int(cfg.get("hop_length", 256)),
        n_mels=int(cfg.get("n_mels", 64)),
        fmin=int(cfg.get("fmin", 50)),
        fmax=int(cfg.get("fmax", sr // 2)),
        power=2.0,
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)

    # Standardisation z-score (robuste au volume).
    mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)
    return mel_db.astype(np.float32)


def fichier_vers_features(
    chemin: str | Path, config: dict[str, Any] | None = None
) -> np.ndarray:
    """Pipeline complet : chemin .wav → features mel ``(n_mels, T)``."""
    config = config or charger_config()
    sr = int(_audio_cfg(config).get("sample_rate", 16000))
    y = charger_audio(chemin, sr)
    y = preparer_waveform(y, config)
    return melspectrogramme(y, config)


def forme_features(config: dict[str, Any] | None = None) -> tuple[int, int]:
    """Renvoie la forme ``(n_mels, T)`` des features, utile pour bâtir le modèle."""
    cfg = _audio_cfg(config)
    sr = int(cfg.get("sample_rate", 16000))
    n_mels = int(cfg.get("n_mels", 64))
    n_samples = int(float(cfg.get("duree_max_s", 4.0)) * sr)
    hop = int(cfg.get("hop_length", 256))
    t = 1 + n_samples // hop
    return n_mels, t
