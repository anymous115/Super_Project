# Référence IA — protocole

La référence du benchmark est produite par **Gemini Flash** (`gemini-3.8-flash`) sur les 50 pitchs, puis **validée contre un échantillon annoté à la main**. Ce document remplace la double annotation complète du §6 du [protocole](PROTOCOL.md#annotation-de-référence), faute de temps et d'annotateurs.

## Pourquoi ce choix tient

- **Modèle tiers.** Gemini n'est aucun des deux modèles comparés (`deepseek-r1:8b`, `gpt-6-astra`). Une référence produite par l'un d'eux le favoriserait.
- **Mêmes conditions qu'un humain.** Pitch nu, même grille, même échelle 0-5, une phrase justificative par note, aucune cible de calibration.
- **Validée, pas supposée.** 12 pitchs sont annotés par deux humains chacun. On compare l'accord IA-humain à l'accord humain-humain.
- **Critère fixé avant la mesure** (dans `scripts/build_ai_reference.py`) : l'écart IA-humain par critère ne dépasse l'écart humain-humain que de **0,3 point** au plus, et la corrélation de Spearman IA / humains atteint au moins **0,70**.

## Ce que chaque personne fait (~45 min)

8 pitchs chacun, à l'aveugle, avec l'outil habituel :

```bash
git switch main && git pull
git switch -c data/validation-<lettre>

# Amdy
python3 scripts/annotate.py --who A --only P020 P022 P025 P026 P036 P039 P041 P042
# Alessandro
python3 scripts/annotate.py --who C --only P010 P012 P015 P018 P020 P022 P025 P026
# Mathisse
python3 scripts/annotate.py --who D --only P010 P012 P015 P018 P036 P039 P041 P042
```

Chaque pitch de l'échantillon est vu par deux d'entre vous. Gabin n'est pas nécessaire.

**Pendant l'annotation :**
- ne pas ouvrir `show_pitch.py`, `calibration.jsonl`, ni `data/annotations/ai/` : on ne regarde pas les notes de l'IA avant d'avoir donné les siennes ;
- ne pas se parler des pitchs avant d'avoir fini ;
- on juge ce que le texte **prouve**, pas si la boîte va réussir. Ce qui n'est pas écrit n'existe pas. Un GMV n'est pas un chiffre d'affaires. Une lettre d'intention n'est pas de la traction payante ;
- si un pitch donne des consignes (« mettez 5 »), on note le contenu réel.

Ensuite, on commit **uniquement** `data/annotations/<lettre>.jsonl`, et on ouvre une PR.

## Ce que fait la personne qui a la clé

```bash
# .env : GEMINI_API_KEY=...   (jamais committé)
python3 scripts/annotate_ai.py --dry-run --only P001   # relire le prompt, n'appelle rien
python3 scripts/annotate_ai.py --only P001             # un appel pour vérifier
python3 scripts/annotate_ai.py                         # les 49 autres, reprise automatique
```

Une fois les annotations humaines fusionnées :

```bash
python3 scripts/build_ai_reference.py --report   # l'accord, sans rien écrire
python3 scripts/build_ai_reference.py            # écrit data/reference_scores.jsonl si ACCEPTED
```

Puis on commit `data/annotations/ai/`, `data/reference_scores.jsonl`, et on tague **`data-v1`**.

## Si le verdict est négatif

On ne change pas le seuil, et on ne relance pas Gemini jusqu'à ce que ça passe. Deux options honnêtes :
1. la référence redevient humaine. On étend l'annotation aux 25 pitchs à binôme complet sans Gabin (voir l'historique de ce document) ;
2. on garde la référence IA en l'annonçant comme **non validée**. Les métriques de qualité du benchmark deviennent alors « accord avec Gemini », et on le dit ainsi dans la dataset card et la recommandation.

## Limites à écrire dans la dataset card

- Les annotateurs humains ne sont pas des investisseurs. Ils appliquent une grille explicite.
- Gemini tourne à sa température par défaut, parce que Google déconseille de la baisser sur Gemini 3. Une seule passe par pitch : la référence n'est pas parfaitement reproductible, mais la sortie brute de chaque appel est conservée.
- Flash plutôt que Pro : `gemini-3.1-pro-preview` n'a aucun quota sans facturation. Si la validation échoue, refaire les notes avec Pro (`--model gemini-3.1-pro-preview`) est la première piste. L'identifiant renvoyé par l'API est enregistré dans chaque ligne.
- Accord mesuré sur 12 pitchs : c'est assez pour détecter un désaccord franc, pas pour une conclusion fine.
