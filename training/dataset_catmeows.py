"""
Loader du dataset public CatMeows (Phase 1).

440 miaulements, 21 chats, 3 contextes encodés dans le nom de fichier :
    C_CATID_BREED_SEX_OWNER_RVV.wav
    ex. « B_ANI01_MC_FN_SIM01_101.wav »
      C     = contexte  → B (brossage) | F (attente nourriture) | I (isolement)
      CATID = ID unique du chat (ANI01, BAC01…) ← sert au split par individu
      BREED = race (MC, EU) ; SEX ; OWNER = propriétaire ; RVV = session+numéro

Point crucial : le split train/val/test se fait **par CHAT**, jamais par
enregistrement. Sinon le modèle apprendrait à reconnaître l'individu (sa voix)
au lieu de l'intention — une fuite de données classique qui gonfle les scores.

Ces 3 classes sont propres à CatMeows et n'ont rien à voir avec MES catégories
(config.yaml) : la Phase 1 valide le pipeline, la Phase 3 basculera sur mes labels.

Test rapide (sur les vraies données) :
    uv run python -m training.dataset_catmeows
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

# Contexte (1re lettre du nom) → nom de classe lisible (en français).
CONTEXTE_VERS_CLASSE: dict[str, str] = {
    "B": "brossage",
    "F": "attente_nourriture",
    "I": "isolement",
}
CLASSES: list[str] = ["attente_nourriture", "isolement", "brossage"]
CLASSE_VERS_INDICE: dict[str, int] = {c: i for i, c in enumerate(CLASSES)}


@dataclass(frozen=True)
class Exemple:
    """Un enregistrement : où il est, sa classe, et quel chat l'a produit."""

    chemin: Path
    classe: str        # nom lisible (« brossage »…)
    indice: int        # indice de classe (0..2)
    chat: str          # ID du chat (pour le split par individu)


def parser_nom(chemin: Path) -> Exemple | None:
    """Décode un nom de fichier CatMeows. Renvoie None si non conforme."""
    parties = chemin.stem.split("_")
    if len(parties) < 2:
        return None
    contexte = parties[0].upper()
    classe = CONTEXTE_VERS_CLASSE.get(contexte)
    if classe is None:
        return None
    chat = parties[1].upper()
    return Exemple(chemin=chemin, classe=classe, indice=CLASSE_VERS_INDICE[classe], chat=chat)


def indexer(dossier: str | Path) -> list[Exemple]:
    """Parcourt le dossier (récursivement) et indexe tous les .wav valides."""
    dossier = Path(dossier)
    if not dossier.exists():
        raise FileNotFoundError(
            f"Dossier CatMeows introuvable : {dossier}\n"
            "→ Voir docs/baseline.md pour le téléchargement depuis Zenodo."
        )
    exemples = [ex for w in sorted(dossier.rglob("*.wav")) if (ex := parser_nom(w))]
    if not exemples:
        raise RuntimeError(f"Aucun .wav CatMeows valide trouvé sous {dossier}")
    return exemples


def _sous_ensemble(exemples: list[Exemple], indices: np.ndarray) -> list[Exemple]:
    return [exemples[i] for i in indices]


def split_par_chat(
    exemples: list[Exemple],
    seed: int = 42,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> tuple[list[Exemple], list[Exemple], list[Exemple]]:
    """Split train/val/test en gardant chaque chat entièrement dans un seul lot.

    Utilise StratifiedGroupKFold (groupe = chat) pour respecter au mieux la
    répartition des classes malgré des chats très déséquilibrés. Aucun chat
    n'apparaît dans deux lots → pas de fuite d'identité.
    """
    y = np.array([ex.indice for ex in exemples])
    groupes = np.array([ex.chat for ex in exemples])
    x_bidon = np.zeros(len(exemples))

    # 1) Isoler le test : n_splits ≈ 1/test_ratio (ex. 0.15 → ~7 lots).
    n_test = max(3, round(1.0 / max(test_ratio, 1e-6)))
    sgkf1 = StratifiedGroupKFold(n_splits=n_test, shuffle=True, random_state=seed)
    trainval_idx, test_idx = next(iter(sgkf1.split(x_bidon, y, groupes)))

    # 2) Extraire la validation depuis le reste, toujours par chat.
    tv = _sous_ensemble(exemples, trainval_idx)
    y_tv = np.array([ex.indice for ex in tv])
    g_tv = np.array([ex.chat for ex in tv])
    # Ratio de val relatif au trainval restant.
    val_rel = val_ratio / max(1.0 - test_ratio, 1e-6)
    n_val = max(3, round(1.0 / max(val_rel, 1e-6)))
    n_val = min(n_val, len(set(g_tv)))  # pas plus de lots que de chats
    sgkf2 = StratifiedGroupKFold(n_splits=n_val, shuffle=True, random_state=seed)
    train_rel_idx, val_rel_idx = next(iter(sgkf2.split(np.zeros(len(tv)), y_tv, g_tv)))

    train = _sous_ensemble(tv, train_rel_idx)
    val = _sous_ensemble(tv, val_rel_idx)
    test = _sous_ensemble(exemples, test_idx)

    # Garde-fou : aucun chat partagé entre les lots.
    chats_train = {e.chat for e in train}
    chats_val = {e.chat for e in val}
    chats_test = {e.chat for e in test}
    assert not (chats_train & chats_val), "Fuite : chat commun train/val"
    assert not (chats_train & chats_test), "Fuite : chat commun train/test"
    assert not (chats_val & chats_test), "Fuite : chat commun val/test"

    return train, val, test


def _stats(nom: str, lot: list[Exemple]) -> str:
    par_classe = {c: 0 for c in CLASSES}
    for e in lot:
        par_classe[e.classe] += 1
    chats = sorted({e.chat for e in lot})
    detail = "  ".join(f"{c}={n}" for c, n in par_classe.items())
    return f"{nom:6} : {len(lot):3} extraits | {len(chats):2} chats | {detail}"


def _resume() -> None:
    """Affiche l'index et le split — test de la Phase 1 sans torch."""
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from core.config import chemin_absolu

    dossier = chemin_absolu("data_catmeows")
    exemples = indexer(dossier)
    print(f"Dataset CatMeows : {len(exemples)} extraits, "
          f"{len({e.chat for e in exemples})} chats, {len(CLASSES)} classes")
    print("Répartition globale par classe :")
    for c in CLASSES:
        print(f"  - {c:20} : {sum(e.classe == c for e in exemples)}")
    print("\nSplit par chat (anti-fuite) :")
    train, val, test = split_par_chat(exemples)
    print(_stats("train", train))
    print(_stats("val", val))
    print(_stats("test", test))
    print("\nChats de test (jamais vus à l'entraînement) :",
          ", ".join(sorted({e.chat for e in test})))
    print("\nIndex + split OK. [OK]")


if __name__ == "__main__":
    _resume()
