# Validation de Mathisse — premier lot

> **Évolution V1 — 24 septembre 2026 :** l’équipe a supprimé la validation humaine obligatoire. Les 50 notes directes IA alimentent Unicornext. Voir [la décision V1](UNICORNEXT_V1.md). Les mentions de validation ci-dessous décrivent le protocole antérieur.

Cette fiche prépare la relecture des pitchs dont `written_by` vaut `D` (Mathisse). Les cinq statuts restent `drafted` tant que la relecture et les corrections éventuelles ne sont pas terminées.

## Ce que tu dois décider

Pour chaque pitch, vérifie : (1) le profil de calibration est-il perceptible dans le texte ? (2) chaque force et limite annoncée repose-t-elle sur une phrase précise ? (3) les chiffres et termes financiers sont-ils cohérents ? (4) la source est-elle correctement anonymisée, ou le pitch est-il clairement synthétique ? (5) une information volontairement absente reste-t-elle vraiment absente ?

Note ta décision **validé / à corriger**, avec les phrases à modifier. Ne change `review_status` dans `data/pitches.jsonl` qu’après une vraie relecture.

| Pitch | Entreprise | Cible de rédaction | Point à vérifier |
|---|---|---:|---|
| P007 | Halden | 76/100 | Bon produit, marché encombré. |
| P008 | Tenura | 75/100 | Belle traction, marché réglementé. |
| P009 | Sparepath | 73/100 | Bon des deux côtés, économie unitaire jamais donnée. |
| P023 | Aloria | 55/100 | Le cas « beige » : tout est moyen, rien ne dépasse. |
| P024 | Harbourline | 54/100 | Bonne traction, équipe inconnue, marché réglementé. |

> Les scores ci-dessus sont des intentions de rédaction, pas une notation indépendante du pitch.

## Pré-contrôles à discuter

- **P007 :** 78 contrats × 52 000 \$ donnent environ 4,06 M\$ d'ARR, cohérents avec 4,1 M\$. En revanche, 78 clients × 2 400 tickets mensuels × 52 % résolus × 0,90 \$ × 12 donnent environ 1,05 M\$. Le minimum de plateforme pourrait expliquer l'écart ; son ordre de grandeur doit être explicite.
- **P008 :** 91 000 unités × 3,60 € × 12 donnent 3,93 M€, cohérents avec 3,9 M€ d'ARR. Le CAC de 31 000 € et l'ACV de 115 000 € à 71 % de marge brute donnent environ 4,6 mois de récupération après signature, alors que le texte annonce 14 mois. Clarifier si les 14 mois incluent le cycle de vente de 11 mois.
- **P009 :** le take rate, le prix de l'abonnement et la marge sont volontairement absents. Vérifier que le texte ne donne aucun chiffre permettant de déduire malgré tout l'économie unitaire.
- **P023 :** 1,4 M\$ d'ARR répartis sur 6 400 payeurs impliquent environ 18,23 \$ par mois et par payeur, alors que le prix direct est 29 \$ et le tarif employeur 16 \$. Le mélange des deux canaux doit rendre ces chiffres compréhensibles.
- **P024 :** 310 clients × 2 280 \$ mensuels × 12 donnent 8,48 M\$, cohérents avec 8,4 M\$ d'ARR. Juger surtout si la faiblesse de l'équipe et les contraintes réglementaires justifient le profil « moyen » malgré cette traction.

Ces calculs sont des pistes de relecture, pas des décisions de validation. Les chiffres du corpus fictif doivent être cohérents entre eux ; les liens d'inspiration ne sont pas des preuves que ces sociétés fictives existent.

## P007 — Halden

**Secteur :** AI SaaS · **Statut :** `drafted` · **Auteur responsable :** D · **Longueur :** 596 mots

**Cible :** 76/100 · **Profil visé :** Bon produit, marché encombré. · **Cas particulier :** aucun

**Provenance :** annuaire YC /industry/ai — automatisation du support client, marché encombré

**Lien d’inspiration :** https://www.ycombinator.com/companies/industry/ai · consulté le 2026-09-22

### Texte à relire

```text
Halden — customer support automation for mid-market SaaS

THE PROBLEM

A SaaS company with 40,000 customers receives around 9,000 support tickets a month. Roughly 60% are variations on eleven questions. Support teams answer them again and again, and the cost scales linearly with the customer base — which is the opposite of how software is supposed to work.

Existing automation makes this worse as often as better. Deflection bots answer confidently from a knowledge base that is out of date, and the customer ends up angrier than before, having spent four minutes to reach a human.

OUR SOLUTION

Halden answers support tickets from the product's actual state rather than from documentation.

When a customer asks why their invoice shows a charge they did not expect, we read their subscription, their usage and their billing history, and explain that specific charge. When we cannot answer with confidence, we route to a human with a summary of what we checked and why we stopped.

That last part matters more than the answers. A system that knows when to stop is the difference between deflection and automation.

THE MARKET

Customer support software is a $28B market. Our segment is B2B SaaS companies between $5M and $100M in revenue — about 24,000 companies — which have enough ticket volume to feel the cost and not enough headcount to absorb it.

COMPETITION

This is a crowded category and getting more so. The incumbent helpdesk vendors all shipped AI features last year. A dozen funded startups do some version of what we do.

We are not going to win on being the only ones. We win deals on integration depth — we connect to the product's own data, not only to its help centre — and on our refusal rate, which we publish. Most competitors optimise for deflection percentage, which is the wrong metric and produces exactly the frustrating experience the category is known for.

THE TEAM

Marcus Wei and Elena Popescu both come from support engineering rather than from machine learning. Marcus ran technical support at a developer tools company through a period when ticket volume grew eight-fold. Elena built internal tooling for a support organisation of 200 people.

Neither has built a company before, and neither has a research background. We have leaned on that: our product decisions come from having been on the receiving end of bad support automation.

Twenty-one people.

TRACTION

- 78 customers, average 2,400 tickets a month each
- $4.1M annual recurring revenue, growing 6% month over month
- 52% of tickets resolved without human involvement, against a 71% industry claim we deliberately do not chase
- customer satisfaction on automated resolutions: 4.4/5, against 4.5 for human-handled
- net revenue retention 118%

The satisfaction parity is the number we care about. Deflection without it is just an obstacle course.

BUSINESS MODEL

Per-resolution pricing at $0.90, with a monthly platform minimum. Average contract value is $52,000. Gross margin is 74% after inference costs, which fall as we route more traffic to smaller models.

Per-resolution billing means we only earn when we actually solve something, which customers like and which makes our revenue track their volume rather than their headcount.

GO-TO-MARKET

Direct sales to heads of support and customer experience, 6-week average cycle. Two helpdesk vendors have integration partnerships with us, which brings warm pipeline but also puts us one product decision away from being competed with directly.

FUNDING

We are raising $11M to deepen integrations with the four most common billing systems, expand the refusal-detection work, and build out a sales team that is currently three people.
```

### Décision de relecture

- [ ] Profil et niveau global crédibles.
- [ ] Chiffres, unités et formulation cohérents.
- [ ] Source/anonymisation ou caractère synthétique vérifiés.
- [ ] Limite propre à ce cas vérifiée.
- **Décision :** à renseigner (`validé` / `à corriger`).
- **Corrections précises :** à renseigner.

## P008 — Tenura

**Secteur :** proptech · **Statut :** `drafted` · **Auteur responsable :** D · **Longueur :** 548 mots

**Cible :** 75/100 · **Profil visé :** Belle traction, marché réglementé. · **Cas particulier :** aucun

**Provenance :** EliseAI — opérations immobilières pilotées par IA

**Lien d’inspiration :** https://news.crunchbase.com/real-estate-property-tech/rebound-ai-fintech-data-eoy-2025/ · consulté le 2026-09-22

### Texte à relire

```text
Tenura — operations software for regulated residential portfolios

THE PROBLEM

A property manager running 4,000 regulated residential units in France or Germany spends most of their week on compliance rather than on property. Rent caps, indexation rules, energy performance obligations and tenant notification requirements change by jurisdiction and by year, and getting one wrong is not a fine — it can invalidate a lease.

The software they use was built for unregulated markets and treats compliance as a document store. The actual rules live in a spreadsheet maintained by whoever has been there longest.

OUR SOLUTION

Tenura encodes the rules and applies them to the portfolio.

When indexation opens on a lease, we compute the permitted increase for that unit under that jurisdiction's current rules, generate the compliant notice, and track the notification deadline. When an energy performance obligation approaches, we flag the units affected and the work required before they can be relet.

The rules are versioned. When a jurisdiction changes its cap, we update one definition and every affected lease recalculates, with an audit trail showing what applied when.

THE MARKET

Residential property management software is a €3.1B market in Europe. Our addressable segment is narrower than that headline suggests: we serve regulated residential portfolios between 1,000 and 20,000 units in France, Germany, Austria and the Netherlands, which is roughly 2,800 organisations.

Regulation is what makes the product valuable and what limits where we can sell it. Each new jurisdiction is months of legal work before the first euro.

COMPETITION

The large property management platforms are strong on accounting and weak on regulation, which they treat as a local configuration problem. Local incumbents in each market understand the rules but sell software that looks like 2009.

Our position is narrow by design. We are not trying to replace the accounting system; we integrate with it.

THE TEAM

Johanna Ritter spent seven years in asset management at a residential REIT, latterly responsible for a 12,000-unit German portfolio through two regulatory changes. Bastien Cordier was engineering lead at a European lease accounting company.

Neither has a legal background, which is why we retain two housing law firms on an ongoing basis rather than pretending we can track this ourselves.

Twenty-six people, four of them full-time on rule maintenance.

TRACTION

- 34 customers covering 91,000 units
- €3.9M annual recurring revenue, growing 5% month over month
- gross retention 97%, no customer lost in two years
- average of 11 months from first contact to signature
- four jurisdictions live, a fifth in legal review

BUSINESS MODEL

€3.60 per unit per month, billed annually, with a floor. Average contract value is €115,000. Gross margin is 71% after rule maintenance, which is a real and permanent cost rather than a one-time build.

Retention is the strength here: once a portfolio's compliance runs through us, leaving means rebuilding the rule set. That is also why our sales cycle is eleven months.

GO-TO-MARKET

Direct enterprise sales, supported by presence at property management industry associations. Acquisition cost is €31,000 per customer, recovered in 14 months — long, but against 97% retention.

FUNDING

We are raising €14M to open two additional jurisdictions, build the energy performance module that three customers have asked for, and grow a sales team that cannot currently cover four countries.
```

### Décision de relecture

- [ ] Profil et niveau global crédibles.
- [ ] Chiffres, unités et formulation cohérents.
- [ ] Source/anonymisation ou caractère synthétique vérifiés.
- [ ] Limite propre à ce cas vérifiée.
- **Décision :** à renseigner (`validé` / `à corriger`).
- **Corrections précises :** à renseigner.

## P009 — Sparepath

**Secteur :** marketplace · **Statut :** `drafted` · **Auteur responsable :** D · **Longueur :** 502 mots

**Cible :** 73/100 · **Profil visé :** Bon des deux côtés, économie unitaire jamais donnée. · **Cas particulier :** missing_info

**Provenance :** annuaire YC /industry/marketplace — pièces détachées industrielles, économie unitaire jamais donnée

**Lien d’inspiration :** https://www.ycombinator.com/companies/industry/marketplace · consulté le 2026-09-22

### Texte à relire

```text
Sparepath — a marketplace for industrial spare parts

THE PROBLEM

When a production line stops for a failed component, the plant manager has hours, not days. Finding the part means calling three distributors, waiting for quotes, and discovering that two of them do not stock it.

Meanwhile, European manufacturers hold an estimated €40B of spare parts inventory, much of it obsolete for the machine it was bought for and perfectly usable for someone else's. There is no liquid market for any of it.

OUR SOLUTION

Sparepath lets a plant search by part number, by machine model, or by photograph, and see available stock across distributors and other manufacturers' surplus inventory in one view.

Sellers list by uploading their inventory export; we normalise part numbers across eleven manufacturer naming conventions, which is the unglamorous work that makes the search actually return results. Buyers see availability, condition, location and delivery time, and order without a quote cycle.

Emergency orders ship the same day where stock is within 300 km. That is the case we win on.

THE MARKET

European industrial MRO — maintenance, repair and operations — is a €95B market. Spare parts procurement is roughly €31B of it, and the surplus resale segment we are opening barely exists as a category today.

We sell to plant maintenance managers in discrete manufacturing: automotive suppliers, packaging, food processing.

COMPETITION

Distributor catalogues are deep within their own brands and blind outside them. Two general industrial marketplaces exist but treat spare parts as another product category, without part number normalisation, which means their search fails on exactly the query that matters.

Our defensibility is the normalisation layer and the inventory already listed. Neither is impossible to replicate; both take time.

THE TEAM

Pieter Vandenberg spent eleven years in industrial distribution, latterly running procurement for a packaging group with fourteen plants. Ana Sousa built search infrastructure at a European e-commerce company.

Seventeen people, six of them in the catalogue team that handles normalisation.

TRACTION

- 1,340 buying plants registered, 620 having ordered in the last quarter
- 210 selling organisations
- €18M in gross merchandise value over the last twelve months, up from €6M
- 2.1 million normalised part references
- median time from search to order: 11 minutes
- 44% of orders are for parts the buyer's usual distributor does not stock

BUSINESS MODEL

We charge sellers a commission on completed transactions and offer a subscription tier for buyers who want stock alerts on their machine fleet.

Volume has grown steadily and the subscription tier is being adopted. We expect the economics to improve as the catalogue deepens.

GO-TO-MARKET

Direct outreach to maintenance managers, plus presence at industrial trade fairs where our buyers already go. Word of mouth within manufacturing groups has been our most effective channel — six of our largest buyers came from a single group's internal recommendation.

FUNDING

We are raising €13M to expand the catalogue team, open the Italian and Spanish markets, and build the machine-fleet monitoring that turns emergency buyers into subscribers.
```

### Décision de relecture

- [ ] Profil et niveau global crédibles.
- [ ] Chiffres, unités et formulation cohérents.
- [ ] Source/anonymisation ou caractère synthétique vérifiés.
- [ ] Limite propre à ce cas vérifiée.
- **Décision :** à renseigner (`validé` / `à corriger`).
- **Corrections précises :** à renseigner.

## P023 — Aloria

**Secteur :** wellness · **Statut :** `drafted` · **Auteur responsable :** D · **Longueur :** 458 mots

**Cible :** 55/100 · **Profil visé :** Le cas « beige » : tout est moyen, rien ne dépasse. · **Cas particulier :** aucun

**Provenance :** Pitch synthétique, sans source externe.

### Texte à relire

```text
Aloria — a guided wellness programme for people who have tried apps before

THE PROBLEM

People who want to improve their sleep, their stress levels or their exercise habits generally know what to do. They download an app, use it for eleven days, and stop. Engagement in consumer wellness apps drops below 5% at ninety days across the category.

The content is not the problem. The follow-through is.

OUR SOLUTION

Aloria combines a structured twelve-week programme with a weekly check-in from a human coach.

The programme covers sleep, movement, nutrition and stress, adapted to what the user reports at the start and adjusted as they go. The coach reviews progress once a week and sends a short message — not a session, a message — which is enough contact to change completion rates without carrying the cost of a full coaching model.

Users log activity in the app, which syncs with the usual wearables.

THE MARKET

Consumer wellness applications represent roughly $11B globally, growing at around 9% a year. Employers are an increasingly common buyer, with wellness benefits now offered by a majority of companies above 500 employees.

Our addressable segment is adults who have previously used and abandoned a wellness app, which is most people who have used one.

COMPETITION

The category is crowded. Several large meditation and fitness apps have far more users and far more content than we do. A handful of coaching-led services charge between $200 and $400 a month.

We sit in the middle: more support than an app, less cost than a coach. That position is reasonable and it is not defensible.

THE TEAM

Julia Sandberg worked in product at a consumer health company for five years. Marc Oliveira was a certified health coach and ran a coaching practice before joining.

Fourteen people, four of them coaches.

TRACTION

- 22,000 registered users, 6,400 paying
- $1.4M annual recurring revenue
- 42% of users complete the twelve-week programme
- monthly churn 6.2%
- four employer contracts covering 2,100 employees

Completion at 42% is meaningfully above the category, and it is the number we would point to if asked for one.

BUSINESS MODEL

$29 a month direct, or $16 per employee per month through employers. Gross margin 61%, held down by coach time. Acquisition cost $74 against a lifetime value we estimate at $310.

The economics work at current scale. Whether they hold as we add coaches is untested.

GO-TO-MARKET

Paid social for direct users, and a small outbound effort to HR benefits managers, which produced the four employer contracts over eight months.

FUNDING

We are raising $6M to grow the employer channel, which has better retention and lower acquisition cost than direct, and to bring coach cost per user down through better tooling.
```

### Décision de relecture

- [ ] Profil et niveau global crédibles.
- [ ] Chiffres, unités et formulation cohérents.
- [ ] Source/anonymisation ou caractère synthétique vérifiés.
- [ ] Limite propre à ce cas vérifiée.
- **Décision :** à renseigner (`validé` / `à corriger`).
- **Corrections précises :** à renseigner.

## P024 — Harbourline

**Secteur :** proptech · **Statut :** `drafted` · **Auteur responsable :** D · **Longueur :** 539 mots

**Cible :** 54/100 · **Profil visé :** Bonne traction, équipe inconnue, marché réglementé. · **Cas particulier :** ambiguous

**Provenance :** Vantaca — logiciel de gestion immobilière

**Lien d’inspiration :** https://news.crunchbase.com/real-estate-property-tech/rebound-ai-fintech-data-eoy-2025/ · consulté le 2026-09-22

### Texte à relire

```text
Harbourline — management software for homeowner associations

THE PROBLEM

A company managing 140 homeowner associations handles governance for each one separately: board meetings, minutes, votes, dues collection, reserve fund accounting, violation notices and the statutory filings that vary by state.

Most of it runs on software written in the 2000s or on nothing at all. Dues collection is by cheque in a majority of associations we have surveyed. A missed statutory notice is not an inconvenience — in several states it invalidates the assessment.

OUR SOLUTION

Harbourline runs the full lifecycle for a homeowner association in one system.

Dues are collected by direct debit with automated delinquency handling. Board votes run electronically with a quorum and record that satisfies statutory requirements in the states we cover. Reserve accounting follows the study. Violation notices are generated with the correct notice periods for the jurisdiction, and the record is kept in a form that stands up when a dispute reaches a lawyer.

Owners get a portal that works on a phone, which is the single most requested thing in this market and the thing the incumbents do worst.

We cover statutory requirements in eleven states. Each one took between three and seven weeks of work with local counsel.

THE MARKET

There are approximately 370,000 homeowner associations in the United States, managed by around 9,000 management companies.

The market is regulated state by state, which is both the moat and the ceiling. Every state we add is a separate body of law, and a competitor entering has to do the same work eleven times to match our coverage. It also means our expansion rate is bounded by legal work rather than by engineering, and that several states have rules restrictive enough that we have decided not to enter them at all.

The eleven states we cover contain roughly 44% of US associations. Realistic reachable revenue is materially smaller than the association count suggests.

COMPETITION

Three legacy vendors hold most of the installed base with products that predate mobile. Two newer entrants cover dues collection only.

THE TEAM

Dana Whitfield and Erik Sandoval founded Harbourline three years ago. Dana previously worked in operations at a property management company for two years. Erik was a software engineer at two mid-sized companies.

Neither of us has founded a company before, neither has worked in association governance, and we learned this market by cold-calling managers for four months before we wrote any code. Twenty-nine people now, and our head of compliance has more relevant experience than either founder.

TRACTION

- 310 management companies, covering 11,900 associations
- $8.4M annual recurring revenue, up from $3.2M eighteen months ago
- 4.1% annual churn
- 74% of associations on the platform now collect dues electronically, against 31% at onboarding
- net revenue retention 128%

BUSINESS MODEL

$2.40 per door per month, plus payment processing revenue on dues collected. Average management company pays $2,280 a month.

Gross margin 81%. Acquisition cost $9,100 against first-year contract value of $27,400.

GO-TO-MARKET

Direct sales to management companies, plus a presence at the state association conferences where these buyers all go.

FUNDING

We are raising $20M to reach six further states and to build the reserve study integration that management companies currently buy separately.
```

### Décision de relecture

- [ ] Profil et niveau global crédibles.
- [ ] Chiffres, unités et formulation cohérents.
- [ ] Source/anonymisation ou caractère synthétique vérifiés.
- [ ] Limite propre à ce cas vérifiée.
- **Décision :** à renseigner (`validé` / `à corriger`).
- **Corrections précises :** à renseigner.
