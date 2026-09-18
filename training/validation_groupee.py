"""Validation imbriquée : tous les réglages restent à l'intérieur des plis."""
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def decoupages(y, groupes, plis, seed):
    y, groupes = np.asarray(y), np.asarray(groupes)
    if plis < 2:
        raise ValueError("Au moins deux plis sont nécessaires.")
    if len(set(y)) < 2:
        raise ValueError("Au moins deux catégories vérifiées sont nécessaires.")
    if any(len(set(groupes[y == label])) < plis for label in set(y)):
        raise ValueError(f"Chaque catégorie doit être présente sur au moins {plis} groupes distincts.")
    cv = StratifiedGroupKFold(n_splits=plis, shuffle=True, random_state=seed)
    splits = list(cv.split(np.zeros(len(y)), y, groupes))
    for train, test in splits:
        if set(groupes[train]) & set(groupes[test]):
            raise ValueError("Fuite de groupes détectée")
        if set(y[train]) != set(y) or set(y[test]) != set(y):
            raise ValueError("Découpage sans toutes les classes : collecter davantage de sessions variées.")
    return splits


def _score_macro(modele, X, y):
    # Pas de classe positive implicite : fonctionne aussi avec deux labels texte.
    return f1_score(y, modele.predict(X), average="macro", zero_division=0)


def recherche(X, y, groupes, plis=3, seed=42, grille=None, dictionnaires=False):
    etapes = ([DictVectorizer(sparse=False)] if dictionnaires else []) + [
        StandardScaler(), LogisticRegression(max_iter=3000, random_state=seed)]
    modele = make_pipeline(*etapes)
    grille = grille or {"logisticregression__C": [0.0001, 0.001, 0.01, 0.1, 1.0],
                        "logisticregression__class_weight": [None, "balanced"]}
    return GridSearchCV(modele, grille, cv=decoupages(y, groupes, plis, seed),
                        scoring=_score_macro,
                        n_jobs=1, error_score="raise", refit=True).fit(X, y)


def validation_imbriquee(X, y, groupes, plis=3, seed=42, grille=None, dictionnaires=False):
    """Rapport hors pli, sans choisir le C ni le seuil sur les tests externes."""
    y, groupes = np.asarray(y), np.asarray(groupes)
    splits = decoupages(y, groupes, plis, seed)
    classes = np.unique(y).tolist()
    predictions = np.empty(len(y), dtype=y.dtype)
    confiances = np.zeros(len(y))
    resultats = []
    prendre = lambda indices: [X[i] for i in indices] if dictionnaires else X[indices]
    # Vérifier TOUS les plis internes avant de lancer le premier entraînement.
    for train, _ in splits:
        decoupages(y[train], groupes[train], plis, seed)
    for numero, (train, test) in enumerate(splits):
        selection = recherche(prendre(train), y[train], groupes[train], plis, seed,
                              grille, dictionnaires)
        pred = selection.predict(prendre(test))
        predictions[test] = pred
        confiances[test] = selection.predict_proba(prendre(test)).max(axis=1)
        resultats.append({"pli": numero + 1, "groupes_train": np.unique(groupes[train]).tolist(),
                          "groupes_test": np.unique(groupes[test]).tolist(),
                          "hyperparametres": selection.best_params_,
                          "f1_macro": f1_score(y[test], pred, average="macro", zero_division=0),
                          "accuracy": accuracy_score(y[test], pred)})
    return {"protocole": "CV imbriquee par groupes, reglages internes uniquement",
            "plis": resultats, "classes": classes,
            "accuracy": accuracy_score(y, predictions),
            "f1_macro": f1_score(y, predictions, average="macro", zero_division=0),
            "f1_moyenne_plis": float(np.mean([r["f1_macro"] for r in resultats])),
            "f1_ecart_type_plis": float(np.std([r["f1_macro"] for r in resultats])),
            "rapport_classes": classification_report(y, predictions, output_dict=True, zero_division=0),
            "confusion": confusion_matrix(y, predictions, labels=classes).tolist(),
            "predictions_hors_pli": predictions.tolist(),
            "scores_max_non_calibres": confiances.tolist(),
            "note": "Scores non calibres. Ne pas choisir un seuil ou annoncer un gagnant sur ces seuls tests."}
