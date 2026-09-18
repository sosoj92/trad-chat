"""Exports privés avec les mêmes exclusions que le futur entraînement."""
import csv
import io
import json
import re
import tempfile
import zipfile

from core.annotations import motif_exclusion
from collecte import stockage


def exporter(mode: str, labels: list[str], exclus: list[str]):
    """ZIP émis par blocs ; fichiers sources et métadonnées préservés."""
    with tempfile.TemporaryFile() as archive:
        records, manquants = [], []
        # Libérer le RLock AVANT le premier yield : le serveur peut reprendre
        # l'itérateur dans un autre thread pour transmettre le bloc suivant.
        with stockage._verrou, zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for source in stockage.tous(inclure_supprimes=mode == "sauvegarde"):
                if mode == "entrainement" and motif_exclusion(source, labels, exclus):
                    continue
                record = dict(source)
                chemin = stockage.chemin_wav(record)
                identifiant = re.sub(r"[^a-zA-Z0-9_-]", "_", record["id"])
                label = re.sub(r"[^a-zA-Z0-9_-]", "_", record["label"])
                chemin_zip = f'audios/{"corbeille" if record.get("supprime") else label}/{identifiant}.wav'
                if not chemin.is_file():
                    manquants.append(record["id"])
                    if mode == "entrainement":
                        continue
                    record["audio_manquant"] = True
                else:
                    z.write(chemin, chemin_zip)
                record["fichier_source"] = record["fichier"]
                record["fichier"] = chemin_zip
                records.append(record)
            z.writestr("manifest.jsonl", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
            colonnes = ["id", "label", "date", "jour_capture", "session_id", "certitude", "type_son",
                        "lieu", "minutes_depuis_repas", "observation_avant", "observation_apres",
                        "note", "debut_s", "fin_s", "fichier", "supprime"]
            csv_io = io.StringIO(newline="")
            writer = csv.DictWriter(csv_io, fieldnames=colonnes, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
            z.writestr("annotations.csv", csv_io.getvalue())
            z.writestr("export.json", json.dumps({"mode": mode, "nombre": len(records),
                        "audios_manquants": manquants, "version": 2}, ensure_ascii=False))
            z.writestr("LIRE_MOI.txt", "Audios ORIGINAUX : appliquer debut_s/fin_s avant entraînement.\n"
                        "Grouper par jour_capture (sinon date[:10]), jamais par extrait aléatoire.\n"
                        "observation_apres, note, certitude et label ne sont pas des entrées prédictives.\n"
                        "Les anciens clips sans certitude/type vérifiés sont exclus du dataset.\n")
        archive.seek(0)
        while bloc := archive.read(1024 * 1024):
            yield bloc
