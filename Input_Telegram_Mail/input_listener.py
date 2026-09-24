"""
Surveille en boucle un bot Telegram et une boîte mail (IMAP), et dépose chaque
pitch reçu dans `inbox/`, où la notation le prend en charge.

Chaque message est :
  1. consigné tel quel dans le fichier de sortie (une ligne JSON par message) ;
  2. confié à `src/ingest/`, qui télécharge le deck PDF s'il y en a un, ignore
     un message déjà reçu, l'enregistre dans `inbox/SUB-XXXX/` et envoie
     l'accusé de réception au fondateur.

Avec `"noter": true` dans config.json, une troisième boucle note ce qui arrive
(extraction, filtre anti-injection, qwen2.5:14b) : un seul terminal suffit pour
toute la chaîne. Il faut alors qu'Ollama tourne.

Lancer :  python Input_Telegram_Mail/input_listener.py

Les réglages publics sont dans config.json (copier config.example.json), les
secrets (token, adresse, mot de passe) dans le fichier .env, qui n'est pas
envoyé sur GitHub.
"""

import email
import imaplib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
FICHIER_CONFIG = DOSSIER / "config.json"
FICHIER_ETAT = DOSSIER / "etat.json"  # mémorise le dernier message Telegram lu

sys.path.insert(0, str(RACINE))
from src.ingest import mail, telegram  # noqa: E402
from src.ingest.normalize import Inbox  # noqa: E402

verrou_ecriture = threading.Lock()


# ---------------------------------------------------------------- secrets

def charger_env():
    """Lit les lignes NOM=valeur du .env (celui du dossier, puis celui du dépôt).
    Une vraie variable d'environnement déjà définie garde la priorité."""
    for fichier in (DOSSIER / ".env", RACINE / ".env"):
        if not fichier.exists():
            continue
        for ligne in fichier.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            nom, valeur = ligne.split("=", 1)
            os.environ.setdefault(nom.strip(), valeur.strip().strip('"').strip("'"))


def secret(*noms):
    """Le premier des noms qui est rempli. Les anciens noms du .env
    (TELEGRAM_BOT_TOKEN, EMAIL_ADDRESS, EMAIL_PASSWORD) marchent aussi."""
    for nom in noms:
        valeur = os.environ.get(nom)
        if valeur:
            return valeur
    raise SystemExit(f"{noms[0]} manquant : remplis-le dans le fichier .env (voir .env.example).")


# ---------------------------------------------------------------- stockage

def consigner(config, source, expediteur, texte, sujet=None):
    """Garde une trace brute du message, avant tout traitement."""
    message = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "expediteur": expediteur,
        "sujet": sujet,
        "texte": texte,
    }
    with verrou_ecriture:
        with open(DOSSIER / config["fichier_sortie"], "a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")


def annoncer(source, soumission):
    if soumission:
        print(f"[{source}] {soumission.submission_id} reçu de {soumission.sender_handle}"
              f" ({len(soumission.attachments)} PDF, {len(soumission.links)} lien(s))")


def lire_etat():
    if FICHIER_ETAT.exists():
        return json.loads(FICHIER_ETAT.read_text(encoding="utf-8"))
    return {}


def ecrire_etat(etat):
    FICHIER_ETAT.write_text(json.dumps(etat), encoding="utf-8")


# ---------------------------------------------------------------- telegram

def appel_telegram(token, methode, params, delai):
    url = f"https://api.telegram.org/bot{token}/{methode}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=delai + 10) as reponse:
        donnees = json.load(reponse)
    if not donnees.get("ok"):
        raise RuntimeError(donnees.get("description", "erreur Telegram"))
    return donnees["result"]


def traiter_update(config, maj, client, boite):
    """Une update Telegram : trace brute, puis dépôt dans inbox/ avec son PDF."""
    msg = maj.get("message") or {}
    texte = msg.get("text") or msg.get("caption") or ""
    if msg.get("document"):
        texte = (texte + f"\n[pièce jointe : {msg['document'].get('file_name', '?')}]").strip()
    if texte:
        consigner(config, "telegram", telegram.sender_handle(msg.get("from", {})), texte)
    return telegram.handle_update(maj, client, boite)


def boucle_telegram(config, boite):
    token = config["telegram"]["token"]
    client = telegram.TelegramClient(token=token)
    etat = lire_etat()
    decalage = etat.get("telegram_offset", 0)
    # Long polling : Telegram garde la requête ouverte jusqu'à `attente` secondes
    # et répond dès qu'un message arrive, donc la réception est quasi immédiate.
    attente = config["intervalle_secondes"]
    print("Telegram : écoute démarrée")

    while True:
        try:
            mises_a_jour = appel_telegram(
                token, "getUpdates", {"offset": decalage, "timeout": attente}, attente
            )
            for maj in mises_a_jour:
                decalage = maj["update_id"] + 1
                try:
                    annoncer("telegram", traiter_update(config, maj, client, boite))
                except Exception as erreur:
                    # Un message qui échoue ne doit pas bloquer la file.
                    print(f"Telegram : message {maj['update_id']} ignoré ({type(erreur).__name__})")
            if mises_a_jour:
                etat = lire_etat()
                etat["telegram_offset"] = decalage
                ecrire_etat(etat)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as erreur:
            # L'URL contient le token : on n'affiche que le type d'erreur.
            print(f"Telegram : erreur ({type(erreur).__name__}), nouvel essai dans {attente} s")
            time.sleep(attente)


# ---------------------------------------------------------------- mail

def traiter_mail(config, brut, boite, repondre):
    """Un mail brut : trace, puis dépôt dans inbox/ avec son PDF et accusé."""
    brouillon, _ = mail.parse_email(brut)
    msg = email.message_from_bytes(brut)
    consigner(config, "mail", brouillon.sender_handle, brouillon.text, sujet=msg.get("Subject"))
    return mail.handle_email(brut, boite, repondre, config["mail"]["adresse"])


def relever_mails(config, boite, repondre):
    cfg = config["mail"]
    with imaplib.IMAP4_SSL(cfg["serveur_imap"], cfg["port"]) as imap:
        imap.login(cfg["adresse"], cfg["mot_de_passe"])
        imap.select(cfg["dossier"])
        _, numeros = imap.search(None, "UNSEEN")
        for numero in numeros[0].split():
            # PEEK : le mail reste non lu tant qu'il n'est pas enregistré ;
            # un plantage en cours de route le laisse dans la file.
            _, donnees = imap.fetch(numero, "(BODY.PEEK[])")
            try:
                annoncer("mail", traiter_mail(config, donnees[0][1], boite, repondre))
            except Exception as erreur:
                print(f"Mail : message {numero.decode()} ignoré ({type(erreur).__name__})")
                continue
            imap.store(numero, "+FLAGS", "\\Seen")


def boucle_mail(config, boite):
    cfg = config["mail"]
    reglages = SimpleNamespace(address=cfg["adresse"], password=cfg["mot_de_passe"],
                               smtp_host=cfg["serveur_smtp"], smtp_port=cfg["port_smtp"])
    repondre = mail.smtp_reply(reglages) if cfg.get("accuse_reception", True) else None
    intervalle = config["intervalle_secondes"]
    print("Mail : surveillance démarrée")
    while True:
        try:
            relever_mails(config, boite, repondre)
        except (imaplib.IMAP4.error, OSError) as erreur:
            print(f"Mail : erreur ({erreur})")
        time.sleep(intervalle)


# ---------------------------------------------------------------- notation

def boucle_notation(config, boite):
    """Note ce qui arrive dans inbox/ (voir scripts/score_inbox.py)."""
    from src.triage import pending, process_inbox

    print("Notation : démarrée (qwen2.5:14b via Ollama)")
    while True:
        try:
            if pending(boite):
                for resultat in process_inbox(boite):
                    total = (resultat.get("run") or {}).get("total_computed")
                    print(f"[notation] {resultat['submission_id']} : {resultat['status']}"
                          + (f", {total:.0f}/100" if total is not None else ""))
        except Exception as erreur:
            print(f"Notation : erreur ({type(erreur).__name__}: {erreur})")
        time.sleep(config["intervalle_secondes"])


# ---------------------------------------------------------------- lancement

def main():
    if not FICHIER_CONFIG.exists():
        print("config.json introuvable : copie config.example.json en config.json.")
        return
    config = json.loads(FICHIER_CONFIG.read_text(encoding="utf-8"))

    # Les secrets viennent du .env, jamais de config.json.
    charger_env()
    if config["telegram"]["actif"]:
        config["telegram"]["token"] = secret("TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN")
    if config["mail"]["actif"]:
        config["mail"]["adresse"] = secret("MAIL_ADRESSE", "EMAIL_ADDRESS")
        config["mail"]["mot_de_passe"] = secret("MAIL_MOT_DE_PASSE", "EMAIL_PASSWORD")

    boite = Inbox()
    fils = []
    if config["telegram"]["actif"]:
        fils.append(threading.Thread(target=boucle_telegram, args=(config, boite), daemon=True))
    if config["mail"]["actif"]:
        fils.append(threading.Thread(target=boucle_mail, args=(config, boite), daemon=True))
    if not fils:
        print("Aucune source active dans config.json.")
        return
    if config.get("noter"):
        fils.append(threading.Thread(target=boucle_notation, args=(config, boite), daemon=True))

    print(f"Pitchs déposés dans {boite.root}")
    for fil in fils:
        fil.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arrêt.")


if __name__ == "__main__":
    main()
