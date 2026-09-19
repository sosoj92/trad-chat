# Mettre l'application sur votre téléphone pour enregistrer votre chat

Vous souhaitez avoir une application sur votre téléphone, appuyer sur
« Enregistrer » quand votre chat miaule et retrouver les sons plus tard ?
Ce guide vous explique **où l'application fonctionne, comment l'ouvrir
sur le téléphone et comment la retrouver le lendemain**.

Il part de zéro : vous n'avez pas besoin de connaître les mots *serveur*,
*hébergement* ou *ngrok*.

## Qu'est-ce que « héberger une application » veut dire ?

Il faut un ordinateur quelque part pour faire tourner le programme qui
reçoit les enregistrements et les sauvegarde. **Héberger**, c'est faire
fonctionner ce programme sur une machine accessible aux appareils qui
l'utilisent. Le programme qui répond au téléphone s'appelle un **serveur**.

Dans la version actuelle, cette machine est **votre ordinateur** :

- Le téléphone affiche les boutons et capte le son avec son microphone.
- Le programme sur votre ordinateur reçoit le son et le conserve sur le disque.
- Un service nommé **ngrok** permet de les relier par une adresse Internet sécurisée.

ngrok ne déplace pas votre application sur ses serveurs : il **relaie la
connexion** vers votre ordinateur. On appelle cette liaison un *tunnel*.
Voilà pourquoi le PC doit rester allumé et connecté pour recevoir les sons.

Une adresse **HTTPS** chiffre le transport des données. Elle permet aussi
au navigateur du téléphone d'utiliser le microphone, avec votre autorisation.
Cela ne signifie pas que les fichiers enregistrés sur le disque sont chiffrés par l'app.

## Ce que vous allez obtenir

Vous ouvrirez une adresse dans Safari ou Chrome, puis pourrez l'ajouter à
l'écran d'accueil comme une app. C'est une **application web progressive**
(*PWA*), pas une application à chercher dans l'App Store ou Google Play.
Le raccourci n'installe pas le serveur sur le téléphone et ne rend pas
toute l'application utilisable sans connexion.

**Pour commencer aujourd'hui : suivez la partie A ci-dessous.**
La [partie B](#b--sans-ordinateur-allumé--préparer-une-variante-cloud) explique
une autre possibilité : louer ou utiliser la machine d'un prestataire,
souvent appelée hébergement *cloud*, pour ne plus laisser le PC allumé.
Cette variante demande une adaptation qui n'est pas encore réalisée ici.

## A — Installer l'application sur le téléphone avec votre ordinateur

### A1. Préparer et lancer l'app sur l'ordinateur

Si c'est votre première installation, suivez les étapes 1 à 3 du
[guide d'installation débutant](installation.md). Elles expliquent comment
télécharger les fichiers et ouvrir un **terminal**, la fenêtre dans laquelle
on tape les commandes.

Si l'app fonctionne déjà sur votre PC, gardez cette installation.
Ne recréez ni dossier ni clé, et ne fermez pas le serveur déjà lancé.

Pour lancer un serveur arrêté, ouvrez le terminal **dans le dossier du
projet**, puis exécutez :

```bash
uv run --no-sync python -m collecte.serveur
```

**Résultat attendu :** le programme reste actif dans cette fenêtre.
Sur le PC, [http://127.0.0.1:8771](http://127.0.0.1:8771) affiche la page de collecte.
Gardez ce premier terminal ouvert.

`8771` est le **port**, un numéro qui permet de joindre le bon programme.
Si vous l'avez changé dans vos réglages, utilisez votre numéro à chaque étape.
L'adresse `127.0.0.1` désigne l'appareil qui l'ouvre : elle ne permet pas
au téléphone de trouver votre PC.

### A2. Installer le service qui donnera une adresse à l'app

1. Sur l'ordinateur, ouvrez le [site officiel ngrok](https://ngrok.com/docs/getting-started/).
2. Créez votre propre compte et choisissez une offre adaptée à votre usage.
   Une offre gratuite existe avec des limites ; aucun forfait payant n'est nécessairement requis pour cet essai.
3. Installez le logiciel ngrok pour votre système en suivant ses instructions.
   Pour Windows : [page officielle de téléchargement](https://ngrok.com/download/windows).
4. Ouvrez un **deuxième terminal**, sans fermer celui du serveur.
5. Tapez `ngrok version`, puis Entrée.

**Résultat attendu :** un numéro de version. Si la commande est introuvable,
terminez l'installation de ngrok et rouvrez le deuxième terminal avant la suite.

Votre compte ngrok fournit un code secret pour associer le logiciel à votre
compte. Le site l'appelle **authtoken**. Dans le tableau de bord ngrok,
copiez la commande d'association proposée, puis exécutez-la localement.
Elle a la forme suivante ; le texte entre guillemets doit être remplacé par
**votre code ngrok**, sans nous l'envoyer :

```bash
ngrok config add-authtoken "VOTRE_CODE_NGROK_A_REMPLACER"
```

Faites cette étape **hors vidéo et hors partage d'écran**.
Ce code est différent de la clé de connexion de l'application :

| Code | À quoi sert-il ? | Où l'utiliser ? |
|---|---|---|
| Authtoken ngrok | Relier le logiciel ngrok à votre compte | Dans la commande d'association sur le PC |
| Clé de collecte | Protéger l'accès aux sons de votre chat | Dans « Clé de connexion » sur la page de l'app |

**Résultat attendu :** ngrok confirme l'enregistrement de son code.
Si vous utilisez déjà ngrok pour un autre projet, ne changez pas sa configuration
et n'arrêtez pas ses connexions sans vérifier ce qui est déjà utilisé.

### A3. Créer l'adresse à ouvrir sur le téléphone

Toujours dans le deuxième terminal :

```bash
ngrok http 8771
```

**Résultat attendu :** ngrok affiche une adresse commençant par `https://`
et une liaison vers le port `8771`. Ce programme reste actif lui aussi.

Ouvrez **l'adresse HTTPS affichée** dans le navigateur du téléphone.
N'utilisez pas l'adresse d'une capture d'écran ou celle de la personne
qui présente le projet. S'il y a un avertissement ngrok, vérifiez que
l'adresse est bien la vôtre avant de continuer.

L'offre gratuite fournit actuellement un domaine de développement lié au
compte, c'est-à-dire un nom d'adresse attribué par ngrok. Il peut rester
identique entre deux lancements ; fiez-vous à ce que votre logiciel affiche,
pas à l'idée qu'il change forcément à chaque fois.
[Source : domaine et limites ngrok](https://ngrok.com/docs/pricing-limits/free-plan-limits).

Si le téléphone affiche la page de connexion de l'app, la liaison est établie.
Sinon, vérifiez d'abord que l'app s'ouvre encore sur le PC.

### A4. Vous connecter et enregistrer un premier son

Pour retrouver la clé de **l'application**, ouvrez au besoin un troisième
terminal dans le dossier du projet. Sans fermer les deux autres, lancez
cette commande hors vidéo :

```bash
uv run --no-sync python -m core.initialiser --afficher-cle
```

Sur le téléphone, saisissez la clé dans « Clé de connexion ».
Ne mettez pas la clé dans l'adresse Internet et ne la publiez pas.
N'utilisez pas le code ngrok à sa place.

Choisissez d'activer le microphone et acceptez la permission dans le navigateur.
Faites un court essai avec votre propre voix, puis arrêtez. Choisissez
**Bruit / non-vocalise** pour que cet essai ne serve pas à entraîner le modèle
de chat. Sauvegardez, rechargez la page et réécoutez le clip depuis
« Derniers enregistrements », puis mettez-le à la corbeille.

**Résultat attendu :** vous retrouvez le son après rechargement.
Vous pouvez maintenant commencer à enregistrer votre chat dans sa vie
normale, en suivant [les conseils de collecte](collecte.md).

### A5. Ajouter l'app à l'écran d'accueil

- **iPhone** : ouvrez l'adresse dans Safari, puis Partager → Sur l'écran d'accueil.
- **Android** : dans un navigateur compatible, cherchez « Installer l'application »
  ou « Ajouter à l'écran d'accueil ». Le libellé dépend du navigateur.

Ouvrez le raccourci et reconnectez-vous si nécessaire. Le navigateur et le
raccourci peuvent mémoriser la clé séparément. Gardez l'app au premier plan
pendant la capture : le micro s'arrête lorsqu'elle passe en arrière-plan.

**Résultat attendu :** une icône permet de rouvrir l'app facilement.
Cela ne supprime pas le besoin d'un PC allumé.

### A6. Revenir le lendemain

Gardez l'ordinateur allumé, connecté et sans mise en veille, ainsi que les
deux programmes actifs : le serveur de collecte et ngrok.

S'ils sont arrêtés, relancez dans deux terminaux distincts :

```bash
uv run --no-sync python -m collecte.serveur
```

```bash
ngrok http 8771
```

La première commande doit partir du dossier du projet. Il n'est pas
nécessaire de retélécharger le code, réinstaller Python ou créer une autre clé.
Ouvrez l'adresse HTTPS actuelle sur le téléphone ; si elle a changé,
remplacez éventuellement l'ancien raccourci.

Une erreur de type « site hors ligne » se vérifie dans cet ordre :

1. L'app s'ouvre-t-elle à l'adresse locale **sur le PC** ?
2. ngrok fonctionne-t-il et vise-t-il le même port que le serveur ?
3. Le téléphone ouvre-t-il l'adresse HTTPS actuellement affichée ?
4. Si seule la connexion est refusée, utilisez-vous la clé de cette installation ?

Une actualisation du téléphone ne rallume pas le PC. N'arrêtez pas tous les
programmes Python ou tous les tunnels pour dépanner.
Voir [le dépannage détaillé](depannage.md).

### A7. Garder ses sons privés et comprendre les limites du gratuit

Cette méthode peut utiliser l'offre gratuite ngrok **dans ses limites**.
Les réécoutes et les exports consomment aussi du transfert de données.
Vérifiez l'usage dans votre compte et les
[conditions actuelles](https://ngrok.com/docs/pricing-limits/free-plan-limits).

Les fichiers sont conservés sur votre PC, mais transitent par le prestataire
ngrok. Ne partagez ni vos clés ni les liens qui les contiennent.
Faites régulièrement une sauvegarde privée de la collecte. Pour conserver
aussi les sons `incertain`, choisissez **sauvegarde complète**, et non
seulement export d'entraînement.

Vous pouvez vous arrêter ici : **la partie suivante n'est pas nécessaire
pour enregistrer votre chat avec la version actuelle.**

## B — Sans ordinateur allumé : préparer une variante cloud

Cette partie est plus avancée. Vercel et Netlify sont des **hébergeurs** :
ils peuvent servir une application depuis leurs machines plutôt que depuis
votre PC. Ils ne sont pas les modèles d'IA du projet. Supabase, proposé
comme autre service dans l'exemple ci-dessous, peut conserver les comptes,
les annotations et les fichiers privés.

Quelques mots pour lire la suite : **frontend** = l'interface visible ;
**backend** = les services qui traitent ses demandes ; **base de données** =
le rangement structuré des annotations ; **stockage** = l'emplacement des
fichiers audio ; **déployer** = installer une version chez l'hébergeur.

Dans le code actuel, les WAV et leur liste d'annotations (`manifest.jsonl`)
sont écrits sur le disque du PC. Publier seulement la page web ne remplace
pas ce rangement, ni le programme qui reçoit les sons. Il faut adapter ces
parties avant de pouvoir fonctionner sans PC allumé.

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

Les étapes pour enregistrer depuis le téléphone avec un PC allumé sont
utilisables dans le projet actuel. Les étapes cloud sont conditionnées
à une adaptation future : aucun déploiement Vercel,
Netlify ou Supabase n'a été effectué pour rédiger ce document.
