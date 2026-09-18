"""
Inférence simple : un fichier .wav → classe prédite + probabilités.

Charge un modèle sauvegardé (qui embarque ses classes et ses réglages audio,
pour que les features soient calculées exactement comme à l'entraînement).

Usage :
    uv run python -m inference.predire chemin/vers/miaou.wav
    uv run python -m inference.predire miaou.wav --modele models/baseline_catmeows_XXXX.pt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

from core.audio import fichier_vers_features
from core.config import chemin_absolu
from training.modeles import construire_modele


def dernier_modele(dossier: Path) -> Path:
    """Renvoie le modèle .pt le plus récent d'un dossier."""
    modeles = sorted(dossier.glob("*.pt"), key=lambda p: p.stat().st_mtime)
    if not modeles:
        raise FileNotFoundError(
            f"Aucun modèle .pt dans {dossier}. Entraîne d'abord : "
            "uv run python -m training.entrainement"
        )
    return modeles[-1]


def charger_modele(chemin: Path, device: torch.device):
    """Charge un modèle et ses métadonnées (classes + config audio)."""
    paquet = torch.load(chemin, map_location=device, weights_only=False)
    modele = construire_modele(paquet["modele"], len(paquet["classes"])).to(device)
    modele.load_state_dict(paquet["state_dict"])
    modele.eval()
    return modele, paquet["classes"], {"audio": paquet["audio"]}


@torch.no_grad()
def predire(chemin_wav: Path, modele, classes: list[str], config_audio: dict, device):
    """Renvoie ``(classe, probabilites_triees)`` pour un fichier audio."""
    feat = fichier_vers_features(chemin_wav, config_audio)
    x = torch.from_numpy(feat).unsqueeze(0).unsqueeze(0).to(device)  # (1,1,n_mels,T)
    probas = torch.softmax(modele(x), dim=1).cpu().numpy()[0]
    ordre = np.argsort(probas)[::-1]
    return classes[ordre[0]], [(classes[i], float(probas[i])) for i in ordre]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(description="Classer un miaulement (.wav)")
    p.add_argument("wav", type=str, help="fichier audio à classer")
    p.add_argument("--modele", type=str, default=None, help="chemin d'un modèle .pt")
    args = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    chemin_modele = Path(args.modele) if args.modele else dernier_modele(chemin_absolu("models"))
    modele, classes, config_audio = charger_modele(chemin_modele, device)

    wav = Path(args.wav)
    if not wav.exists():
        raise FileNotFoundError(f"Fichier introuvable : {wav}")

    classe, probas = predire(wav, modele, classes, config_audio, device)
    print(f"Modèle  : {chemin_modele.name}")
    print(f"Fichier : {wav.name}")
    print(f"\n→ Classe prédite : {classe}\n")
    print("Probabilités :")
    for nom, pr in probas:
        barre = "█" * int(round(pr * 30))
        print(f"  {nom:20} {pr:5.1%} {barre}")


if __name__ == "__main__":
    main()
