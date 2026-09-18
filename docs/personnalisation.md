# Adapter le projet à son propre chat

Chaque personne installe le code chez elle. Aucune connexion à l'installation
de l'autrice, aucun audio privé et aucun modèle personnel ne sont nécessaires.

## Nouvelle installation

Après `uv sync --locked --group collecte` :

```bash
uv run --no-sync python -m core.initialiser --nom-chat "Moka" --categories faim porte jeu
```

Cela crée une clé aléatoire, configure le nom et les catégories et ajoute
automatiquement `autre` et `incertain`. Les identifiants doivent être uniques,
commencer par une lettre et contenir seulement `a-z`, `0-9` et `_` (40 caractères
maximum). Un nom de chat peut contenir des accents et espaces (1 à 60 caractères).

**Si `config.yaml` existe déjà, la commande ne change rien**, même avec de
nouvelles options. C'est une protection contre le remplacement accidentel
d'une configuration et de sa clé.

## Modifier une installation existante

Arrête ton serveur et ouvre **`config.yaml`**, pas `config.example.yaml`.
Modifie seulement les champs voulus ; conserve le reste du fichier :

```yaml
chat:
  nom: "Moka"

labels:
  - faim
  - porte
  - jeu
  - autre
  - incertain
```

Puis relance le diagnostic et le serveur :

```bash
uv run --no-sync python -m core.diagnostic
uv run --no-sync python -m collecte.serveur
```

Recharge la page après connexion. Le nom apparaît dans le titre, les
catégories dans les boutons. Ni le nom ni la clé ne sont intégrés aux
fichiers HTML publics. Le nom du raccourci PWA reste générique.

## Bien choisir les catégories

Commence avec peu de contextes que tu peux observer naturellement. Écris
une définition pour chacun dans tes notes privées : par exemple `porte` =
« vocalisation devant une porte, suivie d'une demande de passage observée ».
Ce n'est qu'une annotation de contexte, pas une preuve d'intention.

Conserve toujours :

- `autre` pour une vocalise identifiable hors catégories ;
- `incertain` pour un miaulement au contexte inconnu, **jamais appris comme classe**.

Les identifiants sont enregistrés dans les annotations. **Renommer ou retirer
un label ne ré-étiquette pas les anciens clips.** Ajoute le nouveau label,
relance, corrige les anciens clips dans l'app, vérifie les comptes puis
retire éventuellement l'ancien label. Fais d'abord une sauvegarde complète.
Un clip dont le label n'est plus reconnu est exclu de l'entraînement.

Les catégories configurées mais encore vides ne deviennent pas des classes
apprises : le classifieur personnel apprend les catégories admissibles
effectivement présentes. Il faut au moins deux catégories représentées et
assez de journées pour les découpages. Une catégorie `autre` rare peut aussi
empêcher l'évaluation : collecte davantage ou exclus-la **explicitement**
de l'expérience via `entrainement.labels_exclus`, en documentant ce choix.

## Deux chats ou deux applications ?

Le champ `chat.nom` est un nom d'affichage, **pas un système de profils**.
Le manifest actuel n'associe pas chaque clip à un identifiant de chat.
Ne remplace donc pas le nom pour mélanger deux chats dans le même dataset.

Pour un second chat, crée un second dossier de projet :

```bash
git clone https://github.com/sosoj92/trad-chat.git trad-chat-luna
cd trad-chat-luna
uv sync --locked --group collecte
uv run --no-sync python -m core.initialiser --nom-chat Luna --port 8772
```

Chaque dossier aura ses données, sa configuration et sa clé. Le second
serveur écoute alors sur `8772` ; adapte aussi le tunnel. Ne partage pas le
même dossier de données entre les deux installations.

## Ce qu'il vaut mieux laisser inchangé au début

Garde les chemins par défaut sous `data/`, `models/` et `logs/`, déjà exclus
de Git. Un chemin personnalisé ailleurs peut ne plus être protégé par le
`.gitignore` : vérifie toujours ce qui est suivi avant de publier.

Les sections `audio`, `augmentation` et la plupart des paramètres
`entrainement` servent à la **baseline historique CatMeows**. Les changer
ne modifie pas automatiquement l'expérience personnelle PANNs : celle-ci
utilise 32 kHz, des extraits de 4 s, des groupes par jour, une seed de 42 et
une grille propre dans le code. Voir [le protocole exact](apprentissage.md).
`temps_reel` et son seuil sont prévus pour une phase future,
pas une fonctionnalité active de la collecte.
