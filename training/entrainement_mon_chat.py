"""Évaluation supervisée perso : PANNs, contexte seul, audio + contexte.

Usage : python -m training.entrainement_mon_chat [--verifier] [--data DOSSIER]
Les résultats restent expérimentaux : aucun modèle n'est déployé automatiquement.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from core.config import charger_config, chemin_absolu
from training.dataset_mon_chat import indexer_mon_chat
from training.validation_groupee import decoupages, recherche, validation_imbriquee


def empreinte(exemples):
    h = hashlib.sha256(b"segments-energie-v1-panns-32k-4s")
    for e in exemples:
        h.update(json.dumps([e.id, e.debut_s, e.fin_s]).encode())
        with e.chemin.open("rb") as f:
            for bloc in iter(lambda: f.read(1024 * 1024), b""):
                h.update(bloc)
    return h.hexdigest()


def embeddings_panns(exemples, config, dossier, fingerprint):
    import librosa
    import torch
    from core.segments import extraire_segment
    from training.panns_cnn14 import SR_PANNS, charger_cnn14
    poids = chemin_absolu("models", config) / "panns" / "Cnn14_mAP=0.431.pth"
    hash_poids = hashlib.sha256(poids.read_bytes()).hexdigest()[:16]
    cache = dossier / f"panns_{fingerprint}_{hash_poids}.npz"
    if cache.exists():
        with np.load(cache, allow_pickle=False) as d:
            return d["X"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Extraction PANNs : {device}", flush=True)
    modele = charger_cnn14(poids, device)
    valeurs = []
    with torch.inference_mode():
        for i in range(0, len(exemples), 4):
            lot = []
            for e in exemples[i:i+4]:
                y, _ = librosa.load(e.chemin, sr=SR_PANNS, mono=True)
                lot.append(extraire_segment(y, SR_PANNS, e.debut_s, e.fin_s))
            valeurs.extend(modele(torch.from_numpy(np.stack(lot)).to(device)).cpu().numpy())
    X = np.array(valeurs)
    np.savez_compressed(cache, X=X, ids=np.array([e.id for e in exemples]), empreinte=fingerprint)
    return X


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, help="Dossier de collecte ou export décompressé")
    p.add_argument("--verifier", action="store_true", help="Vérifier les groupes sans calcul ML")
    p.add_argument("--plis", type=int, default=3)
    p.add_argument("--features", type=Path, help="NPZ d'un autre encodeur gelé : X, ids, empreinte")
    p.add_argument("--nom-encodeur", default="externe")
    args = p.parse_args()
    config = charger_config()
    exemples = sorted(indexer_mon_chat(config, base=args.data), key=lambda e: e.id)
    y = np.array([e.label for e in exemples])
    groupes = np.array([e.jour for e in exemples])
    try:
        externes = decoupages(y, groupes, args.plis, 42)
        for train, _ in externes:
            decoupages(y[train], groupes[train], args.plis, 42)
    except ValueError as exc:
        p.exit(2, f"Collecte insuffisante pour ce protocole : {exc}\n")
    fingerprint = empreinte(exemples)
    print(f"{len(exemples)} clips admissibles, {len(set(groupes))} jours ; empreinte {fingerprint}")
    if args.verifier:
        return
    dossier = chemin_absolu("models", config) / "personnel"
    dossier.mkdir(parents=True, exist_ok=True)
    if args.features:
        with np.load(args.features, allow_pickle=False) as d:
            if list(d["ids"]) != [e.id for e in exemples] or str(d["empreinte"]) != fingerprint:
                raise ValueError("Les features ne correspondent pas aux fichiers / extraits actuels")
            X = d["X"]
        if X.ndim != 2 or len(X) != len(exemples) or not np.isfinite(X).all():
            raise ValueError("Matrice de features invalide")
        encodeur = args.nom_encodeur
    else:
        X = embeddings_panns(exemples, config, dossier, fingerprint)
        encodeur = "panns_cnn14"
    contexte = [e.contexte for e in exemples]
    combine = [{**e.contexte, **{f"audio_{j}": float(v) for j, v in enumerate(x)}}
               for e, x in zip(exemples, X)]
    rapports = {}
    for nom, donnees, dictionnaires in [("audio", X, False), ("contexte", contexte, True),
                                       ("audio_contexte", combine, True)]:
        print(f"Évaluation {nom} (CPU)", flush=True)
        rapports[nom] = validation_imbriquee(donnees, y, groupes, args.plis,
                                            dictionnaires=dictionnaires)
    # Modèle audio ajusté sur toutes les données APRÈS l'évaluation. Ne pas le réévaluer dessus.
    final = recherche(X, y, groupes, args.plis)
    horod = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    chemin = dossier / f"experience_{horod}"
    chemin.mkdir()
    import joblib
    joblib.dump({"pipeline": final.best_estimator_, "encodeur": encodeur,
                 "pretraitement": "segments-energie-v1", "classes": sorted(set(y)),
                 "deploiement": False}, chemin / "classifieur_audio.joblib")
    (chemin / "rapport.json").write_text(json.dumps({"encodeur": encodeur,
        "empreinte": fingerprint, "ids": [e.id for e in exemples], "rapports": rapports},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rapport expérimental : {chemin / 'rapport.json'}")


if __name__ == "__main__":
    main()
