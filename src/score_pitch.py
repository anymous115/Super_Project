"""Le pipeline de scoring, commun aux deux modèles (§9 du protocole).

Charger un pitch, construire le prompt, appeler le modèle, mesurer, valider,
recalculer le total, tout enregistrer, et continuer proprement après un échec.

Les deux backends reçoivent exactement la même chaîne de caractères. C'est la
condition sans laquelle on ne compare plus deux modèles mais deux entrées.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import (CALL_TIMEOUT_SECONDS, DATA, LOCAL_NUM_CTX, LOCAL_NUM_PREDICT,
                     MODELS, RESULTS, TEMPERATURE, ModelConfig, load_env, require_env)
from .guard import scan
from .prompts import build_prompt, fingerprint
from .schemas import output_json_schema, parse_output

RAW_RUNS = RESULTS / "raw_runs.jsonl"


# --- Chargement des pitchs ---------------------------------------------------


def load_pitches(path: Optional[Path] = None, drafted_only: bool = False) -> List[Dict[str, Any]]:
    """Lit `data/pitches.jsonl`, dans l'ordre du fichier.

    L'ordre de passage fait partie des conditions contrôlées (§10) : ne pas trier.
    """
    path = path or DATA / "pitches.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [r for r in rows if r.get("pitch_text")]
    if drafted_only:
        rows = [r for r in rows if r.get("review_status") != "pending"]
    return rows


def injection_ids(path: Optional[Path] = None) -> List[str]:
    """Les pitchs piégés, lus depuis les métadonnées — jamais depuis le texte."""
    return [r["pitch_id"] for r in load_pitches(path) if r.get("is_injection_test")]


# --- Appel des modèles -------------------------------------------------------


@dataclass
class ModelReply:
    text: str
    input_tokens: int
    output_tokens: int
    model_version: str
    # Ollama renvoie la réflexion d'un modèle de raisonnement dans un champ
    # distinct de la réponse, mais la compte dans `eval_count`. Sans la garder,
    # on ne peut pas dire quelle part du coût local part en raisonnement.
    thinking: str = ""
    # "stop" si le modèle a fini, "length" s'il a heurté le plafond.
    done_reason: str = ""


def _call_ollama(model: ModelConfig, system: str, user: str) -> ModelReply:
    import httpx

    load_env()
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    response = httpx.post(
        f"{base.rstrip('/')}/api/chat",
        json={
            "model": model.name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            # La génération est contrainte par le schéma de sortie : le modèle
            # ne peut produire que du JSON de la bonne forme.
            "format": output_json_schema(),
            "options": {
                "temperature": TEMPERATURE,
                "num_ctx": LOCAL_NUM_CTX,
                "num_predict": LOCAL_NUM_PREDICT,
            },
        },
        timeout=CALL_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    message = payload["message"]
    return ModelReply(
        text=message.get("content", ""),
        input_tokens=payload.get("prompt_eval_count", 0),
        output_tokens=payload.get("eval_count", 0),
        model_version=payload.get("model", model.name),
        thinking=message.get("thinking") or "",
        done_reason=payload.get("done_reason", ""),
    )


def _call_openai(model: ModelConfig, system: str, user: str) -> ModelReply:
    from openai import OpenAI

    client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
    completion = client.chat.completions.create(
        model=model.name,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    usage = completion.usage
    return ModelReply(
        text=completion.choices[0].message.content or "",
        input_tokens=getattr(usage, "prompt_tokens", 0),
        output_tokens=getattr(usage, "completion_tokens", 0),
        model_version=completion.model,
    )


BACKENDS = {"ollama": _call_ollama, "openai": _call_openai}


# --- Un appel, une ligne de résultat -----------------------------------------


@dataclass
class RunRecord:
    """Une ligne de `results/raw_runs.jsonl`, telle que la décrit le §9."""

    run_id: str
    timestamp: str
    pitch_id: str
    model: str
    model_version: str
    prompt_version: str
    prompt_fingerprint: str
    temperature: float
    raw_output: str
    raw_thinking: str           # réflexion d'un modèle de raisonnement, hors réponse
    parsed_output: Optional[Dict[str, Any]]
    valid_json: bool            # JSON pur, sans texte autour
    valid_json_cleaned: bool    # valide après retrait des enveloppes connues
    output_chars: int           # longueur de la réponse
    thinking_chars: int         # longueur de la réflexion — comptée dans output_tokens
    truncated: bool             # génération arrêtée par le plafond, pas par le modèle
    pitch_id_echoed: Optional[str]   # l'identifiant que le modèle a renvoyé
    pitch_id_mismatch: bool          # ... et s'il ne correspond pas à celui envoyé
    total_reported: Optional[float]
    total_computed: Optional[float]
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    error: Optional[str]
    # Filtre anti-injection, appliqué au texte avant le modèle (src/guard.py).
    # Un pitch signalé est noté quand même, pour mesure, mais sort du
    # classement automatique et part en revue humaine.
    guard_flagged: bool = False
    guard_families: List[str] = field(default_factory=list)

    def as_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def score_pitch(
    pitch: Dict[str, Any],
    model_key: str,
    prompt_version: str,
    output_language: str = "en",
    trace: bool = True,
) -> RunRecord:
    """Note un pitch et renvoie la ligne de résultat. Ne lève jamais."""
    model = MODELS[model_key]
    verdict = scan(pitch["pitch_text"])
    system, user = build_prompt(
        prompt_version, pitch["pitch_id"], pitch["pitch_text"], output_language
    )

    started = time.perf_counter()
    reply, error = None, None
    try:
        reply = BACKENDS[model.backend](model, system, user)
    except Exception as exc:                      # modèle indisponible, timeout, quota
        error = f"{type(exc).__name__}: {exc}"
    latency = time.perf_counter() - started

    raw = reply.text if reply else ""
    result = parse_output(raw) if reply else None
    parsed = result.parsed if result else None

    record = RunRecord(
        run_id=uuid.uuid4().hex[:12],
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        pitch_id=pitch["pitch_id"],
        model=model.name,
        model_version=reply.model_version if reply else model.name,
        prompt_version=prompt_version,
        prompt_fingerprint=fingerprint(prompt_version),
        temperature=TEMPERATURE,
        raw_output=raw,
        raw_thinking=reply.thinking if reply else "",
        parsed_output=parsed.model_dump() if parsed else None,
        valid_json=bool(result and result.valid_json_strict),
        valid_json_cleaned=bool(result and result.valid_json_cleaned),
        output_chars=len(raw),
        thinking_chars=len(reply.thinking) if reply else 0,
        truncated=bool(reply and reply.done_reason == "length"),
        pitch_id_echoed=parsed.pitch_id if parsed else None,
        pitch_id_mismatch=bool(parsed and parsed.pitch_id != pitch["pitch_id"]),
        total_reported=parsed.total_score if parsed else None,
        # Le total qui fait foi est recalculé ici, jamais repris du modèle (§5).
        total_computed=parsed.computed_total() if parsed else None,
        latency_seconds=round(latency, 3),
        input_tokens=reply.input_tokens if reply else 0,
        output_tokens=reply.output_tokens if reply else 0,
        estimated_cost=model.cost(reply.input_tokens, reply.output_tokens) if reply else 0.0,
        error=error or (result.error if result else "aucune réponse"),
        guard_flagged=verdict.flagged,
        guard_families=verdict.families,
    )

    if trace:
        _trace(record, system, user)
    return record


def _trace(record: RunRecord, system: str, user: str) -> None:
    """Trace l'appel dans Langfuse. L'absence de Langfuse ne casse rien."""
    try:
        from langfuse import Langfuse
    except ImportError:
        return
    try:
        Langfuse().trace(
            name="score_pitch",
            input={"system": system, "user": user},
            output=record.parsed_output or record.raw_output,
            metadata={
                "pitch_id": record.pitch_id,
                "model": record.model,
                "model_version": record.model_version,
                "prompt_version": record.prompt_version,
                "prompt_fingerprint": record.prompt_fingerprint,
                "latency_seconds": record.latency_seconds,
                "valid_json": record.valid_json,
                "error": record.error,
            },
        )
    except Exception:
        # Un tracing indisponible ne doit jamais faire perdre une mesure.
        pass


def append_run(record: RunRecord, path: Optional[Path] = None) -> None:
    """Écrit la ligne immédiatement : une série interrompue garde ses résultats."""
    path = path or RAW_RUNS
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(record.as_json() + "\n")
