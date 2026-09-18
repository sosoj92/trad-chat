"""
Détection grossière « y a-t-il un miaulement ? » (contrôle qualité v1).

But : à l'upload, prévenir si l'enregistrement ne contient probablement pas de
chat (silence, ou juste du bruit ambiant). On ne bloque JAMAIS : on garde tout
(le bruit du quotidien servira d'exemples négatifs pour la détection en
Phase 4). C'est juste un « t'es sûre ? j'entends pas de chat ».

Heuristique simple et sans dépendance lourde, pensée pour les clips LONGS
(pré-buffer 5 s + traîne) : on ne juge PAS le clip entier — un miaou d'1 s noyé
dans 20 s de silence serait dilué. On repère la **fenêtre la plus énergique**
(1 s) et on l'évalue sur deux critères *relatifs* (robustes au volume, car les
enregistrements peuvent être faibles si le chat est loin du micro) :
  * SNR = énergie du pic / fond sonore médian (y a-t-il un événement ?) ;
  * part de l'énergie de ce pic dans la bande des miaulements (~300–3000 Hz).

Seuils calibrés sur de vrais enregistrements (miaous distants) vs négatifs.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

BANDE_MIN_HZ = 300         # fondamentale + harmoniques d'un miaulement
BANDE_MAX_HZ = 3000
SEUIL_SNR = 1.8            # pic / fond : en dessous, pas d'événement franc
RATIO_BANDE_MIN = 0.40     # part de l'énergie du pic dans la bande des miaous
PLANCHER_PIC = 2e-4        # rejette le silence numérique quasi pur
FRAME_S = 0.05             # fenêtre d'analyse de l'enveloppe d'énergie
FENETRE_PIC_S = 1.0        # largeur de la fenêtre « pic » analysée


def lire_wav(chemin: str | Path) -> tuple[np.ndarray, int]:
    """Lit un WAV PCM en mono float32 dans [-1, 1]. Renvoie (signal, sr)."""
    with wave.open(str(chemin), "rb") as w:
        sr = w.getframerate()
        n_canaux = w.getnchannels()
        largeur = w.getsampwidth()
        brut = w.readframes(w.getnframes())

    if largeur == 2:
        y = np.frombuffer(brut, dtype=np.int16).astype(np.float32) / 32768.0
    elif largeur == 4:
        y = np.frombuffer(brut, dtype=np.int32).astype(np.float32) / 2147483648.0
    elif largeur == 1:
        y = (np.frombuffer(brut, dtype=np.uint8).astype(np.float32) - 128) / 128.0
    else:
        raise ValueError(f"Largeur d'échantillon non gérée : {largeur} octets")

    if n_canaux > 1:
        y = y.reshape(-1, n_canaux).mean(axis=1)
    return y, sr


def _ratio_bande(seg: np.ndarray, sr: int) -> float:
    """Part de l'énergie du segment dans la bande des miaulements."""
    if seg.size < 8:
        return 0.0
    spectre = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1.0 / sr)
    total = float(np.sum(spectre**2)) + 1e-12
    masque = (freqs >= BANDE_MIN_HZ) & (freqs <= BANDE_MAX_HZ)
    return float(np.sum(spectre[masque] ** 2) / total)


def analyser(y: np.ndarray, sr: int) -> dict:
    """Analyse un signal sur sa fenêtre la plus énergique. Verdict miaulement.

    Renvoie durée, RMS global (info), SNR pic/fond, ratio de bande du pic,
    et le booléen ``miaulement``.
    """
    duree = float(len(y) / sr) if sr else 0.0
    vide = {"duree_s": round(duree, 2), "rms": 0.0, "snr": 0.0,
            "ratio_bande": 0.0, "miaulement": False}
    if y.size == 0 or sr <= 0:
        return vide

    rms_global = float(np.sqrt(np.mean(y**2)))

    # Enveloppe d'énergie par trames → fond médian et pic.
    fr = max(1, int(FRAME_S * sr))
    n = len(y) // fr
    if n >= 2:
        trames = y[: n * fr].reshape(n, fr)
        rms_trames = np.sqrt(np.mean(trames.astype(np.float64) ** 2, axis=1))
        fond = float(np.median(rms_trames)) + 1e-9
        pic = float(np.max(rms_trames))
    else:
        fond, pic = rms_global + 1e-9, rms_global
    snr = min(pic / fond, 999.0)  # plafonné (fond quasi nul → valeur absurde)

    # Fenêtre 1 s la plus énergique (recherche par somme glissante).
    win = min(len(y), max(fr, int(FENETRE_PIC_S * sr)))
    energie = y.astype(np.float64) ** 2
    cumul = np.concatenate([[0.0], np.cumsum(energie)])
    pas = max(1, int(0.1 * sr))
    debuts = range(0, len(y) - win + 1, pas)
    if debuts:
        i0 = max(debuts, key=lambda i: cumul[i + win] - cumul[i])
    else:
        i0 = 0
    ratio_bande = _ratio_bande(y[i0 : i0 + win], sr)

    miaulement = (snr >= SEUIL_SNR) and (ratio_bande >= RATIO_BANDE_MIN) and (pic >= PLANCHER_PIC)
    return {
        "duree_s": round(duree, 2),
        "rms": round(rms_global, 4),
        "snr": round(snr, 2),
        "ratio_bande": round(ratio_bande, 3),
        "miaulement": bool(miaulement),
    }


def analyser_fichier(chemin: str | Path) -> dict:
    """Analyse un fichier WAV et renvoie le dictionnaire d'analyse."""
    y, sr = lire_wav(chemin)
    return analyser(y, sr)
