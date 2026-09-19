# Utiliser l'app sur son téléphone : ngrok, Vercel ou Netlify ?

**Deux objectifs différents :**

- Utiliser **l'application de ce dépôt dès maintenant** sur son téléphone :
  suivre le [parcours ngrok](#a--le-parcours-actuel--ordinateur--ngrok).
- Utiliser l'app **sans laisser son ordinateur allumé** : il faut d'abord
  construire la [variante cloud](#b--sans-ordinateur-allumé--préparer-une-variante-cloud),
  puis la publier sur Vercel ou Netlify. Cette variante **n'est pas encore implémentée ici**.

Le téléphone affiche la page et capture le micro. Il n'héberge pas le serveur
Python. « Ajouter à l'écran d'accueil » crée un raccourci d'app web, pas un
serveur autonome ni une app native distribuée sur un store.

## Choisir son parcours

| Solution | Où sont les données ? | PC nécessaire pendant la collecte ? | Compatible avec ce dépôt tel quel ? |
|---|---|---|---|
| FastAPI sur le PC + ngrok | Disque du PC ; trafic relayé par ngrok | Oui | Oui |
| Vercel + stockage/base externes | Services cloud privés à configurer | Non, après adaptation | Non : stockage et configuration à adapter |
| Netlify + stockage/base externes | Services cloud privés à configurer | Non, après adaptation | Non : frontend et accès aux données à adapter |

Le code actuel écrit les WAV et `manifest.jsonl` sur disque dans
`collecte/stockage.py`, lit sa configuration privée dans `config.yaml`, et
appelle `/api/...` sur le même site que l'interface. Un verrou protège un
seul processus, pas plusieurs instances cloud.

Conséquence : **une page qui s'affiche ne prouve pas que l'app fonctionne**.
Publier seulement `collecte/static` ne fournit ni les routes API ni le
stockage. Copier le manifest dans `/tmp` ne le rend pas durable.

## A — Le parcours actuel : ordinateur + ngrok

### A1. Installer l'app une fois

Suis d'abord [l'installation sur ordinateur](installation.md). Elle explique
Git, uv, la configuration personnelle et la clé de connexion.
Si ton app fonctionne déjà localement, **ne recrée pas ton installation**.

Dans un terminal ouvert dans le dossier du projet :

```bash
uv run --no-sync python -m core.diagnostic
uv run --no-sync python -m collecte.serveur
```

Laisse ce terminal ouvert. Sur le PC, visite
[http://127.0.0.1:8771](http://127.0.0.1:8771). Si tu as changé le port dans
`config.yaml`, utilise ce port partout dans la suite.

### A2. Configurer son propre compte ngrok

Crée un compte et installe l'agent depuis le
[guide officiel ngrok](https://ngrok.com/docs/getting-started/).
Exécute **localement et hors vidéo** la commande d'association à ton compte
fournie par son tableau de bord. Elle contient ton authtoken ngrok : ne le
mets ni dans ce dépôt ni dans une conversation publique.

Il y a deux secrets distincts :

- **Authtoken ngrok** : associe l'agent installé sur le PC à ton compte ngrok.
- **Clé de collecte** : protège tes audios dans l'application.

N'utilise pas la clé ou le domaine de l'autrice, ni ceux montrés dans une vidéo.
Ne remplace pas le tunnel d'un autre projet : vérifie d'abord ce qui fonctionne
déjà et les limites de ton compte.

### A3. Ouvrir le tunnel

Dans un deuxième terminal :

```bash
ngrok http 8771
```

Copie l'adresse **HTTPS** affichée par ngrok, sans lui ajouter de clé dans
l'URL. Ouvre-la sur le téléphone. S'il y a une page d'avertissement ngrok,
continue seulement après avoir vérifié que c'est bien ton adresse.

L'offre gratuite fournit actuellement un domaine de développement lié au
compte, avec des quotas. Le domaine peut donc rester identique : il ne faut
pas supposer qu'il change à chaque lancement. Vérifie toujours l'adresse
réellement affichée. Sources : [limites et domaine gratuits ngrok](https://ngrok.com/docs/pricing-limits/free-plan-limits).

### A4. Se connecter depuis le téléphone

Dans un autre terminal ouvert dans le dossier du projet, affiche la clé de
collecte **hors capture d'écran** :

```bash
uv run --no-sync python -m core.initialiser --afficher-cle
```

Saisis-la dans « Clé de connexion » sur le téléphone. N'y mets pas l'authtoken
ngrok. Autorise le microphone quand tu veux faire un test.

Fais un court essai avec ta propre voix, choisi comme **Bruit / non-vocalise**.
Enregistre-le, vérifie la réécoute dans les derniers enregistrements après
rechargement, puis mets ce clip de test à la corbeille. Il ne doit pas devenir
un exemple de chat pour l'entraînement.

### A5. Ajouter l'app à l'écran d'accueil

- **iPhone** : ouvre l'adresse dans Safari, puis Partager → Sur l'écran d'accueil.
- **Android** : dans un navigateur compatible, cherche « Installer l'application »
  ou « Ajouter à l'écran d'accueil ». Le libellé dépend du navigateur.

Ouvre le raccourci et reconnecte-toi si nécessaire. Garde l'app au premier
plan pendant la capture : le micro est arrêté quand elle passe en arrière-plan.
Sur téléphone, utilise HTTPS ; une IP du PC en HTTP n'est pas équivalente.

### A6. Revenir le lendemain

Il faut garder l'ordinateur allumé, connecté, sans mise en veille, et les
deux processus actifs : serveur de collecte et ngrok. S'ils sont arrêtés,
relance `uv run --no-sync python -m collecte.serveur`, puis `ngrok http 8771`.
Inutile de relancer l'installation des dépendances ou de créer une nouvelle clé.

Une erreur ngrok de type endpoint hors ligne se vérifie dans cet ordre :

1. L'app fonctionne-t-elle sur `http://127.0.0.1:8771` **sur le PC** ?
2. Le bon tunnel fonctionne-t-il vers le bon port ?
3. Le téléphone ouvre-t-il exactement l'adresse HTTPS actuelle ?
4. Si la page s'affiche mais refuse la connexion : utilises-tu la clé de cette installation ?

Une actualisation du téléphone ne rallume pas le PC. Ne tue pas tous les
processus Python ou tous les tunnels pour dépanner.
Voir aussi [le dépannage détaillé](depannage.md).

### A7. Coût et sauvegardes

Cette méthode peut utiliser l'offre gratuite ngrok **dans ses limites** ;
ce n'est ni un hébergement permanent garanti ni un trafic illimité. Les
réécoutes et les exports consomment aussi du transfert. Vérifie l'usage dans
ton compte et les [conditions actuelles](https://ngrok.com/docs/pricing-limits/free-plan-limits).

Les audios sont stockés sur ton PC, mais transitent par ngrok. Fais des
sauvegardes privées régulières ; pour conserver aussi la quarantaine,
choisis la sauvegarde complète, pas seulement l'export d'entraînement.

## B — Sans ordinateur allumé : préparer une variante cloud

**Cette section est un plan de réalisation, pas une recette de déploiement
direct du dépôt actuel. Aucun backend cloud, migration SQL ou paramétrage
Vercel/Netlify n'est livré par ce guide.**

Une variante accessible gratuitement pour un petit usage peut être conçue
avec un frontend React/Vite sur Vercel **ou** Netlify, et Supabase pour
l'authentification, une base PostgreSQL et un stockage audio privé.
C'est une option d'architecture, pas un service déjà connecté à ce projet.

```text
Téléphone (interface en HTTPS, hébergée sur Vercel ou Netlify)
    ├── connexion → authentification
    ├── WAV privés → stockage d'objets
    └── annotations et catégories → base de données

Export privé → ordinateur → entraînement Python, lancé séparément
```

### B1. Faire produire la variante adaptée

Utilise le [prompt de création](../PROMPT_APP.md), puis ajoute le
[complément cloud](../PROMPT_APP.md#complément--variante-cloud-vercel-ou-netlify).
Travaille dans un projet distinct pour préserver la collecte locale.
Exige un projet exportable et les tests de fonctionnement, pas seulement une maquette.

Les livrables nécessaires avant déploiement sont :

- Le frontend complet avec sa commande de build et son dossier de sortie.
- Les migrations SQL, les politiques d'accès et un bucket audio **privé**.
- Une authentification et des contrôles de propriété côté service, pas
  simplement un bouton « connexion » qui cache l'interface.
- Les variables d'environnement **d'exemple**, sans valeur secrète.
- Un export WAV + annotations compatible avec le pipeline local, y compris
  les règles de quarantaine, et une sauvegarde complète distincte.
- Un test de persistance après rechargement et après redéploiement.

Vercel sait exécuter [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi) :
Python n'est donc pas, à lui seul, l'obstacle. En revanche, les écritures
locales actuelles ne sont pas une base persistante cloud ; il faut les
remplacer par un service de stockage. Vercel recommande un
[stockage d'objets pour les fichiers écrits](https://vercel.com/kb/guide/how-can-i-use-files-in-serverless-functions).

Sur Netlify, la présence de Python pendant la compilation ne signifie pas
qu'un serveur Uvicorn restera actif après le build. Le parcours proposé ici
est un frontend statique communiquant avec les services de données ; une
API éventuelle doit être adaptée à un runtime supporté ou hébergée ailleurs.
Voir [Functions](https://docs.netlify.com/build/functions/get-started/) et
[logiciels de build](https://docs.netlify.com/build/configure-builds/available-software-at-build-time/).

### B2. Préparer les services de données

Seulement après avoir reçu et relu les migrations de la variante générée :

1. Crée ton propre projet Supabase sur l'offre choisie, et vérifie ses quotas.
2. Applique les migrations **de cette variante** : elles doivent créer les
   tables nécessaires aux profils, clips et annotations.
3. Active les politiques de sécurité par propriétaire et crée le bucket audio privé.
4. Configure la connexion des utilisateurs et les URL de retour autorisées.
5. Teste qu'une personne déconnectée, puis un second compte, ne peuvent ni
   lister, ni écouter, ni modifier, ni exporter les données du premier.

Le mode public d'un bucket n'est pas une solution à un refus d'accès.
Les clés privilégiées ne doivent jamais être embarquées dans le JavaScript
du navigateur. Sources : [sécurité des tables](https://supabase.com/docs/guides/database/postgres/row-level-security),
[contrôle du stockage](https://supabase.com/docs/guides/storage/security/access-control).

### B3. Publier la variante sur Vercel

Ces étapes supposent le **frontend React/Vite adapté**, pas le code Python
actuel. Si le générateur a choisi un autre framework, utilise son guide de build.

1. Envoie uniquement le code de cette variante dans **ton** dépôt GitHub,
   sans `.env`, données ou secrets.
2. Dans Vercel, crée un projet et importe ce dépôt. Choisis l'offre Hobby
   seulement si ton usage respecte ses conditions.
3. Choisis le dossier contenant `package.json` comme racine du frontend et
   le preset Vite. Pour une sortie Vite standard, le build est `npm run build`
   et le dossier publié `dist` ; vérifie ces valeurs dans le projet généré.
4. Ajoute les variables définies par ce projet. Si le prompt complémentaire
   ci-dessous a été suivi, le navigateur utilise `VITE_SUPABASE_URL` et
   `VITE_SUPABASE_PUBLISHABLE_KEY` (clé publiable, **pas** une clé privilégiée).
5. Déploie, récupère l'adresse HTTPS de production, puis ajoute-la dans les
   URL autorisées du service d'authentification. Redéploie si tu modifies
   des variables intégrées au build.
6. Effectue la [recette de vérification](#c--recette-de-vérification-avant-la-vraie-collecte).

Si le frontend utilise des routes côté navigateur, configure aussi le retour
vers `index.html` sans masquer les routes API. Référence :
[Vite sur Vercel](https://vercel.com/docs/frameworks/frontend/vite).

Ne configure pas `uvicorn` comme commande de build de ce frontend. Ne charge
pas les poids PANNs pour publier la collecte. Les exports volumineux et uploads
doivent tenir compte des [limites des fonctions Vercel](https://vercel.com/docs/functions/limitations) :
prévoir un transfert privé direct vers le stockage lorsque nécessaire,
pas un gros ZIP transporté aveuglément par une fonction.

### B4. Publier la variante sur Netlify

Même prérequis : un **frontend adapté et connecté au stockage**, pas un
glisser-déposer du dossier `collecte/static` actuel.

1. Crée un projet Netlify depuis le dépôt GitHub de ta variante.
2. Sélectionne le dossier contenant son `package.json` comme base.
3. Pour une sortie React/Vite standard, configure `npm run build` et `dist`.
   Les vrais paramètres doivent correspondre au projet généré.
4. Ajoute les variables publiques de connexion définies dans son fichier
   d'exemple. Aucune clé administrateur dans une variable préfixée `VITE_`.
5. Si l'app utilise des routes côté navigateur, configure le retour vers
   `index.html` prévu par le framework, sans masquer les éventuelles routes API.
6. Déploie, autorise l'URL HTTPS de production dans l'authentification,
   puis effectue la recette ci-dessous.

Sur les deux plateformes, une clé **publiable** ne remplace pas les politiques
d'accès : celles-ci sont ce qui empêche de lire les enregistrements des autres.
Référence de build : [Vite sur Netlify](https://docs.netlify.com/build/frameworks/framework-setup-guides/vite/).

### B5. « Gratuit » veut dire quoi ?

Repères consultés le **19 septembre 2026**, à recontrôler avant de créer un compte :

- **Vercel Hobby** : offre gratuite destinée à un usage personnel non commercial,
  avec limites ; vérifier l'éligibilité de son projet, notamment pour un service
  public ou commercial. [Conditions Hobby](https://vercel.com/docs/plans/hobby).
- **Netlify Free** : offre à crédits, avec une limite affichée de 300 crédits/mois.
  Builds et utilisation consomment des ressources ; ce n'est pas illimité.
  [Tarifs Netlify](https://www.netlify.com/pricing/).
- **Supabase Free** : notamment 1 Go de stockage de fichiers et 500 Mo de base
  affichés à cette date ; pause annoncée après une semaine d'inactivité.
  [Quotas et conditions Supabase](https://supabase.com/pricing).

Les audios, réécoutes, téléchargements, exports et sauvegardes font croître
l'usage. Choisir un plan gratuit ne garantit pas une année entière gratuite
ni une disponibilité permanente. Ne choisis pas une offre payante ou une
recharge automatique simplement pour finir une étape du tutoriel.

## C — Recette de vérification avant la vraie collecte

Pour ngrok comme pour une future variante cloud, vérifier avec un clip de
test non félin : connexion → enregistrement → sauvegarde → rechargement →
réécoute → changement de label → corbeille/restauration → export.

Pour le cloud, vérifier **en plus** :

- Le même clip reste disponible après un redéploiement et PC éteint.
- Une session privée sans connexion n'accède à aucune donnée ; un second
  compte n'accède pas aux clips du premier, même en réutilisant un identifiant.
- Les fichiers ne sont pas publics ; les liens temporaires expirent.
- Les clips `incertain` restent exclus de l'export d'entraînement et présents
  dans la sauvegarde complète.
- Un export permet de retrouver les WAV originaux et les annotations localement.
- Aucun micro ne démarre sans action explicite ; refus de permission et coupure
  réseau sont gérés sans perdre silencieusement le clip en attente.

Ajoute ensuite l'URL HTTPS à l'écran d'accueil du téléphone comme en A5.
L'entraînement du modèle reste une étape séparée, et aucune de ces méthodes
ne transforme la collecte en traducteur personnel déjà validé.

## Quel prompt utiliser ?

- Pour **installer le code existant** : [INSTALL_WITH_AI.md](../INSTALL_WITH_AI.md).
- Pour **recréer une app avec un générateur/assistant** : [PROMPT_APP.md](../PROMPT_APP.md).
- Pour **comprendre l'expérience scientifique** : [tutoriel ML](tutoriel.md).

Les étapes ngrok décrivent le parcours du projet actuel. Les étapes cloud
sont conditionnées à une adaptation future : aucun déploiement Vercel,
Netlify ou Supabase n'a été effectué pour rédiger ce document.
