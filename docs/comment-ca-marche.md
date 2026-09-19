# Comment un enregistrement peut-il aider une IA à reconnaître un nouveau miaulement ?

Ce guide ne demande aucune connaissance en programmation. L'objectif du
projet est de tester si les sons de **votre chat** permettent de distinguer
certains contextes que vous avez observés. Pas de découvrir automatiquement
un dictionnaire « chat → français ».

## 1. D'abord, on fabrique des exemples

Imaginons Moka, un chat fictif. Vous enregistrez un miaulement devant une
porte, puis vous observez qu'il demande à passer. Vous choisissez la
catégorie `porte` et notez votre observation.

Le son et l'annotation forment **un exemple**. En réunissant beaucoup
d'exemples, on construit un **jeu de données**, souvent appelé *dataset*.
Une catégorie s'appelle aussi une *étiquette* ou un *label*.

Une observation peut soutenir une hypothèse ; elle ne prouve pas l'intention
du chat. S'il miaule sans contexte clair, choisissez `incertain`. Ces clips
restent en quarantaine : conservés pour une correction future, mais exclus
de l'apprentissage. Dans l'app, vérifiez aussi le type de son et la certitude
de l'annotation : changer une catégorie ne confirme pas automatiquement le contexte.

**À cette étape, l'app est un carnet d'observation sonore.** Elle reçoit
des enregistrements, pas de nouvelles connaissances magiquement incorporées
dans un modèle. Le téléphone capture le son ; le programme sur le PC le sauvegarde.

## 2. Oui, la suite est du machine learning

Le *machine learning*, ou apprentissage automatique, consiste à apprendre
des règles à partir d'exemples plutôt que de programmer chaque cas à la main.

Ici, nous fournissons les exemples **avec leurs catégories** : c'est de
l'apprentissage **supervisé**. On veut que le programme repère des régularités
utiles pour distinguer, par exemple, `porte` et `faim`. Ces noms décrivent
nos annotations, pas des mots dont on aurait prouvé l'existence chez le chat.

Corriger un label apporte un nouvel exemple supervisé. Ce n'est pas du
*reinforcement learning* : on n'entraîne pas ici un agent à choisir des
actions en fonction d'une récompense. Il n'y a pas non plus de recherche
dans des articles pour fabriquer une réponse, ni de conversation avec un
grand modèle de langage. Aucune API de ce type n'est requise pour collecter.

## 3. Pourquoi réutiliser PANNs ?

Apprendre toute l'analyse acoustique à partir de quelques sons domestiques
serait difficile. Nous réutilisons donc **PANNs CNN14**, un réseau de neurones
audio préentraîné par ses auteurs sur **AudioSet**, une grande collection
de sons du quotidien. Un réseau de neurones est ici un modèle qui transforme
les données en plusieurs étapes dont les réglages ont été appris.

Le travail de départ vient des [auteurs de PANNs](https://github.com/qiuqiangkong/audioset_tagging_cnn).
Il n'a pas été créé de zéro pour ce projet, et il ne connaît pas pour autant
les habitudes particulières de votre chat. Réutiliser un modèle déjà entraîné
pour une nouvelle tâche s'appelle le **transfer learning**, ou apprentissage
par transfert.

Dans notre programme, PANNs transforme chaque extrait en **2 048 nombres**
qui décrivent des caractéristiques apprises du son. Cette représentation
est appelée un *embedding*. Ce ne sont ni 2 048 mots, ni une phrase cachée.

Nous gardons les réglages de PANNs inchangés : on dit qu'il est **gelé**.
Un petit modèle supplémentaire, une **régression logistique**, apprend
ensuite à associer ces représentations à vos catégories. Malgré son nom,
c'est ici un outil de classement : un *classifieur*.

On ne réentraîne donc pas actuellement l'ensemble de PANNs sur votre chat.
Le code correspondant est dans [le script personnel](../training/entrainement_mon_chat.py).

## 4. Que fait-on concrètement au fichier audio ?

Vous n'avez pas besoin de régler ces paramètres pour enregistrer :

1. Le navigateur prépare un fichier WAV, un format de son, à 16 kHz mono.
   « Mono » signifie une seule piste ; 16 kHz indique le rythme de numérisation.
2. Lors de l'entraînement personnel, le programme remet le son au format
   attendu par PANNs : 32 kHz, avec un extrait de 4 secondes. Passer à 32 kHz
   n'invente pas des détails absents de l'enregistrement original.
3. Le modèle calcule une représentation temps/fréquences du son, appelée
   spectrogramme log-mel, puis la liste de caractéristiques.
4. Le petit classifieur apprend les associations avec les catégories.

Les bornes choisies dans l'app servent à sélectionner l'extrait sans
abîmer le WAV original. Si l'intervalle est trop long, le programme choisit
une fenêtre énergique : un bruit de vaisselle pourrait être plus fort que
le chat. D'où l'intérêt de réécouter et vérifier les enregistrements.

## 5. Et CatMeows, dans tout ça ?

**AudioSet et CatMeows n'ont pas le même rôle.** AudioSet est à l'origine
de l'apprentissage de PANNs. CatMeows est le jeu de miaulements public sur
lequel nous avons fait les premiers essais du projet, avant une évaluation
personnelle. Les [ressources et liens exacts](ressources.md) sont détaillés à part.

CatMeows ne remplace pas vos enregistrements et ses catégories ne sont pas
automatiquement les vôtres. Le programme personnel part des poids PANNs
AudioSet ; il ne charge pas automatiquement un réseau réentraîné sur CatMeows.
Les résultats des premiers essais ne constituent donc pas le score de votre chat.

## 6. Comment reconnaître un son jamais entendu ?

Quand l'apprentissage a été fait, un nouveau son peut être transformé de
la même manière en caractéristiques. Le classifieur applique alors ses
réglages appris pour proposer une catégorie parmi celles qu'il connaît.
Il n'a pas besoin d'avoir vu ce fichier exact auparavant.

On appelle cela **généraliser** : réussir au-delà des exemples d'entraînement.
C'est l'objectif, pas un acquis. Un son nouveau peut correspondre à une
situation inconnue, ou ressembler à plusieurs catégories. Le système ne
découvre pas automatiquement une nouvelle catégorie simplement parce que
le chat produit un son différent.

Une bonne évaluation garde des journées entières à l'écart de l'apprentissage.
Sinon, deux sons presque identiques issus de la même scène pourraient se
retrouver à la fois dans les exemples appris et dans le test, donnant une
impression trompeuse de réussite. Le programme refuse certains découpages
quand les données sont insuffisantes : c'est une protection, pas une panne.

Le script compare aussi le son seul, le contexte seul et les deux ensemble.
Si connaître la pièce ou le délai depuis le repas suffit, il ne faut pas
attribuer tout le résultat à la compréhension du miaulement. Les observations
après coup servent à annoter, **pas à renseigner le modèle au moment de prédire**.

## 7. Pourquoi continuer à enregistrer petit à petit ?

De nouveaux exemples bien annotés peuvent apporter de la diversité :
autres jours, distances, bruits de fond et situations normales. Mais une
collection plus grosse et mal annotée peut aussi dégrader le résultat.

Le cycle prévu est donc :

1. Enregistrer pendant la vie normale du chat, sans provoquer de stress.
2. Réécouter et corriger les annotations, en gardant les cas inconnus à part.
3. Lancer explicitement une nouvelle expérience d'entraînement quand les
   données sont assez variées pour le protocole.
4. Comparer les résultats, puis vérifier sur de futures journées qui n'ont
   pas servi à choisir le modèle ou ses réglages.

Les modèles et rapports sont enregistrés séparément. **La collecte ne
réentraîne ni ne déploie automatiquement le modèle dans l'application.**
Pas de durée magique d'un an, ni de nombre universel de sons garantissant
une bonne précision. La qualité et les tests déterminent la suite.

## 8. Où en est l'application aujourd'hui ?

L'enregistrement, les corrections et les sauvegardes sont disponibles.
Les programmes d'entraînement et d'évaluation personnels sont préparés.
Un système de prédiction personnelle en direct, avec un seuil fiable pour
dire « je ne sais pas », n'est pas encore branché dans l'application.

Vous pouvez donc déjà **constituer votre collection et apprendre la méthode**.
Pour commencer : [installation débutant](installation.md), puis
[utilisation sur téléphone](hebergement.md). Pour réaliser l'expérience ML :
[tutoriel pratique](tutoriel.md), puis [protocole technique](apprentissage.md).
