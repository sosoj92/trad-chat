# Du premier miaulement à une expérience de machine learning

Ce tutoriel utilise **Moka, un chat fictif**, pour les exemples. Il ne fournit
aucun enregistrement personnel. Tu peux apprendre la démarche même si les
résultats ne permettent finalement pas de reconnaître les contextes de ton chat.

## Étape 0 — Formuler une question qu'on peut tester

Une bonne question : « Est-ce que les vocalisations de Moka devant la porte
et près du repas présentent des différences utilisables sur de nouvelles journées ? »

Une affirmation qu'on ne peut pas déduire de ce projet : « Je sais traduire
exactement ce que pense mon chat. »

**À faire :** choisis deux ou trois catégories, définis ce qui te permet de
les annoter, puis [installe l'app](installation.md) et
[personnalise-la](personnalisation.md). Ne retarde pas les repas et ne provoque
ni isolement ni stress pour produire des exemples.

**Tu as réussi si :** l'application fonctionne et tu peux expliquer ce que
chaque catégorie signifie, ainsi que les cas où tu ne sais pas.

## Étape 1 — Construire des exemples, pas seulement accumuler des sons

Un exemple supervisé associe des données d'entrée à une étiquette humaine.
Ici : un extrait audio et, éventuellement, le contexte disponible au moment
du son → une catégorie annotée après observation.

Exemple fictif : tu enregistres un miaulement et choisis `incertain`. Vingt
secondes plus tard, Moka va à sa gamelle. Dans « Derniers enregistrements »,
touche son label puis `faim` : **deux taps** pour le ré-étiquetage. Dans les
détails, indique ce que tu as observé et ajuste la certitude si c'est justifié.
L'observation peut soutenir l'hypothèse « faim », pas la démontrer.

Le changement de label **ne confirme pas automatiquement** le contexte :
un clip toujours « À vérifier » reste exclu de l'entraînement. C'est volontaire.

| Champ | À quoi il sert | Entrée du modèle personnel ? |
|---|---|---|
| Audio et bornes de l'extrait | Son à analyser | Oui |
| Lieu et délai depuis le repas, au moment du son | Contexte disponible lors d'une future prédiction | Oui, dans les variantes avec contexte |
| Observation après coup, notes | Justifier et corriger l'annotation | Non |
| Label | Réponse humaine à apprendre | Cible, pas variable d'entrée |
| Certitude et type de son | Contrôler l'admissibilité | Non |
| Jour / session | Séparer et auditer les exemples | Groupement, pas variable d'entrée |

`autre` n'est pas une poubelle à annotations inconnues. C'est une vocalise
identifiable hors catégories. `incertain` reste une quarantaine séparée,
exclue même si tu oublies de la déclarer dans les exclusions de la config.

**Exercice :** réécoute quelques clips un autre jour. Est-ce que tu les
étiquetterais de la même manière sans te souvenir du moment ? Note les
ambiguïtés au lieu de forcer une catégorie.

## Étape 2 — Collecter de la diversité

Trente clips consécutifs de la même scène ne représentent pas trente
situations indépendantes. Le modèle pourrait retenir la télévision, la
pièce ou la distance du téléphone au lieu du son du chat.

Collecte au fil des situations normales, sur plusieurs jours, avec des
conditions variées pour **chaque** catégorie. Contrôle le nombre de clips
admissibles et le nombre de jours par classe dans l'application. Le repère
« 30+ / classe » ne garantit ni un split valide ni un modèle utile.

Pour un dataset utilisable, vérifie : son réellement félin, catégorie
cohérente, certitude au moins « Probable », dates exploitables et extrait
audible. La certitude humaine ne devient pas pour autant une vérité
scientifique sur l'intention du chat.

**À faire :** sauvegarde régulièrement en mode **sauvegarde complète**.
L'export d'entraînement n'inclut pas la quarantaine : ce n'est pas un backup
complet. Voir [collecte et sauvegardes](collecte.md).

## Étape 3 — Comprendre ce que le modèle apprend

Le point de départ personnel est **PANNs CNN14**, un réseau préentraîné sur
AudioSet pour l'analyse de sons. On garde son encodeur **gelé** : ses poids
ne changent pas dans cette expérience. Pour chaque extrait, il produit un
vecteur de 2 048 nombres, appelé *embedding*.

On ajuste ensuite un classifieur plus simple, une **régression logistique**,
qui apprend à séparer tes catégories à partir de ces vecteurs. Malgré son
nom, c'est ici un modèle de classification.

La chaîne personnelle est : rééchantillonnage en 32 kHz → bornes annotées →
fenêtre de 4 s (complétée si courte, fenêtre énergique si longue) → représentation
log-mel dans PANNs → embedding → standardisation → classifieur. Une fenêtre
énergique peut contenir une voix ou un choc : réécoute tes extraits.

C'est du **transfer learning supervisé**, pas du reinforcement learning.
Le transfert économise l'apprentissage de toutes les caractéristiques
acoustiques depuis zéro ; il ne garantit pas qu'elles soient adaptées à ton chat.
Tu n'as pas besoin d'attendre exactement un an : l'admissibilité et la diversité
du dataset déterminent quand une première évaluation est faisable.

## Étape 4 — Vérifier avant d'entraîner

Installe les dépendances facultatives en suivant
[l'installation ML](installation.md#6-facultatif--préparer-le-machine-learning),
puis lance :

```bash
uv run --no-sync python -m training.entrainement_mon_chat --verifier
```

Cette commande ne modifie pas la collecte et ne calcule pas d'embeddings.
Elle vérifie si les catégories présentes peuvent être réparties selon le
protocole. Un message « collecte insuffisante » signifie qu'il faut encore
collecter ou revoir les annotations, pas contourner la validation.

Le script emploie une **validation croisée imbriquée 3 × 3 par journées** :

- Les journées externes tenues à l'écart servent à mesurer les prédictions.
- À l'intérieur des journées d'entraînement, d'autres découpages sélectionnent
  la régularisation `C` et la pondération des classes par petite grille.
- Le scaler et les paramètres du classifieur sont appris uniquement dans
  les ensembles autorisés. Aucun clip d'une journée de test ne sert à ces réglages.

Toutes les classes présentes doivent apparaître dans chaque train et test.
Trois journées par catégorie ne suffisent donc pas forcément. Il n'y a pas
de bascule automatique vers un split aléatoire par clip lorsque ça échoue.

**Exercice :** si dix extraits d'une même scène se retrouvaient des deux côtés
du split, mesurerait-on la reconnaissance d'une nouvelle journée, ou celle
d'une scène déjà entendue ?

## Étape 5 — Lancer et lire l'expérience

Après téléchargement des poids officiels et vérification réussie :

```bash
uv run --no-sync python -m training.entrainement_mon_chat
```

Le script compare **audio seul**, **contexte seul**, puis **audio + contexte**.
Il enregistre un rapport privé dans `models/personnel/experience_<date>/rapport.json`
et un classifieur audio final marqué `deploiement=False`. L'app ne se met pas
à prédire automatiquement. L'extraction utilise CUDA si disponible, sinon
le CPU ; le classifieur et les métriques utilisent le CPU.

Lis les résultats ainsi :

- **Accuracy** : proportion totale de prédictions correctes. Trompeuse si une classe domine.
- **F1 macro** : moyenne des F1 de chaque classe, avec le même poids par classe.
- **Rappel par classe** : parmi les vrais exemples de cette classe, combien sont retrouvés ?
- **Précision par classe** : parmi les prédictions de cette classe, combien sont correctes ?
- **Matrice de confusion** : quelles catégories sont confondues ?
- **Résultats par pli** : le résultat tient-il sur plusieurs groupes de journées ?

Exemple **purement fictif** : si 90 clips sur 100 sont « faim », répondre
toujours « faim » donne 90 % d'accuracy, mais ne reconnaît aucun des 10 autres
clips. Un gros pourcentage seul ne suffit donc pas.

Si le contexte seul fait aussi bien, tu n'as pas démontré que le son apporte
quelque chose. Si l'audio semble meilleur, vérifie encore qu'il ne reconnaît
pas un bruit de fond associé à la catégorie. L'écart-type entre plis n'est
pas un intervalle de confiance ; les exemples restent peu nombreux.

## Étape 6 — Tester de vrais nouveaux miaulements

Une prédiction sur un nouveau son est possible parce que le classifieur
applique la séparation apprise à son nouvel embedding. Ce n'est pas une
recherche du même fichier dans une base. Il peut aussi se tromper, surtout
si le son ou la situation ne ressemblent pas aux exemples d'apprentissage.

Réserve de **futures journées indépendantes** qui n'ont servi ni au choix
des catégories, du modèle, des hyperparamètres, ni du seuil. Leur évaluation
finale et la calibration du seuil ne sont pas encore automatisées ici.
Ne présente pas `scores_max_non_calibres` comme des probabilités fiables
ou comme un taux garanti de compréhension.

La Phase 4 devra ajouter détection de vocalise, abstention « je ne sais pas »,
calibration sur données vérifiées et branchement de l'inférence personnelle.
Les clips `incertain` peuvent aider à explorer ce qui est inconnu ; sans
ré-étiquetage fiable, ils ne suffisent pas à calibrer ni évaluer un seuil.

## Pour expliquer ton expérience à quelqu'un

> « Je construis un petit dataset privé des vocalisations de mon chat,
> annoté selon ce que j'observe. Je teste si un modèle audio préentraîné
> permet de distinguer certains contextes sur des journées non vues.
> Ça ne traduit pas des phrases et je dois encore vérifier si ça marche. »

Pour aller plus loin : [protocole technique](apprentissage.md),
[expériences CatMeows](baseline.md), [sources officielles](ressources.md).
