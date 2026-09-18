# 🐱 Traducteur de chat

> Comprendre ce que raconte mon chat — un cran plus sérieusement qu'un gadget.

**En une phrase :** pas de « traduction » magique, mais un **classifieur
d'intentions de miaulements**. D'abord entraîné sur un dataset public, puis
affiné sur **mon** chat grâce à une petite app mobile de labellisation, et
finalement branché sur mon assistant vocal **Jarvis**.

L'idée de fond : les chats développent un « dialecte » propre avec leur humain.
On ne vise donc pas un traducteur universel, mais un classifieur **personnalisé**.

## État du projet

🚧 **Prototype** — collecte enrichie disponible ; protocole supervisé personnel préparé, pas encore de modèle personnel validé.

| Phase | Sujet | État |
|-------|-------|------|
| 0 | Fondations (structure, config, conventions) | ✅ fait |
| 1 | Baseline sur le dataset public CatMeows | ✅ fait (68 % acc — voir [docs/baseline.md](docs/baseline.md)) |
| 2 | App mobile de collecte (PWA + serveur) | ✅ fait (voir [docs/collecte.md](docs/collecte.md)) |
| 3 | Apprentissage supervisé sur mon chat | 🛠 pipeline préparé ; collecte / validation à réaliser ([protocole](docs/apprentissage.md)) |
| 4 | Écoute temps réel sur le PC | ⬜ à venir |
| 5 | Intégration Jarvis | ⬜ à venir |

## Structure

```
chat-traducteur/
├── collecte/     # Phase 2 — app mobile de collecte + serveur qui reçoit les audios
├── core/         # utilitaires partagés : config centrale + journalisation
├── data/         # datasets (gitignorés, structure conservée via .gitkeep)
│   ├── catmeows/ #   dataset public (Phase 1)
│   └── mon_chat/ #   MES enregistrements labellisés — JAMAIS versionné
├── training/     # Phases 1 & 3 — scripts d'entraînement et d'évaluation
├── inference/    # Phases 1 & 4 — détection + classification
├── models/       # modèles entraînés (gitignorés, gros fichiers)
├── docs/         # rapports (baseline.md, collecte.md, mon_chat_v1.md…)
├── config.example.yaml   # modèle de config (versionné)
├── config.yaml           # config réelle (NON versionnée — token, chemins…)
└── pyproject.toml        # projet uv, Python 3.13
```

## Démarrage

Sources du modèle, des données et articles : [ressources du projet](docs/ressources.md).
Voir aussi les [notices tierces](THIRD_PARTY_NOTICES.md).

Prérequis : [uv](https://docs.astral.sh/uv/) et Python 3.13.

```bash
# 1. Créer sa config à partir du modèle
cp config.example.yaml config.yaml   # (Windows PowerShell : copy config.example.yaml config.yaml)

# 2. Installer l'environnement de base
uv sync

# 3. Vérifier que tout est en place (résumé de la config + labels détectés)
uv run python -m core.config
```

Les dépendances lourdes (ML, serveur) sont dans des **groupes optionnels**,
installés au fil des phases :

```bash
uv sync --group training     # Phases 1 & 3
uv sync --group collecte     # Phase 2
uv sync --group temps-reel   # Phase 4
```

## Conventions

- **Config centrale** dans `config.yaml`, non versionnée, **aucun secret en
  dur** dans le code.
- **Données perso privées** : `data/mon_chat/`, `models/`, `logs/` et
  `config.yaml` sont gitignorés dès le premier commit (on entend l'appart et
  ma voix en fond sur les enregistrements).
- **Labels dynamiques** : les catégories vivent dans `config.yaml`. En
  ajouter/retirer suffit, le pipeline s'adapte au nombre de classes.
- **Code en français**, docstrings soignées (publication open source possible,
  sans les audios perso).

## Attentes honnêtes

Le modèle tente d'associer un son à un **contexte observé**, pas de traduire
des phrases ni de lire les pensées du chat. Aucune précision n'est garantie
sur les futures journées. La qualité des annotations, leur diversité et une
évaluation indépendante décideront si les prédictions sont utiles.
Ce n'est **pas** un outil vétérinaire. Les corrections humaines constituent
des données supervisées, pas une boucle de reinforcement learning.

Les scripts comparent audio seul, contexte seul et audio + contexte. PANNs
CNN14 reste le point de départ ; aucun gain avec Perch ou BEATs n'est encore
démontré sur ce chat. La collecte ne lance ni entraînement ni déploiement
automatique. Voir [le protocole](docs/apprentissage.md).
