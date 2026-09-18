"""
Transfer learning : backbone PANNs CNN14 (gelé) + tête de classification.

Idée : au lieu d'apprendre un CNN de zéro sur 295 miaulements, on réutilise
CNN14 pré-entraîné sur AudioSet (2 M de sons) comme extracteur de features
(embedding 2048-D par clip), puis on entraîne une simple tête linéaire dessus
(« linear probe »). Sur très peu de données, c'est souvent bien plus robuste.

Comparaison HONNÊTE : exactement le même split PAR CHAT et la même seed que la
baseline CNN (training/entrainement.py), donc mêmes chats de test jamais vus.

Usage :
    uv run python -m training.transfer_panns
Les embeddings sont mis en cache (models/panns/embeddings_catmeows.npz) :
le 1er run les calcule (~1 min sur GPU), les suivants sont instantanés.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import librosa
from core.config import charger_config, chemin_absolu
from core.journalisation import configurer_journalisation, obtenir_logger
from training.dataset_catmeows import CLASSES, Exemple, indexer, split_par_chat
from training.evaluation import rapport_texte, sauver_matrice_confusion
from training.panns_cnn14 import SR_PANNS, charger_cnn14

log = obtenir_logger(__name__)

DUREE_S = 4.0
LONGUEUR = int(DUREE_S * SR_PANNS)
CACHE = "embeddings_catmeows.npz"


def _charger_waveform(chemin: Path) -> np.ndarray:
    """Charge un clip à 32 kHz mono, rogne les silences, durée fixe."""
    y, _ = librosa.load(str(chemin), sr=SR_PANNS, mono=True)
    y, _ = librosa.effects.trim(y, top_db=30)
    if y.size < LONGUEUR:
        y = np.pad(y, (0, LONGUEUR - y.size))
    else:
        y = y[:LONGUEUR]
    return y.astype(np.float32)


def extraire_embeddings(
    exemples: list[Exemple], chemin_poids: Path, device: torch.device, batch: int = 16
) -> np.ndarray:
    """Calcule les embeddings CNN14 (N, 2048) pour une liste d'exemples."""
    modele = charger_cnn14(chemin_poids, device)
    embs = []
    with torch.no_grad():
        for i in range(0, len(exemples), batch):
            lot = exemples[i : i + batch]
            ondes = np.stack([_charger_waveform(ex.chemin) for ex in lot])
            x = torch.from_numpy(ondes).to(device)
            embs.append(modele(x).cpu().numpy())
            log.info("Embeddings %d/%d", min(i + batch, len(exemples)), len(exemples))
    return np.concatenate(embs, axis=0)


def obtenir_embeddings(exemples: list[Exemple], config: dict) -> np.ndarray:
    """Embeddings avec cache disque (recalcul seulement si absent/incohérent)."""
    dossier = chemin_absolu("models", config) / "panns"
    dossier.mkdir(parents=True, exist_ok=True)
    cache = dossier / CACHE
    cles = np.array([ex.chemin.name for ex in exemples])

    if cache.exists():
        d = np.load(cache, allow_pickle=True)
        if len(d["cles"]) == len(cles) and bool(np.all(d["cles"] == cles)):
            log.info("Embeddings chargés du cache (%s)", cache.name)
            return d["X"]
        log.info("Cache périmé → recalcul.")

    poids = dossier / "Cnn14_mAP=0.431.pth"
    if not poids.exists():
        raise FileNotFoundError(
            f"Poids PANNs absents : {poids}\n→ Télécharger (voir docs/baseline.md, §Transfer)."
        )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("Extraction des embeddings sur %s…", device)
    X = extraire_embeddings(exemples, poids, device)
    np.savez(cache, X=X, cles=cles)
    log.info("Embeddings mis en cache (%s)", cache.name)
    return X


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    config = charger_config()
    configurer_journalisation(config)
    reglages = config.get("entrainement", {})
    seed = int(reglages.get("seed", 42))

    exemples = indexer(chemin_absolu("data_catmeows", config))
    X = obtenir_embeddings(exemples, config)
    y = np.array([ex.indice for ex in exemples])

    # Même split PAR CHAT et même seed que la baseline CNN.
    train, val, test = split_par_chat(
        exemples, seed=seed,
        val_ratio=float(reglages.get("val_ratio", 0.15)),
        test_ratio=float(reglages.get("test_ratio", 0.15)),
    )
    idx = {ex.chemin.name: i for i, ex in enumerate(exemples)}
    i_train = [idx[e.chemin.name] for e in train]
    i_val = [idx[e.chemin.name] for e in val]
    i_test = [idx[e.chemin.name] for e in test]

    def probe(c: float):
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=3000, class_weight="balanced", C=c),
        )

    # Linear probe : on sélectionne la régularisation C sur la VALIDATION
    # (2048 features pour 295 exemples → un C trop grand sur-apprend).
    meilleur_c, meilleur_f1 = 1.0, -1.0
    for c in (0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0):
        clf_c = probe(c).fit(X[i_train], y[i_train])
        f1v = f1_score(y[i_val], clf_c.predict(X[i_val]), average="macro", zero_division=0)
        log.info("C=%.3f → F1 val %.1f%%", c, 100 * f1v)
        if f1v > meilleur_f1:
            meilleur_f1, meilleur_c = f1v, c
    log.info("Meilleur C = %.3f (F1 val %.1f%%)", meilleur_c, 100 * meilleur_f1)

    clf = probe(meilleur_c).fit(X[i_train], y[i_train])
    y_test = y[i_test]
    y_pred = clf.predict(X[i_test])

    print("\n===== TRANSFER (PANNs CNN14 + linear probe) — TEST (chats jamais vus) =====")
    print(rapport_texte(y_test, y_pred, CLASSES))

    acc = accuracy_score(y_test, y_pred)
    f1m = f1_score(y_test, y_pred, average="macro", zero_division=0)

    docs = chemin_absolu("logs", config).parent / "docs"
    sauver_matrice_confusion(
        y_test, y_pred, CLASSES, docs / "transfer_confusion.png",
        titre="Transfer PANNs — confusion (test)")

    # Sauvegarde de la tête + scaler (réutilisable).
    import joblib

    dossier_models = chemin_absolu("models", config)
    horod = datetime.now().strftime("%Y%m%d_%H%M")
    chemin = dossier_models / f"transfer_panns_{horod}_acc{int(round(acc*100)):02d}.joblib"
    joblib.dump({"pipeline": clf, "classes": CLASSES}, chemin)

    print(f"\nTransfer  : accuracy {acc:.1%} · F1 macro {f1m:.1%}")
    print("Baseline CNN (rappel) : accuracy 68,1 % · F1 macro 59,0 %")
    print(f"Modèle : {chemin.name}")
    print("Figure : docs/transfer_confusion.png")

    # Refaire chaque réglage dans les plis internes : meilleur_c a déjà vu
    # la validation historique, qui recouvre certains futurs tests externes.
    from training.validation_groupee import validation_imbriquee

    groupes = np.array([ex.chat for ex in exemples])
    try:
        rapport = validation_imbriquee(X, y, groupes, plis=3, seed=seed)
    except ValueError as exc:
        print(f"\nCV imbriquée indisponible avec ces groupes : {exc}")
    else:
        import json
        chemin_rapport = chemin.with_suffix(".cv.json")
        chemin_rapport.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nCV imbriquée 3 × 3 PAR CHAT (réglages internes, prédictions hors pli) :")
        print(f"  accuracy {rapport['accuracy']:.1%} | F1 macro {rapport['f1_macro']:.1%}")
        print(f"  Rapport : {chemin_rapport.name}")


if __name__ == "__main__":
    main()
