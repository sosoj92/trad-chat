# Sécurité et données privées

Ce projet est un prototype pour une installation personnelle, pas un service
multi-utilisateur durci. La clé de collecte donne accès aux enregistrements,
aux annotations et aux exports : considère-la comme un mot de passe.

- Utilise la clé aléatoire créée par l'initialiseur ; ne partage pas `config.yaml`.
- Privilégie la saisie de la clé dans le champ de connexion, pas dans une URL
  susceptible de rester dans l'historique, les logs ou une capture d'écran.
- Garde le serveur lié à `127.0.0.1` si tu utilises un tunnel local, et n'ouvre
  pas directement son port sur Internet en HTTP.
- Le stockage sur disque et les sauvegardes ne sont pas chiffrés par l'app.
  Protège les accès à ton ordinateur et à tes copies.
- Les URL HTTPS de tunnel font transiter les données par leur fournisseur.
- Ne charge pas un fichier `.pth`, `.pt` ou `.joblib` non fiable : les formats
  de modèles utilisés peuvent exécuter du code lors du chargement.

## Si une clé a été exposée

Arrête ton tunnel de collecte, remplace `collecte.token` par une nouvelle
valeur aléatoire locale, relance ton serveur et reconnecte tes appareils.
Ne coupe pas les tunnels des autres applications. Retirer la clé d'un commit
récent ne l'efface pas des copies et de l'historique : **il faut la changer**.

## Signaler un problème

Ne publie pas de secret ni d'enregistrement dans une issue. Si GitHub propose
un signalement de vulnérabilité privé pour ce dépôt, utilise-le. Sinon demande
un canal privé avec une description générale, sans détails exploitables.
Les bugs ordinaires peuvent être décrits publiquement avec des données synthétiques.
