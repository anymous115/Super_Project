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
    for concept in ("Jeu de données", "Référence humaine", "Prompt engineering", "Matrice expérimentale", "Sécurité", "Conclusion"):
        assert concept in text
    assert text.count("TODO") >= 8


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
