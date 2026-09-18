"""Le parcours débutant ne doit écraser ni réglages, ni clé, ni données."""
import copy
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit
from unittest.mock import patch

import yaml

from core.config import RACINE, ErreurConfig, charger_config, labels_exclus, token_sur, valider_collecte
from core.diagnostic import diagnostiquer
from core.initialiser import initialiser


class TestInstallation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="miaou-installation-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.modele = (RACINE / "config.example.yaml").read_text(encoding="utf-8")
        (self.base / "config.example.yaml").write_text(self.modele, encoding="utf-8")
        self.addCleanup(charger_config.cache_clear)

    def config(self):
        return yaml.safe_load((self.base / "config.yaml").read_text(encoding="utf-8"))

    def test_initialisation_et_non_ecrasement(self):
        self.assertTrue(initialiser(self.base, nom_chat="  Moka  "))
        config = self.config()
        self.assertEqual(config["chat"]["nom"], "Moka")
        self.assertEqual(config["collecte"]["host"], "127.0.0.1")
        self.assertTrue(token_sur(config["collecte"]["token"]))
        self.assertGreaterEqual(len(config["collecte"]["token"]), 40)
        self.assertIn("incertain", labels_exclus(config))
        valider_collecte(config)
        avant = (self.base / "config.yaml").read_bytes()
        donnees = self.base / "data" / "mon_chat" / "manifest.jsonl"
        donnees.parent.mkdir(parents=True)
        donnees.write_bytes(b'{"id":"exemple-fictif"}\n')
        self.assertFalse(initialiser(self.base, nom_chat="Ne pas remplacer", port=8772))
        self.assertEqual((self.base / "config.yaml").read_bytes(), avant)
        self.assertEqual(donnees.read_bytes(), b'{"id":"exemple-fictif"}\n')

    def test_deux_installations_independantes(self):
        autre = self.base / "autre"
        autre.mkdir()
        (autre / "config.example.yaml").write_text(self.modele, encoding="utf-8")
        initialiser(self.base)
        initialiser(autre, nom_chat="Luna", port=8772, categories=["jeu", "porte"])
        config = yaml.safe_load((autre / "config.yaml").read_text(encoding="utf-8"))
        self.assertNotEqual(config["collecte"]["token"], self.config()["collecte"]["token"])
        self.assertEqual(config["labels"], ["jeu", "porte", "autre", "incertain"])
        self.assertEqual(config["collecte"]["port"], 8772)

    def test_parametres_invalides_ne_creent_pas_de_config(self):
        cas = [{"nom_chat": " "}, {"nom_chat": "x" * 61}, {"port": 80},
               {"port": 65536}, {"port": True}, {"categories": ["faim", "faim"]},
               {"categories": ["../faim"]}, {"categories": ["Câlin"]}]
        for parametres in cas:
            with self.subTest(parametres=parametres):
                with self.assertRaises(ErreurConfig):
                    initialiser(self.base, **parametres)
                self.assertFalse((self.base / "config.yaml").exists())

    def test_refus_cles_publiques_et_categories_reservees(self):
        for token in (None, 123, "", "court", "CHANGE-MOI-token-secret", " CHANGE-MOI-token-secret "):
            self.assertFalse(token_sur(token))
        initialiser(self.base)
        config = self.config()
        for valeur in ([], ["faim", "porte"], ["autre", "incertain", "porte", "porte"]):
            invalide = copy.deepcopy(config)
            invalide["labels"] = valeur
            with self.assertRaises(ErreurConfig):
                valider_collecte(invalide)
        config.pop("chat")  # Compatibilité des configurations d'avant le tutoriel.
        valider_collecte(config)

    def test_diagnostic_ne_divulgue_pas_les_valeurs(self):
        initialiser(self.base, nom_chat="NomPriveFictif")
        config = self.config()
        lignes, erreurs = diagnostiquer(config)
        self.assertEqual(erreurs, 0)
        texte = str(lignes)
        self.assertNotIn(config["collecte"]["token"], texte)
        self.assertNotIn("NomPriveFictif", texte)
        config["collecte"]["token"] = "court"
        lignes, erreurs = diagnostiquer(config)
        self.assertGreater(erreurs, 0)
        self.assertNotIn("court", str(lignes))
        with patch("core.diagnostic.charger_config", side_effect=ErreurConfig("secret-fictif")):
            lignes, erreurs = diagnostiquer()
        self.assertGreater(erreurs, 0)
        self.assertNotIn("secret-fictif", str(lignes))

    def test_yaml_invalide_ne_reproduit_pas_un_secret(self):
        chemin = self.base / "config.yaml"
        chemin.write_text('collecte: [secret-fictif-ne-pas-afficher', encoding="utf-8")
        with self.assertRaises(ErreurConfig) as erreur:
            charger_config(chemin)
        self.assertNotIn("secret-fictif", str(erreur.exception))


class TestDocumentation(unittest.TestCase):
    def test_liens_markdown_locaux(self):
        fichiers = list(RACINE.glob("*.md")) + list((RACINE / "docs").glob("*.md"))
        for fichier in fichiers:
            for lien in re.findall(r"\]\(([^)\s]+)\)", fichier.read_text(encoding="utf-8")):
                url = urlsplit(lien)
                if url.scheme or not url.path:
                    continue
                with self.subTest(fichier=fichier.name, lien=lien):
                    cible = (fichier.parent / unquote(url.path)).resolve()
                    self.assertTrue(cible.is_relative_to(RACINE))
                    self.assertTrue(cible.exists(), f"Lien absent : {lien}")


if __name__ == "__main__":
    unittest.main()
