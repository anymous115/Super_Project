import json
from pathlib import Path

from src.project_status import collect_project_status


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_status_evolue_avec_les_livrables(tmp_path):
    write_jsonl(
        tmp_path / "data/pitches.jsonl",
        [
            {
                "pitch_id": "P001",
                "pitch_text": "Pitch",
                "review_status": "validated",
                "source_type": "derived",
                "source_url": "https://example.test",
            }
        ],
    )
    write_jsonl(tmp_path / "results/raw_runs.jsonl", [
        {"pitch_id": "P001", "model": "local", "prompt_version": "V0", "valid_json": True},
        {"pitch_id": "P001", "model": "local", "prompt_version": "V2", "valid_json": True,
         "parsed_output": {"recommendation": "review"}},
    ])

    snapshot = collect_project_status(tmp_path)

    assert snapshot.metrics["drafted_pitches"] == 1
    assert snapshot.metrics["validated_pitches"] == 1
    assert snapshot.metrics["engine_runs"] == 2
    assert snapshot.metrics["scored_pitches"] == 1
    assert snapshot.phases[1].tasks[0].progress == 1 / 50
    assert snapshot.phases[2].tasks[-1].state == "Terminé"


def test_export_contient_progression_et_prochaines_actions(tmp_path):
    snapshot = collect_project_status(tmp_path)
    payload = snapshot.to_dict()

    assert 0 <= payload["progress"] <= 1
    assert payload["current_phase"] == 1
    assert payload["next_actions"]
    assert payload["next_actions"][0]["action"]
