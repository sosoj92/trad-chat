# Contribuer

Les améliorations de documentation, d'accessibilité, les tests et les
corrections reproductibles sont bienvenues. Pour proposer du code, crée
un fork et une branche, puis une pull request avec l'objectif et les tests.
Ne joins pas de données domestiques pour démontrer un bug.

## Environnement de test léger

Dans une copie de travail distincte de ton serveur actif :

```bash
uv sync --locked --group test
uv run --no-sync python -m core.initialiser --nom-chat Demo
uv run --no-sync python -m core.diagnostic
uv run --no-sync python -m unittest discover -s tests -v
```

Les tests fabriquent des WAV synthétiques dans des dossiers temporaires.
Ils ne requièrent ni PyTorch, ni microphone, ni dataset téléchargé. Une
configuration de démonstration est requise avant l'import du serveur.
Pour vérifier le JavaScript si Node.js est installé :

```bash
node --check collecte/static/app.js
```

## Avant une pull request

- Préserve les originaux et les annotations existantes ; ajoute un test pour les migrations.
- Préserve l'exclusion de `incertain`, les splits par groupes et les frontières train/test.
- Distingue expérimentation et fonctionnalités effectivement disponibles.
- Utilise des exemples fictifs dans la documentation et des chemins relatifs.
- Relis `git diff --cached` : pas de clé, donnée, modèle, export ou log privé.
- N'utilise pas `git add -f` pour contourner les exclusions des données.

Les dépendances sont verrouillées dans `uv.lock`. Si tu changes
`pyproject.toml`, régénère le lock avec `uv lock`, puis vérifie le parcours
de collecte sans dépendances ML. Un nouveau modèle doit documenter ses
sources, ses conditions et son protocole d'évaluation, pas seulement un score.

Voir [confidentialité](docs/confidentialite.md) et [sécurité](SECURITY.md).
