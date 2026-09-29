import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def boite_vide(tmp_path_factory, monkeypatch):
    """Aucun test ne lit la vraie `inbox/` : elle peut contenir de vrais pitchs."""
    monkeypatch.setattr("src.intake.INBOX", tmp_path_factory.mktemp("inbox-vide"))
