# Publication sans données personnelles

Le dépôt partage le code, la configuration **d'exemple**, les tests sur
données synthétiques et les figures d'évaluation du dataset public CatMeows.
Il ne contient pas la collecte privée ni un modèle entraîné sur celle-ci.

Ne jamais ajouter au dépôt :

- `config.yaml`, ses sauvegardes, `.env` ou toute clé / URL authentifiée ;
- `data/mon_chat/`, audios, annotations, manifests et exports ZIP ;
- modèles, embeddings, rapports personnels et journaux d'exécution ;
- réglages locaux / historiques d'assistants (`.claude/`, `.codex/`, etc.).

Ces chemins et formats sont exclus par `.gitignore`. Cela ne protège pas un
fichier déjà suivi par Git, un ajout forcé, ni une donnée recopiée dans le
code ou un document. Relire les changements avant chaque publication.

La première publication utilise un historique neuf et une identité GitHub
`noreply`, sans transmettre les adresses personnelles des anciens commits.
L'historique original demeure local. Ne pas pousser d'autres anciennes
branches ou tags sans les auditer à leur tour.

Pour installer l'app, suivre [le guide](installation.md) et utiliser
`core.initialiser` : une clé aléatoire est créée localement sans remplacer
une configuration existante. Les clés présentes dans les tests ne protègent
que des serveurs de test locaux et des données synthétiques.

`uv.lock` ne contient que les versions, empreintes et URL publiques des
dépendances. Les données placées dans un autre sous-dossier de `data/` sont
aussi ignorées ; un chemin personnalisé ailleurs doit être vérifié séparément.

Les captures d'écran, issues, messages de commit et liens partagés peuvent
eux aussi divulguer des données. Ne pas y joindre les audios, notes privées,
clés de connexion ou URLs comprenant `?token=...`.
