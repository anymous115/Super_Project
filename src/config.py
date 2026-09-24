"""Constantes figées de l'expérience.

Tout ce qui est ici est décidé en phase 1 et ne bouge plus pendant une série de
mesures (§10 du protocole). Un changement de valeur invalide les résultats déjà
produits — il se fait par PR, pas en cours de run.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"

# --- Grille de notation (§5) -------------------------------------------------

WEIGHTS: Dict[str, int] = {
    "team": 20,
    "market": 25,
    "product": 15,
    "traction": 25,
    "business_model": 15,
}
CRITERIA = tuple(WEIGHTS)
MAX_NOTE = 5

assert sum(WEIGHTS.values()) == 100, "les poids de la grille doivent totaliser 100"

# --- Règle de sélection (§5) -------------------------------------------------

SELECTION_FLOOR = 5      # plancher sous 50 soumissions
SELECTION_RATE = 0.10    # 10 % au-dessus
SELECTION_CAP = 50       # plafond

# --- Conditions de mesure (§10) ----------------------------------------------

TEMPERATURE = 0.0
# Une passe sur les 50 pitchs (§10 : « réduire d'abord les répétitions, pas les
# pitchs »). À température 0, répéter toute la matrice mesure surtout ce qu'on
# sait déjà ; la stabilité est mesurée à part, sur un échantillon.
REPETITIONS = 1

# Test de stabilité : 3 passes en V2, le prompt de production, sur 10 pitchs
# répartis sur les trois paliers, dont deux injections.
STABILITY_PROMPT = "V2"
STABILITY_REPETITIONS = 3
STABILITY_SAMPLE = (
    "P003", "P008",                          # fort
    "P014", "P021", "P028", "P033",          # moyen, dont l'illusion du GMV
    "P040", "P045",                          # faible
    "P025", "P049",                          # injections
)
PROMPT_VERSIONS = ("V0", "V1", "V2")

# Bornes de génération du modèle local.
#
# Ollama charge un modèle avec une fenêtre de 4 096 tokens par défaut, trop
# juste pour un pitch plus le prompt V2 : on la fixe à 8 192. Chaque appel est
# plafonné en temps, pour qu'un appel bloqué devienne un échec enregistré.
LOCAL_NUM_CTX = 8192
CALL_TIMEOUT_SECONDS = 600

# `qwen2.5:14b` répond en 430 à 600 tokens, JSON compris : 2 048 laisse une
# marge large. Historique : `deepseek-r1:8b`, modèle de raisonnement, épuisait
# 4 096 tokens en réflexion sans répondre sur 14 pitchs sur 18 (23 septembre
# 2026) — c'est ce qui a fait changer de modèle.
LOCAL_NUM_PREDICT = 2048


@dataclass(frozen=True)
class ModelConfig:
    """Un modèle du benchmark, avec ce qu'il faut pour le tracer et le chiffrer."""

    key: str              # "local" ou "frontier"
    name: str             # identifiant passé à l'API
    backend: str          # "ollama" ou "openai"
    price_in: float       # $ par million de tokens d'entrée
    price_out: float      # $ par million de tokens de sortie
    version_pin: Optional[str] = None   # version exacte, relevée au premier appel

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return input_tokens / 1e6 * self.price_in + output_tokens / 1e6 * self.price_out


MODELS: Dict[str, ModelConfig] = {
    "local": ModelConfig(
        key="local",
        # Choisi le 23 septembre 2026 après mesure sur les 50 pitchs : voir
        # README, « Moteur de scoring ».
        name="qwen2.5:14b",
        backend="ollama",
        price_in=0.0,
        price_out=0.0,
    ),
    # Tarifs relevés le 22 septembre 2026 — voir README, « Tarifs retenus ».
    "frontier": ModelConfig(
        key="frontier",
        name="gpt-6-astra",
        backend="openai",
        price_in=10.0,
        price_out=50.0,
    ),
}

# --- Environnement -----------------------------------------------------------


def load_env() -> None:
    """Charge le .env s'il existe. Sans python-dotenv, on ne bloque pas."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env = ROOT / ".env"
    if env.exists():
        load_dotenv(env)


def require_env(name: str) -> str:
    """Lit une variable d'environnement, avec un message utile si elle manque."""
    load_env()
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} n'est pas défini. Copier .env.example en .env et le remplir. "
            "Le .env n'est jamais committé."
        )
    return value
