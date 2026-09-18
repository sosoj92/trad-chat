"""
Entraînement de la baseline CatMeows (Phase 1).

Pipeline complet : index + split par chat → datasets torch (avec augmentation
sur le train) → petit CNN → entraînement avec pondération des classes
(déséquilibre) et early stopping sur le F1 macro de validation → évaluation
honnête sur des chats jamais vus → sauvegarde du modèle et des figures.

Usage :
    uv run python -m training.entrainement
    uv run python -m training.entrainement --epochs 30 --batch-size 16
"""

from __future__ import annotations

import argparse
import copy
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from core.audio import forme_features
from core.config import charger_config, chemin_absolu
from core.journalisation import configurer_journalisation, obtenir_logger
from training.dataset_catmeows import CLASSES, indexer, split_par_chat
from training.evaluation import (
    exporter_mal_classes,
    predire_lot,
    rapport_texte,
    sauver_matrice_confusion,
)
from training.jeu_torch import JeuMiaulements
from training.modeles import compter_parametres, construire_modele

log = obtenir_logger(__name__)


def choisir_device(pref: str) -> torch.device:
    """Résout le périphérique : 'auto' → cuda si dispo, sinon cpu."""
    if pref == "cpu":
        return torch.device("cpu")
    if pref == "cuda" or (pref == "auto" and torch.cuda.is_available()):
        if torch.cuda.is_available():
            return torch.device("cuda")
        log.warning("CUDA demandé mais indisponible → repli sur CPU.")
    return torch.device("cpu")


def poids_classes(exemples, n_classes: int, device: torch.device) -> torch.Tensor:
    """Poids inversement proportionnels à la fréquence (contre le déséquilibre)."""
    comptes = Counter(ex.indice for ex in exemples)
    total = sum(comptes.values())
    poids = [total / (n_classes * max(comptes.get(i, 0), 1)) for i in range(n_classes)]
    return torch.tensor(poids, dtype=torch.float32, device=device)


def une_epoque(modele, loader, critere, optimiseur, device) -> float:
    """Une époque d'entraînement. Renvoie la perte moyenne."""
    modele.train()
    perte_totale = 0.0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimiseur.zero_grad()
        perte = critere(modele(x), y)
        perte.backward()
        optimiseur.step()
        perte_totale += perte.item() * x.size(0)
    return perte_totale / len(loader.dataset)


def sauver_courbes(historique: dict[str, list[float]], chemin: Path) -> None:
    """Sauvegarde les courbes perte/F1 (détection d'overfitting)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chemin.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(historique["perte_train"], label="train")
    ax1.plot(historique["perte_val"], label="val")
    ax1.set_title("Perte"); ax1.set_xlabel("époque"); ax1.legend()
    ax2.plot(historique["f1_val"], label="F1 macro val", color="green")
    ax2.set_title("F1 macro (validation)"); ax2.set_xlabel("époque"); ax2.legend()
    fig.tight_layout()
    fig.savefig(chemin, dpi=120)
    plt.close(fig)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    config = charger_config()
    configurer_journalisation(config)
    p = argparse.ArgumentParser(description="Entraînement baseline CatMeows")
    reglages = config.get("entrainement", {})
    p.add_argument("--epochs", type=int, default=int(reglages.get("epochs", 50)))
    p.add_argument("--batch-size", type=int, default=int(reglages.get("batch_size", 16)))
    p.add_argument("--lr", type=float, default=float(reglages.get("learning_rate", 1e-3)))
    p.add_argument("--modele", type=str, default="petit_cnn")
    args = p.parse_args()

    seed = int(reglages.get("seed", 42))
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = choisir_device(reglages.get("device", "auto"))
    log.info("Périphérique : %s", device)
    if device.type == "cuda":
        log.info("GPU : %s", torch.cuda.get_device_name(0))

    # --- Données ---
    exemples = indexer(chemin_absolu("data_catmeows", config))
    train, val, test = split_par_chat(
        exemples, seed=seed,
        val_ratio=float(reglages.get("val_ratio", 0.15)),
        test_ratio=float(reglages.get("test_ratio", 0.15)),
    )
    log.info("Split par chat — train=%d val=%d test=%d exemples", len(train), len(val), len(test))

    jeu_train = JeuMiaulements(train, config, entrainement=True, seed=seed)
    jeu_val = JeuMiaulements(val, config, entrainement=False, seed=seed)
    jeu_test = JeuMiaulements(test, config, entrainement=False, seed=seed)

    dl_train = DataLoader(jeu_train, batch_size=args.batch_size, shuffle=True, num_workers=0)
    dl_val = DataLoader(jeu_val, batch_size=args.batch_size, shuffle=False, num_workers=0)
    dl_test = DataLoader(jeu_test, batch_size=args.batch_size, shuffle=False, num_workers=0)

    # --- Modèle ---
    n_classes = len(CLASSES)
    modele = construire_modele(args.modele, n_classes).to(device)
    log.info("Modèle '%s' — %d paramètres, features %s",
             args.modele, compter_parametres(modele), forme_features(config))

    poids = poids_classes(train, n_classes, device)
    critere = nn.CrossEntropyLoss(weight=poids)
    optimiseur = torch.optim.Adam(modele.parameters(), lr=args.lr)

    # --- Boucle d'entraînement avec early stopping (sur F1 macro val) ---
    patience = int(reglages.get("early_stopping_patience", 8))
    from sklearn.metrics import f1_score

    historique = {"perte_train": [], "perte_val": [], "f1_val": []}
    meilleur_f1 = -1.0
    meilleur_etat = None
    sans_amelioration = 0

    for epoque in range(1, args.epochs + 1):
        perte_train = une_epoque(modele, dl_train, critere, optimiseur, device)

        # Perte + F1 de validation
        modele.eval()
        with torch.no_grad():
            perte_val = 0.0
            for x, y in dl_val:
                x, y = x.to(device), y.to(device)
                perte_val += critere(modele(x), y).item() * x.size(0)
            perte_val /= len(dl_val.dataset)
        y_vrai, y_pred, _ = predire_lot(modele, dl_val, device)
        f1_val = f1_score(y_vrai, y_pred, average="macro", zero_division=0)

        historique["perte_train"].append(perte_train)
        historique["perte_val"].append(perte_val)
        historique["f1_val"].append(f1_val)
        log.info("Époque %2d/%d | perte train %.3f | perte val %.3f | F1 val %.1f%%",
                 epoque, args.epochs, perte_train, perte_val, 100 * f1_val)

        if f1_val > meilleur_f1:
            meilleur_f1 = f1_val
            meilleur_etat = copy.deepcopy(modele.state_dict())
            sans_amelioration = 0
        else:
            sans_amelioration += 1
            if sans_amelioration >= patience:
                log.info("Early stopping (pas d'amélioration depuis %d époques).", patience)
                break

    # --- Évaluation finale sur le test (chats jamais vus) ---
    if meilleur_etat is not None:
        modele.load_state_dict(meilleur_etat)
    y_vrai, y_pred, probas = predire_lot(modele, dl_test, device)
    rapport = rapport_texte(y_vrai, y_pred, CLASSES)
    print("\n===== TEST (chats jamais vus) =====")
    print(rapport)

    from sklearn.metrics import accuracy_score

    acc_test = accuracy_score(y_vrai, y_pred)

    # --- Sauvegardes : modèle + figures + mal classés ---
    dossier_models = chemin_absolu("models", config)
    dossier_models.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M")
    nom_modele = f"baseline_catmeows_{horodatage}_acc{int(round(acc_test * 100)):02d}.pt"
    chemin_modele = dossier_models / nom_modele
    torch.save({
        "state_dict": modele.state_dict(),
        "classes": CLASSES,
        "modele": args.modele,
        "audio": config.get("audio", {}),
        "meta": {"date": horodatage, "acc_test": acc_test, "f1_val": meilleur_f1},
    }, chemin_modele)
    log.info("Modèle sauvegardé : %s", chemin_modele)

    dossier_docs = chemin_absolu("logs", config).parent / "docs"
    sauver_courbes(historique, dossier_docs / "baseline_courbes.png")
    sauver_matrice_confusion(y_vrai, y_pred, CLASSES, dossier_docs / "baseline_confusion.png")
    chemin_csv, n_rates = exporter_mal_classes(
        test, y_vrai, y_pred, probas, CLASSES, dossier_docs / "baseline_mal_classes.csv"
    )
    log.info("Figures + %d exemples mal classés exportés (%s)", n_rates, chemin_csv)
    print(f"\nModèle : {chemin_modele.name}")
    print(f"Figures : docs/baseline_courbes.png, docs/baseline_confusion.png")
    print(f"Mal classés : docs/baseline_mal_classes.csv ({n_rates} exemples à écouter)")


if __name__ == "__main__":
    main()
