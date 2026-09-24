"""Exercise navigation and saved comparisons without invoking a model."""
from dataclasses import replace
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from src.intake import load_dossiers, load_shortlist, save_shortlist


def test_shortlist_roundtrip_and_invalid_content(tmp_path):
    path = tmp_path / 'shortlist.json'
    assert load_shortlist(path) == []
    save_shortlist(['P001', 'P002', 'P001'], path)
    assert load_shortlist(path) == ['P001', 'P002']
    path.write_text('{}')
    with pytest.raises(ValueError):
        load_shortlist(path)


def test_navigation_comparison_and_empty_search(tmp_path):
    path = tmp_path / 'shortlist.json'
    base = load_dossiers()[0]
    scored = replace(base, score=80, scores=dict(team=4, market=4, product=4, traction=4, business_model=4), recommendation='shortlist', flagged=False)
    with patch('src.intake.load_dossiers', return_value=[scored]), patch('src.intake.load_shortlist', side_effect=lambda:load_shortlist(path)), patch('src.intake.save_shortlist', side_effect=lambda ids:save_shortlist(ids,path)):
        app = AppTest.from_file('../app.py').run()
        assert not app.exception
        app.radio(key='page').set_value('search').run()
        app.button(key=f'save_search_{base.pitch_id}').click().run()
        assert load_shortlist(path) == [base.pitch_id]
        app.button(key=f'open_search_{base.pitch_id}').click().run()
        assert app.radio(key='page').value == 'detail'
        assert not app.exception
        app.radio(key='page').set_value('shortlist').run()
        app.multiselect[0].set_value([base.pitch_id]).run()
        assert app.metric[0].value == '80'
        assert not app.exception
        app.button(key=f'save_shortlist_{base.pitch_id}').click().run()
        assert load_shortlist(path) == []
        app.radio(key='page').set_value('search').run()
        app.text_input[0].set_value('no-match-at-all').run()
        assert not app.exception
        app.radio(key='page').set_value('submit').run()
        assert len(app.text_area) == 2
        assert not app.exception


def test_load_error_has_retry():
    with patch('src.intake.load_dossiers', side_effect=OSError('unavailable')):
        app = AppTest.from_file('../app.py').run()
        assert not app.exception
        assert app.error
        assert app.button[0].label == 'Réessayer'


def test_all_fifty_profiles_can_be_browsed_including_flagged():
    app = AppTest.from_file('../app.py').run()
    app.radio(key='page').set_value('search').run()
    open_buttons = [b for b in app.button if (b.key or '').startswith('open_search_')]
    assert len(open_buttons) == 50
    app.button(key='open_search_P049').click().run()
    assert len(app.selectbox(key='active_pitch').options) == 50
    assert app.selectbox(key='active_pitch').value == 'P049'
    assert app.warning
    assert not app.button(key='save_detail').disabled
    app.button(key='next_profile').click().run()
    assert app.selectbox(key='active_pitch').value == 'P050'
    assert app.button(key='next_profile').disabled
    app.button(key='previous_profile').click().run()
    assert app.selectbox(key='active_pitch').value == 'P049'
    assert not app.exception
