# Candidats de sourcing — les 37 pitchs dérivés

Matière première identifiée pour chaque slot dérivé de [`CALIBRATION_GRID.md`](CALIBRATION_GRID.md). Les 13 slots synthétiques ne figurent pas ici : il n'y a rien à sourcer.

Ce sont des **ancrages**, pas des obligations. Un autre cas qui colle mieux au profil le remplace. La seule contrainte est de respecter la cible de score et le profil du slot.

> **Une société = un slot.** Les alternatives sont indiquées pour que deux rédacteurs ne partent pas de la même boîte. Le premier qui prend note son choix dans `data/pitches.jsonl`.

## Pourquoi trois viviers

Tout ce qui est publié est un **survivant** : on ne publie pas le deck d'une société qui n'a jamais levé. Les bibliothèques de decks ne contiennent donc, par construction, aucun mauvais pitch — elles ne couvrent que 12 slots sur 50.

| Palier | Slots | Vivier | Logique |
|---|---|---|---|
| Fort | 12 | Levées récentes documentées | Le biais de survivant est ici ce qu'on cherche |
| Moyen | 17 | Annuaire YC + levées modestes + échecs récents | Variance naturelle |
| Faible | 8 | **Post-mortems d'échec** | La seule source de mauvais pitchs qui existe |

---

## Table maître

### Palier fort — P001 à P012

| Slot | Secteur | Cible | Ancrage principal | Alternative |
|---|---|---:|---|---|
| P001 | climate-tech | 92 | **Tulum Energy** — 27 M$, hydrogène turquoise par pyrolyse du méthane | DePoly |
| P002 | fintech B2B | 88 | **Agora** — 50 M$ Série A, infrastructure stablecoin en marque blanche | Natural (30 M$, paiements pour agents IA) |
| P003 | health-tech | 85 | **Hello Patient** — 22,5 M$ Série A, IA conversationnelle pour la communication patient | Doctolib |
| P004 | dev tools | 82 | **Embedder** — YC S2025, agent de code firmware, 20+ plateformes MCU/SoC | annuaire YC dev tools (462 sociétés) |
| P005 | cybersecurity | 79 | **Upwind Security** — 180 M$ Série A, visibilité cloud à l'exécution | — |
| **P006** | logistics | **78** | **Flock Freight** — 215 M$ Série D, valorisation 1 Md$, mutualisation de camions LTL | Augment (85 M$, logistique autonome) |
| P007 | AI SaaS | 76 | annuaire YC — chercher un dossier solide, marché encombré | — |
| P008 | proptech | 75 | **EliseAI** — opérations immobilières pilotées par IA | Mews, Property Finder |
| P009 | marketplace | 73 | annuaire YC `/industry/marketplace` | — |
| P010 | foodtech D2C | 72 | **Olipop** — 50 M$ Série C menée par J.P. Morgan, valorisation 1,85 Md$ | ByHeart |
| P011 | HR / future of work | 71 | **Ashby** — 50 M$ Série D, plateforme de recrutement analytique | Darwinbox (140 M$) |
| P012 | mobility | 70 | **Donut Lab** — 25 M€ seed, composants de mobilité électrique | — |

> **P006 mérite un traitement à part.** C'est le premier recalé, à un point du dernier retenu. Il doit être **franchement bon**, pas un dossier moyen déguisé — d'où un ancrage pris dans le même vivier que le palier fort. Si ce pitch est bâclé, le test central du jeu de données ne teste rien.

### Palier moyen — 17 slots dérivés

| Slot | Secteur | Cible | Ancrage | Ce qu'il apporte |
|---|---|---:|---|---|
| P013 | foodtech D2C | 68 | **ByHeart** — 72,2 M$, nutrition infantile, transparence des ingrédients | Traction réelle, marges D2C tendues |
| P014 | HR | 66 | **Zelt** — 5,7 M€, unifie paie, onboarding, matériel et avantages | Marché porteur, différenciation faible |
| P015 ⚠️ | climate-tech | 65 | **DePoly** — 23 M$, recyclage chimique du PET | Techno crédible, économie contestable |
| P016 | health-tech | 64 | **Forward Health** — 650 M$ levés, valo 1 Md$, CarePods à 1 M$ pièce sur 5 sites, arrêt fin 2024 | Impressionnant en façade, remboursement jamais traité |
| P017 ⚠️ | cybersecurity | 62 | **Zip Security** — seed puis Série A, cyber accessible aux PME | Équipe forte, produit décrit vaguement |
| P018 | dev tools | 61 | annuaire YC `/industry/developer-tools` | Communauté active, monétisation embryonnaire |
| P019 | agritech | 60 | **Guardian Agriculture** — matériel fonctionnel, essais sans commandes | Techno qui marche, go-to-market absent |
| P020 | fintech B2B | 59 | **Solid** — 81 M$, Chapter 11 en avril 2025 | Croissance réelle, dépendance à un partenaire |
| P021 | media / creator | 58 | **Spotter** — valo 1,7 Md$ en 2022, objectifs manqués en 2025 | Audience massive sur une seule plateforme |
| P022 | logistics | 57 | **Octup** — 12 M$ seed, plateforme IA pour prestataires 3PL | Opérations solides, marché étroit |
| P024 ⚠️ | proptech | 54 | **Vantaca** — logiciel de gestion immobilière | Bonne traction, équipe inconnue, secteur réglementé |
| P026 | edtech | 52 | **Edukoya** — arrêt 2025, rentabilité jamais atteinte | Bons résultats, économie absente |
| P030 | social app | 48 | annuaire YC `/industry/consumer` | Engagement réel, aucun modèle |
| P032 | foodtech D2C | 46 | **MyGlamm / POPxo / Moms Co** — effondrement par intégrations ratées | Marque connue, exécution défaillante |
| P033 ⚠️ | hardware | 45 | **Jawbone** — le pitch d'avant l'échec | Techno réelle, demande jamais démontrée |
| P035 | climate-tech | 43 | Climate-tech britannique arrêtée peu après une annonce d'expansion, ~200 licenciements | Sujet porteur, exécution absente |
| P037 | agritech | 41 | **Vertical Future** — ferme verticale, coûts énergétiques intenables | Produit testé, l'agriculteur ne peut pas payer |

### Palier faible — 8 slots dérivés

| Slot | Secteur | Cible | Ancrage | Mode d'échec |
|---|---|---:|---|---|
| P039 | media / creator | 38 | **StreamElements** — 23 M de créateurs, 111 M$ levés, jamais rentable | Vanity metrics |
| P040 | cybersecurity | 36 | Société cyber ayant cédé activité et techno à Tufin, ~300 licenciements | Menace réelle, solution jamais expliquée |
| P041 | social app | 34 | **Crowdmix** — bêta seule sortie, argent parti en frais de structure | Exécution absente |
| P042 | proptech | 32 | **Masteos** — 40 M€ Série A en 2022, redressement judiciaire en janvier 2024 | Marché retourné, hypothèses non révisées |
| P043 | edtech | 30 | **Byju's** — jusqu'à 22 Md$ de valorisation, vente agressive | Croissance achetée |
| P045 | hardware | 25 | **Juicero** — presse à jus connectée à 700 $ | Aucune demande |
| P047 | agritech | 19 | **FarmWise** — essais jamais convertis en commandes | Coûts intenables |
| P048 | mobility | 16 | **Bird / Circ** — ~100 licenciements, jusqu'à 10 000 trottinettes recyclées | Modèle déjà démenti |

---

## La technique du palier faible

Un post-mortem raconte la fin ; on a besoin du début.

**On lit pourquoi la société est morte, puis on écrit le pitch tel qu'il aurait été présenté avant l'échec**, avec les faiblesses déjà lisibles pour qui sait lire.

StreamElements l'illustre : 23 millions de créateurs servis, 111 M$ levés, revenus adossés à une seule plateforme puis dilution des budgets publicitaires. Le pitch dérivé affiche donc des chiffres d'audience spectaculaires et aucune économie derrière — et on demande au modèle de refuser de compter l'audience comme de la traction.

C'est un pitch faible **authentique**, pas une caricature. La différence s'entend, et c'est ce qu'on veut faire détecter.

## Sources

### Palier fort et levées récentes
[Tech.eu — plus grandes seed européennes 2025](https://tech.eu/2026/01/23/from-idea-to-impact-europes-15-largest-tech-seed-rounds-in-2025/) · [TechCrunch — Natural](https://techcrunch.com/2026/07/20/natural-raises-30m-to-reinvent-payments-for-ai-agents-and-take-on-stripe/) · [Crunchbase — santé/IA](https://news.crunchbase.com/health-wellness-biotech/ai-healthcare-funding-rises-2025/) · [Pinpoint — financement cyber 2025](https://pinpointsearchgroup.com/2025-cyber-security-vendor-funding-report/) · [Crunchbase — proptech](https://news.crunchbase.com/real-estate-property-tech/rebound-ai-fintech-data-eoy-2025/) · [People Matters — HR tech 2025](https://me.peoplemattersglobal.com/article/funding-investment/the-world-invests-in-the-future-of-work-2025s-top-hr-tech-funding-45364) · [Vestbee — foodtech 2025](https://www.vestbee.com/insights/articles/the-state-of-foodtech-in-2025-investment-opportunities-and-key-risks)

### Bibliothèques de decks
[CB Insights — 29 licornes](https://www.cbinsights.com/research/billion-dollar-startup-pitch-decks/) · [Business Insider — 1 100+ decks](https://finance.yahoo.com/news/pitch-deck-library-search-over-150726372.html) · [Slidebean](https://slidebean.com/pitch-deck-examples) · [Cirrus Insight](https://www.cirrusinsight.com/blog/startup-pitch-decks)

> **Attention à la date.** Un deck de 2008 noté avec une grille de 2026 récolte un score artificiellement bas : montants, repères de marché et standards de traction ont bougé. Privilégier le récent, ou réactualiser les ordres de grandeur en rédigeant.

### Annuaire YC
[ycombinator.com/companies](https://www.ycombinator.com/companies), une page par industrie :

```
/companies/industry/developer-tools     462 sociétés
/companies/industry/health-tech
/companies/industry/proptech
/companies/industry/hr-tech
/companies/industry/consumer
```

Un one-liner YC n'est pas un pitch : c'est un point de départ à développer jusqu'à 800 mots. [VCBacked](https://www.vcbacked.co/yc) permet de dépasser le plafond de 1 000 résultats de l'annuaire officiel.

### Post-mortems d'échec
[CB Insights — 483 post-mortems](https://www.cbinsights.com/research/startup-failure-post-mortem/) · [Foundevo — 442](https://www.foundevo.com/442-startup-failure-post-mortems/) · [Failory — réseaux sociaux](https://www.failory.com/startups/social-media-failures) · [Failory — edtech](https://www.failory.com/startups/edtech-failures) · [Sifted — faillites 2024](https://sifted.eu/articles/startups-went-bust-2024) · [AgTech Navigator](https://www.agtechnavigator.com/Article/2026/01/28/why-agtech-start-ups-failed-last-year-and-a-playbook-for-2026/) · [Mission Media — StreamElements](https://missionmedia.asia/creator-economy-platforms-collapse-streamelements/) · [CB Insights — hardware](https://www.cbinsights.com/research/report/hardware-startups-failure-success/)

---

## Rappel : la source ne fixe pas la note

Byju's a valu 22 Md$, StreamElements a levé 111 M$, Forward Health 650 M$. Leurs pitchs n'étaient sûrement pas mauvais.

Le post-mortem sert à **écrire un pitch faible crédible**, pas à justifier un score. La note de référence vient uniquement de la double annotation à l'aveugle, sur le texte et rien d'autre.

C'est la règle la plus facile à enfreindre sans s'en rendre compte : on connaît la fin de l'histoire en rédigeant, et la tentation est de noter l'entreprise plutôt que le pitch.

## Ce qui reste à faire

- [x] **4 slots sans ancrage nommé** — P007 automatisation du support, P009 pièces détachées industrielles, P018 outil de build open source, P030 application sociale de groupe : choisis dans l'annuaire YC par industrie
- [x] Confirmer les 33 ancrages ci-dessus, ou les remplacer — tous conservés
- [x] Renseigner `source_url` et `accessed_at` dans `data/pitches.jsonl` — **37/37 dérivés**
- [x] Renseigner `written_by` — 13 · 12 · 12 · 12
- [ ] Initialiser `data/dataset_card.md`
- [ ] Valider humainement les 44 pitchs encore en `drafted`

> Les 50 pitchs sont rédigés. Ce qui reste sur ce document est clos ; la suite se joue dans l'annotation.

Les 13 slots synthétiques n'ont rien à sourcer : P023, P025, P027, P028, P029, P031, P034, P036, P038, P044, P046, P049, P050.
