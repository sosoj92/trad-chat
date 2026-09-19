# Installer sa propre application

Objectif : obtenir une app de collecte privée, pas encore une app qui prédit
le contexte des miaulements. Aucune clé d'API d'IA n'est nécessaire pour la
collecte. Un fournisseur de tunnel peut avoir ses propres conditions et quotas.

## 1. Préparer l'ordinateur

- Installe [Git](https://git-scm.com/downloads).
- Installe [uv en suivant sa documentation officielle](https://docs.astral.sh/uv/getting-started/installation/).
- Rouvre le terminal après installation. Sous Windows, utilise **PowerShell**.
- Vérifie `git --version` et `uv --version`.

Python 3.13 est fixé dans `.python-version`. uv peut le télécharger ; une
connexion Internet est donc nécessaire à l'installation. Ne télécharge pas
de GPU/CUDA ou de dataset pour simplement enregistrer des sons.

Le parcours local est vérifié sous Windows. La collecte utilise des
dépendances multiplateformes, mais cela ne signifie pas que tous les micros,
navigateurs ou environnements macOS/Linux ont été testés sur matériel réel.

## 2. Créer une installation personnelle

Exécute ces commandes une par une :

```bash
git clone https://github.com/sosoj92/trad-chat.git
cd trad-chat
uv sync --locked --group collecte
uv run --no-sync python -m core.initialiser --nom-chat Moka
uv run --no-sync python -m core.diagnostic
```

Un *clone* copie le code sur ton ordinateur. Pas besoin de compte GitHub
pour cloner un dépôt public. Pour proposer des modifications, consulte
[CONTRIBUTING](../CONTRIBUTING.md). L'option GitHub « Download ZIP » fonctionne
aussi : décompresse le dossier, ouvre un terminal dedans et commence à `uv sync`.

Résultat attendu : une configuration créée, puis des lignes `[OK]`. Un port
occupé produit `[INFO]` : le diagnostic ne coupe aucun service.

`config.yaml` est ta configuration **privée** ; `config.example.yaml` est
seulement le modèle public. Ne copie pas une clé montrée dans une vidéo.
Relancer l'initialisation ne remplace ni la clé ni les réglages existants.
Pour changer des réglages existants, suis [personnalisation](personnalisation.md).

## 3. Tester sur l'ordinateur

Dans le premier terminal :

```bash
uv run --no-sync python -m collecte.serveur
```

Laisse-le ouvert. Visite [http://127.0.0.1:8771](http://127.0.0.1:8771).
`127.0.0.1` désigne **l'ordinateur qui ouvre la page**, pas un site public.
Sur le téléphone, cette adresse ne désigne donc pas ton PC.

Dans un deuxième terminal ouvert dans le dossier du projet :

```bash
uv run --no-sync python -m core.initialiser --afficher-cle
```

Hors capture vidéo, colle la clé affichée dans « Clé de connexion ».
Le nom du chat apparaît après connexion. Autorise le microphone uniquement
si tu veux faire un essai. Pour un test technique, un son de ta propre voix
suffit : classe-le en **Bruit / non-vocalise**, pas comme un exemple de chat.
Vérifie qu'il apparaît dans « Derniers enregistrements » et que tu peux le
réécouter, puis mets cet essai à la corbeille.

## 4. Ouvrir sur le téléphone

Le [tutoriel d'hébergement détaillé](hebergement.md) reprend ce parcours
et explique les différences avec Vercel/Netlify, leurs offres gratuites
et les adaptations nécessaires pour fonctionner PC éteint.

Le microphone d'une page web exige un contexte sécurisé : localhost convient
pour tester sur le PC, mais une IP du réseau en HTTP ne suffit pas pour le téléphone.

1. Installe et configure **ton** compte ngrok selon le
   [guide officiel](https://ngrok.com/docs/getting-started/).
2. Garde le serveur de collecte ouvert et lance dans un autre terminal :

   ```bash
   ngrok http 8771
   ```

3. Ouvre sur le téléphone l'adresse **HTTPS** indiquée par cette commande.
4. Renseigne ta clé de collecte dans le champ de connexion, puis autorise le micro.
5. Facultatif : Safari → Partager → Sur l'écran d'accueil sur iPhone ;
   utilise l'option d'installation/ajout à l'accueil de ton navigateur sur Android.

La clé de collecte et l'authtoken ngrok sont **deux secrets différents**.
Ne colle pas l'authtoken ngrok dans l'application. Le tunnel relaie le trafic
via un prestataire : les fichiers sont stockés sur ton PC, mais le transport
n'est pas entièrement local. Utilise cette option seulement si cela te convient.

Un seul processus de collecte doit accéder à un même dossier de données.
N'interromps pas le tunnel d'une autre application : si tu en as déjà un,
vérifie les possibilités de ton compte ou configure un autre accès HTTPS
pour ce projet.

Le PC, le serveur et le tunnel doivent rester actifs. Si l'adresse change,
ouvre la nouvelle et recrée éventuellement le raccourci. Une actualisation
sur le téléphone ne relance pas un serveur arrêté.

## 5. Au quotidien

- Pour relancer : `uv run --no-sync python -m collecte.serveur`, puis ton tunnel.
- Pour arrêter un serveur lancé dans ton terminal : `Ctrl+C` dans **ce** terminal.
- Pour vérifier l'installation : `uv run --no-sync python -m core.diagnostic`.
- Pour enregistrer et sauvegarder : [notice de collecte](collecte.md).
- En cas de problème : [dépannage](depannage.md).

`--no-sync` utilise l'environnement déjà installé sans le modifier. Garde-le
sur les commandes de lancement, surtout si tu as ajouté les dépendances ML.
Avant une mise à jour ou un changement de dépendances, arrête proprement
**ton serveur** et sauvegarde tes données. Ne lance pas `uv sync` pendant
qu'un serveur utilise cet environnement Python.

## 6. Facultatif : préparer le machine learning

Ne fais cette étape qu'après avoir commencé la collecte et lu le
[tutoriel](tutoriel.md). Elle télécharge des dépendances beaucoup plus lourdes.
Le choix de référence sans NVIDIA est **CPU**, pas un entraînement dans le cloud.

Serveur arrêté, depuis la racine :

```bash
uv sync --locked --group collecte --group training --group transfer --extra cpu
uv run --no-sync python -m core.diagnostic --ml
uv run --no-sync python -m training.entrainement_mon_chat --verifier
```

Sans données suffisantes, « Collecte insuffisante pour ce protocole » est
normal. `--verifier` ne télécharge aucun modèle et n'entraîne rien.

Pour extraire les caractéristiques audio, télécharge manuellement le fichier
**`Cnn14_mAP=0.431.pth`** depuis les
[poids officiels PANNs sur Zenodo](https://zenodo.org/records/3987831).
Crée le dossier `models/panns` puis place ce fichier dedans, sans le renommer.
La taille est de l'ordre de 327 Mo. Ne prends pas un autre checkpoint au nom
ressemblant. Les poids et modèles sérialisés ne doivent venir que de sources
de confiance : leur chargement peut exécuter du code.

Le téléchargement de CatMeows est **facultatif** et indépendant : il sert à
reproduire la baseline publique, pas à faire fonctionner ta collecte.
Voir [les ressources et leurs conditions](ressources.md).

### Variante NVIDIA

Sur Windows/Linux x86-64 avec une carte et un pilote compatibles CUDA 12.4,
utilise à la place de la commande CPU :

```bash
uv sync --locked --group collecte --group training --group transfer --extra cu124
uv run --no-sync python -m core.diagnostic --ml
```

Ne combine pas `--extra cpu` et `--extra cu124`. La résolution CUDA conserve
PyTorch 2.6 ; l'environnement CPU est verrouillé séparément dans `uv.lock`.
Ne présume pas que les deux donnent des résultats bit à bit identiques.
Sur Mac, utilise le parcours CPU : l'accélération Apple MPS n'est pas câblée
dans le script personnel. Si ta plateforme n'a pas de paquet compatible,
ne modifie pas le lock au hasard : garde la collecte et signale l'environnement
sans publier tes données. Explication des index :
[documentation uv / PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/).

Ensuite : [commandes d'évaluation personnelle](apprentissage.md#commandes).
Cela ne branche pas automatiquement un modèle dans l'app.
