"""
Surveille en boucle un bot Telegram et une boîte mail (IMAP).
Chaque nouveau message est récupéré et stocké (une ligne JSON par message
dans le fichier de sortie), puis passé à la fonction `traiter_message`.

Uniquement la bibliothèque standard de Python : rien à installer.
Lancer :  python input_listener.py

Les réglages publics sont dans config.json, les secrets (token, adresse,
mot de passe) dans le fichier .env, qui n'est pas envoyé sur GitHub.
"""

import email
import imaplib
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from email.header import decode_header, make_header
from html.parser import HTMLParser
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
FICHIER_CONFIG = DOSSIER / "config.json"
FICHIER_ENV = DOSSIER / ".env"
FICHIER_ETAT = DOSSIER / "etat.json"  # mémorise le dernier message Telegram lu

verrou_ecriture = threading.Lock()


# ---------------------------------------------------------------- secrets

def charger_env():
    """Lit les lignes NOM=valeur du .env. Une vraie variable d'environnement
    déjà définie garde la priorité."""
    if not FICHIER_ENV.exists():
        return
    for ligne in FICHIER_ENV.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        nom, valeur = ligne.split("=", 1)
        os.environ.setdefault(nom.strip(), valeur.strip().strip('"').strip("'"))


def secret(nom):
    valeur = os.environ.get(nom)
    if not valeur:
        raise SystemExit(f"{nom} manquant : remplis-le dans le fichier .env (voir .env.example).")
    return valeur


# ---------------------------------------------------------------- stockage

def traiter_message(message):
    """Point d'entrée pour la suite du projet : appelé à chaque nouveau message.
    `message` est un dict : source, expediteur, sujet, texte, date."""
    print(f"[{message['source']}] {message['expediteur']} : {message['texte'][:80]!r}")


def stocker(config, source, expediteur, texte, sujet=None):
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
    traiter_message(message)


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


def boucle_telegram(config):
    token = config["telegram"]["token"]
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
                msg = maj.get("message") or maj.get("channel_post")
                if not msg:
                    continue
                texte = msg.get("text") or msg.get("caption")
                if not texte:
                    continue
                auteur = msg.get("from") or msg.get("chat", {})
                expediteur = auteur.get("username") or auteur.get("first_name") or auteur.get("title") or str(auteur.get("id"))
                stocker(config, "telegram", expediteur, texte)
            if mises_a_jour:
                etat = lire_etat()
                etat["telegram_offset"] = decalage
                ecrire_etat(etat)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as erreur:
            print(f"Telegram : erreur ({erreur}), nouvel essai dans {attente} s")
            time.sleep(attente)


# ---------------------------------------------------------------- mail

class ExtracteurTexte(HTMLParser):
    def __init__(self):
        super().__init__()
        self.morceaux = []

    def handle_data(self, data):
        self.morceaux.append(data)


def decoder_entete(valeur):
    return str(make_header(decode_header(valeur))) if valeur else ""


def decoder_partie(partie):
    brut = partie.get_payload(decode=True) or b""
    return brut.decode(partie.get_content_charset() or "utf-8", errors="replace")


def texte_du_mail(msg):
    """Renvoie le texte brut du mail, ou le HTML débarrassé de ses balises à défaut."""
    html = None
    for partie in msg.walk():
        if partie.get_content_maintype() == "multipart" or partie.get_filename():
            continue
        if partie.get_content_type() == "text/plain":
            return decoder_partie(partie).strip()
        if partie.get_content_type() == "text/html" and html is None:
            html = decoder_partie(partie)
    if html is None:
        return ""
    extracteur = ExtracteurTexte()
    extracteur.feed(html)
    return " ".join(" ".join(extracteur.morceaux).split())


def relever_mails(config):
    cfg = config["mail"]
    with imaplib.IMAP4_SSL(cfg["serveur_imap"], cfg["port"]) as imap:
        imap.login(cfg["adresse"], cfg["mot_de_passe"])
        imap.select(cfg["dossier"])
        _, numeros = imap.search(None, "UNSEEN")
        for numero in numeros[0].split():
            # Lire le corps (RFC822) marque automatiquement le mail comme lu,
            # il ne sera donc pas récupéré une seconde fois.
            _, donnees = imap.fetch(numero, "(RFC822)")
            msg = email.message_from_bytes(donnees[0][1])
            stocker(
                config,
                "mail",
                decoder_entete(msg.get("From")),
                texte_du_mail(msg),
                sujet=decoder_entete(msg.get("Subject")),
            )


def boucle_mail(config):
    intervalle = config["intervalle_secondes"]
    print("Mail : surveillance démarrée")
    while True:
        try:
            relever_mails(config)
        except (imaplib.IMAP4.error, OSError) as erreur:
            print(f"Mail : erreur ({erreur})")
        time.sleep(intervalle)


# ---------------------------------------------------------------- lancement

def main():
    if not FICHIER_CONFIG.exists():
        print("config.json introuvable.")
        return
    config = json.loads(FICHIER_CONFIG.read_text(encoding="utf-8"))

    # Les secrets viennent du .env, jamais de config.json (qui est public).
    charger_env()
    if config["telegram"]["actif"]:
        config["telegram"]["token"] = secret("TELEGRAM_TOKEN")
    if config["mail"]["actif"]:
        config["mail"]["adresse"] = secret("MAIL_ADRESSE")
        config["mail"]["mot_de_passe"] = secret("MAIL_MOT_DE_PASSE")

    fils = []
    if config["telegram"]["actif"]:
        fils.append(threading.Thread(target=boucle_telegram, args=(config,), daemon=True))
    if config["mail"]["actif"]:
        fils.append(threading.Thread(target=boucle_mail, args=(config,), daemon=True))
    if not fils:
        print("Aucune source active dans config.json.")
        return

    for fil in fils:
        fil.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arrêt.")


if __name__ == "__main__":
    main()
