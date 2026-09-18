# Dépannage sans perdre ses données

Commence par `uv run --no-sync python -m core.diagnostic` depuis la racine.
Le diagnostic n'affiche pas ta clé et ne lance ni micro ni tunnel.

## `uv` ou `git` n'est pas reconnu

Termine l'installation depuis les liens du [guide](installation.md), puis
ferme et rouvre le terminal. Vérifie `uv --version` et `git --version`.
N'efface pas tes données pour résoudre un problème de commande introuvable.

## Configuration absente, invalide ou clé d'exemple

Pour une installation neuve :

```bash
uv run --no-sync python -m core.initialiser --nom-chat Moka
```

Si tu avais copié le modèle à la main, l'initialisation ne l'écrasera pas.
Dans `config.yaml`, remplace seulement `collecte.token` par une clé générée
localement avec `uv run --no-sync python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Fais-le hors vidéo. Ne supprime pas le fichier complet et ne change pas les
chemins si cette installation contient déjà des enregistrements.

Une clé trop courte ou la valeur publique d'exemple empêche le démarrage.
Pour une erreur YAML, vérifie l'indentation avec des espaces et compare les
noms des champs au modèle. Ne publie jamais le contenu complet de ta config
ni une erreur qui en reproduit une ligne privée.

## Token invalide / erreur 401

Vérifie que tu ouvres la bonne installation et la bonne adresse actuelle.
Lis la clé de **ce** dossier avec `core.initialiser --afficher-cle`, puis
ressaisis-la dans l'app. Le navigateur et le raccourci installé peuvent avoir
des mémoires séparées ; une nouvelle adresse peut demander à nouveau la clé.
Ne désactive pas l'authentification pour résoudre le problème.

## Erreur ngrok / site hors ligne

1. Sur le PC, vérifie d'abord `http://127.0.0.1:8771`.
2. Si le serveur est arrêté, relance-le depuis le dossier du projet.
3. Vérifie le terminal de **ton** tunnel et son adresse HTTPS actuelle.
4. Ouvre cette adresse sur le téléphone ; remplace un ancien raccourci si nécessaire.

Une erreur de tunnel n'est pas corrigée par un simple rafraîchissement sur
le téléphone. Si ngrok indique qu'un autre tunnel utilise déjà les ressources
de ton compte, ne le coupe pas à l'aveugle : identifie d'abord l'autre application.

## Port déjà occupé

Ton app est peut-être déjà ouverte. Sinon choisis un autre port libre dans
`collecte.port`, relance ce serveur et adapte l'adresse et la commande ngrok.
Le diagnostic n'arrête aucun processus. Évite les commandes qui tuent tous
les processus Python ou tous les tunnels.

## Le micro ne s'active pas / s'arrête sur téléphone

Ouvre l'app en HTTPS, autorise le microphone dans le navigateur et garde la
page au premier plan. Une IP locale en HTTP n'est pas suffisante. L'arrêt
en arrière-plan est prévu ; cette PWA n'est pas un enregistreur permanent.
Réessaie dans le navigateur avant de réinstaller un raccourci.

## Des clips ne comptent pas pour l'entraînement

`incertain`, « À vérifier », un bruit non félin, un fichier absent ou un label
retiré sont exclus. Le nombre total n'est pas le nombre admissible. Regarde
les filtres et détails avant de changer une annotation. Ne confirme pas des
clips uniquement pour atteindre un quota. Voir [les règles exactes](apprentissage.md).

## L'entraînement refuse de commencer

Avec `--verifier`, il faut au moins deux catégories admissibles et assez de
journées par catégorie pour **tous** les découpages internes et externes.
Une catégorie très rare peut empêcher la validation. Ce refus protège
l'évaluation ; ce n'est pas une invitation à mélanger les journées.

Si les poids PANNs sont absents, suis [l'installation ML](installation.md).
La collecte fonctionne sans eux. Si CUDA manque, le parcours CPU est possible,
mais l'extraction peut être plus lente. Ne change pas d'environnement pendant
que le serveur tourne.

## Demander de l'aide

Précise ton système, la commande et un message d'erreur **expurgé**. Ne joins
ni config réelle, audio domestique, manifest, export, nom privé, chemin de
profil utilisateur ou URL contenant une clé. Utilise un exemple synthétique.
Consulte aussi [la confidentialité](confidentialite.md).
