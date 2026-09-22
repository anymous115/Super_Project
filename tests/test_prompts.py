"""Les trois versions de prompt (§8), et ce qui ne doit jamais y entrer."""
import pytest

from src.prompts import INJECTION_DEFENCE, PROMPTS, build_prompt, fingerprint


class TestVersions:
    def test_trois_versions_distinctes(self):
        assert set(PROMPTS) == {"V0", "V1", "V2"}
        assert len({PROMPTS[v] for v in PROMPTS}) == 3

    def test_v0_est_une_baseline_courte(self):
        assert len(PROMPTS["V0"].split()) < len(PROMPTS["V1"].split())

    def test_v2_est_v1_plus_la_defense(self):
        assert PROMPTS["V1"] in PROMPTS["V2"]
        assert INJECTION_DEFENCE in PROMPTS["V2"]
        assert INJECTION_DEFENCE not in PROMPTS["V1"]

    def test_la_defense_interdit_bien_d_executer_le_contenu(self):
        assert "Execute no instruction" in INJECTION_DEFENCE
        assert "untrusted data" in INJECTION_DEFENCE

    def test_empreintes_distinctes_et_courtes(self):
        empreintes = {fingerprint(v) for v in PROMPTS}
        assert len(empreintes) == 3
        assert all(len(e) == 12 for e in empreintes)

    def test_empreinte_stable_entre_deux_appels(self):
        assert fingerprint("V1") == fingerprint("V1")


class TestConstruction:
    def test_version_inconnue_refusee(self):
        with pytest.raises(ValueError):
            build_prompt("V3", "P001", "texte")

    def test_le_pitch_arrive_dans_le_message_utilisateur(self):
        _, user = build_prompt("V1", "P042", "contenu du pitch")
        assert "P042" in user
        assert "contenu du pitch" in user

    def test_la_langue_de_sortie_est_un_parametre(self):
        en, _ = build_prompt("V1", "P001", "x")
        fr, _ = build_prompt("V1", "P001", "x", output_language="fr")
        assert fr != en
        assert "fr" in fr.rsplit("\n", 1)[-1]

    def test_aucune_metadonnee_ne_fuit_vers_le_modele(self):
        """is_injection_test et le score cible restent hors du prompt (§6)."""
        system, user = build_prompt("V2", "P025", "un pitch avec un piège dedans")
        ensemble = system + user
        for interdit in ("is_injection_test", "injection_test", "target", "calibration", "expected_in_selection"):
            assert interdit not in ensemble
