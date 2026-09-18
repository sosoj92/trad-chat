"""Diagnostic local en lecture seule : ni secret affiché, ni microphone activé."""
import argparse
import importlib.util
import socket
import sys

from core.config import ErreurConfig, charger_config, chemin_absolu, valider_collecte


def diagnostiquer(config=None, ml=False):
    lignes, erreurs = [], 0
    python_ok = (3, 13) <= sys.version_info[:2] < (3, 14)
    lignes.append(("OK" if python_ok else "ERREUR", "Python 3.13 requis pour le parcours testé."))
    erreurs += not python_ok
    try:
        config = charger_config() if config is None else config
        valider_collecte(config)
    except (ErreurConfig, OSError):
        lignes.append(("ERREUR", "Configuration absente ou invalide. Voir docs/installation.md et config.example.yaml. Aucune valeur privée affichée."))
        return lignes, erreurs + 1
    lignes.append(("OK", "Configuration valide ; clé privée présente (masquée)."))
    modules = ["fastapi", "uvicorn", "multipart", "numpy"]
    if ml:
        modules += ["sklearn", "librosa", "torch", "torchlibrosa"]
    for module in modules:
        present = importlib.util.find_spec(module) is not None
        lignes.append(("OK" if present else "ERREUR", f"Dépendance : {module}"))
        erreurs += not present
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", config["collecte"]["port"]))
            lignes.append(("OK", "Port local disponible."))
        except OSError:
            lignes.append(("INFO", "Port occupé : l'app tourne peut-être déjà. Ne pas arrêter un autre service sans vérifier."))
    if ml and importlib.util.find_spec("torch") is not None:
        try:
            import torch
            lignes.append(("OK", "PyTorch : CUDA disponible." if torch.cuda.is_available() else "PyTorch : CPU disponible, CUDA non disponible."))
        except Exception:
            lignes.append(("ERREUR", "PyTorch installé mais impossible à charger ; voir docs/installation.md."))
            erreurs += 1
        poids = chemin_absolu("models", config) / "panns" / "Cnn14_mAP=0.431.pth"
        lignes.append(("OK" if poids.is_file() else "INFO", "Poids PANNs présents." if poids.is_file() else
                       "Poids PANNs absents : optionnels pour collecter, requis pour l'extraction audio."))
    lignes.append(("INFO", "Téléphone : utiliser HTTPS avec son propre tunnel. Aucun tunnel lancé par ce diagnostic."))
    return lignes, erreurs


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ml", action="store_true", help="Vérifier aussi l'environnement d'entraînement")
    args = p.parse_args()
    lignes, erreurs = diagnostiquer(ml=args.ml)
    for niveau, message in lignes:
        print(f"[{niveau}] {message}")
    raise SystemExit(1 if erreurs else 0)


if __name__ == "__main__":
    main()
