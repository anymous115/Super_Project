#!/usr/bin/env python3
"""Estime le poids en tokens et le coût de la matrice, depuis le corpus réel.

Le §10 du protocole chiffrait le budget sur l'hypothèse de 800 mots par pitch —
le plafond, pas la réalité. Le corpus fait 476 mots en moyenne, et l'écart est
trop grand pour être ignoré dans une étude qui compare des coûts.

Ce script recalcule à partir des fichiers, pour que le chiffre du README ne
puisse pas dériver du corpus.

    python3 scripts/estimate_cost.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MODELS, PROMPT_VERSIONS, REPETITIONS  # noqa: E402
from src.prompts import build_prompt  # noqa: E402
from src.score_pitch import load_pitches  # noqa: E402

# Règle usuelle pour l'anglais. Une estimation, pas une mesure : les vrais
# comptes viennent de `results/raw_runs.jsonl` une fois la série lancée.
CHARS_PER_TOKEN = 4
OUTPUT_TOKENS = 400      # taille observée d'une réponse structurée complète


def main() -> int:
    pitches = load_pitches()
    if not pitches:
        print("aucun pitch rédigé", file=sys.stderr)
        return 1

    print(f"corpus : {len(pitches)} pitchs, "
          f"{sum(len(p['pitch_text'].split()) for p in pitches) // len(pitches)} mots en moyenne\n")

    print(f"{'prompt':<8}{'tokens entrée / appel':>24}{'total entrée (frontier)':>26}")
    per_version = {}
    for version in PROMPT_VERSIONS:
        total_chars = 0
        for pitch in pitches:
            system, user = build_prompt(version, pitch["pitch_id"], pitch["pitch_text"])
            total_chars += len(system) + len(user)
        tokens = total_chars / CHARS_PER_TOKEN
        per_version[version] = tokens
        print(f"{version:<8}{tokens / len(pitches):>24,.0f}{tokens * REPETITIONS:>26,.0f}")

    calls = len(pitches) * len(PROMPT_VERSIONS) * REPETITIONS
    tokens_in = sum(per_version.values()) * REPETITIONS
    tokens_out = OUTPUT_TOKENS * calls

    print(f"\npart frontier — {calls} appels sur {REPETITIONS} répétitions")
    print(f"  entrée : {tokens_in / 1000:>8,.0f} k tokens")
    print(f"  sortie : {tokens_out / 1000:>8,.0f} k tokens")

    frontier = MODELS["frontier"]
    cost = frontier.cost(tokens_in, tokens_out)
    print(f"\n{frontier.name} à {frontier.price_in:.0f} $/M entrée et "
          f"{frontier.price_out:.0f} $/M sortie : {cost:,.2f} $")
    print(f"le modèle local ne coûte rien en API — {calls} appels sur la machine de mesure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
