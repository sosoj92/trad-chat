"""Stockage local : audio original conservé, manifest atomique et sauvegardé.

Un seul processus serveur (verrou inter-threads). Ne pas lancer plusieurs
workers partageant ce dossier. Les tests remplacent _base par un dossier temporaire.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import chemin_absolu

_verrou = threading.RLock()


def _base() -> Path:
    dossier = chemin_absolu("data_mon_chat")
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier


def _manifest() -> Path:
    return _base() / "manifest.jsonl"


def _charger() -> list[dict[str, Any]]:
    with _verrou:
        fichier = _manifest()
        if not fichier.exists():
            return []
        return [json.loads(l) for l in fichier.read_text(encoding="utf-8").splitlines() if l.strip()]


def _reecrire(records: list[dict[str, Any]]) -> None:
    """Sauvegarde avant chaque remplacement atomique ; pas de troncature directe."""
    cible = _manifest()
    if cible.exists():
        sauvegardes = _base() / ".backups"
        sauvegardes.mkdir(exist_ok=True)
        nom = datetime.now(timezone.utc).strftime("manifest_%Y%m%d_%H%M%S_%f.jsonl")
        shutil.copy2(cible, sauvegardes / nom)
    fd, nom_tmp = tempfile.mkstemp(prefix="manifest_", suffix=".tmp", dir=_base())
    tmp = Path(nom_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, cible)
    finally:
        tmp.unlink(missing_ok=True)


def ajouter(record: dict[str, Any]) -> None:
    with _verrou:
        _reecrire(_charger() + [record])


def enregistrer_audio(record: dict, donnees: bytes) -> tuple[dict, bool]:
    """Une nouvelle tentative de la même capture ne crée pas de doublon."""
    with _verrou:
        records = _charger()
        existant = next((r for r in records if r.get("capture_id") == record["capture_id"]), None)
        if existant:
            return existant, False
        cible = chemin_wav(record)
        cible.parent.mkdir(parents=True, exist_ok=True)
        with cible.open("xb") as f:
            f.write(donnees)
        try:
            _reecrire(records + [record])
        except Exception:
            # Uniquement le nouveau fichier créé par cet appel.
            cible.unlink()
            raise
        return record, True


def tous(inclure_supprimes: bool = False) -> list[dict[str, Any]]:
    records = _charger()
    return sorted((r for r in records if inclure_supprimes or not r.get("supprime")),
                  key=lambda r: r.get("date", r.get("id", "")), reverse=True)


def recents(n: int = 20) -> list[dict[str, Any]]:
    return tous()[:n]


def stats(labels: list[str]) -> dict[str, int]:
    compteur = dict.fromkeys(labels, 0)
    for record in tous():
        compteur[record["label"]] = compteur.get(record["label"], 0) + 1
    return compteur


def par_id(id_: str) -> dict | None:
    return next((r for r in _charger() if r.get("id") == id_), None)


def chemin_wav(record: dict) -> Path:
    base = _base().resolve()
    chemin = (base / record["fichier"]).resolve()
    if not chemin.is_relative_to(base):
        raise ValueError("Chemin audio hors du dossier de collecte")
    # Compatibilité avec les anciennes suppressions (chemin non mis à jour).
    if record.get("supprime") and not chemin.exists():
        chemin = base / ".trash" / chemin.name
    return chemin


def modifier(id_: str, changements: dict) -> dict | None:
    """Modifie les annotations uniquement ; l'audio original ne bouge pas."""
    with _verrou:
        records = _charger()
        cible = next((r for r in records if r.get("id") == id_ and not r.get("supprime")), None)
        if cible is None:
            return None
        changements = {k: v for k, v in changements.items() if cible.get(k) != v}
        if changements:
            maintenant = datetime.now(timezone.utc).isoformat()
            cible.setdefault("historique", []).append({
                "date": maintenant, "avant": {k: cible.get(k) for k in changements},
                "apres": changements,
            })
            cible.update(changements)
            cible["modifie_le"] = maintenant
            _reecrire(records)
        return cible


def rebaptiser(id_: str, nouveau_label: str) -> dict | None:
    return modifier(id_, {"label": nouveau_label})


def supprimer(id_: str) -> bool:
    """Suppression logique récupérable, sans déplacement du fichier original."""
    return modifier(id_, {"supprime": True}) is not None


def restaurer(id_: str) -> bool:
    with _verrou:
        records = _charger()
        cible = next((r for r in records if r.get("id") == id_ and r.get("supprime")), None)
        if cible is None:
            return False
        chemin = chemin_wav(cible)
        if not chemin.is_file():
            raise ValueError("Audio absent : restauration impossible")
        cible["fichier"] = chemin.relative_to(_base().resolve()).as_posix()
        cible["supprime"] = False
        cible.setdefault("historique", []).append({
            "date": datetime.now(timezone.utc).isoformat(), "action": "restauration",
        })
        _reecrire(records)
        return True
