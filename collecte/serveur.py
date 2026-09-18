"""Collecte privée : annotations, originaux, exports et préparation supervisée.

Lancer avec un seul worker : python -m collecte.serveur.
"""
from __future__ import annotations

import io
import json
import secrets
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import numpy as np
from fastapi import Depends, FastAPI, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from collecte import detection, stockage
from collecte.annotations import Annotation, Capture, verifier_duree
from collecte.exporter import exporter
from core.annotations import jour_record, motif_exclusion
from core.config import charger_config, labels as get_labels, labels_exclus as get_labels_exclus
from core.journalisation import configurer_journalisation, obtenir_logger

log = obtenir_logger(__name__)
_STATIC = Path(__file__).parent / "static"
_config = charger_config()
_labels = get_labels(_config)
_labels_exclus = get_labels_exclus(_config)
_collecte_cfg = _config.get("collecte", {})
_TOKEN = str(_collecte_cfg.get("token", ""))

app = FastAPI(title="Collecte miaulements", docs_url=None, redoc_url=None)


def verifier_token(x_token: str | None = Header(default=None),
                   token: str | None = Query(default=None)) -> None:
    fourni = x_token or token or ""
    if not _TOKEN or not secrets.compare_digest(fourni.encode(), _TOKEN.encode()):
        raise HTTPException(401, "Token invalide ou manquant.")


@app.get("/")
def page_accueil() -> FileResponse:
    return FileResponse(_STATIC / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/sw.js")
def service_worker() -> FileResponse:
    return FileResponse(_STATIC / "sw.js", media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})


@app.get("/manifest.webmanifest")
def manifest_pwa() -> FileResponse:
    return FileResponse(_STATIC / "manifest.webmanifest", media_type="application/manifest+json")


def motif_record(record: dict) -> str | None:
    motif = motif_exclusion(record, _labels, _labels_exclus)
    if motif is not None:
        return motif
    try:
        if not stockage.chemin_wav(record).is_file():
            return "audio_manquant"
    except (ValueError, KeyError):
        return "audio_invalide"
    return None


def public_record(record: dict) -> dict:
    resultat = {k: v for k, v in record.items() if k != "fichier"}
    resultat["audio"] = f'/api/audio/{record["id"]}'
    resultat["motif_exclusion"] = motif_record(record)
    return resultat


@app.get("/api/labels", dependencies=[Depends(verifier_token)])
def api_labels() -> dict:
    return {"labels": _labels, "labels_exclus": _labels_exclus}


@app.get("/api/stats", dependencies=[Depends(verifier_token)])
def api_stats() -> dict:
    records = stockage.tous()
    compteur, entrainables = dict.fromkeys(_labels, 0), dict.fromkeys(_labels, 0)
    jours = {label: set() for label in _labels}
    quarantaine, a_verifier = 0, 0
    for r in records:
        label = r["label"]
        compteur[label] = compteur.get(label, 0) + 1
        motif = motif_record(r)
        if motif is None:
            entrainables[label] += 1
            jours[label].add(jour_record(r))
        elif motif == "quarantaine":
            quarantaine += 1
        else:
            a_verifier += 1
    return {"stats": compteur, "total": len(records), "entrainables": entrainables,
            "total_entrainable": sum(entrainables.values()), "quarantaine": quarantaine,
            "a_verifier": a_verifier, "jours_par_classe": {k: len(v) for k, v in jours.items()},
            "modele_personnel": "non_entraine"}


@app.get("/api/recents", dependencies=[Depends(verifier_token)])
def api_recents(n: int = Query(default=50, ge=1, le=1000), label: str = "",
                a_verifier: bool = False, corbeille: bool = False) -> dict:
    records = [r for r in stockage.tous(inclure_supprimes=corbeille)
               if bool(r.get("supprime")) == corbeille]
    if label:
        records = [r for r in records if r["label"] == label]
    if a_verifier:
        records = [r for r in records if motif_record(r)]
    return {"recents": [public_record(r) for r in records[:n]], "total_filtre": len(records)}


@app.post("/api/upload", dependencies=[Depends(verifier_token)])
async def api_upload(fichier: UploadFile, label: str = Form(...), note: str = Form(default=""),
                     metadata: str = Form(default="")) -> JSONResponse:
    if label not in _labels:
        raise HTTPException(400, "Label inconnu")
    maintenant = datetime.now().astimezone()
    try:
        # Compatibilité ancien frontend : données manquantes signalées à vérifier.
        valeurs = json.loads(metadata) if metadata else {
            "capture_id": str(uuid4()), "session_id": "legacy-" + maintenant.date().isoformat(),
            "date_capture": maintenant.isoformat(), "jour_capture": maintenant.date().isoformat(),
            "note": note,
        }
        annotation = Capture.model_validate(valeurs)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(422, "Annotations invalides : " + str(exc)) from exc

    donnees = await fichier.read(10 * 1024 * 1024 + 1)
    if len(donnees) > 10 * 1024 * 1024:
        raise HTTPException(413, "Fichier trop volumineux (10 Mo maximum)")
    try:
        with wave.open(io.BytesIO(donnees), "rb") as w:
            sr, canaux, largeur, frames = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
            brut = w.readframes(frames)
        if (sr, canaux, largeur) != (16000, 1, 2) or len(brut) != frames * 2 or not frames:
            raise ValueError("WAV requis : PCM 16 bits, mono, 16 kHz, non vide")
        duree = frames / sr
        if duree > 125:
            raise ValueError("125 secondes maximum")
        verifier_duree(annotation, duree)
    except (ValueError, wave.Error, EOFError) as exc:
        raise HTTPException(422, str(exc) or "WAV invalide") from exc

    y = np.frombuffer(brut, dtype="<i2").astype(np.float32) / 32768
    analyse = detection.analyser(y, sr)  # ancien booléen conservé, jamais présenté comme preuve
    alertes = []
    if np.max(np.abs(y)) < 0.003:
        alertes.append("Niveau sonore faible : vérifie en réécoutant.")
    if float(np.mean(np.abs(y) >= 0.999)) > 0.01:
        alertes.append("Saturation possible : éloigne un peu le micro.")
    if duree < 0.25:
        alertes.append("Extrait très court.")
    id_ = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f") + "_" + uuid4().hex[:8]
    record = {**annotation.model_dump(mode="json"), "id": id_, "label": label,
              "date": annotation.date_capture.isoformat(), "recu_le": maintenant.isoformat(),
              "fichier": f"{label}/{id_}.wav", **analyse, "supprime": False,
              "audio_valide": True, "sample_rate": sr, "canaux": canaux,
              "qualite": alertes, "schema_version": 2}
    record, nouveau = stockage.enregistrer_audio(record, donnees)
    return JSONResponse({"ok": True, "id": record["id"], "doublon_evite": not nouveau,
                         "analyse": analyse, "avertissement": " ".join(record.get("qualite", [])) or None})


@app.get("/api/audio/{id_}", dependencies=[Depends(verifier_token)])
def api_audio(id_: str) -> FileResponse:
    record = stockage.par_id(id_)
    if record is None:
        raise HTTPException(404, "Introuvable")
    chemin = stockage.chemin_wav(record)
    if not chemin.is_file():
        raise HTTPException(404, "Fichier absent")
    return FileResponse(chemin, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@app.patch("/api/annotations/{id_}", dependencies=[Depends(verifier_token)])
def api_annotations(id_: str, annotation: Annotation) -> dict:
    record = stockage.par_id(id_)
    if record is None or record.get("supprime"):
        raise HTTPException(404, "Introuvable")
    try:
        verifier_duree(annotation, float(record.get("duree_s", 0)))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    resultat = stockage.modifier(id_, annotation.model_dump(mode="json"))
    if resultat is None:
        raise HTTPException(404, "Introuvable")
    return {"ok": True, "record": public_record(resultat)}


@app.post("/api/relabel", dependencies=[Depends(verifier_token)])
def api_relabel(id_: str = Form(...), label: str = Form(...)) -> dict:
    if label not in _labels:
        raise HTTPException(400, "Label inconnu")
    if stockage.rebaptiser(id_, label) is None:
        raise HTTPException(404, "Introuvable")
    return {"ok": True}


@app.post("/api/supprimer", dependencies=[Depends(verifier_token)])
def api_supprimer(id_: str = Form(...)) -> dict:
    if not stockage.supprimer(id_):
        raise HTTPException(404, "Introuvable")
    return {"ok": True}


@app.post("/api/restaurer", dependencies=[Depends(verifier_token)])
def api_restaurer(id_: str = Form(...)) -> dict:
    try:
        if not stockage.restaurer(id_):
            raise HTTPException(404, "Introuvable")
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"ok": True}


@app.get("/api/export", dependencies=[Depends(verifier_token)])
def api_export(mode: Literal["entrainement", "sauvegarde"] = "entrainement"):
    return StreamingResponse(exporter(mode, _labels, _labels_exclus), media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="miaou-{mode}.zip"',
                                      "Cache-Control": "no-store"})


app.mount("/static", StaticFiles(directory=_STATIC), name="static")


def lancer() -> None:
    import uvicorn
    configurer_journalisation(_config)
    if _TOKEN in ("", "CHANGE-MOI-token-secret"):
        log.warning("Configure un token privé dans config.yaml.")
    uvicorn.run(app, host=str(_collecte_cfg.get("host", "0.0.0.0")),
                port=int(_collecte_cfg.get("port", 8771)), log_level="info")


if __name__ == "__main__":
    lancer()
