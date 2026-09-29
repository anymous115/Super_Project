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


def _patches(tmp_path, dossiers, saved):
    """Une shortlist et un suivi dans un dossier temporaire, jamais les vrais fichiers."""
    from src.intake import load_followups, save_followups

    shortlist, followups = tmp_path / 'shortlist.json', tmp_path / 'followups.json'
    save_shortlist(saved, shortlist)
    return followups, (
        patch('src.intake.load_dossiers', return_value=dossiers),
        patch('src.intake.load_shortlist', side_effect=lambda: load_shortlist(shortlist)),
        patch('src.intake.save_shortlist', side_effect=lambda ids: save_shortlist(ids, shortlist)),
        patch('src.intake.load_followups', side_effect=lambda: load_followups(followups)),
        patch('src.intake.save_followups', side_effect=lambda rows: save_followups(rows, followups)),
    )


def _open_profile(app, pid):
    app.radio(key='page').set_value('detail').run()
    app.selectbox(key='active_pitch').set_value(pid).run()


def test_dossier_en_shortlist_propose_de_donner_suite_et_memorise_le_contact(tmp_path):
    from src.intake import load_followups

    base = load_dossiers()[0]
    liked = replace(base, score=80, scores=dict(team=4, market=4, product=4, traction=4, business_model=4),
                    recommendation='shortlist', flagged=False, contact_channel='email', contact_handle='jane@acme.io')
    followups, patches = _patches(tmp_path, [liked], [base.pitch_id])
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        app = AppTest.from_file('../app.py').run()
        _open_profile(app, base.pitch_id)
        assert not app.exception
        assert f'contacted_{base.pitch_id}' in [b.key for b in app.button]
        assert len(app.get('link_button')) == 1                     # « Répondre par e-mail »
        assert 'mailto:jane@acme.io' in app.get('link_button')[0].proto.url
        app.button(key=f'contacted_{base.pitch_id}').click().run()
        assert base.pitch_id in load_followups(followups)
        app.button(key=f'contacted_{base.pitch_id}').click().run()   # on peut annuler
        assert load_followups(followups) == {}
        assert not app.exception


def test_dossier_pas_en_shortlist_ne_propose_pas_de_donner_suite(tmp_path):
    base = load_dossiers()[0]
    liked = replace(base, contact_channel='email', contact_handle='jane@acme.io')
    _, patches = _patches(tmp_path, [liked], [])
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        app = AppTest.from_file('../app.py').run()
        _open_profile(app, base.pitch_id)
        assert not app.exception
        assert f'contacted_{base.pitch_id}' not in [b.key for b in app.button]
        assert len(app.get('link_button')) == 0


def test_dossier_de_demonstration_montre_des_actions_desactivees_avec_leur_raison(tmp_path):
    base = load_dossiers()[0]                                        # aucun contact : entreprise fictive
    _, patches = _patches(tmp_path, [base], [base.pitch_id])
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        app = AppTest.from_file('../app.py').run()
        _open_profile(app, base.pitch_id)
        assert not app.exception
        assert all(app.button(key=k).disabled for k in ('reply_off', 'email_off', 'call_off'))
        assert any('démonstration' in c.value for c in app.caption)
