# Ressources du projet

## Données réellement utilisées

- **CatMeows, version 1.0.2** : [fiche officielle et téléchargement](https://zenodo.org/records/4008297).
  440 miaulements de 21 chats, avec trois contextes : brossage, attente de
  nourriture et isolement dans un environnement inconnu. C'est le dataset
  de la baseline, pas un dictionnaire de traductions. Les auteurs indiquent
  un usage scientifique et non commercial et demandent une attribution.
- **AudioSet** : [présentation officielle Google](https://research.google.com/audioset/).
  Dataset de préentraînement du modèle PANNs. Le projet réutilise les poids
  préentraînés ; il ne réentraîne pas PANNs sur l'ensemble d'AudioSet.
- **Collecte personnelle** : sons et annotations créés avec la PWA,
  conservés localement et exclus du dépôt GitHub. Aucun lien de téléchargement
  public de ces données n'est fourni.

## Modèle réutilisé

- **PANNs CNN14** : [code officiel](https://github.com/qiuqiangkong/audioset_tagging_cnn).
- **Poids exacts** : [archive officielle Zenodo](https://zenodo.org/records/3987831),
  fichier `Cnn14_mAP=0.431.pth`.
- **Article** : [PANNs: Large-Scale Pretrained Audio Neural Networks for Audio Pattern Recognition](https://arxiv.org/abs/1912.10211).

L'architecture est adaptée dans `training/panns_cnn14.py`. L'encodeur gelé
produit des vecteurs de 2048 caractéristiques. Une
[régression logistique scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
apprend les catégories à partir de ces vecteurs. Voir aussi
[les notices tierces](../THIRD_PARTY_NOTICES.md).

Un petit CNN entraîné de zéro sert de comparaison initiale ; c'est du code
du projet, pas un autre modèle préentraîné téléchargé.

## Pistes évoquées, pas encore utilisées

- [Perch — Google Research](https://github.com/google-research/perch).
- [BEATs — Microsoft](https://github.com/microsoft/unilm/tree/master/beats).

Ces liens sont des pistes de comparaison. Aucun résultat sur la collecte
personnelle n'est revendiqué avec ces modèles.

## À dire correctement quand on présente le projet

Le projet actuel fait de la classification audio supervisée et prépare du
transfer learning personnalisé. Il n'utilise **ni RAG ni reinforcement
learning**, et la collecte seule ne déclenche pas d'entraînement automatique.
L'app mobile sert à enregistrer et annoter ; aucun traducteur personnel
validé n'est encore déployé.

Pour le protocole et les résultats historiques :
[apprentissage](apprentissage.md), [baseline](baseline.md),
[collecte](collecte.md), [confidentialité](confidentialite.md).
