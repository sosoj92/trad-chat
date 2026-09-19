# Être accompagné pour installer Trad Chat

Ce prompt sert à **installer le code existant**, pas à générer une nouvelle
application. Pour la recréer, consulte [PROMPT_APP.md](PROMPT_APP.md).
Pour choisir entre ngrok et une future variante Vercel/Netlify, lis
[le guide téléphone et hébergement](docs/hebergement.md).

Tu peux donner ce prompt à un assistant qui lit le dépôt, ou lui fournir
uniquement les fichiers publics de ce GitHub. Ne lui envoie pas `config.yaml`,
ta clé, tes audios ou un export de collecte.

Copie le bloc suivant :

```text
Je veux installer le projet éducatif Trad Chat pour mon propre chat :
https://github.com/sosoj92/trad-chat

Commence par lire README.md, docs/installation.md, docs/personnalisation.md
et docs/confidentialite.md. Appuie-toi sur le code et les commandes du dépôt,
pas sur l'hypothèse qu'il s'agit déjà d'un traducteur opérationnel.

Demande-moi mon système d'exploitation, si Git et uv sont installés, et si
je veux seulement tester sur PC ou aussi utiliser mon téléphone. Guide-moi
une étape à la fois, avec le résultat attendu et une vérification simple.
Explique les termes techniques sans supposer que je sais programmer.

Commence par la collecte uniquement : pas de GPU, pas de téléchargement
de modèle ou dataset, pas d'abonnement ni de clé d'API LLM nécessaire.
Utilise core.initialiser pour générer une configuration privée et une clé
aléatoire. Si config.yaml existe, ne l'écrase pas et ne le supprime pas.
Ne demande jamais que je te colle une clé, une config privée ou des audios.
Pour lire la clé, indique la commande locale explicite, hors vidéo ; tu
n'as pas besoin de voir sa valeur pour m'aider.

N'arrête pas les autres applications, processus Python ou tunnels. Ne lance
pas uv sync dans un environnement utilisé par un serveur actif. Propose un
autre port si nécessaire. Explique qu'un téléphone a besoin d'HTTPS, d'un
serveur actif sur le PC et éventuellement de mon propre tunnel. N'utilise
aucune URL ni clé appartenant à l'autrice du projet.

Ne déclenche pas le microphone pour moi. Accompagne-moi pour un test dont
j'autorise la capture, puis la lecture et la mise à la corbeille du clip
de test. Explique les labels autre/incertain, la certitude et les sauvegardes.

Une fois la collecte fonctionnelle, explique comment poursuivre avec
docs/tutoriel.md. L'apprentissage est supervisé et lancé explicitement ;
il ne garantit pas une traduction ni une communication bidirectionnelle.
Ne modifie ni ne publie mes données, et demande avant tout nouvel envoi
vers un service externe. Si une étape échoue, diagnostique sans supprimer
mes fichiers et sans me demander de divulguer des informations privées.
```

Un assistant peut se tromper. Avant d'exécuter une commande, vérifie qu'elle
concerne le bon dossier et qu'elle ne publie pas de données. Le guide reste
utilisable sans assistant : [installation manuelle](docs/installation.md).
