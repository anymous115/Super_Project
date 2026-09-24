#!/usr/bin/env python3
"""Note les pitchs reçus dans inbox/ (le chaînon entre ingestion et interface).

    python scripts/score_inbox.py            # note ce qui attend, puis sort
    python scripts/score_inbox.py --watch    # recommence toutes les 30 s
    python scripts/score_inbox.py queue      # affiche les files, sans rien noter

À lancer à côté de `Input_Telegram_Mail/input_listener.py`.
Le modèle local doit tourner (`ollama serve`, modèle `qwen2.5:14b`).
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.triage import load_queue, pending, process_inbox  # noqa: E402

LABELS = {"scored": "noté", "review": "⚠ revue humaine", "unreadable": "illisible", "error": "erreur"}


def show() -> None:
    queue = load_queue()
    print(f"{len(queue.ranked)} classés · {len(queue.review)} en revue humaine · "
          f"{len(queue.unreadable)} illisibles · {len(queue.errors)} en erreur · {len(queue.waiting)} en attente\n")
    for rank, item in enumerate(queue.ranked, 1):
        run = item["run"]
        mark = "★" if item["submission_id"] in queue.selected else " "
        print(f"{mark} {rank:>3}. {item['submission_id']}  {run['total_computed']:>5.1f}  "
              f"{run['parsed_output']['recommendation']:<9}  {item['channel']:<8}  {item['sender_handle']}")
    for item in queue.review:
        print(f"  ⚠  {item['submission_id']}  revue humaine — {', '.join(item['run']['guard_families'])}")
    for item in queue.unreadable:
        print(f"  ✗  {item['submission_id']}  illisible — {'; '.join(item['extraction']['warnings'])}")


def run_once() -> int:
    waiting = len(pending())
    if not waiting:
        return 0
    print(f"{waiting} soumission(s) à noter…", flush=True)
    for payload in process_inbox():
        total = payload["run"]["total_computed"] if payload.get("run") else None
        print(f"  {payload['submission_id']}  {LABELS.get(payload['status'], payload['status'])}"
              + (f"  {total:.1f}" if total is not None else ""), flush=True)
    return waiting


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", nargs="?", choices=("score", "queue"), default="score")
    parser.add_argument("--watch", action="store_true", help="recommencer toutes les 30 s")
    args = parser.parse_args()

    if args.action == "queue":
        show()
        return
    try:
        while True:
            run_once()
            if not args.watch:
                break
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nArrêt.")


if __name__ == "__main__":
    main()
