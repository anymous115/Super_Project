"""Descriptions factuelles des idées du corpus, liées au texte source."""
import hashlib
import json

from .config import DATA

_IDEAS = json.loads((DATA / 'startup_ideas.json').read_text(encoding='utf-8'))


def startup_idea(dossier) -> str:
    row = _IDEAS.get(dossier.pitch_id)
    if row and row['source_sha256'] == hashlib.sha256(dossier.text.encode('utf-8')).hexdigest():
        return row['idea']
    # Pour un nouveau dépôt, utiliser uniquement une description explicite du titre.
    title = dossier.text.strip().splitlines()[0] if dossier.text.strip() else ''
    if ' — ' in title:
        return title.split(' — ', 1)[1].strip()
    return 'L’idée de cette startup n’est pas encore résumée en une phrase.'
