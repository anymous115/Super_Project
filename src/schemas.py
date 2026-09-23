"""Sortie structurée des modèles, validée avec Pydantic (§7 du protocole).

Deux règles portent tout ce fichier :

1. **Le total est recalculé dans le code.** Le modèle en propose un, on le garde
   pour mesurer s'il sait faire l'arithmétique, mais le score qui compte est
   `computed_total()`.
2. **Une sortie invalide est un échec, pas quelque chose à réparer.** Le taux de
   JSON valide est lui-même une métrique de comparaison entre les deux modèles.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import CRITERIA, MAX_NOTE, WEIGHTS

RECOMMENDATIONS = ("reject", "review", "shortlist")


class Scores(BaseModel):
    """Une note entière de 0 à 5 par critère de la grille."""

    model_config = ConfigDict(extra="forbid")

    team: int = Field(ge=0, le=MAX_NOTE)
    market: int = Field(ge=0, le=MAX_NOTE)
    product: int = Field(ge=0, le=MAX_NOTE)
    traction: int = Field(ge=0, le=MAX_NOTE)
    business_model: int = Field(ge=0, le=MAX_NOTE)

    def weighted_total(self) -> float:
        return sum(getattr(self, c) / MAX_NOTE * WEIGHTS[c] for c in CRITERIA)


class PitchScore(BaseModel):
    """L'objet que les deux modèles produisent, à l'identique."""

    model_config = ConfigDict(extra="forbid")

    pitch_id: str
    scores: Scores
    total_score: float
    strengths: List[str]
    risks: List[str]
    missing_information: List[str]
    recommendation: str
    evidence: List[str]

    def computed_total(self) -> float:
        """Le seul total qui fait foi."""
        return self.scores.weighted_total()

    def total_drift(self) -> float:
        """Écart entre le total annoncé par le modèle et le total recalculé."""
        return abs(self.total_score - self.computed_total())


def _check_recommendation(value: str) -> None:
    if value not in RECOMMENDATIONS:
        raise ValueError(f"recommendation doit valoir {' | '.join(RECOMMENDATIONS)}, reçu {value!r}")


# --- Lecture d'une réponse brute ---------------------------------------------

_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.S)
_THINK = re.compile(r"^\s*<think>.*?</think>\s*", re.S)


def strip_wrappers(raw: str) -> str:
    """Retire un bloc <think> de tête et une clôture ```json.

    Les modèles de raisonnement comme `deepseek-r1:8b` émettent leur
    raisonnement avant la réponse. Le protocole interdit de corriger une sortie
    à la main ; nettoyer mécaniquement une enveloppe connue n'est pas la même
    chose, mais ce n'est pas non plus du JSON strict — d'où les deux taux
    rapportés côte à côte dans `ParseResult`.
    """
    text = _THINK.sub("", raw)
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    return text.strip()


@dataclass
class ParseResult:
    """Ce qu'on a pu tirer d'une réponse, et par quel chemin."""

    parsed: Optional[PitchScore]
    valid_json_strict: bool       # la réponse était du JSON pur, sans rien autour
    valid_json_cleaned: bool      # valide après retrait des enveloppes connues
    error: Optional[str]

    @property
    def ok(self) -> bool:
        return self.parsed is not None


def _load(text: str) -> PitchScore:
    payload = json.loads(text)
    score = PitchScore.model_validate(payload)
    _check_recommendation(score.recommendation)
    return score


def parse_output(raw: str) -> ParseResult:
    """Valide une réponse de modèle, en distinguant strict et nettoyé."""
    if not raw or not raw.strip():
        return ParseResult(None, False, False, "réponse vide")

    try:
        return ParseResult(_load(raw), True, True, None)
    except (json.JSONDecodeError, ValidationError, ValueError):
        pass

    cleaned = strip_wrappers(raw)
    try:
        return ParseResult(_load(cleaned), False, True, None)
    except json.JSONDecodeError as exc:
        return ParseResult(None, False, False, f"JSON illisible : {exc}")
    except (ValidationError, ValueError) as exc:
        return ParseResult(None, False, False, f"schéma non respecté : {exc}")


# Le placeholder ne doit pas être un identifiant plausible : avec "P001",
# deepseek-r1 recopiait P001 en notant P046. L'identifiant vient du message
# utilisateur, pas du gabarit.
JSON_SHAPE = json.dumps(
    {
        "pitch_id": "<the pitch_id given above>",
        "scores": {c: 0 for c in CRITERIA},
        "total_score": 0,
        "strengths": ["..."],
        "risks": ["..."],
        "missing_information": ["..."],
        "recommendation": "reject | review | shortlist",
        "evidence": ["..."],
    },
    indent=2,
)


def output_json_schema() -> Dict[str, Any]:
    """Le schéma de `PitchScore`, passé à Ollama pour contraindre la génération.

    Avec un schéma, le modèle ne peut produire que du JSON de cette forme : plus
    de bloc markdown, plus de champ manquant. La validation Pydantic reste en
    aval, parce qu'un schéma ne vérifie pas tout (le total, par exemple).
    """
    schema = PitchScore.model_json_schema()
    schema["properties"]["recommendation"]["enum"] = list(RECOMMENDATIONS)
    return schema
