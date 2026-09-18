// Service worker minimal : juste ce qu'il faut pour être « installable » en PWA
// (ajout à l'écran d'accueil iPhone). On ne met PAS l'API en cache — les
// données doivent toujours être fraîches — on se contente de laisser passer.
self.addEventListener("install", (e) => self.skipWaiting());
self.addEventListener("activate", (e) => self.clients.claim());
self.addEventListener("fetch", (e) => {
  // Passe-plat réseau. En cas de coupure, on ne sert rien de périmé.
  return;
});
