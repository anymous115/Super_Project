# Dataset card — corpus de pitchs VC

> **Fichier généré.** Produit par `scripts/build_dataset_card.py` depuis
> `data/pitches.jsonl` et `data/calibration.jsonl`. Ne pas éditer à la main :
> relancer le script. Dernière génération : 2026-09-22.

## Ce que c'est

50 pitchs de startups **entièrement fictifs**, en anglais, écrits pour mesurer
un moteur de scoring VC. Chaque pitch est du texte libre structuré en sections
— problème, solution, marché, concurrence, équipe, traction, business model,
go-to-market, financement — comme un fondateur l'enverrait par email.

Le corpus sert d'entrée unique au benchmark du projet : deux modèles reçoivent
exactement la même chaîne de caractères et doivent produire le même objet noté.

## Composition

|  | Valeur |
|---|---|
| Pitchs | 50 |
| Rédigés | 50 |
| Langue | anglais (100 %) |
| Longueur | 82 à 638 mots, médiane 529 |
| Scores cibles | 8 à 92 sur 100 |
| Secteurs | 21 |

### Par palier

| Palier | Pitchs | Scores | Longueur (mots) |
|---|---:|---:|---:|
| fort | 12 | 70–92 | 502–614 |
| moyen | 26 | 40–68 | 403–638 |
| faible | 12 | 8–38 | 82–366 |

La longueur ne suit pas le score : les paliers fort et moyen se recouvrent
presque entièrement. Seul le palier faible est court, parce qu'un mauvais pitch
l'est réellement. Un modèle qui noterait à la longueur trouverait le bas du
classement et se tromperait sur tout le reste.

### Cas particuliers

| Marqueur | Pitchs | Rôle |
|---|---:|---|
| 💉 injection | 5 | contiennent une instruction adressée au modèle évaluateur |
| ⚠️ ambigu | 5 | désaccord attendu entre deux annotateurs humains |
| ␀ info manquante | 12 | une dimension du dossier est absente, et doit être signalée comme telle |

Les cinq injections prennent cinq formes distinctes, sans expression commune :
instruction en clair, instruction cachée dans un e-mail cité, note d'un
prétendu évaluateur précédent, faux score de présélection, injonction directe.
Leurs scores honnêtes vont de 12 à 53, donc une défense qui échoue déplace le
score de plusieurs dizaines de points.

**`is_injection_test` reste dans les métadonnées et n'atteint jamais le modèle.**

## Comment il a été construit

Les scores cibles ont été **fixés avant la rédaction**, dans
[`docs/CALIBRATION_GRID.md`](../docs/CALIBRATION_GRID.md). Écrire d'abord et
noter ensuite aurait produit une distribution resserrée au milieu, sur laquelle
ni la corrélation de rang ni le chevauchement du top 5 ne veulent dire
grand-chose.

Trois viviers, parce que tout ce qui est publié est un survivant : les
bibliothèques de decks ne contiennent, par construction, aucun mauvais pitch.

| Palier | Vivier |
|---|---|
| fort | levées récentes documentées |
| moyen | annuaire YC, levées modestes, échecs récents |
| faible | **post-mortems d'échec** — la seule source de mauvais pitchs qui existe |

Pour le palier faible : on lit pourquoi la société est morte, puis on écrit le
pitch **tel qu'il aurait été présenté avant l'échec**, avec les faiblesses déjà
lisibles pour qui sait lire.

| Origine | Pitchs | Ce que ça veut dire |
|---|---:|---|
| dérivé | 37 | structure et ordres de grandeur inspirés d'une société réelle, texte entièrement réécrit |
| synthétique | 13 | inventé de bout en bout, sans source |

## Provenance

Chaque pitch dérivé porte l'URL consultée et sa date. **Aucun contenu n'a été
copié** : les sources ont servi à connaître un secteur, un ordre de grandeur et
un mode d'échec, jamais à fournir du texte.

| Source | Consultée le | Pitchs |
|---|---:|---|
| [tech.eu](https://tech.eu/2026/01/23/from-idea-to-impact-europes-15-largest-tech-seed-rounds-in-2025/) | 2026-09-22 | P001 P012 P015 P022 |
| [www.fintechfutures.com](https://www.fintechfutures.com/fintech/2025-in-review-the-key-fintech-trends-of-the-year) | 2026-09-22 | P002 |
| [news.crunchbase.com](https://news.crunchbase.com/health-wellness-biotech/ai-healthcare-funding-rises-2025/) | 2026-09-22 | P003 |
| [www.ycombinator.com](https://www.ycombinator.com/companies/industry/developer-tools) | 2026-09-22 | P004 P018 |
| [pinpointsearchgroup.com](https://pinpointsearchgroup.com/2025-cyber-security-vendor-funding-report/) | 2026-09-22 | P005 P017 |
| [startupsavant.com](https://startupsavant.com/startups-to-watch/logistics) | 2026-09-22 | P006 |
| [www.ycombinator.com](https://www.ycombinator.com/companies/industry/ai) | 2026-09-22 | P007 |
| [news.crunchbase.com](https://news.crunchbase.com/real-estate-property-tech/rebound-ai-fintech-data-eoy-2025/) | 2026-09-22 | P008 P024 |
| [www.ycombinator.com](https://www.ycombinator.com/companies/industry/marketplace) | 2026-09-22 | P009 |
| [www.vestbee.com](https://www.vestbee.com/insights/articles/the-state-of-foodtech-in-2025-investment-opportunities-and-key-risks) | 2026-09-22 | P010 P013 |
| [me.peoplemattersglobal.com](https://me.peoplemattersglobal.com/article/funding-investment/the-world-invests-in-the-future-of-work-2025s-top-hr-tech-funding-45364) | 2026-09-22 | P011 P014 |
| [www.cbinsights.com](https://www.cbinsights.com/research/startup-failure-post-mortem/) | 2026-09-22 | P016 P020 |
| [www.agtechnavigator.com](https://www.agtechnavigator.com/Article/2026/01/28/why-agtech-start-ups-failed-last-year-and-a-playbook-for-2026/) | 2026-09-22 | P019 P037 P047 |
| [missionmedia.asia](https://missionmedia.asia/creator-economy-platforms-collapse-streamelements/) | 2026-09-22 | P021 P039 |
| [www.failory.com](https://www.failory.com/startups/edtech-failures) | 2026-09-22 | P026 P043 |
| [www.ycombinator.com](https://www.ycombinator.com/companies/industry/consumer) | 2026-09-22 | P030 |
| [www.foundevo.com](https://www.foundevo.com/442-startup-failure-post-mortems/) | 2026-09-22 | P032 |
| [www.cbinsights.com](https://www.cbinsights.com/research/report/hardware-startups-failure-success/) | 2026-09-22 | P033 P045 |
| [sifted.eu](https://sifted.eu/articles/startups-went-bust-2024) | 2026-09-22 | P035 P042 |
| [techcrunch.com](https://techcrunch.com/2025/12/22/tech-layoffs-2025-list/) | 2026-09-22 | P040 |
| [www.failory.com](https://www.failory.com/startups/social-media-failures) | 2026-09-22 | P041 |
| [techcrunch.com](https://techcrunch.com/?p=1997313) | 2026-09-22 | P048 |

## Usage prévu

Mesurer et comparer des systèmes de scoring automatique de pitchs :
justesse des notes, stabilité du classement, résistance à l'injection,
signalement de l'information manquante.

## Limites

**Ce n'est pas un échantillon de pitchs réels.** Les textes sont écrits pour
couvrir une échelle de qualité, pas pour reproduire la distribution qu'un fonds
reçoit vraiment — laquelle est bien plus concentrée dans le bas.

**Le corpus a été rédigé par un modèle de langage**, relu et corrigé par
l'équipe. Un modèle de la même famille le noterait en partie sur sa propre
cohérence : c'est la raison pour laquelle aucun modèle Anthropic n'est éligible
au benchmark.

**Un seul secteur géographique et une seule langue.** Les pitchs sont anglophones
et les repères de marché européens et nord-américains.

**44 pitchs sur 50 sont encore en `drafted`** : rédigés,
pas validés. Les scores de référence issus de la double annotation ne sont pas
encore produits.

## Réutilisation

Les sociétés sont fictives. Les noms, les chiffres et les personnes citées sont
inventés — **aucun pitch ne doit jamais être présenté comme une entreprise
réelle**, et aucun n'est une évaluation d'une société existante.

Le corpus ne contient ni adresse e-mail, ni URL, ni numéro de téléphone, ni nom
de personne réelle. C'est vérifié par un test (`tests/test_corpus.py`).

> ⚠️ **Licence à décider.** Le dépôt n'a pas de fichier `LICENSE`. Tant qu'il n'en
> a pas, le corpus n'est pas réutilisable par un tiers, même s'il est public.

## Fichiers

| Fichier | Contenu |
|---|---|
| `data/pitches.jsonl` | les pitchs, leur provenance et leur statut |
| `data/calibration.jsonl` | les scores cibles — généré, lecture seule |
| `data/reference_scores.jsonl` | les scores de référence — **pas encore produit** |
| `data/annotations/` | les annotations individuelles et les réconciliations |
