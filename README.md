# 🐱 Trad Chat — un projet à refaire avec ton propre chat

Enregistre ses miaulements, annote ce que tu observes et découvre comment
entraîner puis évaluer un petit modèle de machine learning personnalisé.

**Ce n'est pas un traducteur de langage félin.** C'est une expérience pour
chercher si les sons permettent de reconnaître certains **contextes observés**,
comme une demande devant la porte. Le résultat peut être décevant : apprendre
à le mesurer fait partie du projet !

**Tu viens de la vidéo ?** Commence par le [guide d'installation](docs/installation.md),
puis suis le [tutoriel éducatif](docs/tutoriel.md).
Tu préfères être accompagné ? Voici le [prompt d'installation avec une IA](INSTALL_WITH_AI.md).

### Installer, recréer ou héberger ?

- **Installer le code déjà prêt** : [installation](docs/installation.md) et [prompt d'accompagnement](INSTALL_WITH_AI.md).
- **Recréer l'app avec un générateur/assistant** : [prompt complet de l'application](PROMPT_APP.md), actualisé et sans données privées.
- **L'utiliser sur son téléphone** : [tutoriel ngrok et guide Vercel/Netlify](docs/hebergement.md).

Le parcours ngrok fonctionne avec l'ordinateur allumé. Une version autonome
sur Vercel/Netlify nécessite un stockage cloud et une adaptation : le guide
distingue ce parcours à construire du code actuellement disponible.

## Ce que tu peux faire aujourd'hui

- Utiliser une petite application web sur ton téléphone, avec ton ordinateur comme serveur.
- Donner le nom de ton chat et choisir tes catégories, sans modifier le code.
- Enregistrer, réécouter et corriger rapidement les annotations.
- Garder tes audios et tes notes dans **ton installation privée**, pas sur ce GitHub.
- Quand la collecte le permet, lancer explicitement une expérience d'apprentissage supervisé.

La collecte fonctionne **sans GPU, sans modèle à télécharger et sans clé d'API LLM**.
L'ordinateur doit rester allumé pour recevoir les enregistrements. Ce dépôt
n'est pas un service hébergé disponible en permanence.

| Disponible | Encore expérimental / à construire |
|---|---|
| App de collecte et ré-étiquetage | Modèle personnel validé sur de futures journées |
| Configuration propre à chaque installation | Seuil de confiance calibré et abstention |
| Scripts d'évaluation audio / contexte | Détection et prédiction personnelles en temps réel |
| Expériences historiques sur CatMeows | Intégration Jarvis et communication humain → chat |

## Démarrage rapide sur ordinateur

Prérequis : [Git](https://git-scm.com/downloads) et
[uv](https://docs.astral.sh/uv/getting-started/installation/).
Le projet utilise Python 3.13 ; uv peut l'installer si nécessaire.
Commandes dans PowerShell sous Windows, ou dans un terminal sous macOS/Linux :

```bash
git clone https://github.com/sosoj92/trad-chat.git
cd trad-chat
uv sync --locked --group collecte
uv run --no-sync python -m core.initialiser --nom-chat Moka
uv run --no-sync python -m core.diagnostic
uv run --no-sync python -m collecte.serveur
```

Remplace `Moka` par le nom de ton chat. L'initialisation crée `config.yaml`
avec une clé aléatoire et **refuse d'écraser une configuration existante**.
Elle ne touche pas aux enregistrements. Ouvre ensuite
[l'app locale](http://127.0.0.1:8771).

Dans un **deuxième terminal**, depuis le dossier du projet, affiche ta clé :

```bash
uv run --no-sync python -m core.initialiser --afficher-cle
```

Colle-la dans « Clé de connexion ». **Ne filme et ne partage pas cette clé.**
Pour le téléphone, il faut une adresse HTTPS : suis
[la configuration de ton propre tunnel](docs/installation.md#4-ouvrir-sur-le-téléphone).
N'utilise pas l'adresse ni la clé de la personne qui présente le projet.

## Le parcours pédagogique

1. [Installer et réussir un premier enregistrement](docs/installation.md).
2. [Adapter l'application à son chat](docs/personnalisation.md) : nom, catégories, port.
3. [Apprendre à annoter](docs/tutoriel.md) : observation, hypothèse, incertitude, diversité.
4. [Comprendre et lancer l'apprentissage](docs/apprentissage.md) : transfert, validation par journées, métriques.
5. [Comparer avec les expériences publiques](docs/baseline.md), sans confondre leurs scores avec ceux de son chat.

```text
Un son + tes observations
         ↓
Collecte privée → correction / quarantaine
         ↓
Clips vérifiés répartis sur plusieurs journées
         ↓
PANNs (encodeur gelé) → classifieur supervisé léger
         ↓
Évaluation sur des journées non vues → utile ou pas ?
```

Les corrections sont des **annotations humaines**, pas du reinforcement
learning. Le modèle ne s'entraîne pas tout seul au fil des enregistrements.
Il n'y a ni RAG ni génération de phrases dans le pipeline actuel.

### Deux catégories à ne pas confondre

| Catégorie | Signification | Entraînement |
|---|---|---|
| `autre` | Vocalise identifiable hors catégories : trille, feulement, gazouillis… | Admissible comme classe atypique si vérifiée |
| `incertain` | Miaulement normal, contexte inconnu | **Toujours exclu**, en quarantaine |

Un objectif de 30 clips par classe est un **repère de collecte**, pas une
garantie de performance. Plusieurs journées, des annotations cohérentes et
un test indépendant comptent davantage qu'un gros nombre de clips voisins.
Ne provoque pas de stress ou d'inconfort pour remplir une catégorie.
Ce projet n'est pas un outil vétérinaire.

## Repères dans le code

```text
collecte/                  API FastAPI et application mobile web
core/initialiser.py        Création sûre d'une configuration personnelle
core/diagnostic.py         Vérifications locales, sans afficher de secret
training/                  Datasets, modèles et évaluation supervisée
inference/                 Inférence historique CatMeows ; pas l'app personnelle
tests/                     Tests isolés avec données synthétiques
docs/                      Guides et rapports pédagogiques
config.example.yaml        Modèle public ; config.yaml reste privé
uv.lock                    Versions des dépendances pour reproduire l'installation
```

## Ressources, confidentialité et contribution

- [Modèles, données, articles et liens officiels](docs/ressources.md).
- [Notice d'utilisation quotidienne](docs/collecte.md) et [dépannage](docs/depannage.md).
- [Ce qui doit rester privé](docs/confidentialite.md) et [sécurité](SECURITY.md).
- [Contribuer et lancer les tests](CONTRIBUTING.md).
- [Licences et conditions des ressources tierces](THIRD_PARTY_NOTICES.md).

Les données CatMeows et les poids PANNs ne sont pas livrés avec ce dépôt.
Consulte leurs conditions avant téléchargement ou réutilisation ; les
conditions du code, du dataset et des modèles sont distinctes.
Chaque personne collecte ses propres données. **Un dossier de projet = un chat** :
il n'y a pas encore de gestion multi-chat dans une même installation.
