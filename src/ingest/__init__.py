"""Ingestion des pitchs : un adaptateur par canal, un événement commun (§4).

- `normalize` : l'objet `Submission` et le stockage `Inbox` ;
- `telegram`  : le bot du fonds ;
- `mail`      : l'adresse e-mail dédiée.

Ces modules ne tournent pas seuls : ils traduisent un message en `Submission`.
La relève (Telegram, IMAP) et la boucle de notation sont dans
`Input_Telegram_Mail/input_listener.py`, le seul écouteur du dépôt.
"""
