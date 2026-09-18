"""Sélection non destructive d'un extrait, commune au train et à l'inférence."""
import numpy as np


def extraire_segment(y: np.ndarray, sr: int, debut_s=0.0, fin_s=None,
                     duree_max_s=4.0) -> np.ndarray:
    """Intervalle manuel, puis fenêtre la plus énergique si trop long.

    Il s'agit d'une heuristique d'activité sonore, pas d'un détecteur de chat.
    Le fichier source n'est jamais modifié. Le dernier intervalle est considéré.
    """
    if sr <= 0:
        raise ValueError("Fréquence audio invalide")
    fin_s = len(y) / sr if fin_s is None else fin_s
    if not (0 <= debut_s < fin_s <= len(y) / sr + 0.02):
        raise ValueError("Bornes audio invalides")
    y = y[int(debut_s * sr):min(len(y), round(fin_s * sr))]
    cible = round(duree_max_s * sr)
    if not len(y) or cible <= 0:
        raise ValueError("Extrait vide")
    if len(y) > cible:
        cumul = np.concatenate(([0.0], np.cumsum(y.astype(np.float64) ** 2)))
        debuts = np.unique(np.r_[np.arange(0, len(y) - cible + 1, max(1, sr // 10)),
                                 len(y) - cible])
        debut = debuts[np.argmax(cumul[debuts + cible] - cumul[debuts])]
        y = y[debut:debut + cible]
    return np.pad(y, (0, max(0, cible - len(y)))).astype(np.float32)
