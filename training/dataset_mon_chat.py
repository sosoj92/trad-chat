"""
Loader du dataset perso ``data/mon_chat/`` (fondation Phase 3).

Lit le ``manifest.jsonl`` produit par l'app de collecte (Phase 2) et renvoie
les exemples labellisés avec MES catégories (config.yaml), prêts pour le
fine-tuning.

GARANTIE IMPORTANTE : les labels mis en quarantaine (``entrainement.labels_exclus``,
dont ``incertain``) sont **exclus par défaut**. « incertain » = miaulement normal
au contexte inconnu : on ne veut surtout pas l'apprendre comme une classe. Il
reste récupérable (``inclure_exclus=True``) pour ré-étiquetage ou pour calibrer
le seuil de confiance en Phase 4.

Test rapide :
    uv run python -m training.dataset_mon_chat
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from core.annotations import jour_record, motif_exclusion

from core.config import (
    charger_config,
    chemin_absolu,
    labels_entrainement,
    labels_exclus,
)


@dataclass(frozen=True)
class ExempleMonChat:
    """Un enregistrement perso : fichier, label, identifiant."""

    chemin: Path
    label: str
    id: str
    jour: str = ""
    session_id: str = ""
    debut_s: float = 0.0
    fin_s: float | None = None
    contexte: dict | None = None


def _lire_manifest(base: Path) -> list[dict]:
    manifest = base / "manifest.jsonl"
    if not manifest.exists():
        return []
    records = []
    with manifest.open("r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne:
                records.append(json.loads(ligne))
    return records


def indexer_mon_chat(
    config: dict | None = None,
    inclure_exclus: bool = False,
    base: Path | None = None,
) -> list[ExempleMonChat]:
    """Indexe les enregistrements perso non supprimés.

    Args:
        inclure_exclus: si False (défaut), retire les labels en quarantaine
            (``incertain``). Mettre True seulement pour de l'inspection ou du
            ré-étiquetage — JAMAIS pour l'entraînement.
    """
    config = config or charger_config()
    base = (base or chemin_absolu("data_mon_chat", config)).resolve()
    exclus = set(labels_exclus(config))

    exemples = []
    for r in _lire_manifest(base):
        if r.get("supprime"):
            continue
        label = r.get("label", "")
        if not inclure_exclus and motif_exclusion(r, labels_entrainement(config), list(exclus)):
            continue
        chemin = (base / r["fichier"]).resolve()
        if not chemin.is_relative_to(base) or not chemin.is_file():
            continue
        # Liste blanche : aucune observation après coup, note ou certitude en entrée ML.
        contexte = {"lieu": r.get("lieu", "") or "inconnu"}
        minutes = r.get("minutes_depuis_repas")
        contexte["repas_inconnu"] = float(minutes is None)
        contexte["minutes_depuis_repas"] = float(minutes or 0)
        exemples.append(ExempleMonChat(
            chemin=chemin, label=label, id=r["id"], jour=jour_record(r),
            session_id=r.get("session_id") or jour_record(r),
            debut_s=float(r.get("debut_s", 0)), fin_s=r.get("fin_s"), contexte=contexte,
        ))
    return exemples


def index_labels_entrainement(config: dict | None = None) -> dict[str, int]:
    """Table label → indice, restreinte aux labels d'entraînement (sans exclus)."""
    return {nom: i for i, nom in enumerate(labels_entrainement(config))}


def stats_mon_chat(config: dict | None = None) -> dict[str, dict]:
    """Comptes par label, en séparant labels d'entraînement et quarantaine."""
    config = config or charger_config()
    exclus = set(labels_exclus(config))
    tous = indexer_mon_chat(config, inclure_exclus=True)
    comptes: dict[str, int] = {}
    for ex in tous:
        comptes[ex.label] = comptes.get(ex.label, 0) + 1
    admissibles = indexer_mon_chat(config)
    entrainables = {l: sum(e.label == l for e in admissibles) for l in labels_entrainement(config)}
    quarantaine = {l: comptes.get(l, 0) for l in exclus}
    return {"entrainables": entrainables, "quarantaine": quarantaine, "total": len(tous),
            "a_verifier": len(tous) - len(admissibles) - sum(quarantaine.values())}


def _resume() -> None:
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    config = charger_config()
    s = stats_mon_chat(config)
    n_train = len(indexer_mon_chat(config))                       # exclut la quarantaine
    n_tot = len(indexer_mon_chat(config, inclure_exclus=True))    # tout
    print(f"data/mon_chat — {n_tot} enregistrements ({n_train} utilisables à l'entraînement)")
    print("\nClasses d'entraînement (objectif ~30+/classe) :")
    for label, n in s["entrainables"].items():
        jauge = "✓" if n >= 30 else ""
        print(f"  {label:16} : {n:3}  {jauge}")
    if s["quarantaine"]:
        print("\nQuarantaine (EXCLUE de l'entraînement) :")
        for label, n in s["quarantaine"].items():
            print(f"  {label:16} : {n:3}  (à ré-étiqueter / calibration seuil Phase 4)")
    print(f"\nAutres clips à vérifier / hors dataset : {s['a_verifier']}")
    print("\nLoader OK. [OK]")


if __name__ == "__main__":
    _resume()
