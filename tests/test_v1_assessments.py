import json
from pathlib import Path

from src.config import DATA, CRITERIA
from src.intake import load_dossiers, queue
from src.v1_assessments import V1_ASSESSMENTS, load_v1_assessments


def test_fifty_assessments_are_grounded_and_consistent():
    pitches = [json.loads(line) for line in (DATA / 'pitches.jsonl').read_text().splitlines()]
    rows = load_v1_assessments(pitches)
    assert len(rows) == len(pitches) == 50
    for pitch in pitches:
        row = rows[pitch['pitch_id']]
        assert set(row['criterion_reasons']) == set(CRITERIA)
        assert all(row['criterion_reasons'].values())
        assert row['parsed_output']['evidence']
        assert row['parsed_output']['risks']
        assert row['parsed_output']['missing_information']
        assert row['assessor'] == 'Codex — évaluation directe'


def test_changed_text_does_not_reuse_a_v1_score():
    pitch = json.loads((DATA / 'pitches.jsonl').read_text().splitlines()[0])
    assert pitch['pitch_id'] in load_v1_assessments([pitch])
    pitch['pitch_text'] += '\nA material change.'
    assert load_v1_assessments([pitch]) == {}


def test_v1_ignores_human_validation_and_retains_guard(tmp_path):
    pitches = [json.loads(line) for line in (DATA / 'pitches.jsonl').read_text().splitlines()]
    for pitch in pitches:
        pitch['review_status'] = 'drafted'
    corpus = tmp_path / 'pitches.jsonl'
    corpus.write_text(''.join(json.dumps(p)+'\n' for p in pitches))
    dossiers = load_dossiers(corpus, tmp_path/'no-runs', tmp_path/'no-intake', tmp_path/'no-intake-runs')
    assert len(dossiers) == 50
    assert all(d.score is not None and d.assessment_source.startswith('Codex') for d in dossiers)
    groups = queue(dossiers)
    assert len(groups['ranked']) == 50
    assert len(groups['review']) == 5
    assert len(groups['selected']) == 5
    assert {d.pitch_id for d in groups['review']} <= {d.pitch_id for d in groups['ranked']}
    assert len({d.pitch_id for d in groups['ranked']}) == 50
    assert not groups['pending']
