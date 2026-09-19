# 🐱 Trad Chat — créez une application pour enregistrer et mieux comprendre votre chat

Et si l'on pouvait apprendre à reconnaître certains contextes à partir des
miaulements de **son propre chat** ? C'est l'expérience proposée ici.

Vous enregistrez des sons, vous notez ce que vous observez, puis vous utilisez
ces exemples pour entraîner et tester un modèle d'intelligence artificielle.
Le but, petit à petit, est qu'il reconnaisse des contextes sur **de nouveaux
miaulements qu'il n'a jamais entendus**. Ce résultat reste à vérifier :
il ne s'agit pas de traduire des phrases ni de lire les pensées du chat.

**Pas besoin de savoir programmer pour suivre le guide de collecte.**
GitHub est simplement le site où nous partageons les fichiers du projet
et leur mode d'emploi. Vous pouvez les récupérer pour créer votre propre installation.

## Pour commencer, qu'est-ce que vous voulez faire ?

- **Avoir l'application sur votre téléphone pour enregistrer votre chat** :
  commencez par [installer l'application pas à pas](docs/installation.md),
  puis [la rendre accessible depuis votre téléphone](docs/hebergement.md).
- **Comprendre comment l'IA fonctionne** :
  lisez l'explication juste ci-dessous, ou [la version détaillée sans prérequis](docs/comment-ca-marche.md).
- **Retrouver le modèle et les données de départ** :
  leurs liens sont dans la section suivante.
- **Recréer vous-même l'application avec une IA** :
  utilisez [le prompt de création](PROMPT_APP.md).
  Pour seulement installer le code existant, voici [le prompt d'accompagnement](INSTALL_WITH_AI.md).

## Les ressources de départ : nous ne partons pas de zéro

Un **modèle** est un programme dont certains réglages ont été appris à partir
d'exemples. Un **dataset**, ou jeu de données, est une collection d'exemples
utilisée pour apprendre ou évaluer ce programme. Ce ne sont pas la même chose.

| Ressource | Son rôle dans ce projet | Où la retrouver |
|---|---|---|
| **PANNs, modèle CNN14** | Modèle déjà entraîné à analyser des sons, réutilisé comme point de départ | [GitHub officiel PANNs](https://github.com/qiuqiangkong/audioset_tagging_cnn) |
| **Fichier du modèle PANNs** | Les réglages déjà appris, appelés « poids » : fichier `Cnn14_mAP=0.431.pth` | [Téléchargement officiel sur Zenodo](https://zenodo.org/records/3987831) |
| **AudioSet, de Google** | Grande collection de sons qui a servi à entraîner PANNs avant notre projet | [Site officiel AudioSet](https://research.google.com/audioset/) |
| **CatMeows** | 440 sons de 21 chats, utilisés pour les premiers essais de classification du projet | [Dataset et conditions sur Zenodo](https://zenodo.org/records/4008297) |
| **Vos propres enregistrements** | Les exemples nécessaires pour adapter l'expérience à votre chat et à vos catégories | Créés avec l'application ; ils restent privés, hors de ce GitHub |

Pour comprendre le travail des auteurs : [article scientifique PANNs](https://arxiv.org/abs/1912.10211).
Pour les versions, les outils et les conditions d'utilisation :
[ressources détaillées](docs/ressources.md) et [notices tierces](THIRD_PARTY_NOTICES.md).

**Vous n'avez rien de tout cela à télécharger pour commencer à enregistrer.**
La collecte fonctionne sans modèle et sans carte graphique dédiée.
AudioSet n'a pas besoin d'être téléchargé dans ce projet. CatMeows est
facultatif, pour reproduire les essais publics.

## Comment ça fonctionne, simplement ?

Oui, c'est du **machine learning**, c'est-à-dire de l'apprentissage à partir
d'exemples. Ici, on prépare un apprentissage **supervisé** : une personne
associe une catégorie à chaque son, selon ce qu'elle a observé.

1. **Vous enregistrez.** Le téléphone capture une vocalisation.
2. **Vous ajoutez du contexte.** Par exemple : le chat miaulait devant la
   porte et a demandé à passer. Vous choisissez la catégorie `porte`.
   Si vous ne savez pas, vous choisissez `incertain`.
3. **On réutilise un modèle audio existant.** PANNs transforme le son en une
   liste de nombres qui représente ses caractéristiques acoustiques.
   Réutiliser ce qu'un modèle a déjà appris s'appelle le **transfer learning**,
   ou apprentissage par transfert.
4. **Un petit modèle apprend vos catégories.** Dans le programme actuel,
   PANNs reste inchangé ; une régression logistique — un outil qui classe
   des exemples — apprend à relier ces caractéristiques à vos annotations.
5. **On vérifie sur des sons non utilisés pour apprendre.** Les journées
   de test sont séparées des journées d'apprentissage pour évaluer si le
   modèle reconnaît autre chose que les scènes déjà enregistrées.

### Pourquoi cela pourrait marcher sur de nouveaux miaulements ?

L'idée n'est pas de retrouver exactement le même fichier audio. Le modèle
apprend des régularités dans les caractéristiques des exemples. Il peut
ensuite appliquer ce qu'il a appris à un nouveau son, même s'il n'est pas
identique aux précédents. Cette capacité s'appelle la **généralisation**.

Elle n'est pas garantie : des contextes peuvent produire des sons très
semblables, et le modèle peut retenir un bruit de fond plutôt que la
vocalisation. C'est pourquoi on varie les journées et les situations, puis
on mesure les erreurs sur de nouveaux exemples.

**Enregistrer davantage ne réentraîne pas automatiquement l'IA.**
L'amélioration se fait par cycles : collecter → corriger les annotations →
lancer un nouvel entraînement → vérifier sur des données non vues.
Un gain est possible, pas assuré. Il n'est pas nécessaire d'attendre
exactement un an, et un modèle pour votre chat n'est pas automatiquement
fiable pour celui du voisin.

Pour les curieux : [comment ça marche de bout en bout](docs/comment-ca-marche.md).
Pour faire l'expérience : [tutoriel de collecte et d'apprentissage](docs/tutoriel.md).

## Pour utiliser l'application et enregistrer votre chat

Vous aurez besoin d'un téléphone avec microphone, d'un ordinateur et
d'une connexion Internet. L'installation se prépare sur **l'ordinateur**.

Le téléphone affiche les boutons et enregistre. Un programme lancé sur
l'ordinateur reçoit les sons et les conserve : c'est ce qu'on appelle le
**serveur**. Faire tourner ce programme pour rendre l'app utilisable,
c'est l'**héberger**.

Pour ouvrir l'app du PC sur le téléphone, on utilise un outil nommé **ngrok** :
il crée une adresse Internet sécurisée qui relaie la connexion vers votre
ordinateur. Vous n'avez pas besoin de savoir le configurer à l'avance :
[le guide vous accompagne depuis le début](docs/hebergement.md).

L'application s'ouvre dans Safari ou Chrome et peut être ajoutée à l'écran
d'accueil. On appelle cela une **application web progressive**, ou PWA :
pas besoin de passer par un magasin d'applications.

**Avec la version actuelle, l'ordinateur doit rester allumé pour recevoir
les enregistrements.** Une version hébergée chez un prestataire, comme
Vercel ou Netlify, pourrait s'en passer après adaptation du stockage.
Cette variante n'est pas encore construite ; le
[guide d'hébergement](docs/hebergement.md) distingue les deux possibilités.

## Ce qui fonctionne aujourd'hui et ce qui reste à faire

| Vous pouvez déjà… | Ce qui n'est pas encore disponible dans l'app… |
|---|---|
| Enregistrer, réécouter et corriger les catégories | Une prédiction personnelle validée en direct |
| Choisir le nom et les catégories de votre chat | Un niveau de confiance calibré pour dire « je ne sais pas » |
| Sauvegarder et exporter vos données privées | Une version cloud autonome prête à déployer |
| Lancer les scripts d'entraînement et d'évaluation quand les données le permettent | Une traduction de phrases ou une communication humain → chat |

PANNs a été essayé sur CatMeows, en comparaison avec un petit réseau créé
pour le projet. Ces résultats sont [documentés](docs/baseline.md), mais
**ils ne prouvent pas la performance sur votre chat**. Aucun modèle
personnel validé n'est fourni avec ce dépôt.

### Quand on ne sait pas, on ne devine pas

- `autre` : une vocalise identifiable hors catégories, par exemple un
  trille ; elle peut servir d'exemple atypique si l'annotation est vérifiée.
- `incertain` : un miaulement au contexte inconnu ; il reste à part et
  **n'est pas utilisé pour entraîner le modèle** tant qu'il n'est pas ré-étiqueté.

Les « 30+ enregistrements par catégorie » sont un repère, pas une garantie
de réussite. N'incommodez pas le chat pour obtenir des sons. Ce projet ne
remplace pas un avis vétérinaire. Vos observations indiquent un contexte,
pas une certitude sur ce que l'animal pense.

## Les guides, selon votre besoin

- [Installer l'application sans savoir programmer](docs/installation.md).
- [La rendre accessible sur votre téléphone pour enregistrer votre chat](docs/hebergement.md).
- [Choisir le nom et les catégories de votre chat](docs/personnalisation.md).
- [Comprendre la technologie et les nouveaux miaulements](docs/comment-ca-marche.md).
- [Apprendre à collecter, annoter et évaluer](docs/tutoriel.md).
- [Retrouver les modèles, datasets et outils utilisés](docs/ressources.md).
- [Enregistrer et corriger au quotidien](docs/collecte.md) · [résoudre un problème](docs/depannage.md).
- [Recréer l'app avec un prompt](PROMPT_APP.md) · [se faire accompagner pour l'installer](INSTALL_WITH_AI.md).

## Pour les personnes qui veulent explorer le code

L'interface est écrite en HTML et JavaScript ; le serveur en Python avec
FastAPI. PyTorch fait fonctionner PANNs et scikit-learn entraîne le petit
classifieur. Les [ressources détaillées](docs/ressources.md) expliquent ces rôles.

```text
collecte/                  Interface mobile et serveur de collecte
core/initialiser.py        Configuration privée et génération de la clé
core/diagnostic.py         Vérifications locales sans afficher de secret
training/                  Apprentissage et évaluation
inference/                 Inférence historique CatMeows, pas l'app personnelle
docs/                      Guides, sources et résultats
tests/                     Vérifications avec sons synthétiques
```

[Protocole technique](docs/apprentissage.md) · [Contribuer et tester](CONTRIBUTING.md) ·
[Confidentialité](docs/confidentialite.md) · [Sécurité](SECURITY.md).

Le code public ne contient ni votre clé, ni vos audios, ni vos annotations.
Chaque personne crée sa propre installation : **un dossier de projet = un chat**.
