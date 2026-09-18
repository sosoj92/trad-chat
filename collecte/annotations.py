"""Validation des annotations ; observation après coup jamais utilisée en entrée ML."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Annotation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    note: str = Field(default="", max_length=500)
    observation_avant: str = Field(default="", max_length=500)
    observation_apres: str = Field(default="", max_length=500)
    lieu: str = Field(default="", max_length=80)
    minutes_depuis_repas: int | None = Field(default=None, ge=0, le=10080)
    certitude: Literal["a_verifier", "probable", "confirmee"] = "a_verifier"
    type_son: Literal["vocalise", "bruit", "inconnu"] = "vocalise"
    debut_s: float = Field(default=0, ge=0)
    fin_s: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def verifier_intervalle(self):
        if self.fin_s is not None and self.fin_s <= self.debut_s:
            raise ValueError("La fin de l'extrait doit suivre son début.")
        return self


class Capture(Annotation):
    capture_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,80}$")
    session_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,80}$")
    date_capture: datetime
    jour_capture: date

    @model_validator(mode="after")
    def verifier_date(self):
        if self.date_capture.tzinfo is None:
            raise ValueError("Le fuseau de la capture est requis.")
        if abs((self.jour_capture - self.date_capture.date()).days) > 1:
            raise ValueError("Jour local incompatible avec la date de capture.")
        return self


def verifier_duree(annotation: Annotation, duree: float) -> None:
    if annotation.debut_s >= duree or (
        annotation.fin_s is not None and annotation.fin_s > duree + 0.02
    ):
        raise ValueError("Extrait en dehors de la durée du fichier.")
