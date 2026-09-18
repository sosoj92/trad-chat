"""Tests isolés : aucun appel ni aucune écriture dans data/mon_chat réel."""
import io
import json
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import wave
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import uvicorn

from collecte import serveur, stockage
from core.annotations import motif_exclusion
from core.segments import extraire_segment
from training.dataset_mon_chat import indexer_mon_chat
from training.validation_groupee import validation_imbriquee


def wav_test():
    sortie = io.BytesIO()
    with wave.open(sortie, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes((np.sin(np.arange(16000) * 0.2) * 2000).astype("<i2").tobytes())
    return sortie.getvalue()


class TestCollecte(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.racine = tempfile.TemporaryDirectory(prefix="miaou-tests-")
        cls.base = Path(cls.racine.name)
        cls.stock = patch.object(stockage, "_base", return_value=cls.base)
        cls.stock_mock = cls.stock.start()
        cls.token = patch.object(serveur, "_TOKEN", "test-token-isole")
        cls.token.start()
        cls.sock = socket.socket()
        cls.sock.bind(("127.0.0.1", 0))
        cls.url = f"http://127.0.0.1:{cls.sock.getsockname()[1]}"
        cls.server = uvicorn.Server(uvicorn.Config(serveur.app, log_level="error", access_log=False))
        cls.thread = threading.Thread(target=cls.server.run, kwargs={"sockets": [cls.sock]}, daemon=True)
        cls.thread.start()
        import time
        for _ in range(100):
            if cls.server.started: break
            time.sleep(0.05)
        if not cls.server.started: raise RuntimeError("Serveur test indisponible")

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(timeout=5)
        cls.sock.close()
        cls.stock.stop(); cls.token.stop()
        cls.racine.cleanup()

    def setUp(self):
        self.base = Path(self.racine.name) / self._testMethodName
        self.base.mkdir()
        self.stock_mock.return_value = self.base

    def requete(self, chemin, method="GET", donnees=None, content_type=None, auth=True):
        headers = {"X-Token": "test-token-isole"} if auth else {}
        if content_type: headers["Content-Type"] = content_type
        r = urllib.request.Request(self.url + chemin, data=donnees, headers=headers, method=method)
        return urllib.request.urlopen(r, timeout=10)

    def post(self, chemin, data):
        from urllib.parse import urlencode
        return json.load(self.requete(chemin, "POST", urlencode(data).encode(), "application/x-www-form-urlencoded"))

    def upload(self, identifiant, label="faim", **metadata):
        meta = {"capture_id": identifiant, "session_id": "session-test-1", "date_capture": "2026-09-18T08:00:00Z",
                "jour_capture": "2026-09-18", "certitude": "probable", "type_son": "vocalise", **metadata}
        boundary = "MIAOUTESTBOUNDARY"
        body = b""
        for nom, valeur in {"label": label, "metadata": json.dumps(meta)}.items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{nom}"\r\n\r\n{valeur}\r\n'.encode()
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="fichier"; filename="test.wav"\r\n'
                 'Content-Type: audio/wav\r\n\r\n').encode() + wav_test() + f'\r\n--{boundary}--\r\n'.encode()
        return json.load(self.requete("/api/upload", "POST", body, f"multipart/form-data; boundary={boundary}"))

    def test_parcours_et_preservation(self):
        with self.assertRaises(urllib.error.HTTPError) as erreur:
            self.requete("/api/stats", auth=False)
        self.assertEqual(erreur.exception.code, 401)
        clip = self.upload("capture-test-unique", label="incertain", observation_apres="Il va à sa gamelle")
        id_ = clip["id"]
        record = stockage.par_id(id_)
        original = stockage.chemin_wav(record).read_bytes()
        double = self.upload("capture-test-unique", label="incertain")
        self.assertEqual(id_, double["id"])
        self.assertTrue(double["doublon_evite"])
        self.assertEqual(motif_exclusion(record, serveur._labels, []), "quarantaine")
        self.post("/api/relabel", {"id_": id_, "label": "faim"})
        annotation = {"certitude": "confirmee", "type_son": "vocalise", "note": "<script>test</script>",
                      "observation_apres": "Il va à sa gamelle", "debut_s": 0.1, "fin_s": 0.7}
        json.load(self.requete(f"/api/annotations/{id_}", "PATCH", json.dumps(annotation).encode(), "application/json"))
        record = stockage.par_id(id_)
        self.assertEqual(record["session_id"], "session-test-1")
        self.assertEqual(record["jour_capture"], "2026-09-18")
        self.assertEqual(stockage.chemin_wav(record).read_bytes(), original)
        self.assertGreaterEqual(len(record["historique"]), 2)
        self.assertTrue(list((self.base / ".backups").glob("*.jsonl")))
        self.upload("capture-incertain", label="incertain")
        self.upload("capture-bruit-test", label="autre", type_son="bruit")
        # Ancien record : visible mais pas admissible tant qu'il n'est pas vérifié.
        legacy = {"id": "legacy", "label": "faim", "fichier": record["fichier"], "date": "2026-09-17T10:00:00"}
        stockage.ajouter(legacy)
        stats = json.load(self.requete("/api/stats"))
        self.assertEqual(stats["total_entrainable"], 1)
        self.assertEqual(stats["quarantaine"], 1)
        with zipfile.ZipFile(io.BytesIO(self.requete("/api/export").read())) as z:
            exported = [json.loads(l) for l in z.read("manifest.jsonl").decode().splitlines()]
            self.assertEqual([r["id"] for r in exported], [id_])
            self.assertEqual(z.read(exported[0]["fichier"]), original)
        config = {"labels": serveur._labels, "entrainement": {}}
        exemples = indexer_mon_chat(config, base=self.base)
        self.assertEqual([e.id for e in exemples], [id_])
        self.assertNotIn("observation_apres", exemples[0].contexte)
        self.post("/api/supprimer", {"id_": id_})
        self.assertEqual(json.load(self.requete("/api/stats"))["total_entrainable"], 0)
        self.post("/api/restaurer", {"id_": id_})
        self.assertEqual(stockage.chemin_wav(stockage.par_id(id_)).read_bytes(), original)
        with self.assertRaises(urllib.error.HTTPError) as erreur:
            self.requete(f"/api/annotations/{id_}", "PATCH", b'{"debut_s":10}', "application/json")
        self.assertEqual(erreur.exception.code, 422)

    def test_validation_metadata(self):
        with self.assertRaises(urllib.error.HTTPError) as erreur:
            self.upload("capture-invalide", fin_s=5)
        self.assertEqual(erreur.exception.code, 422)
        self.assertFalse(any(r.get("capture_id") == "capture-invalide" for r in stockage.tous()))

    def test_profil_prive_et_compatibilite(self):
        with patch.object(serveur, "_config", {"chat": {"nom": "Moka Test"}}):
            with self.assertRaises(urllib.error.HTTPError) as erreur:
                self.requete("/api/labels", auth=False)
            self.assertEqual(erreur.exception.code, 401)
            donnees = json.load(self.requete("/api/labels"))
            self.assertEqual(donnees["chat"]["nom"], "Moka Test")
            self.assertEqual(donnees["labels"], serveur._labels)
            self.assertNotIn(b"Moka Test", self.requete("/", auth=False).read())
        with patch.object(serveur, "_config", {}):
            self.assertEqual(json.load(self.requete("/api/labels"))["chat"]["nom"], "Mon chat")

    def test_cle_exemple_refusee_meme_si_fournie(self):
        with patch.object(serveur, "_TOKEN", "CHANGE-MOI-token-secret"):
            with self.assertRaises(urllib.error.HTTPError) as erreur:
                self.requete("/api/labels?token=CHANGE-MOI-token-secret", auth=False)
            self.assertEqual(erreur.exception.code, 401)

    def test_reecriture_atomique(self):
        stockage.ajouter({"id": "atomic", "label": "autre", "fichier": "absent.wav", "note": "conserver"})
        avant = (self.base / "manifest.jsonl").read_bytes()
        with patch("collecte.stockage.os.replace", side_effect=OSError("simulation")):
            with self.assertRaises(OSError): stockage.modifier("atomic", {"note": "nouveau"})
        self.assertEqual((self.base / "manifest.jsonl").read_bytes(), avant)

    def test_sauvegarde_et_export_threadpool(self):
        from concurrent.futures import ThreadPoolExecutor
        from collecte.exporter import exporter
        clip = self.upload("backup-incertain", label="incertain")
        self.post("/api/supprimer", {"id_": clip["id"]})
        export = exporter("sauvegarde", serveur._labels, serveur._labels_exclus)
        premier = next(export)
        # StreamingResponse peut terminer l'itération dans un AUTRE thread.
        with ThreadPoolExecutor(max_workers=1) as pool:
            with self.assertRaises(StopIteration):
                pool.submit(next, export).result(timeout=5)
        with zipfile.ZipFile(io.BytesIO(premier)) as z:
            record = json.loads(z.read("manifest.jsonl"))
            self.assertTrue(record["supprime"])
            self.assertEqual(record["label"], "incertain")
            self.assertEqual(z.read(record["fichier"]), wav_test())
        with self.assertRaises(urllib.error.HTTPError) as erreur:
            self.requete("/api/export", auth=False)
        self.assertEqual(erreur.exception.code, 401)

    def test_ancien_audio_restaure(self):
        corbeille = self.base / ".trash"
        corbeille.mkdir()
        (corbeille / "ancien.wav").write_bytes(wav_test())
        stockage.ajouter({"id": "ancien", "label": "autre", "fichier": "autre/ancien.wav", "supprime": True})
        self.post("/api/restaurer", {"id_": "ancien"})
        record = stockage.par_id("ancien")
        self.assertFalse(record["supprime"])
        self.assertEqual(stockage.chemin_wav(record).read_bytes(), wav_test())

    def test_audio_absent_non_compte(self):
        clip = self.upload("capture-audio-absent")
        # Simule une incohérence de chemin sans supprimer le fichier audio.
        stockage.modifier(clip["id"], {"fichier": "absent.wav"})
        stats = json.load(self.requete("/api/stats"))
        self.assertEqual(stats["total_entrainable"], 0)
        self.assertEqual(stats["a_verifier"], 1)

    def test_double_envoi_concurrent(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultats = list(pool.map(lambda _: self.upload("capture-concurrente"), range(2)))
        self.assertEqual(resultats[0]["id"], resultats[1]["id"])
        self.assertEqual(len(stockage.tous()), 1)
        self.assertEqual(len(list(self.base.rglob("*.wav"))), 1)


class TestML(unittest.TestCase):
    def test_segment_en_fin_de_clip(self):
        y = np.zeros(320000, dtype=np.float32); y[-8000:] = 0.5
        extrait = extraire_segment(y, 16000)
        self.assertEqual(len(extrait), 64000)
        self.assertGreater(float(np.max(extrait)), 0)
        manuel = extraire_segment(y, 16000, 0, 1)
        self.assertEqual(float(np.max(manuel)), 0)
        with self.assertRaises(ValueError): extraire_segment(y, 16000, 20, 19)
        with self.assertRaises(ValueError): extraire_segment(y, 0)

    def test_validation_imbriquee(self):
        groupes = np.repeat([f"jour-{i}" for i in range(12)], 6)
        y = np.tile(["faim", "porte"] * 3, 12)
        rng = np.random.default_rng(42)
        X = rng.normal(size=(len(y), 8))
        rapport = validation_imbriquee(X, y, groupes, grille={"logisticregression__C": [0.01, 1.0]})
        self.assertEqual(len(rapport["predictions_hors_pli"]), len(y))
        for pli in rapport["plis"]:
            self.assertFalse(set(pli["groupes_train"]) & set(pli["groupes_test"]))
        with self.assertRaises(ValueError):
            validation_imbriquee(X[:6], y[:6], groupes[:6])

    def test_contexte_sans_fuite_et_labels_numeriques(self):
        groupes = np.repeat(np.arange(12), 4)
        y = np.tile([0, 1, 0, 1], 12)
        X = [{"lieu": "piece-" + str(groupe), "minutes_depuis_repas": 15} for groupe in groupes]
        rapport = validation_imbriquee(X, y, groupes, dictionnaires=True,
                                     grille={"logisticregression__C": [0.1]})
        self.assertEqual(len(rapport["predictions_hors_pli"]), len(y))
        json.dumps(rapport)  # types numpy convertis pour un rapport exportable


if __name__ == "__main__":
    unittest.main()
