"""Démo locale jetable : aucun accès au dataset personnel, arrêt après 10 min."""
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import uvicorn

from collecte import serveur, stockage
from tests.test_collecte import wav_test


def main():
    with tempfile.TemporaryDirectory(prefix="miaou-demo-") as dossier:
        with patch.object(stockage, "_base", return_value=Path(dossier)), \
                patch.object(serveur, "_TOKEN", "demo-locale-synthetique"):
            for i, label in enumerate(("faim", "incertain", "porte")):
                stockage.enregistrer_audio({
                    "id": f"demo-{i}", "capture_id": f"demo-capture-{i}",
                    "date": f"2026-09-18T10:0{i}:00+02:00", "jour_capture": "2026-09-18",
                    "session_id": "demo-session", "label": label,
                    "certitude": "a_verifier" if label == "incertain" else "probable",
                    "type_son": "vocalise", "fichier": f"{label}/demo-{i}.wav",
                    "duree_s": 1, "debut_s": 0, "fin_s": None,
                    "note": "Démonstration synthétique — aucun véritable enregistrement",
                }, wav_test())
            server = uvicorn.Server(uvicorn.Config(serveur.app, host="127.0.0.1", port=8772,
                                                    log_level="warning", access_log=False))
            timer = threading.Timer(600, lambda: setattr(server, "should_exit", True))
            timer.daemon = True
            timer.start()
            print("Démo synthétique sur http://127.0.0.1:8772 — arrêt automatique dans 10 min", flush=True)
            try:
                server.run()
            finally:
                timer.cancel()


if __name__ == "__main__":
    main()
