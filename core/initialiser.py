"""Créer une configuration privée pour son chat, sans écraser une installation."""
import argparse
import os
from pathlib import Path
import secrets
import sys

import yaml

from core.config import ErreurConfig, RACINE, charger_config, valider_collecte


def initialiser(racine: Path = RACINE, nom_chat="Mon chat", port=8771, categories=None) -> bool:
    cible = racine / "config.yaml"
    if cible.exists():
        return False
    config = yaml.safe_load((racine / "config.example.yaml").read_text(encoding="utf-8"))
    config["chat"] = {"nom": nom_chat.strip()}
    config["collecte"]["token"] = secrets.token_urlsafe(32)
    config["collecte"]["host"] = "127.0.0.1"
    config["collecte"]["port"] = port
    if categories is not None:
        config["labels"] = list(categories)
        for reserve in ("autre", "incertain"):
            if reserve not in config["labels"]:
                config["labels"].append(reserve)
    valider_collecte(config)
    texte = "# Configuration PRIVEE. Ne pas publier. Guide : docs/personnalisation.md\n"
    texte += yaml.safe_dump(config, allow_unicode=True, sort_keys=False)
    # Création exclusive : même deux lancements concurrents ne remplacent pas une clé.
    try:
        fd = os.open(cible, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(texte)
    charger_config.cache_clear()
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--nom-chat", default="Mon chat", help="Nom affiché après connexion (reste privé)")
    p.add_argument("--port", type=int, default=8771)
    p.add_argument("--categories", nargs="+", help="Ex. faim porte jeu ; autre/incertain sont conservés")
    p.add_argument("--afficher-cle", action="store_true", help="Afficher la clé existante LOCALEMENT, hors capture vidéo")
    args = p.parse_args()
    try:
        if args.afficher_cle:
            config = charger_config()
            valider_collecte(config)
            print("Clé PRIVÉE — ne pas partager ni filmer :")
            print(config["collecte"]["token"])
            return
        nouveau = initialiser(nom_chat=args.nom_chat, port=args.port, categories=args.categories)
    except yaml.YAMLError:
        p.exit(2, "Modèle YAML invalide : vérifier config.example.yaml (valeurs masquées).\n")
    except (ErreurConfig, OSError) as exc:
        p.exit(2, f"Initialisation impossible : {exc}\n")
    print("Configuration privée créée, clé aléatoire enregistrée dans config.yaml." if nouveau else
          "config.yaml existe déjà : aucun réglage, aucune clé et aucune donnée n'ont été modifiés.")
    print("Diagnostic : uv run --no-sync python -m core.diagnostic")
    print("Lire sa clé hors vidéo : uv run --no-sync python -m core.initialiser --afficher-cle")


if __name__ == "__main__":
    main()
