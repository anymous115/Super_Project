"""Le notebook reste aligné sur le projet et exécutable syntaxiquement."""
import json
from pathlib import Path


NOTEBOOK = Path(__file__).resolve().parent.parent / "08_quality_vs_cost_benchmark.ipynb"


def load_notebook():
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def test_notebook_ne_depend_plus_du_starter_du_cours():
    text = NOTEBOOK.read_text(encoding="utf-8")
    assert "benchmark_task.jsonl" not in text
    assert "from utils import" not in text
    assert "from eval import" not in text
    assert "VC Pitch Intake & Triage" in text


def test_notebook_couvre_les_etapes_du_benchmark():
    notebook = load_notebook()
    text = "\n".join(
        "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")
        for cell in notebook["cells"]
    )
    for concept in (
        "Jeu de données",
        "Repères de calibration",
        "Prompt engineering",
        "Passage du moteur sur le corpus",
        "Sécurité",
        "Conclusion",
    ):
        assert concept in text
    assert "qwen2.5:14b" in text
    assert "Filtre anti-injection" in text
    assert "Extraction PDF" in text
    assert all(
        "TODO" not in "".join(cell.get("source", []))
        for cell in notebook["cells"] if cell["cell_type"] == "code"
    )


def test_notebook_reflete_le_protocole_local_actuel():
    text = NOTEBOOK.read_text(encoding="utf-8")
    assert "50 pitchs × 1 modèle local × 1 prompt V2 × 1 répétition = 50 appels" in text
    assert "900 appels" not in text
    assert "six configurations" not in text
    assert "data/reference_scores.jsonl" not in text


def test_notebook_contient_les_visuels_pedagogiques():
    notebook = load_notebook()
    text = "\n".join(
        "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")
        for cell in notebook["cells"]
    )
    assert "import pandas as pd" in text
    assert "import matplotlib.pyplot as plt" in text
    assert text.count("plt.show()") >= 4
    assert text.count("🎤") >= 5
    assert "Parcours court pour la présentation" in text


def test_cellules_python_sont_syntaxiquement_valides():
    notebook = load_notebook()
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert len(code_cells) >= 15
    for index, cell in enumerate(code_cells):
        source = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")
        compile(source, f"notebook-cell-{index}", "exec")


def test_revue_qualitative_executable_seule(monkeypatch, tmp_path, capsys):
    from src import config

    source = next(
        "".join(cell["source"]) for cell in load_notebook()["cells"]
        if cell["cell_type"] == "code" and "review_rows = []" in "".join(cell["source"])
    )
    monkeypatch.setattr(config, "RESULTS", tmp_path)
    namespace = {}
    exec(source, namespace)
    assert namespace["review_df"].empty
    assert "en attente des sorties V2" in capsys.readouterr().out

    record = {"pitch_id": "P001", "model": config.MODELS["local"].name,
              "prompt_version": "V2", "total_computed": 0,
              "parsed_output": {"evidence": ["preuve"]}}
    records = [dict(record, total_computed=90), record,
               dict(record, prompt_version="V1", total_computed=80),
               dict(record, model="autre-modele", total_computed=70),
               dict(record, pitch_id="inconnu"),
               dict(record, pitch_id="P002"),
               dict(record, pitch_id="P002", parsed_output=None)]
    (tmp_path / "raw_runs.jsonl").write_text(
        "\n".join(json.dumps(row) for row in records), encoding="utf-8"
    )
    namespace = {}
    exec(source, namespace)
    review = namespace["review_df"]
    assert review["pitch_id"].tolist() == ["P001"]
    assert review.iloc[0]["score"] == 0
    assert review.iloc[0]["preuves"] == 1
    assert review.iloc[0]["écart"] == abs(review.iloc[0]["cible"])


def test_demo_inference_gere_echec_et_succes(monkeypatch, capsys):
    import importlib
    from src.config import MODELS, WEIGHTS

    scoring = importlib.import_module("src.score_pitch")
    source = next(
        "".join(cell["source"]) for cell in load_notebook()["cells"]
        if cell["cell_type"] == "code" and "record = score_pitch(pitch," in "".join(cell["source"])
    )

    def unavailable(*args):
        raise ConnectionError("serveur inaccessible")

    monkeypatch.setitem(scoring.BACKENDS, "ollama", unavailable)
    namespace = {}
    exec(source, namespace)
    assert namespace["record"].parsed_output is None
    assert "ConnectionError: serveur inaccessible" in capsys.readouterr().out

    monkeypatch.setitem(scoring.BACKENDS, "ollama", lambda *args: scoring.ModelReply(
        text="réponse invalide", input_tokens=10, output_tokens=2,
        model_version=MODELS["local"].name,
    ))
    exec(source, {})
    assert "Réponse non exploitable (extrait) : réponse invalide" in capsys.readouterr().out

    output = {
        "pitch_id": "P005", "scores": {name: 3 for name in WEIGHTS},
        "total_score": 60, "strengths": ["Équipe"], "risks": ["Marché"],
        "missing_information": [], "recommendation": "review", "evidence": ["preuve"],
    }
    monkeypatch.setitem(scoring.BACKENDS, "ollama", lambda *args: scoring.ModelReply(
        text=json.dumps(output), input_tokens=10, output_tokens=30,
        model_version=MODELS["local"].name,
    ))
    namespace = {}
    exec(source, namespace)
    assert namespace["record"].total_computed == 60
    assert "Recommandation : review" in capsys.readouterr().out
