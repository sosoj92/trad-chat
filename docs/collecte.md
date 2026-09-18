# Collecte des miaulements — Phase 2

Une PWA pour enregistrer le chat et annoter le **contexte observé**, pas un
traducteur déjà entraîné. Les fichiers restent sur ton PC.

## Lancer et ouvrir l'app

Depuis la racine du projet :

```powershell
uv sync --group collecte
uv run python -m collecte.serveur
```

Le port configuré est 8771. Lancer **un seul processus / worker** sur le dossier
de collecte. Le serveur utilise un verrou inter-threads, pas inter-processus.

Configurer une clé privée difficile à deviner dans `collecte.token` de
`config.yaml` (non versionné). Pour le téléphone, le microphone nécessite
une connexion HTTPS : une IP locale en HTTP ne suffit pas.

Dans un autre terminal :

```powershell
ngrok http 8771
```

Ouvrir l'URL HTTPS affichée par ngrok, puis renseigner **Clé de connexion**.
Un lien `https://TON-DOMAINE/?token=TA_CLE` fonctionne aussi. La clé est
mémorisée dans ce navigateur et retirée de l'adresse après lecture.
Ne pas partager le lien complet, la clé, les audios ou les exports privés.

Sur iPhone : Safari → Partager → Sur l'écran d'accueil. Le navigateur et
l'app installée peuvent demander chacun la clé. Le PC, le serveur et le
tunnel doivent rester actifs ; actualiser le téléphone ne répare pas un
tunnel arrêté. L'URL du tunnel peut changer.

## Enregistrer et annoter

1. **Activer le micro**. Un pré-tampon conserve jusqu'aux 5 dernières secondes.
2. **Enregistrer**, puis **Stop**. Le clip inclut le pré-tampon disponible.
   Limite : 120 secondes de capture, plus 5 secondes de pré-tampon.
3. Réécouter et préciser le **type de son** et la **certitude du contexte**.
   Dans les détails facultatifs : lieu au moment du son, minutes depuis le
   repas, observations au moment du son, observations après coup et note.
4. Toucher une catégorie pour sauvegarder le clip sur le PC.

La certitude vaut **À vérifier** par défaut. Cela permet de capturer vite
sans transformer une supposition en donnée d'entraînement. Les niveaux
**Probable** et **Confirmé par mes observations** rendent un clip admissible
si les autres critères le permettent ; cela ne prouve pas l'intention du chat.

Les alertes signalent un niveau très faible, une saturation possible ou un
clip très court. **Ce n'est pas un détecteur fiable de chat.** L'ancien
indicateur heuristique reste dans les métadonnées pour compatibilité, mais
n'est plus présenté comme une preuve.

Le microphone s'arrête lorsque l'app passe en arrière-plan. Aucun
enregistrement permanent en arrière-plan n'est promis. Après encodage, un
clip en attente est conservé dans IndexedDB si le navigateur le permet et
reproposé au rechargement. En cas d'échec réseau, réessayer l'envoi conserve
le même identifiant de capture et ne crée pas de doublon. Ce mécanisme ne
rend pas toute l'app utilisable hors ligne. Ne pas fermer la page pendant
l'enregistrement ou l'encodage.

## « autre » et « incertain » : deux rôles distincts

| Label | Sens | Utilisation |
|---|---|---|
| **autre** | Vocalise identifiable hors catégories : trille, feulement, gazouillis… | Classe atypique / négative par rapport aux contextes visés, admissible si vérifiée. |
| **incertain** | Miaulement normal mais contexte inconnu | **Quarantaine, exclue de l'entraînement**, jamais une classe apprise. |

Un clip incertain attend un ré-étiquetage, ou peut être réservé à l'étude de
l'abstention / du seuil de confiance en Phase 4. **Des clips sans vérité
terrain ne suffisent pas à calibrer ou valider un seuil.** Il faudra aussi
des exemples vérifiés et un test indépendant.

La catégorie incertaine apparaît **grisée, à part**, sans compter dans les
objectifs. `incertain` est toujours exclu par défaut, même si la configuration
omet ce nom dans `entrainement.labels_exclus`.

Pour les sons du quotidien (vaisselle, télévision…), choisir **Bruit /
non-vocalise** comme type. Ils sont conservés pour un futur détecteur, mais
restent hors du classifieur de contextes, y compris si le label est `autre`.
`autre` seul signifie une vocalise identifiable atypique, pas tout bruit.

## Corriger en deux taps

Dans **Derniers enregistrements** :

1. Toucher le bouton du label `Incertain ✎`.
2. Toucher `Faim` : la correction est immédiatement sauvegardée.

Le fichier WAV ne bouge pas : **le manifest fait foi**, pas le nom du dossier.
La certitude ne change pas implicitement avec le label. Dans **Détails**,
préciser ce qui a été observé et, si approprié, passer à probable ou confirmé.

Les filtres retrouvent une catégorie, les clips à vérifier ou la corbeille.
Une suppression est logique et réversible via **Restaurer**.

## Choisir l'extrait utile

Dans **Détails → Choisir l'extrait utile**, saisir début et fin en secondes,
puis réécouter. Cela sauvegarde des bornes, **sans couper ni écraser l'original**.

L'entraînement applique ces bornes. Pour un intervalle de plus de 4 secondes,
il choisit ensuite la fenêtre la plus énergique ; sans bornes, il cherche
dans tout le clip, y compris à la fin. Un bruit fort peut gagner : ce n'est
pas une segmentation sémantique du miaulement. Les clips courts sont complétés
par des zéros jusqu'à 4 secondes.

## Compteurs et qualité de collecte

Les compteurs distinguent clips enregistrés, clips étiquetés utilisables et
nombre de journées représentées. Les clips à vérifier, les bruits, les sons
inconnus, les labels exclus, les suppressions et les clips invalides sont
hors dataset.

**Les anciens clips sans nouvelles annotations restent visibles et intacts,
mais doivent être vérifiés dans Détails avant d'entrer dans l'entraînement.**
Aucune certitude n'est inventée rétroactivement.

30 exemples par classe est un **repère**, pas une garantie de fiabilité.
Varier les journées, situations, pièces et distances au micro. Plusieurs
clips de la même scène ne valent pas autant de scènes indépendantes.
Ne pas provoquer de détresse pour obtenir une catégorie. L'app ne pose aucun
diagnostic et ne permet pas de conclure qu'un chat a mal.

## Données et sauvegardes

```text
data/mon_chat/
├── manifest.jsonl       # annotations, capture, extrait et historique
├── faim/ porte/ …       # WAV originaux, dossier du label INITIAL
├── .backups/            # manifest précédent avant chaque modification
└── .trash/              # anciens fichiers supprimés ; compatibilité
```

Chaque remplacement du manifest est atomique après sauvegarde de sa version
précédente. Les nouvelles suppressions ne déplacent pas les WAV.

- **Exporter le dataset étiqueté** : ZIP avec WAV originaux, JSONL, CSV et
  métadonnées d'export, filtrés avec les mêmes règles que le loader ML.
- **Sauvegarde complète** : tous les enregistrements du manifest courant,
  y compris quarantaine, corbeille et historique des annotations. Les anciens
  manifests de `.backups/` ne sont pas dans ce ZIP ; copier le dossier entier
  permet aussi de les sauvegarder.

Les fichiers manquants sont signalés dans `export.json`. Un WAV exporté est
l'original ; les bornes de sélection restent dans les métadonnées. Les notes
privées figurent dans les exports : ne pas les publier sans revue.

## Technique et apprentissage

- PCM WAV 16 bits, mono, 16 kHz, rééchantillonné dans le navigateur.
- Capture AudioWorklet si disponible, repli ScriptProcessor sinon.
- Date originale, jour local et identifiant de session conservés lors des
  corrections. Session renouvelée après 30 minutes d'écart ou changement de jour.
- Authentification requise sur les routes de données ; audios et exports non
  mis en cache par l'app.
- Routes : `/api/labels`, `/api/stats`, `/api/recents`, `/api/upload`,
  `/api/audio/{id}`, `/api/annotations/{id}`, `/api/relabel`,
  `/api/supprimer`, `/api/restaurer`, `/api/export`.

La collecte **ne lance pas d'entraînement automatiquement**. Voir
[apprentissage.md](apprentissage.md) pour le protocole supervisé, les
découpages par groupes, la recherche d'hyperparamètres et les limites.
