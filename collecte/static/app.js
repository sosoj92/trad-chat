"use strict";
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, c => ({
  "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
}[c]));
const noms = {faim:"Faim", porte:"Porte", calin:"Câlin", jeu:"Jeu", mecontent:"Mécontent",
  douleur_alerte:"Douleur / alerte", nuit:"Nuit", autre:"Autre vocalise", incertain:"Incertain"};
let TOKEN = (new URLSearchParams(location.search).get("token") || "").trim();
try {
  if (TOKEN) localStorage.setItem("token", TOKEN);
  else TOKEN = localStorage.getItem("token") || "";
} catch (_) {}
// Retirer le secret de l'adresse après lecture.
if (TOKEN) history.replaceState(null, "", location.pathname);
let LABELS = [], EXCLUS = [], envoi = false, brouillon = null, capture = null;
let recents = new Map(), editionId = null, audioLecture = null, urlLecture = null;
let messageTimer;

function msg(texte, type="warn", duree=5000) {
  clearTimeout(messageTimer);
  $("zoneMsg").innerHTML = '<div class="msg ' + type + '">' + escapeHTML(texte) + "</div>";
  if (duree) messageTimer = setTimeout(() => { $("zoneMsg").textContent = ""; }, duree);
}
async function api(chemin, opts={}) {
  opts.headers = {"X-Token": TOKEN, "ngrok-skip-browser-warning": "true", ...opts.headers};
  opts.cache = "no-store";
  const r = await fetch(chemin, opts);
  if (r.status === 401) {
    $("connexion").classList.remove("cache");
    msg("Connexion requise : colle ta clé. Ton clip reste en attente.", "err", 0);
    throw new Error("401");
  }
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error(typeof detail.detail === "string" ? detail.detail : "Erreur serveur (" + r.status + ")");
  }
  return r;
}
function erreur(e) { if (e.message !== "401") msg(e.message || "Opération impossible.", "err", 0); }

// Un seul clip en attente, persistant sur ce navigateur si IndexedDB est disponible.
function ouvrirDB() {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open("miaou-collecte", 1);
    r.onupgradeneeded = () => r.result.createObjectStore("attente");
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}
async function stockerBrouillon(valeur, lecture=false) {
  const db = await ouvrirDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("attente", lecture ? "readonly" : "readwrite");
    const s = tx.objectStore("attente");
    const r = lecture ? s.get("clip") : (valeur ? s.put(valeur, "clip") : s.delete("clip"));
    tx.oncomplete = () => { db.close(); resolve(r.result); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}
function sauverAttente() {
  if (brouillon) brouillon.annotation = lireAnnotation("cap");
  return stockerBrouillon(brouillon).catch(() => {
    msg("Stockage local indisponible : garde cette page ouverte jusqu’à l’envoi.", "warn", 0);
  });
}
function champsAnnotation(prefixe, valeurs={}) {
  const champ = (nom, titre, type="text") => '<label class="champ">' + titre +
    '<input id="' + prefixe + "-" + nom + '" type="' + type + '" value="' +
    escapeHTML(valeurs[nom] ?? "") + '"' +
    (type === "number" ? ' min="0" step="' + (nom.endsWith("_s") ? "0.01" : "1") + '"' : ' maxlength="80"') + '></label>';
  const choix = (nom, titre, options, defaut) => '<label class="champ">' + titre +
    '<select id="' + prefixe + "-" + nom + '">' + options.map(([v,t]) =>
      '<option value="' + v + '"' + ((valeurs[nom] ?? defaut) === v ? " selected" : "") + ">" + t + "</option>"
    ).join("") + "</select></label>";
  const texte = (nom, titre) => '<label class="champ">' + titre + '<textarea rows="2" maxlength="500" id="' +
    prefixe + "-" + nom + '">' + escapeHTML(valeurs[nom]) + "</textarea></label>";
  return choix("certitude", "À quel point es-tu sûre du contexte ?", [
    ["a_verifier","À vérifier — hors entraînement"],["probable","Probable"],["confirmee","Confirmé par mes observations"]
  ], "a_verifier") +
  choix("type_son", "Qu’as-tu enregistré ?", [["vocalise","Vocalise du chat"],["bruit","Bruit / non-vocalise"],["inconnu","Je ne sais pas"]], "vocalise") +
  '<details><summary>Ajouter le contexte observé</summary>' +
  champ("lieu", "Lieu au moment du son") +
  champ("minutes_depuis_repas", "Minutes depuis le repas (laisser vide si inconnu)", "number") +
  texte("observation_avant", "Ce que j’observais au moment du son") +
  texte("observation_apres", "Ce qui s’est passé ensuite (pour vérifier mon étiquette)") +
  texte("note", "Note libre") + '</details>' +
  '<details><summary>Choisir l’extrait utile</summary><p class="sous">Indique les secondes de début et de fin après réécoute. L’original reste intact. Sans sélection, le futur entraînement utilisera une fenêtre sonore de 4 s.</p>' +
  '<div class="filtres">' + champ("debut_s", "Début (s)", "number") + champ("fin_s", "Fin (s), vide = tout", "number") + '</div>' +
  '<button class="mini" type="button" data-extrait="' + prefixe + '">Écouter cet extrait</button></details>';
}
function lireAnnotation(prefixe) {
  const texte = nom => $(prefixe + "-" + nom).value.trim();
  return {certitude:texte("certitude"), type_son:texte("type_son"), lieu:texte("lieu"),
    minutes_depuis_repas:texte("minutes_depuis_repas") === "" ? null : Number(texte("minutes_depuis_repas")),
    observation_avant:texte("observation_avant"), observation_apres:texte("observation_apres"),
    note:texte("note"), debut_s:Number(texte("debut_s") || 0),
    fin_s:texte("fin_s") === "" ? null : Number(texte("fin_s"))};
}
function brancherExtrait(container, prefixe, player) {
  container.querySelector("[data-extrait]").onclick = async () => {
    const a = lireAnnotation(prefixe);
    const fin = a.fin_s ?? player.duration;
    if (!Number.isFinite(fin) || a.debut_s < 0 || fin <= a.debut_s || fin > player.duration + 0.02) {
      msg("Choisis un intervalle dans la durée du clip.", "err"); return;
    }
    player.currentTime = a.debut_s;
    player.ontimeupdate = () => { if (player.currentTime >= fin) { player.pause(); player.ontimeupdate = null; } };
    try { await player.play(); } catch (e) { erreur(e); }
  };
}
function montrerBrouillon() {
  const prev = $("preview");
  prev.pause(); prev.ontimeupdate = null;
  if (prev.src.startsWith("blob:")) URL.revokeObjectURL(prev.src);
  prev.src = URL.createObjectURL(brouillon.blob);
  $("annotationCapture").innerHTML = champsAnnotation("cap", brouillon.annotation);
  brancherExtrait($("annotationCapture"), "cap", prev);
  $("annotationCapture").onchange = () => sauverAttente();
  $("carteLabel").classList.remove("cache");
  $("btnRec").disabled = true;
  $("etatEnvoi").textContent = "À sauvegarder — choisis le contexte ci-dessous.";
}

// Capture PCM en premier plan. Session = série de captures séparées de moins de 30 min.
let ctx, source, processeur, flux, pre, preWrite=0, preFilled=0, preLen=0;
let enCours=false, recChunks=[], t0=0, timerId, sessionId=null, derniereCapture=0, jourSession=null, finalisation=false;
const PREBUFFER_S=5, SR_CIBLE=16000;
const uuid = () => crypto.randomUUID();
function nouvelleCapture() {
  const maintenant = new Date();
  const local = new Date(maintenant.getTime() - maintenant.getTimezoneOffset()*60000).toISOString().slice(0,10);
  if (!sessionId || local !== jourSession || Date.now() - derniereCapture > 30 * 60 * 1000) sessionId = uuid();
  derniereCapture = Date.now(); jourSession = local;
  return {capture_id:uuid(), session_id:sessionId, date_capture:maintenant.toISOString(), jour_capture:local};
}
function recevoirPCM(inp) {
  for (const v of inp) {
    pre[preWrite] = v; preWrite = (preWrite + 1) % preLen;
    preFilled = Math.min(preLen, preFilled + 1);
  }
  if (enCours) recChunks.push(new Float32Array(inp));
}
async function activerMicro() {
  $("btnMicro").disabled = true;
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    await ctx.resume();
    flux = await navigator.mediaDevices.getUserMedia({audio:{
      echoCancellation:false, noiseSuppression:false, autoGainControl:false}});
    preLen = Math.floor(PREBUFFER_S * ctx.sampleRate);
    pre = new Float32Array(preLen); preWrite=0; preFilled=0;
    source = ctx.createMediaStreamSource(flux);
    if (ctx.audioWorklet) {
      await ctx.audioWorklet.addModule("/static/capture-worklet.js");
      processeur = new AudioWorkletNode(ctx, "capture-pcm");
      processeur.port.onmessage = e => recevoirPCM(e.data);
    } else {
      processeur = ctx.createScriptProcessor(4096,1,1);
      processeur.onaudioprocess = e => recevoirPCM(e.inputBuffer.getChannelData(0));
    }
    source.connect(processeur); processeur.connect(ctx.destination);
    flux.getAudioTracks()[0].onended = () => desactiverMicro();
    $("carteMicro").classList.add("cache"); $("carteRec").classList.remove("cache");
    $("btnRec").disabled = !!brouillon;
  } catch (_) {
    await desactiverMicro();
    msg("Micro inaccessible. Ouvre l’app en HTTPS et autorise le microphone dans le navigateur.", "err", 0);
  } finally { $("btnMicro").disabled = false; }
}
async function desactiverMicro() {
  if (enCours) await arreter();
  if (flux) flux.getTracks().forEach(t => t.stop());
  if (processeur) processeur.disconnect();
  if (source) source.disconnect();
  if (ctx && ctx.state !== "closed") await ctx.close();
  flux=null; processeur=null; source=null;
  $("carteMicro").classList.remove("cache"); $("carteRec").classList.add("cache");
}
function demarrer() {
  if (brouillon || finalisation || !ctx || ctx.state !== "running") return;
  capture = nouvelleCapture();
  const tampon = new Float32Array(preFilled), debut=(preWrite-preFilled+preLen)%preLen;
  for (let i=0;i<preFilled;i++) tampon[i]=pre[(debut+i)%preLen];
  recChunks=[tampon]; enCours=true; t0=Date.now();
  $("btnRec").classList.add("rec"); $("btnRecTxt").textContent="Stop";
  timerId=setInterval(() => {
    const secondes=(Date.now()-t0)/1000;
    $("timer").textContent="● " + secondes.toFixed(1) + " s + pré-tampon";
    if (secondes>=120) arreter();
  },100);
}
async function reechantillonner(data, srcRate, dstRate) {
  if (srcRate === dstRate) return data;
  // Le moteur audio applique son rééchantillonnage, pas une modification d'en-tête.
  const Offline = window.OfflineAudioContext || window.webkitOfflineAudioContext;
  const rendu = new Offline(1, Math.max(1, Math.round(data.length*dstRate/srcRate)), dstRate);
  const buffer = rendu.createBuffer(1,data.length,srcRate);
  buffer.copyToChannel(data,0);
  const s = rendu.createBufferSource(); s.buffer=buffer; s.connect(rendu.destination); s.start();
  return (await rendu.startRendering()).getChannelData(0);
}
function encoderWav(data, sr) {
  const buf=new ArrayBuffer(44+data.length*2), v=new DataView(buf);
  const txt=(o,s) => {for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};
  txt(0,"RIFF");v.setUint32(4,36+data.length*2,true);txt(8,"WAVE");
  txt(12,"fmt ");v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);
  v.setUint32(24,sr,true);v.setUint32(28,sr*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);
  txt(36,"data");v.setUint32(40,data.length*2,true);
  data.forEach((x,i)=>{const s=Math.max(-1,Math.min(1,x));v.setInt16(44+2*i,s<0?s*32768:s*32767,true);});
  return new Blob([buf],{type:"audio/wav"});
}
async function arreter() {
  if (!enCours || finalisation) return;
  enCours=false;finalisation=true;clearInterval(timerId);
  $("btnRec").disabled=true;$("btnRec").classList.remove("rec");$("btnRecTxt").textContent="Enregistrer";
  const taux=ctx.sampleRate;
  try {
    const plat=new Float32Array(recChunks.reduce((s,c)=>s+c.length,0));
    let o=0;for(const c of recChunks){plat.set(c,o);o+=c.length;}
    // Le timer peut se déclencher un peu tard : respecter la limite serveur.
    const data=await reechantillonner(plat.subarray(0, Math.floor(125*taux)),taux,SR_CIBLE);
    brouillon={blob:encoderWav(data,SR_CIBLE),capture,annotation:{debut_s:0,certitude:"a_verifier",type_son:"vocalise"}};
    recChunks=[];
    montrerBrouillon();await sauverAttente();
    $("carteLabel").scrollIntoView({behavior:"smooth"});
    $("timer").textContent="Clip prêt à annoter";
  } catch(e) { erreur(e); }
  finally { finalisation=false; }
}
document.addEventListener("visibilitychange",()=>{
  if(document.hidden && flux) {
    desactiverMicro().catch(erreur);
    msg("Micro arrêté en quittant l’app. Réactive-le pour la prochaine capture.", "warn",0);
  }
});

async function envoyer(label) {
  if (!brouillon || envoi) return;
  envoi=true;$("btnAnnuler").disabled=true;
  $("tuiles").querySelectorAll("button").forEach(b=>b.disabled=true);
  try {
    await sauverAttente();
    const fd=new FormData();fd.append("fichier",brouillon.blob,"miaou.wav");fd.append("label",label);
    fd.append("metadata",JSON.stringify({...brouillon.annotation,...brouillon.capture}));
    $("etatEnvoi").textContent="Envoi en cours…";
    const j=await (await api("/api/upload",{method:"POST",body:fd})).json();
    brouillon=null;
    await stockerBrouillon(null).catch(()=>{}); // idempotence protège une reprise après échec de suppression locale
    $("carteLabel").classList.add("cache");$("btnRec").disabled=false;
    msg(j.avertissement || "Sauvegardé : " + (noms[label]||label),j.avertissement?"warn":"ok");
    await rafraichir().catch(() => msg("Clip sauvegardé. Actualisation de la liste indisponible ; recharge la page plus tard.", "warn", 0));
  } catch(e) {
    $("etatEnvoi").textContent="Non envoyé. Ton clip est conservé ; réessaie en choisissant la catégorie.";
    erreur(e);
  } finally {
    envoi=false;$("btnAnnuler").disabled=false;
    $("tuiles").querySelectorAll("button").forEach(b=>b.disabled=false);
  }
}
async function chargerLabels() {
  const j=await (await api("/api/labels")).json();LABELS=j.labels;EXCLUS=j.labels_exclus||[];
  $("titreCollecte").textContent=j.chat?.nom ? "🐱 Collecte — " + j.chat.nom : "🐱 Collecte de miaulements";
  $("tuiles").innerHTML="";
  LABELS.forEach(l=>{const b=document.createElement("button");b.className="tuile";b.textContent=noms[l]||l;b.onclick=()=>envoyer(l);$("tuiles").appendChild(b);});
  const ancien=$("filtreLabel").value;
  $("filtreLabel").innerHTML='<option value="">Toutes les catégories</option>'+
    LABELS.map(l=>'<option value="'+escapeHTML(l)+'">'+escapeHTML(noms[l]||l)+'</option>').join("");
  $("filtreLabel").value=ancien;
}
async function rafraichir() {
  const s=await (await api("/api/stats")).json();
  $("total").textContent="("+s.total+")";
  $("bilan").textContent=s.total_entrainable+" étiquetés utilisables · "+s.quarantaine+" incertains · "+s.a_verifier+" à vérifier";
  const puce=l=>'<span class="puce '+(EXCLUS.includes(l)?"quarantaine":"")+'">'+
    escapeHTML(noms[l]||l)+' <b>'+(s.stats[l]||0)+'</b>'+
    (EXCLUS.includes(l)?' — quarantaine':'<br><small>'+(s.entrainables[l]||0)+' utilisables · '+(s.jours_par_classe[l]||0)+' jours</small>')+'</span>';
  $("compteurs").innerHTML=LABELS.filter(l=>!EXCLUS.includes(l)).map(puce).join("")+
    '<span class="sep" aria-hidden="true"></span>'+LABELS.filter(l=>EXCLUS.includes(l)).map(puce).join("");
  await chargerRecents();
}
async function chargerRecents() {
  const filtres=new URLSearchParams({n:"100",label:$("filtreLabel").value});
  if($("filtreEtat").value)filtres.set($("filtreEtat").value,"true");
  const j=await (await api("/api/recents?"+filtres)).json();
  recents=new Map(j.recents.map(r=>[r.id,r]));
  $("tailleListe").textContent=j.recents.length+" affichés sur "+j.total_filtre;
  $("recents").innerHTML=j.recents.length?"":'<p class="sous">Aucun enregistrement dans ce filtre.</p>';
  for(const it of j.recents) {
    const wrap=document.createElement("div");
    const id=escapeHTML(it.id);
    const statut=it.motif_exclusion?(it.motif_exclusion==="quarantaine"?"En quarantaine":"À vérifier / hors dataset"):"Étiqueté utilisable";
    wrap.innerHTML='<div class="rec-item"><button class="mini" aria-label="Écouter" data-play="'+id+'">▶</button>'+
      '<div class="rec-meta"><button class="lbl-chip" data-toggle="'+id+'" '+(it.supprime?"disabled":"")+'>'+escapeHTML(noms[it.label]||it.label)+' ✎</button>'+
      '<div class="sub">'+escapeHTML(it.date?.replace("T"," ")||"Date inconnue")+' · '+it.duree_s+' s<br>'+statut+
      (it.note?' · '+escapeHTML(it.note):'')+'</div></div>'+
      (it.supprime?'<button class="mini" data-restore="'+id+'">Restaurer</button>':
       '<button class="mini" data-edit="'+id+'">Détails</button><button class="mini danger" aria-label="Mettre à la corbeille" data-del="'+id+'">✕</button>')+'</div>'+
      '<div class="relabel-picker cache" id="pick-'+id+'">'+LABELS.map(l=>'<button class="tuile-mini" data-rl="'+id+'" data-to="'+escapeHTML(l)+'">'+escapeHTML(noms[l]||l)+'</button>').join("")+'</div>';
    $("recents").appendChild(wrap);
  }
}
async function fichierAudio(id) {
  return URL.createObjectURL(await (await api("/api/audio/"+encodeURIComponent(id))).blob());
}
$("recents").onclick=async e=>{
  const b=e.target.closest("button");if(!b)return;
  try {
    if(b.dataset.toggle) { $("pick-"+b.dataset.toggle).classList.toggle("cache");return; }
    if(b.dataset.play) {
      if(audioLecture)audioLecture.pause();
      if(urlLecture)URL.revokeObjectURL(urlLecture);
      urlLecture=await fichierAudio(b.dataset.play);audioLecture=new Audio(urlLecture);await audioLecture.play();return;
    }
    if(b.dataset.edit) {await ouvrirEdition(b.dataset.edit);return;}
    let route,id;
    if(b.dataset.rl){route="relabel";id=b.dataset.rl;}
    if(b.dataset.del){if(!confirm("Mettre dans la corbeille ? L’audio pourra être restauré."))return;route="supprimer";id=b.dataset.del;}
    if(b.dataset.restore){route="restaurer";id=b.dataset.restore;}
    if(!route)return;
    b.disabled=true;
    const fd=new FormData();fd.append("id_",id);if(route==="relabel")fd.append("label",b.dataset.to);
    await api("/api/"+route,{method:"POST",body:fd});await rafraichir();
    msg(route==="relabel"?"Catégorie corrigée. Vérifie aussi la certitude dans Détails.":"Modification sauvegardée.","ok");
  } catch(e){erreur(e);} finally {b.disabled=false;}
};
async function ouvrirEdition(id) {
  const record=recents.get(id);editionId=id;
  $("annotationEdition").innerHTML=champsAnnotation("edit",{...record,type_son:record.type_son||"inconnu",debut_s:record.debut_s||0});
  $("editPreview").pause(); $("editPreview").ontimeupdate=null;
  if($("editPreview").src.startsWith("blob:"))URL.revokeObjectURL($("editPreview").src);
  $("editPreview").src=await fichierAudio(id);
  brancherExtrait($("annotationEdition"),"edit",$("editPreview"));
  $("edition").showModal();
}
$("formEdition").onsubmit=async e=>{
  e.preventDefault();
  const b=e.submitter;b.disabled=true;
  try{
    await api("/api/annotations/"+encodeURIComponent(editionId),{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(lireAnnotation("edit"))});
    $("editPreview").pause();$("edition").close();await rafraichir();msg("Observations sauvegardées.","ok");
  }catch(e){erreur(e);}finally{b.disabled=false;}
};
$("fermerEdition").onclick=()=>{$("editPreview").pause();$("edition").close();};
async function telecharger(mode,bouton) {
  bouton.disabled=true;
  try{
    const url=URL.createObjectURL(await (await api("/api/export?mode="+mode)).blob());
    const a=document.createElement("a");a.href=url;a.download="miaou-"+mode+".zip";document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),60000);
  }catch(e){erreur(e);}finally{bouton.disabled=false;}
}
$("exportTrain").onclick=()=>telecharger("entrainement",$("exportTrain"));
$("exportBackup").onclick=()=>telecharger("sauvegarde",$("exportBackup"));
$("filtreLabel").onchange=()=>chargerRecents().catch(erreur);
$("filtreEtat").onchange=()=>chargerRecents().catch(erreur);
$("btnMicro").onclick=activerMicro;$("btnMicroOff").onclick=()=>desactiverMicro().catch(erreur);
$("btnRec").onclick=()=>enCours?arreter():demarrer();
$("btnAnnuler").onclick=async()=>{
  if(!confirm("Abandonner le clip non envoyé ?"))return;
  brouillon=null;await stockerBrouillon(null).catch(()=>{});
  $("preview").pause();$("carteLabel").classList.add("cache");$("btnRec").disabled=false;
};
$("connexion").onsubmit=async event=>{
  event.preventDefault();const b=event.currentTarget.querySelector("button");b.disabled=true;
  TOKEN=$("tokenConnexion").value.trim();
  try{
    await chargerLabels();await rafraichir();
    try{localStorage.setItem("token",TOKEN);}catch(_){}
    $("connexion").classList.add("cache");$("tokenConnexion").value="";msg("Connexion réussie.","ok");
  }catch(e){erreur(e);}finally{b.disabled=false;}
};
async function initialiser(){
  if(!TOKEN)$("connexion").classList.remove("cache");
  try{brouillon=await stockerBrouillon(null,true);if(brouillon)montrerBrouillon();}catch(_){}
  if(TOKEN){try{await chargerLabels();await rafraichir();}catch(e){erreur(e);}}
  if("serviceWorker" in navigator)navigator.serviceWorker.register("/sw.js").catch(()=>{});
}
initialiser();
