# Apprentissage personnel — préparation Phase 3

## Ce qui est implémenté

Un protocole **supervisé** : annotations humaines → encodeur audio gelé →
classifieur léger. Les corrections ne sont pas du reinforcement learning.
L'app collecte des données, mais ne réentraîne et ne déploie rien seule.

Point de départ : **PANNs CNN14 préentraîné sur AudioSet**, embeddings 2048-D,
puis StandardScaler et régression logistique. Le scaler et le classifieur
sont ajustés uniquement sur les sous-ensembles d'entraînement appropriés.

PANNs extrait sur CUDA si disponible, sinon CPU. La régression logistique,
la recherche d'hyperparamètres et les métriques tournent sur CPU. Les poids
PANNs existants sont réutilisés ; aucun téléchargement automatique ni appel
à une API Claude / LLM n'est ajouté par ce pipeline.

## Quelles données entrent dans le modèle ?

Exclusions par défaut communes à l'app, l'export et au loader :

- `incertain`, toujours, et les autres labels configurés comme exclus ;
- clips supprimés, labels non reconnus ;
- type différent de `vocalise` ou contexte `à vérifier` ;
- absence de date de capture exploitable ou audio explicitement invalide ;
- fichier audio absent ou hors du dossier du dataset.

Les clips `probable` et `confirmee` sont admissibles. Les anciens clips sans
type / certitude doivent être révisés ; on ne leur invente pas d'annotation.
`inclure_exclus=True` est réservé à l'inspection, jamais à l'entraînement.

Le label décrit un contexte supposé. Voir le chat aller à sa gamelle peut
étayer « faim », mais ne démontre pas ce qu'il avait l'intention de dire.

Le WAV est chargé à 32 kHz, puis les bornes d'extrait sont appliquées avant
la mise à longueur fixe de 4 secondes. Pour un long intervalle, la fenêtre la plus énergique est choisie
(pas forcément le chat). Les originaux ne sont jamais découpés sur disque.

## Comparaisons prévues dans le script

Les mêmes groupes et la même seed servent à trois évaluations :

1. **Audio seul** : embeddings de l'encodeur.
2. **Contexte seul** : lieu et minutes depuis le repas, avec indicateur de
   délai inconnu.
3. **Audio + contexte** : concaténation des deux.

Ces deux champs doivent représenter ce qui était disponible **au moment du
son**, pas une déduction rétrospective. Les observations après coup, notes,
certitudes, labels et identifiants n'entrent jamais comme variables
prédictives. Les textes libres restent uniquement des aides à l'annotation.

Le contexte seul sert de contrôle : si l'audio n'apporte aucun gain sur des
journées nouvelles, ne pas présenter le résultat comme une traduction du son.
Les futurs usages sans lieu / délai de repas devront utiliser l'audio seul
ou faire l'objet d'une évaluation spécifique des informations manquantes.

## Découpages et hyperparamètres

Pour le chat personnel, les groupes sont les **jours locaux de capture**.
Tous les clips d'une journée restent ensemble. Les sessions sont aussi
conservées dans les données pour l'audit. Éviter les séries qui traversent
minuit et ne jamais dupliquer un extrait entre deux jeux.

Validation croisée **imbriquée 3 × 3** par défaut : plis externes pour les
prédictions hors pli ; plis internes pour sélectionner `C` et la pondération
des classes. Petite grille de `C` : 0.0001, 0.001, 0.01, 0.1, 1. Ce choix est
un point de départ, pas une recherche universellement optimale.

Chaque découpage vérifie l'absence de groupes communs et la présence de toutes
les classes. Le script s'arrête avant entraînement si les groupes ne permettent
pas ce protocole. Trois journées par classe ne suffisent pas nécessairement :
les plis internes doivent aussi être faisables. Aucun repli automatique vers
un split aléatoire par clip ne masque le manque de données.

Rapports : F1 macro, accuracy, précision / rappel / F1 par classe, matrice de
confusion et résultats par pli. L'écart-type entre plis n'est pas un intervalle
de confiance. Après comparaison de plusieurs encodeurs, conserver un **jeu
final de futures journées** qui n'a servi ni au choix du modèle ni au seuil.
Ce jeu final et la calibration ne sont pas encore automatisés.

La CV du script historique CatMeows `training.transfer_panns` utilise aussi
des réglages internes et des groupes **par chat**. Les anciens résultats de
CV, calculés avec un `C` présélectionné, restent historiques et ne doivent pas
être présentés comme une nouvelle évaluation imbriquée.

## Commandes

Depuis la racine, avec les dépendances ML déjà installées selon le
[guide d'installation](installation.md#6-facultatif--préparer-le-machine-learning) :

```powershell
# Lecture seule : vérifier si le dataset permet les découpages
uv run --no-sync python -m training.entrainement_mon_chat --verifier

# Entraîner / évaluer explicitement lorsque la collecte est suffisante
uv run --no-sync python -m training.entrainement_mon_chat

# Évaluer un export décompressé dans un dossier distinct
uv run --no-sync python -m training.entrainement_mon_chat --data CHEMIN_DU_DATASET

# Tests : uniquement des données synthétiques dans des dossiers temporaires
uv run --no-sync python -m unittest discover -s tests -v
```

Les expériences sont écrites dans `models/personnel/experience_<date>/`
(privé, ignoré par Git). Un modèle audio final est réajusté après l'évaluation
et sauvegardé avec `deploiement=False`. Les modèles et audios existants ne
sont pas remplacés. Les résultats personnels peuvent révéler des habitudes :
ne pas publier les rapports bruts sans revue.

## Autres encodeurs : point d'extension, pas comparaison déjà faite

`--features AUTRE.npz --nom-encodeur NOM` permet de soumettre les embeddings
d'un autre encodeur **gelé** au même protocole. Le NPZ doit contenir :

- `X` : matrice numérique finie, une ligne par clip ;
- `ids` : identifiants dans l'ordre trié du loader ;
- `empreinte` : chaîne renvoyée par `empreinte(exemples)` pour ces originaux
  et ces bornes (également affichée par `--verifier` si les groupes sont valides).

L'empreinte protège l'alignement des clips, pas la validité scientifique de
l'encodeur. Documenter son checkpoint et son prétraitement ; ne pas lui fournir
des embeddings appris sur les tests externes. Perch / BEATs ne sont ni
téléchargés ni évalués par cette modification. Aucun « meilleur modèle » n'est
annoncé sans comparaison mesurée sur les données pertinentes.

## Ce qui reste en Phase 4

Détection fiable de vocalise, calibration sur données vérifiées, seuil
d'abstention (« je ne sais pas »), test final indépendant et inférence en
temps réel. `scores_max_non_calibres` est un score brut, pas une probabilité
garantie. Les clips incertains seuls ne constituent pas une vérité terrain
pour apprendre ce seuil. Pas de traduction de phrases ni de promesse de
communication bidirectionnelle avec le chat.
