# Modèle d'IA, jeux de données et outils utilisés

Cette page donne les sources de départ et le rôle réel de chacune.
Pour une explication sans prérequis : [comment ça marche](comment-ca-marche.md).

Un **modèle** contient des réglages appris ; un **jeu de données** (*dataset*)
contient des exemples pour apprendre ou tester ; une **bibliothèque** est
du code réutilisable pour effectuer des opérations. Ici, « bases de données
de sons » désigne des datasets, pas un service de stockage de vos fichiers.

Les ressources sont aussi présentées directement dans [l'accueil du projet](../README.md).

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

**À ne pas confondre :** CatMeows a servi aux essais publics du projet.
Le script personnel charge directement les poids PANNs préentraînés sur
AudioSet ; il ne charge pas automatiquement un modèle réentraîné sur CatMeows.
Les trois contextes de CatMeows ne définissent pas les catégories de votre chat.

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

### Que faut-il télécharger, et quand ?

- **Pour enregistrer :** seulement le code et les logiciels indiqués dans
  [l'installation](installation.md). Aucun poids PANNs ni dataset n'est requis.
- **Pour l'apprentissage personnel audio :** les poids exacts PANNs ci-dessus,
  puis vos propres exemples annotés et vérifiés.
- **Pour reproduire les premiers essais publics :** CatMeows, suivant
  [le guide de reproduction](baseline.md) et les conditions de ses auteurs.
- **AudioSet :** aucun téléchargement nécessaire ; on réutilise ce que PANNs
  a appris dessus, pas toute la collection de sons.

Un fichier de poids est un fichier de réglages, pas le code complet de l'app.
Les poids et les datasets ne sont pas inclus dans ce GitHub. Consultez les
conditions propres à chaque ressource avant leur réutilisation.

## Les outils techniques, avec leur rôle

| Outil | Ce qu'il fait ici | Source |
|---|---|---|
| Python | Langage du serveur et des scripts d'apprentissage | [Site officiel](https://www.python.org/) |
| FastAPI | Permet au programme sur le PC de recevoir les sons et de répondre à l'app | [Documentation](https://fastapi.tiangolo.com/) |
| HTML / JavaScript | Affichent les boutons et pilotent la capture audio dans le navigateur | [Interface du projet](../collecte/static/app.js) |
| PyTorch | Exécute les réseaux de neurones, dont PANNs et le CNN de comparaison | [Site officiel](https://pytorch.org/) |
| librosa | Lit et prépare les fichiers son pour l'analyse | [Documentation](https://librosa.org/doc/latest/) |
| scikit-learn | Entraîne la régression logistique, sélectionne ses réglages et calcule les scores | [Classifieur utilisé](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) |
| uv | Installe les logiciels nécessaires et lance le projet | [Documentation](https://docs.astral.sh/uv/) |
| ngrok | Donne une adresse HTTPS pour joindre l'app sur le PC depuis le téléphone ; ne fait aucun apprentissage | [Documentation](https://ngrok.com/docs/getting-started/) |

Les versions installées sont verrouillées dans [uv.lock](../uv.lock).
Vercel, Netlify et Supabase sont des pistes pour une autre façon d'héberger
l'app, **pas des composants déjà branchés dans cette version**. Voir
[le guide téléphone et hébergement](hebergement.md).

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
