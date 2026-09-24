#!/usr/bin/env python3
"""Lance la réception des pitchs sur un canal (§4 du protocole).

    python scripts/ingest.py telegram          # écoute le bot en continu
    python scripts/ingest.py email             # relève la boîte chaque minute
    python scripts/ingest.py email --once      # un seul relevé, puis sortie
    python scripts/ingest.py list              # les soumissions déjà reçues

Les deux canaux tournent dans deux terminaux séparés. Ils écrivent dans le même
dossier `inbox/`, sans risque de collision de numéros.

Les identifiants sont lus dans `.env` (voir `.env.example`).
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ingest.normalize import Inbox  # noqa: E402


def show(inbox: Inbox) -> None:
    submissions = inbox.submissions()
    if not submissions:
        print(f"Aucune soumission dans {inbox.root}.")
        return
    for s in submissions:
        pieces = f"{len(s.attachments)} PDF, {len(s.links)} lien(s)"
        first_line = (s.text.splitlines() or [""])[0][:60]
        print(f"{s.submission_id}  {s.channel:<8}  {s.received_at}  {s.sender_handle:<28}  {pieces}  {first_line}")
        for warning in s.warnings:
            print(f"{'':>10}⚠ {warning}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel", choices=("telegram", "email", "list"))
    parser.add_argument("--once", action="store_true", help="un seul relevé, puis sortie")
    args = parser.parse_args()

    try:
        if args.channel == "telegram":
            from src.ingest import telegram
            telegram.run(once=args.once)
        elif args.channel == "email":
            from src.ingest import mail
            mail.run(once=args.once)
        else:
            show(Inbox())
    except RuntimeError as exc:          # variable d'environnement manquante
        sys.exit(str(exc))
    except KeyboardInterrupt:
        print("\nArrêt.")


if __name__ == "__main__":
    main()
