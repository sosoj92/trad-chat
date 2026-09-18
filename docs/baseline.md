# Baseline CatMeows — Phase 1

But de la phase : **valider tout le pipeline ML** (données → features →
modèle → évaluation → inférence) sur un dataset public, *avant* de collecter
mes propres enregistrements. Ce n'est pas le modèle final — c'est un point de
référence honnête.

> **TL;DR** — 68 % d'accuracy / 59 % de F1 macro sur des chats **jamais vus**,
> 3 classes. Modeste mais réel : le pipeline tient, les 3 classes sont
> distinguées, et les erreurs sont surtout des hésitations peu confiantes.
> Le transfer learning a aussi été essayé, sans gain démontré ici (voir plus bas).

---

## 1. Dataset

**CatMeows** (Ntalampiras et al.) — 440 miaulements, 21 chats, 3 contextes
d'émission encodés dans le nom de fichier :

| Code | Classe (nom interne) | Contexte réel | Nb extraits |
|------|----------------------|---------------|------------:|
| `B`  | `brossage`           | pendant le brossage | 127 |
| `F`  | `attente_nourriture` | attente de nourriture | 92 |
| `I`  | `isolement`          | isolement en environnement inconnu | 221 |

Dataset **déséquilibré** : l'isolement représente la moitié des exemples.

### Téléchargement (Zenodo, public, sans compte)

Le dataset n'est pas versionné (`data/catmeows/` est gitignoré). Consulte
d'abord ses conditions sur la [fiche officielle](https://zenodo.org/records/4008297)
(usage scientifique / non commercial indiqué par les auteurs). Télécharge
`dataset.zip`, puis décompresse-le dans `data/catmeows/` avec l'explorateur
de fichiers de ton système. Le téléchargement n'est pas nécessaire pour
l'application de collecte personnelle.

Les 440 `.wav` atterrissent dans `data/catmeows/dataset/`. Le loader les
retrouve récursivement, aucune organisation manuelle n'est nécessaire.
*(Alternative : Kaggle `andrewmvd/cat-meow-classification`, mêmes fichiers.)*

---

## 2. Méthodologie

**Split par CHAT, pas par enregistrement.** C'est le point critique : si des
extraits d'un même chat se retrouvaient à la fois en entraînement et en test,
le modèle apprendrait à reconnaître *l'individu* (le timbre de sa voix) au
lieu de *l'intention* — une fuite de données qui gonflerait artificiellement
les scores. On utilise `StratifiedGroupKFold` (groupe = chat) pour garder
chaque chat entièrement dans un seul lot tout en équilibrant au mieux les
classes.

| Lot | Extraits | Chats | Détail |
|-----|---------:|------:|--------|
| train | 295 | 14 | tous les chats sauf ceux ci-dessous |
| val   | 73  | 4  | — |
| test  | 72  | 3  | BAC01, DAK01, JJX01 (jamais vus) |

**Prétraitement** (`core/audio.py`, partagé avec l'inférence) : 16 kHz mono →
rognage des silences → normalisation d'amplitude → durée fixe 4 s →
spectrogramme mel 64 bandes (`64 × 251`), standardisé (z-score, robuste au
volume).

**Augmentation** (train uniquement, à la volée, chaque augmentation avec
p = 0,5) : décalage temporel, léger pitch shift (±1 demi-ton), bruit gaussien,
SpecAugment (masquage de bandes fréquence/temps).

**Modèle** : petit CNN 2D « from scratch » (4 blocs conv → pooling global →
tête linéaire), **241 k paramètres**. Perte pondérée par l'inverse de la
fréquence des classes (contre le déséquilibre). Adam (lr 1e-3), early stopping
sur le F1 macro de validation.

---

## 3. Résultats (test — chats jamais vus)

**Accuracy 68,1 % · F1 macro 59,0 %**

| Classe | Précision | Rappel | F1 | Support |
|--------|----------:|-------:|----:|--------:|
| attente_nourriture | 0,50 | 0,31 | 0,38 | 16 |
| isolement          | 0,79 | 0,87 | 0,83 | 39 |
| brossage           | 0,53 | 0,59 | 0,56 | 17 |

Figures : `docs/baseline_confusion.png` (matrice de confusion),
`docs/baseline_courbes.png` (perte + F1 val), `docs/baseline_mal_classes.csv`
(23 exemples ratés, avec chemin audio pour les écouter).

### Ce qui marche / ce qui coince

- ✅ **isolement** bien reconnu (F1 0,83) — c'est la classe la plus fournie et
  la plus contrastée acoustiquement (miaulements longs et plaintifs).
- 🟡 **brossage** correct (0,56).
- 🔴 **attente_nourriture** faible (rappel 0,31) : souvent confondu avec
  isolement. Peu d'exemples (92) et acoustiquement proche.
- 📉 Les erreurs viennent en grande partie d'**un seul chat de test (BAC01)** :
  son « attente de nourriture » ressemble à de l'isolement pour le modèle. Avec
  seulement 3 chats de test, un individu atypique pèse lourd → estimation
  bruitée (voir §5).
- 🎯 **Les erreurs sont peu confiantes** (0,35–0,56). Le modèle hésite plus
  qu'il ne se trompe avec aplomb : un seuil de confiance (Phase 4) rangerait
  ces cas en « incertain » plutôt que de donner une réponse fausse.

---

## 4. Une leçon en passant : l'augmentation trop forte tue l'apprentissage

Premier run avec augmentation **systématique** (pitch shift + bruit +
SpecAugment à chaque exemple, chaque époque) :
→ modèle **dégénéré**, 57 % d'accuracy en prédisant quasi toujours
« isolement », `attente_nourriture` à **F1 = 0**. La perte d'entraînement
stagnait : le modèle n'arrivait même pas à apprendre le train.

En rendant chaque augmentation probabiliste (p = 0,5) et un peu plus légère :
→ **57 % → 68 %** d'accuracy, **36 % → 59 %** de F1 macro, les 3 classes
prédites. Sur un dataset minuscule, trop augmenter empêche d'apprendre.

---

## 5. Limites honnêtes & prochains leviers

**Limites**
- Test sur **3 chats seulement** → chiffre à ±plusieurs points près. Pour une
  estimation stable, une **validation croisée k-fold par chat** (prévue en
  Phase 3) serait plus fiable qu'un split unique.
- Le CNN **sous-apprend encore** un peu (perte train ~0,92) : petit modèle,
  petit dataset.
- Ces 3 classes CatMeows ne sont **pas** mes catégories finales — la Phase 3
  rebranchera le pipeline sur mes labels et mon chat.

**Leviers d'amélioration (par ordre d'intérêt)**
1. **Transfer learning** : ✅ essayé — voir §7. Aucun avantage démontré ici ;
   à évaluer sur les données personnelles en Phase 3.
2. **k-fold par chat** pour un score stable : ✅ voir §7 (variance énorme !).
3. Rééquilibrage plus fin / focal loss pour `attente_nourriture`.
4. **Fine-tuning** (dégel) du backbone PANNs, au-delà du simple linear probe.

---

## 6. Reproduire

```bash
uv sync --locked --group collecte --group training --extra cpu
# (télécharger le dataset : voir §1)
uv run --no-sync python -m training.dataset_catmeows   # vérifier l'index + le split
uv run --no-sync python -m training.entrainement       # entraîner + évaluer + sauver
uv run --no-sync python -m inference.predire un_miaou.wav   # tester l'inférence
```

Modèle produit : `models/baseline_catmeows_<date>_acc<XX>.pt` (embarque ses
classes et ses réglages audio, donc l'inférence est autonome).

---

## 7. Transfer learning — PANNs CNN14 (levier testé)

**Idée :** au lieu d'un CNN appris de zéro, réutiliser **CNN14 de PANNs**
(pré-entraîné sur AudioSet, ~2 M de sons) comme extracteur de features
(embedding 2048-D par clip), puis une tête légère (« linear probe »). Le
backbone est vendorisé (`training/panns_cnn14.py`) pour ne pas dépendre du
paquet `panns_inference` (fragile). Mêmes split par chat et seed que le CNN.

**Résultats (même split, test = 3 chats jamais vus)**

| Modèle | Accuracy | F1 macro |
|--------|---------:|---------:|
| CNN maison (from scratch) | 68,1 % | 59,0 % |
| PANNs CNN14 + linear probe | 65,3 % | 57,4 % |

**Résultat historique — CV 5-fold PAR CHAT non imbriquée** :
**accuracy 60,2 % ± 9,7 % · F1 macro 54,3 % ± 8,2 %**.

Attention : cette ancienne CV réutilisait un `C` choisi sur une validation
recouvrant certains plis de test. Ce n'est pas une estimation indépendante
du choix d'hyperparamètres. Le script utilise désormais une CV imbriquée
3 × 3 ; elle doit être relancée pour produire de nouveaux scores. Les chiffres
ci-dessus sont conservés comme trace historique, pas comme validation du
nouveau protocole.

**Ce qu'on en retient (honnête)**
- Les résultats varient fortement entre groupes. L'écart-type des anciens
  plis n'est pas un intervalle de confiance ni un test d'équivalence : le
  « 68 % vs 65 % » ne permet pas de déclarer les modèles équivalents ou de
  désigner un gagnant robuste.
- La **régularisation forte est cruciale** pour le linear probe (C=0.001 :
  F1 val 72 % ; C=1 : 60 %) — 2048 features pour 295 exemples surapprennent vite.
- Le transfer ne bat **pas** le CNN sur CatMeows : 3 classes larges,
  apprenables de zéro ; les features AudioSet ne sont pas spécialisées « chat ».
- L'extracteur PANNs est prêt comme point de départ de la **Phase 3**.
  Son bénéfice sur le chat personnel reste à mesurer, sans le présupposer.

**Reproduire**
```bash
uv sync --locked --group collecte --group training --group transfer --extra cpu
# Télécharger Cnn14_mAP=0.431.pth dans models/panns/ (guide installation ML).
uv run --no-sync python -m training.transfer_panns   # embeddings (cache) + probe + CV
```
