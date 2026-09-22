# Sourcing des 50 pitchs

Comment alimenter chaque ligne de [`CALIBRATION_GRID.md`](CALIBRATION_GRID.md) en matière première réelle, sans copier quoi que ce soit ni prétendre qu'une entreprise fictive existe.

## Le problème à résoudre

Tout ce qui est public est un **survivant**. Business Insider a 1 100+ decks, CB Insights ceux de 29 licornes, Slidebean des dizaines d'exemples — ce sont les boîtes qui ont levé. Aucun pitch médiocre, aucun pitch mauvais.

Or la grille demande 12 faibles et 26 moyens. Si on ne trouve que des pitchs forts, on les invente tous, et le jeu de données devient une pure production de LLM notée par un LLM : boucle fermée, aucune texture réelle.

## La solution : trois viviers, un par palier

| Palier | Vivier | Pourquoi ça marche |
|---|---|---|
| **Forts** (P001-P005) | Decks publics de boîtes financées | Ce sont justement les survivants. Ici c'est ce qu'on veut. |
| **Moyens** (P006-P015) | Annuaire YC, Product Hunt | 6 300+ boîtes YC, dont l'immense majorité n'est ni un échec ni une licorne. Variance naturelle. |
| **Faibles** (P016-P020) | **Post-mortems d'échec** | 483 post-mortems publics chez CB Insights, écrits par les fondateurs eux-mêmes. |

Le troisième vivier est la vraie trouvaille. Un post-mortem dit noir sur blanc pourquoi la boîte est morte : pas de besoin marché (44 %), pas de product-market fit (43 %), économie unitaire intenable (19 %). C'est la matière exacte d'un pitch faible.

**La technique** : on lit le post-mortem, puis on écrit le pitch **tel qu'il aurait été présenté avant l'échec** — avec les faiblesses déjà visibles dans le texte pour qui sait lire. C'est un pitch faible authentique, pas une caricature écrite à dessein. La différence se sent, et c'est précisément ce qu'on demande au modèle de détecter.

## Sources

### Palier fort

- [CB Insights — decks de 29 licornes](https://www.cbinsights.com/research/billion-dollar-startup-pitch-decks/)
- [Business Insider — bibliothèque de 1 100+ decks](https://finance.yahoo.com/news/pitch-deck-library-search-over-150726372.html)
- [Slidebean — exemples de decks](https://slidebean.com/pitch-deck-examples)
- [Failory — deck Airbnb](https://www.failory.com/pitch-deck/airbnb)

Attention à la date : le deck Airbnb est de 2008. Un pitch de 2008 noté avec une grille de 2026 produit un score artificiellement bas. Privilégier les décks récents, ou actualiser les repères de marché.

### Palier moyen

- [Annuaire officiel YC](https://www.ycombinator.com/companies) — gratuit, filtrable par industrie, région, taille d'équipe, batch. La source principale.
- [VCBacked — 6 302 sociétés YC](https://www.vcbacked.co/yc) — utile pour parcourir hors du plafond de 1 000 résultats de l'annuaire officiel.

Un one-liner YC n'est pas un pitch : c'est un point de départ (problème, secteur, client visé) à développer jusqu'à 650 mots.

### Palier faible

- [CB Insights — 483 post-mortems d'échec](https://www.cbinsights.com/research/startup-failure-post-mortem/)
- [Foundevo — 442 post-mortems](https://www.foundevo.com/442-startup-failure-post-mortems/)
- [Why Startups Fail — insights](https://www.whystartupsfail.com/insights)
- [CB Insights — top 9 des raisons d'échec](https://www.cbinsights.com/research/report/startup-failure-reasons-top/)

Le dernier lien sert de grille de lecture : il donne les modes d'échec classiques, qu'on répartit entre les 5 pitchs faibles pour qu'ils ne se ressemblent pas tous.

## Affectation des slots

Elle n'est pas reproduite ici — trois documents portant les mêmes 50 lignes finiraient par diverger.

| Document | Fait autorité sur |
|---|---|
| [`CALIBRATION_GRID.md`](CALIBRATION_GRID.md) | Score cible, profil, flags, origine (dérivé ou synthétique) |
| [`SOURCING_CANDIDATES.md`](SOURCING_CANDIDATES.md) | Les ancrages réels identifiés, avec leurs sources |

En résumé : **37 dérivés du réel, 13 synthétiques**. Les synthétiques sont exactement ceux que le réel ne peut pas fournir — les 5 injections, le buzzword creux, le quasi-vide, le grandiloquent, le « beige » intégral et quelques cas dont le défaut *est* le sujet du test.

Répartition par palier : 12 forts, 26 moyens, 12 faibles.

## Procédure de dérivation

Pour chacun des 37 pitchs dérivés :

1. Choisir une boîte réelle dans le vivier du palier, cohérente avec le secteur du slot.
2. Noter `source_url` et la date d'accès.
3. Extraire la **structure** : problème, client visé, approche, modèle économique.
4. **Changer le nom**, le pays si besoin, les chiffres, les noms de fondateurs.
5. Rédiger jusqu'à 650 mots, au format de `pitch_text`.
6. **Retirer ou ajouter délibérément** ce que la grille de calibration demande pour ce slot — l'information absente est un choix de conception, pas un oubli.
7. Renseigner `source_type: "derived"` et `source_note`.

### Règles non négociables

- Jamais de copier-coller : on reprend la structure, pas les phrases.
- Jamais présenter un pitch fictif comme une entreprise réelle.
- Aucun nom de fondateur réel, aucune coordonnée personnelle.
- Aucun contenu derrière un paywall ou une plateforme privée.
- URL, date d'accès et conditions de réutilisation consignées dans `data/dataset_card.md`.

### Le piège du score

Le devenir réel de la boîte source **ne fixe pas** le score de référence. Une entreprise qui a échoué peut avoir eu un excellent pitch ; une licorne peut avoir pitché médiocrement. Le score de référence vient uniquement de la double annotation à l'aveugle, sur le texte et rien d'autre.

Le post-mortem sert à **écrire un pitch faible crédible**, pas à justifier une note.

## Ordre de travail

1. Chacun prend 5 slots et identifie les boîtes sources → mettre les URL dans l'issue, avant de rédiger.
2. Relecture croisée des 20 sources : cohérence secteur/palier, pas de doublon, rien de confidentiel.
3. Rédaction des 20 `pitch_text`.
4. Double annotation à l'aveugle, selon les binômes de la grille de calibration.
5. Rendu des PDF, dataset card, gel de `data-v1`.

L'étape 1 est rapide et débloque tout le reste. L'étape 4 est le vrai goulot : 40 annotations à produire et réconcilier.
