# Installer l'application pour enregistrer votre chat

**À la fin de ce guide**, vous aurez votre propre application de collecte :
vous pourrez enregistrer, réécouter et classer les sons de votre chat.
Elle ne prédit pas encore leur contexte en direct.

Vous n'avez pas besoin de savoir programmer. Les commandes ci-dessous sont
à copier une par une ; chaque étape indique ce que vous devez obtenir.

## Avant de commencer : de quoi avez-vous besoin ?

- Un **ordinateur** connecté à Internet, où seront conservés les sons.
- Votre **téléphone avec microphone**, pour enregistrer votre chat.
- De la place sur le disque de l'ordinateur pour les enregistrements.
- Un navigateur web : par exemple Safari, Chrome ou Edge.

Le téléphone sert d'enregistreur. Le programme sur l'ordinateur reçoit et
sauvegarde les fichiers : on l'appelle un **serveur**. Il doit rester allumé
pendant que vous utilisez cette version de l'application.

Aucun abonnement à une IA, aucune clé d'API d'IA et aucune carte graphique
spéciale ne sont nécessaires pour **collecter**. L'entraînement du modèle
viendra plus tard. Ne téléchargez ni PANNs ni les datasets pour cette première étape.

**Vous avez déjà une installation qui fonctionne ?** Ne remplacez ni son
dossier ni sa configuration. Passez à l'étape 3 pour la relancer.
N'installez pas de nouvelles dépendances pendant que votre serveur tourne.

## 1. Préparer l'ordinateur

### Comprendre les deux outils nécessaires

**Python** est le langage dans lequel le programme de collecte est écrit.
**uv** est l'outil qui installe la bonne version de Python et les petits
programmes dont le projet a besoin. Ces derniers s'appellent des *dépendances*.

Un **terminal** est une fenêtre où l'on écrit des commandes. Ce n'est pas
un fichier du projet et il ne faut pas coller les commandes dans le navigateur.

### Sur Windows

1. Dans le menu Démarrer, cherchez **PowerShell** et ouvrez-le.
2. Pour installer uv, vous pouvez utiliser cette commande si Windows dispose de WinGet :

   ```powershell
   winget install --id=astral-sh.uv -e
   ```

3. Si `winget` n'est pas reconnu, utilisez les instructions **Windows** du
   [guide officiel d'installation de uv](https://docs.astral.sh/uv/getting-started/installation/).
   N'utilisez pas les commandes macOS/Linux par erreur.
4. Après l'installation, fermez et rouvrez PowerShell.
5. Tapez `uv --version`, puis appuyez sur **Entrée**.

**Résultat attendu :** une ligne donnant la version de uv. Si la commande
n'est pas reconnue, arrêtez-vous ici et consultez [le dépannage](depannage.md).

### Sur macOS ou Linux

Ouvrez l'application **Terminal**, puis suivez la partie correspondant à
votre système dans le même [guide uv](https://docs.astral.sh/uv/getting-started/installation/).
Rouvrez le terminal et vérifiez avec `uv --version`.

Le projet demande Python 3.13 ; uv peut le télécharger automatiquement à
l'étape suivante. Vous n'avez pas besoin d'installer plusieurs versions à la main.
Les tests automatiques de collecte passent sous Windows, macOS et Linux ;
cela ne signifie pas que tous les microphones et navigateurs ont été testés.

## 2. Créer une installation personnelle

### 2a. Télécharger les fichiers du projet

Le mot **dépôt** désigne simplement le dossier de code partagé sur GitHub.

1. Sur l'ordinateur, ouvrez [la page du projet](https://github.com/sosoj92/trad-chat).
2. Cliquez sur le bouton **Code**, puis sur **Download ZIP**.
3. Décompressez le fichier téléchargé : sous Windows, clic droit → **Extraire tout**.
4. Ouvrez le dossier extrait. Il s'appelle généralement `trad-chat-main`.
   Vous devez y voir `README.md`, `pyproject.toml` et `config.example.yaml`.
   Si vous ne voyez qu'un autre dossier, ouvrez aussi ce dossier.

**Ne travaillez pas à l'intérieur du fichier ZIP.** Gardez le dossier extrait
à un endroit que vous retrouverez facilement. Aucun compte GitHub n'est
nécessaire pour télécharger le code public.

Si vous connaissez déjà Git, vous pouvez le cloner à la place du ZIP.
Cloner signifie télécharger une copie que Git pourra ensuite mettre à jour :

```bash
git clone https://github.com/sosoj92/trad-chat.git
cd trad-chat
```

Choisissez **une seule** des deux méthodes. Git n'est pas nécessaire si vous utilisez le ZIP.

### 2b. Ouvrir un terminal dans le bon dossier

**Windows :** dans l'Explorateur de fichiers, ouvrez le dossier qui contient
`README.md`, cliquez dans la barre d'adresse, tapez `powershell`, puis Entrée.
La fenêtre s'ouvre dans ce dossier.

**macOS/Linux :** dans le Terminal, tapez `cd ` avec un espace, puis
glissez le dossier du projet dans la fenêtre pour insérer son chemin ;
appuyez sur Entrée. Si votre gestionnaire de fichiers propose « Ouvrir dans
un terminal », cette option convient aussi.

Vérifiez le contenu avec :

```bash
ls
```

**Résultat attendu :** la liste contient notamment `README.md` et
`pyproject.toml`. Si ce n'est pas le cas, revenez au dossier extrait :
les commandes suivantes doivent être lancées depuis cette *racine du projet*.

Dans les blocs ci-dessous, copiez uniquement la commande, sans les lignes
de délimitation ni le mot `bash` ou `powershell`. Appuyez sur Entrée
et attendez la fin avant de passer à la suivante.

### 2c. Installer ce qui permet à l'app de fonctionner

```bash
uv sync --locked --group collecte
```

Cette commande prépare l'environnement Python du projet dans un dossier
`.venv`. Le premier lancement télécharge des logiciels : cela peut prendre
du temps. Elle ne télécharge ni modèle d'IA ni sons de chats.

**Résultat attendu :** l'installation se termine sans erreur et vous pouvez
taper une nouvelle commande. Ne poursuivez pas si une erreur reste affichée.

### 2d. Donner un nom à votre chat et créer votre clé

```bash
uv run --no-sync python -m core.initialiser --nom-chat "Moka"
```

Remplacez `Moka` par le nom de votre chat, en gardant les guillemets.
La commande crée `config.yaml`, le fichier de **vos réglages privés**,
et y enregistre une clé aléatoire. Cette clé est le mot de passe de votre app.

**Résultat attendu :** « Configuration privée créée ». Si le fichier existe
déjà, le programme dit qu'il n'a rien changé : il protège vos réglages.
Ne supprimez pas ce fichier pour passer outre. Le fichier
`config.example.yaml` est seulement un modèle public, pas votre configuration.

### 2e. Vérifier avant de démarrer

```bash
uv run --no-sync python -m core.diagnostic
```

Le *diagnostic* vérifie l'installation sans activer le micro ni afficher la clé.

**Résultat attendu :** des lignes `[OK]`. Une ligne `[INFO]` sur un port
occupé peut signifier que l'app tourne déjà. Ne fermez pas un autre programme
au hasard. Une ligne `[ERREUR]` doit être résolue avant la suite :
consultez [le dépannage](depannage.md).

## 3. Tester sur l'ordinateur

### 3a. Lancer le programme qui recevra les sons

Dans le terminal ouvert dans le projet :

```bash
uv run --no-sync python -m collecte.serveur
```

**Cette fois, la commande doit continuer à tourner.** Une fenêtre qui reste
occupée n'est pas une panne : le programme attend les connexions.
Laissez-la ouverte.

Sur **l'ordinateur**, ouvrez votre navigateur et entrez :
[http://127.0.0.1:8771](http://127.0.0.1:8771).

`127.0.0.1` signifie « cet ordinateur ». `8771` est le *port*, un numéro
qui permet de joindre le bon programme. Sur le téléphone, cette même
adresse ne désigne pas votre PC. Nous créerons son adresse Internet à l'étape 4.

**Résultat attendu :** la page de collecte et le champ « Clé de connexion ».

### 3b. Retrouver la clé et se connecter

Ouvrez **un deuxième terminal dans le même dossier**, comme à l'étape 2b.
Ne fermez pas le premier. Hors enregistrement vidéo ou partage d'écran, lancez :

```bash
uv run --no-sync python -m core.initialiser --afficher-cle
```

Copiez la clé affichée et collez-la dans « Clé de connexion » sur la page de
l'application. Ne la mettez pas dans GitHub, un commentaire ou une vidéo.

**Résultat attendu :** vous pouvez accéder à l'app et le nom de votre chat
apparaît. Pour changer les catégories plus tard, suivez
[la personnalisation](personnalisation.md) ; ce n'est pas nécessaire pour ce premier essai.

### 3c. Vérifier qu'un enregistrement est vraiment sauvegardé

1. Choisissez d'activer le microphone et autorisez-le dans le navigateur.
2. Enregistrez quelques secondes de **votre propre voix**, puis arrêtez.
   Il n'est pas nécessaire de faire miauler votre chat pour tester.
3. Réécoutez et choisissez le type **Bruit / non-vocalise**.
4. Enregistrez ce clip dans une catégorie : le type non-vocalise le maintient
   hors du dataset d'entraînement, même si vous choisissez `autre`.
5. Rechargez la page et retrouvez le clip dans « Derniers enregistrements ».
6. Réécoutez-le puis mettez cet essai à la corbeille.

**Résultat attendu :** le son reste disponible après rechargement.
Cela vérifie la sauvegarde, pas seulement l'affichage des boutons.

## 4. Ouvrir sur le téléphone

Pour que votre téléphone puisse joindre le programme sur l'ordinateur,
il lui faut une adresse accessible et sécurisée.

Nous allons utiliser **ngrok**, un service qui crée une adresse Internet
reliée à votre programme local. Cette liaison est appelée un **tunnel** :
le service relaie les demandes et les fichiers entre le téléphone et le PC.
L'adresse commence par **HTTPS**, ce qui chiffre le transport et permet
au navigateur mobile d'utiliser le microphone avec votre permission.

👉 Continuez avec [le guide pour rendre l'application accessible sur votre
téléphone](hebergement.md). Il explique le compte ngrok, la différence entre
ses clés et celle de l'app, l'adresse à ouvrir et l'ajout à l'écran d'accueil.

Le guide explique également ce qu'il faudrait adapter pour que l'app
fonctionne sans ordinateur allumé, chez un hébergeur comme Vercel ou Netlify.
Ce deuxième fonctionnement n'est pas encore prêt dans ce dépôt.

## 5. Au quotidien

Rouvrez un terminal dans le dossier du projet, puis lancez :

```bash
uv run --no-sync python -m collecte.serveur
```

Laissez ce terminal ouvert. Dans un autre, relancez la liaison avec le téléphone :

```bash
ngrok http 8771
```

Ouvrez l'adresse HTTPS affichée, ou votre raccourci si son adresse est toujours
la bonne. Il ne faut **pas** réinstaller les logiciels ni créer une nouvelle
clé à chaque utilisation.

Pour arrêter : appuyez sur `Ctrl+C` dans **le terminal du programme concerné**.
Fermer le serveur ou mettre le PC en veille empêche de recevoir les enregistrements.
Actualiser le téléphone ne relance pas le PC.

Pour la suite : [enregistrer et corriger ses annotations](collecte.md),
[sauvegarder ses données](collecte.md) et [dépanner un problème](depannage.md).

Le réglage `--no-sync` utilise les logiciels déjà installés sans les changer.
Avant une mise à jour des dépendances, sauvegardez vos données et arrêtez
**votre** serveur. Ne lancez pas `uv sync` pendant qu'il utilise ce même environnement.

## 6. Facultatif : préparer le machine learning

Vous pouvez vous arrêter avant cette section et utiliser la collecte normalement.
La suite concerne l'apprentissage du modèle, pas l'installation sur le téléphone.
Lisez d'abord [l'explication simple du fonctionnement](comment-ca-marche.md)
et [le tutoriel pratique](tutoriel.md).

Cette étape télécharge des logiciels beaucoup plus lourds. **CPU** veut dire
processeur de l'ordinateur ; **GPU** désigne la carte graphique, qui peut
accélérer certains calculs. Le choix proposé par défaut est le CPU : aucun
calcul ne part automatiquement chez un hébergeur.

Serveur arrêté, depuis la racine :

```bash
uv sync --locked --group collecte --group training --group transfer --extra cpu
uv run --no-sync python -m core.diagnostic --ml
uv run --no-sync python -m training.entrainement_mon_chat --verifier
```

Sans données suffisantes, « Collecte insuffisante pour ce protocole » est
normal. `--verifier` ne télécharge aucun modèle et n'entraîne rien.

Pour extraire les caractéristiques audio, téléchargez manuellement le fichier
**`Cnn14_mAP=0.431.pth`** depuis les
[poids officiels PANNs sur Zenodo](https://zenodo.org/records/3987831).
Créez le dossier `models/panns` puis placez ce fichier dedans, sans le renommer.
La taille est de l'ordre de 327 Mo. Ne prenez pas un autre fichier de poids au nom
ressemblant. Les poids et modèles sérialisés ne doivent venir que de sources
de confiance : leur chargement peut exécuter du code.

Le téléchargement de CatMeows est **facultatif** et indépendant : il sert à
reproduire les premiers essais publics, pas à faire fonctionner votre collecte.
Voir [les ressources et leurs conditions](ressources.md).

### Variante NVIDIA

Sur Windows/Linux x86-64 avec une carte et un pilote compatibles CUDA 12.4,
utilisez à la place de la commande CPU :

```bash
uv sync --locked --group collecte --group training --group transfer --extra cu124
uv run --no-sync python -m core.diagnostic --ml
```

Ne combinez pas `--extra cpu` et `--extra cu124`. La résolution CUDA conserve
PyTorch 2.6 ; l'environnement CPU est verrouillé séparément dans `uv.lock`.
Ne présumez pas que les deux donnent des résultats bit à bit identiques.
Sur Mac, utilisez l'option CPU : l'accélération Apple MPS n'est pas câblée
dans le script personnel. Si votre plateforme n'a pas de paquet compatible,
ne modifiez pas `uv.lock` au hasard : gardez la collecte et signalez l'environnement
sans publier vos données. Explication des index :
[documentation uv / PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/).

Ensuite : [commandes d'évaluation personnelle](apprentissage.md#commandes).
Cela ne branche pas automatiquement un modèle dans l'app.
