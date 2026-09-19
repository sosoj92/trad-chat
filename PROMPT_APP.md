# Le prompt pour recréer l'application de collecte

Oui, publier un prompt est pertinent : il rend les choix du projet visibles
et permet de refaire l'exercice avec son chat. Mais il ne remplace ni les
sources, ni les tests, ni un guide d'installation.

**Ce texte est une version réécrite et actualisée du cahier des charges de
l'app, pas la transcription exacte d'un ancien échange ni une garantie de
reproduire le même code.** Le brief initial par phases était destiné à un
assistant de code. Il contenait des pistes qui n'ont pas toutes été réalisées.
Le dépôt et ses tests décrivent ce qui existe réellement aujourd'hui.

Tu peux donner ce prompt à un assistant de développement ou à un générateur
d'applications, par exemple Emergent. Ce document ne garantit ni la gratuité
du générateur, ni l'export de son code, ni son déploiement sur une autre plateforme :
vérifie ces possibilités avant de commencer. Ne fournis aucune clé ou donnée privée.

Pour seulement **installer cette app**, utilise plutôt
[le prompt d'accompagnement](INSTALL_WITH_AI.md).
Pour choisir où la faire tourner : [guide d'hébergement](docs/hebergement.md).

## Prompt principal à copier

```text
Crée une application éducative de collecte des vocalisations de MON chat.
Référence publique : https://github.com/sosoj92/trad-chat
Si tu peux lire ce dépôt, commence par README.md, docs/collecte.md,
docs/apprentissage.md et docs/confidentialite.md. Sinon, dis-le : n'invente
pas ce que contient le code.

BUT ET LIMITES
Je veux enregistrer, réécouter et annoter des vocalisations pour préparer
une expérience de classification supervisée. Ce n'est pas un traducteur
de phrases félines, un diagnostic vétérinaire ni une communication humain-chat.
N'affiche aucun score de compréhension inventé et n'ajoute ni RAG, ni LLM,
ni reinforcement learning, ni entraînement automatique à la collecte.

AVANT DE CODER
Demande-moi seulement le nom d'affichage du chat, mes catégories et mon
choix d'architecture : PC + tunnel HTTPS, ou variante cloud adaptée.
Explique où seront stockées et par où transiteront les données.
Si je n'ai pas choisi, recommande le parcours local existant pour commencer.
Travaille dans un dossier/projet distinct ; ne remplace aucune installation,
configuration, clé ou donnée existante. Ne lance aucun service payant et
ne publie aucune donnée sans mon accord. Utilise des exemples fictifs.

VERSION LOCALE DE REFERENCE
PWA mobile-first en français, utilisable d'une main sur iPhone et Android,
servie avec son API par FastAPI/Python 3.13. Une installation = un chat.
Configuration privée centralisée : nom d'affichage, catégories, port,
chemins et clé de connexion aléatoire. Fournis config.example.yaml sans
secret et un initialiseur qui refuse d'écraser une config existante.
Adresse locale de référence : 127.0.0.1:8771. Téléphone via HTTPS, par exemple
avec son propre tunnel ngrok ; une IP locale en HTTP ne suffit pas.
Ne réutilise pas un tunnel, domaine, port occupé ou secret d'un autre projet.

ENREGISTREMENT
Gros boutons Activer le micro, Enregistrer, Stop ; durée et état visibles.
Le micro ne démarre que sur action explicite. Après activation, pré-tampon
de 5 secondes maximum ; il ne peut pas récupérer un son antérieur à l'activation.
Capture de 120 secondes maximum, plus le pré-tampon disponible.
Le navigateur produit de vrais WAV PCM16, mono, 16 kHz : ne renomme pas
un WebM/M4A en WAV. Rééchantillonne correctement et teste le format.
Prévois réécoute et contrôle de l'extrait avant envoi.
Arrête le micro en arrière-plan ; ne promets pas d'écoute permanente.
Conserve le clip encodé en attente dans IndexedDB si disponible, avec son
identifiant de capture, et propose de réessayer après une coupure réseau.
Ne promets pas un fonctionnement entièrement hors ligne.

CATEGORIES ET ANNOTATIONS
Catégories personnalisables, par défaut faim, porte, calin, autre, incertain.
autre = vocalise identifiable hors catégories (trille, feulement, gazouillis),
admissible comme classe atypique lorsque l'annotation est vérifiée.
incertain = miaulement normal mais contexte inconnu : quarantaine, TOUJOURS
exclue du dataset et des exports d'entraînement, jamais une classe apprise.
Cette catégorie peut attendre un ré-étiquetage ou une étude future du seuil ;
des clips inconnus seuls ne permettent pas de calibrer ce seuil.

Champs séparés :
- type_son : vocalise / bruit / inconnu ;
- certitude : a_verifier / probable / confirmee ; défaut a_verifier ;
- date de capture, jour local, identifiant de session ;
- lieu et minutes depuis le repas, disponibles au moment du son ;
- observation au moment du son, observation après coup, note facultative ;
- bornes début/fin de l'extrait, sans modifier le WAV original.

Un changement de label ne doit pas confirmer automatiquement le contexte.
Les bruits non félins, clips à vérifier, fichiers absents, labels inconnus,
clips supprimés et incertain ne sont pas admissibles à l'entraînement.
Un seuil d'énergie peut alerter sur la qualité, pas prouver qu'un chat miaule.

INTERFACE ET RE-ETIQUETAGE
Une liste Derniers enregistrements avec réécoute, date, label, statut et détails.
Changement rapide en deux taps : toucher le label, toucher la nouvelle catégorie.
Cas de test : incertain, puis observation de la gamelle, correction en faim.
L'édition détaillée reste possible pour la certitude et les observations.
Compteurs : total, admissibles, à vérifier et jours par classe.
Afficher incertain à part, grisé, hors des objectifs 30+/classe.
Le nombre 30 est un repère de collecte, pas une garantie de performance.
Filtres, corbeille logique, restauration et historique des corrections.
Pas de suppression définitive d'un original par simple changement de label.
Ne pas mélanger silencieusement plusieurs chats ; séparer les installations.

STOCKAGE ET SECURITE
Version locale : WAV originaux et manifest.jsonl dans data/mon_chat/.
Sauvegarde du manifest avant remplacement atomique ; un seul processus
écrivain sur ce dossier. Envoi idempotent par capture_id : un retry ne
doit pas créer un doublon. Les chemins de fichiers restent dans le dataset.
Protéger toutes les routes de données, lecture audio et export compris.
Clé générée localement, jamais codée dans le frontend, les logs ou GitHub.
Champ de connexion plutôt que secret dans l'URL. Refuser une clé d'exemple.
Nom du chat visible seulement après connexion. Rendu des textes sans injection HTML.
Gitignore : config réelle, .env, audios, manifests, exports, modèles, logs,
clés et historiques d'assistants. Ne pas rendre les données publiques pour
corriger un problème d'authentification.

EXPORT ET APPRENTISSAGE
Deux exports protégés : sauvegarde complète, et dataset admissible à l'entraînement.
Documenter qu'un export d'entraînement n'est pas une sauvegarde complète.
Conserver WAV originaux, identifiants, dates, sessions, bornes et annotations.
Pour réutiliser le pipeline du dépôt, vérifier le schéma avec ses loaders.
Le pipeline personnel existant utilise PANNs CNN14 gelé + régression
logistique et validation imbriquée par journées : ne pas inventer un autre
protocole ni annoncer qu'il est déployé dans l'app.
Ne pas utiliser les observations après coup comme variables prédictives.
Ne pas inclure PyTorch ou des poids ML dans l'installation de collecte.

LIVRABLES ET TESTS
Code exportable, README débutant, config d'exemple, installation pas à pas,
diagnostic sans secrets, guide téléphone/HTTPS, sauvegarde et dépannage.
Tests isolés sur WAV synthétiques : auth, capture/réécoute, double envoi,
relabel en deux taps, quarantaine, préservation du WAV, export, restauration,
absence d'écrasement de configuration et reprise après erreur réseau.
Ne déclenche pas mon microphone pour tester et n'utilise pas mes vrais audios.
Indique ce qui a été réellement testé et ce qui reste à vérifier sur mobile.
Livre par étapes : collecte fonctionnelle d'abord, pas un faux écran de traduction.
```

## Complément — Variante cloud Vercel ou Netlify

**À ajouter au prompt principal seulement si tu veux une autre architecture,
sans PC allumé.** Ce complément demande une adaptation ; il ne décrit pas
une fonctionnalité déjà fournie par le dépôt.

```text
Je choisis la VARIANTE CLOUD. Remplace uniquement l'architecture locale du
prompt principal par les exigences suivantes, en conservant les fonctions,
les règles d'annotation et les tests de confidentialité.

Construis un frontend React/TypeScript/Vite exportable, déployable sur Vercel
ou Netlify, sans dépendre du serveur allumé chez moi. Utilise mon propre
projet Supabase pour Auth, PostgreSQL et un bucket de stockage audio privé.
Ne connecte ni ne transfère ma collecte actuelle sans accord explicite.
N'ajoute ni entraînement ML ni génération de texte dans le navigateur.

Livre les migrations et politiques d'accès avec le code. Un utilisateur
authentifié ne peut lire/écrire que ses propres lignes et objets. Fais vérifier
ces règles par le service, pas seulement par l'interface. Toute API privilégiée
doit valider l'identité et la propriété de chaque ressource avant d'agir.
Reste sur un chat par compte pour cette première version ; ne mélange pas les profils.
Conserve les originaux, l'historique et l'idempotence avec une contrainte
unique par propriétaire et capture_id. Gère l'échec partiel entre stockage
du WAV et écriture des métadonnées sans perte ni doublon silencieux.

Le frontend utilise VITE_SUPABASE_URL et VITE_SUPABASE_PUBLISHABLE_KEY.
La clé publiable peut être dans le navigateur UNIQUEMENT avec les politiques
d'accès adéquates. Aucune clé service_role, secret privilégié, chaîne de
connexion PostgreSQL ou mot de passe dans une variable VITE_ ou dans le code.
Ne crée pas de bucket public. Réécoute et export nécessitent autorisation ;
les liens signés doivent expirer. Garde une politique de cache adaptée aux données privées.

Prévois un upload authentifié direct vers le stockage ou un mécanisme signé,
avec restrictions de taille, format et propriété. Ne fais pas passer tous
les WAV et gros ZIP par une fonction aux limites incompatibles. Ne conserve
pas le dataset durablement dans /tmp, le filesystem d'une fonction ou GitHub.
Fournis une solution d'export privé adaptée au volume, avec reprise d'erreur.

Documente précisément : npm ci, npm run build, dossier dist, versions
supportées, variables publiques et éventuels secrets serveur, migrations,
bucket privé, URL de retour Auth, routes PWA et configuration de déploiement.
Ne prétends pas qu'un import du dépôt Python original suffit.
Les comptes, plans et déploiements externes nécessitent mon accord ; propose
le niveau gratuit si éligible et explique ses quotas, pauses et limites.
Ne promets pas une année gratuite ou un service permanent sans vérifier l'usage.

Teste : utilisateur anonyme refusé ; second compte isolé du premier ; WAV
toujours présent après redéploiement et PC éteint ; échec réseau récupérable ;
export admissible sans incertain ; sauvegarde complète avec quarantaine ;
lecture et compatibilité de l'export avec le loader Python du projet.
Fournis un guide séparant les tests réellement exécutés des contrôles restants.
```

## Comment s'en servir dans une vidéo

Montre le prompt, puis un véritable cycle enregistrement → annotation →
correction → sauvegarde. Un écran généré seul n'est pas une preuve de stockage
ni d'apprentissage. Masque les clés, les URL authentifiées, les notes privées
et les informations des comptes d'hébergement.

Le prompt initial évoquait notamment un accès par IP locale, des heuristiques
de détection et des performances espérées. Cette version demande HTTPS sur
téléphone, sépare qualité audio et détection, conserve la quarantaine et ne
promet aucun score : ce sont des ajustements issus du développement du projet.
