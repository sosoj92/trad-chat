"""Contrat commun collecte / export / entraînement, sans dépendance ML."""

from datetime import datetime

CERTITUDES = ("a_verifier", "probable", "confirmee")
TYPES_SON = ("vocalise", "bruit", "inconnu")


def jour_record(record: dict) -> str:
    """Jour local de capture, ou date historique. Jamais la date de correction."""
    jour = record.get("jour_capture") or record.get("date", "")[:10]
    try:
        return datetime.strptime(jour, "%Y-%m-%d").date().isoformat()
    except (ValueError, TypeError):
        return ""


def motif_exclusion(record: dict, labels: list[str], exclus: list[str]) -> str | None:
    """Critères uniques partagés par le loader, les compteurs et l'export."""
    if record.get("supprime"):
        return "supprime"
    if record.get("label") in set(exclus) | {"incertain"}:
        return "quarantaine"
    if record.get("label") not in labels:
        return "label_inconnu"
    if record.get("type_son", "inconnu") != "vocalise":
        return "type_son_a_verifier"
    if record.get("certitude", "a_verifier") not in ("probable", "confirmee"):
        return "annotation_a_verifier"
    if not jour_record(record):
        return "date_manquante"
    if record.get("audio_valide") is False:
        return "audio_invalide"
    return None
