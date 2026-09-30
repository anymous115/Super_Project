# Unicornext — Notes orales (version 2)

Durée : **10 minutes de présentation + 2 minutes de démonstration**. 14 diapositives, sans annexes.

Les extraits affichés proviennent du notebook `08_quality_vs_cost_benchmark.ipynb`. Les numéros de cellules indiquent leur position dans le fichier, et non leur numéro d’exécution. Les adaptations concernent les retours à la ligne. La régression orange est une analyse complémentaire des résultats enregistrés.

## 1. Unicornext : le premier tri des pitchs pour un fonds VC

**00:00–00:45 · 45 secondes**

Notre produit s’adresse à l’analyste d’un fonds de venture capital, qui doit sélectionner les startups à examiner plus en détail. Les fondateurs envoient des dossiers par e-mail, Telegram ou via un dépôt. Les textes et les formats varient, et les informations utiles ne se trouvent pas au même endroit. Le problème métier est donc de centraliser ces dossiers et de les comparer avec une grille commune. Unicornext extrait les informations, attribue des notes par critère et présente les preuves et les réserves. L’investisseur peut alors choisir quels dossiers approfondir. La valeur recherchée est un tri plus homogène et une lecture plus rapide. Nous n’avons pas mesuré ce gain de temps chez un fonds réel.

Sources : CONTEXT.md ; README.md ; docs/UNICORNEXT_V1.md

## 2. Comment un investisseur utilise le produit

**00:45–01:30 · 45 secondes**

Prenons un scénario d’utilisation. Un fondateur dépose son pitch en texte ou PDF, ou l’envoie par les canaux connectés. Le système extrait le texte et prépare une analyse avec Qwen V2. L’investisseur ouvre sa file de dossiers pour repérer ceux à approfondir. Sur une fiche, il voit les notes d’équipe, de marché, de produit, de traction et de modèle économique, puis les citations qui appuient l’analyse et les informations manquantes. Il compare ensuite des entreprises et prépare sa shortlist, avant d’engager un échange avec le fondateur. La décision d’investissement lui revient. Dans la démo, les cinquante dossiers fictifs ont des évaluations Codex déjà enregistrées. Les nouveaux dépôts utilisent Qwen via Ollama.

Sources : README.md ; app.py ; src/intake.py ; src/followup.py

## 3. Le notebook explique le moteur du produit

**01:30–01:55 · 25 secondes**

Le notebook est notre laboratoire, l’application est la restitution. Nous avons d’abord construit le corpus et la grille, puis comparé trois versions du prompt. Les sorties enregistrées permettent de mesurer les écarts et la fiabilité. Le produit réutilise le moteur pour les nouveaux dossiers. Nous allons maintenant montrer les cellules qui portent ces choix : chargement, statistiques, calibration, prompts, comparaison des notes et contrôles. Le projet a évolué du benchmark qualité-coût initial vers un produit avec un moteur local, avec l’accord du professeur.

Sources : CONTEXT.md ; 08_quality_vs_cost_benchmark.ipynb ; src/benchmark.py

## 4. Charger et vérifier notre dataset

**01:55–02:35 · 40 secondes**

Cette cellule charge les pitchs puis vérifie deux invariants : cinquante lignes et aucun texte vide. Les compréhensions de listes extraient ensuite les secteurs et comptent les mots de chaque texte. Nous ne commençons donc pas par appeler le modèle : nous contrôlons les données qui lui seront envoyées. Le corpus contient cinquante pitchs fictifs en anglais, répartis sur vingt et un secteurs. Trente-sept sont dérivés de sources documentées, treize sont synthétiques, et cinq contiennent volontairement des tentatives d’injection. Avec un à trois pitchs par secteur, le corpus sert à varier les cas de test, sans mesurer une performance sectorielle fiable.

Sources : Notebook §2, cellule 7 ; data/pitches.jsonl

À montrer : Cellule 7 · chargement et contrôles · extrait exact.

```python
pitches = load_pitches()
assert len(pitches) == 50
assert all(p['pitch_text'].strip() for p in pitches)

sector_counts = Counter(p['sector'] for p in pitches)
word_counts = [len(p['pitch_text'].split()) for p in pitches]
```

## 5. Décrire les données avant de noter les pitchs

**02:35–03:10 · 35 secondes**

Ici, Pandas nous donne la longueur des pitchs et la répartition sectorielle. Matplotlib transforme les longueurs en histogramme, avec huit intervalles. Il faut expliquer ce que représente chaque barre : le nombre de textes dans une plage de longueur. La moyenne est de 477 mots, la médiane de 529 et l’écart-type de 124. La calibration comporte douze pitchs faibles, vingt-six moyens et douze forts. Les données ne sont donc pas équilibrées entre les paliers. Ce sont des propriétés du corpus, pas des résultats du modèle.

Sources : Notebook §2, cellule 11 ; data/pitches.jsonl ; data/calibration.jsonl

À montrer : Cellule 11 · statistiques descriptives · extrait, mise en lignes adaptée.

```python
lengths = dataset_df['words']
sector_distribution = (
    dataset_df['sector'].value_counts().sort_values()
)
ax_length.hist(lengths, bins=8, color=PLOT_COLORS['primary'],
               edgecolor='white')
```

## 6. Construire le classement calibré

**03:10–03:45 · 35 secondes**

La première ligne associe chaque identifiant à sa cible de rédaction. La fonction select applique ensuite la règle de classement et renvoie le top cinq pour cinquante dossiers. La cellule suivante trie la calibration par rang pour afficher la courbe. La frontière est volontairement serrée : P005 a une cible de 79 et P006 de 77. Elle permet d’examiner si le modèle distingue des dossiers proches. Ces notes ont servi à écrire le corpus. Elles constituent un repère de cohérence, pas une vérité expertisée à reproduire automatiquement.

Sources : Notebook §2, cellules 13 et 15 ; src/metrics.py ; data/calibration.jsonl

À montrer : Cellules 13 et 15 · calibration et tri · extraits, mise en lignes adaptée.

```python
target_totals = {row['pitch_id']: row['target_score']
                 for row in calibration}
print('Top 5 de calibration :', select(target_totals))
ranking_df = pd.DataFrame(calibration).sort_values('rank')
```

## 7. V0, V1, V2 : faire évoluer les instructions

**03:45–05:00 · 75 secondes**

Voici la cellule qui permet d’afficher et de comparer les prompts. La boucle parcourt les versions, récupère leur texte, puis affiche une empreinte et leur longueur avant de rendre le prompt en Markdown. L’empreinte identifie exactement la version utilisée dans les résultats. Le texte des prompts est défini dans src/prompts.py. V0 demande cinq notes et du JSON. V1 ajoute le rôle d’analyste VC, une échelle de zéro à cinq, des preuves copiées du texte et des règles sur les informations absentes. Par exemple, quatre signifie une preuve précise, tandis que zéro correspond à un critère non renseigné. V2 reprend V1 et déclare le pitch non fiable : les instructions du fondateur ne doivent pas modifier la grille. Un rappel placé après le texte répète cette frontière. Le progrès recherché vient de ces consignes, pas simplement de l’ajout de mots.

Sources : Notebook §4, cellule 23 ; src/prompts.py, V0, V1, INJECTION_DEFENCE et POST_PITCH_REMINDER

À montrer : Cellule 23 · affichage des versions · cellule complète.

```python
for version in PROMPT_VERSIONS:
    prompt = PROMPTS[version]
    print(f'{version} — empreinte {fingerprint(version)} — {len(prompt.split())} mots')
    display(Markdown(f'### {version}\n```text\n{prompt}\n```'))
```

## 8. Vérifier le contexte réellement envoyé

**05:00–05:50 · 50 secondes**

Cette cellule choisit P005 puis appelle build_prompt. Elle récupère deux messages distincts : système et utilisateur. Les deux assertions vérifient que le nom du marqueur d’injection et celui du score cible ne sont pas présents dans ces messages. Nous ne devons pas donner la réponse attendue au modèle. La fonction reçoit uniquement la version, l’identifiant et le texte. Le système porte la grille et les règles, l’utilisateur contient le pitch délimité par des marqueurs. Le rappel V2 arrive après le texte. Dans les résultats, on compare ensuite le même modèle, le même corpus et la même température. Cela permet d’interpréter les différences entre prompts sans les confondre avec un changement de modèle.

Sources : Notebook §4, cellule 27 ; src/prompts.py::build_prompt ; src/config.py

À montrer : Cellule 27 · entrée du modèle · extrait, mise en lignes adaptée.

```python
sample = next(p for p in pitches if p['pitch_id'] == 'P005')
system_prompt, user_prompt = build_prompt(
    'V2', sample['pitch_id'], sample['pitch_text']
)

assert 'is_injection_test' not in system_prompt + user_prompt
assert 'target_score' not in system_prompt + user_prompt
```

## 9. Aligner les scores et leurs références

**05:50–06:20 · 30 secondes**

Le pivot transforme les résultats en une ligne par pitch et une colonne par prompt. La jointure ajoute ensuite la référence de calibration. Le nom claude_rating vient du notebook, mais correspond aux cibles de rédaction. Une autre jointure ajoute les évaluations directes Codex. Qwen est le modèle exécuté via Ollama. Pour P001, les trois valeurs sont 92, 76 et 75. La référence change donc la lecture des désaccords. Il n’y a pas d’appel à Claude ou Codex dans cette cellule.

Sources : Notebook §7 bis, cellule 40 ; résultats et évaluations JSONL du dépôt

À montrer : Cellule 40 · pivot et jointure · extrait, mise en lignes adaptée.

```python
ratings = (
    runs_df[runs_df['total_computed'].notna()]
    .pivot_table(index='pitch_id',
                 columns='prompt_version',
                 values='total_computed')
    .add_prefix('ollama_rating_')
)
ratings = ratings.join(claude)
```

## 10. Calculer la RMSE pour chaque prompt

**06:20–07:20 · 60 secondes**

La fonction convertit les deux séries en tableaux numériques, soustrait les notes, élève les écarts au carré, prend leur moyenne puis la racine carrée. La RMSE est donc exprimée en points sur cent et donne plus de poids aux gros désaccords. Dans la boucle du notebook, cette fonction s’applique à chaque prompt et à chacune des deux références. Sur les cinquante pitchs, injections incluses, la RMSE face à la calibration passe de 29,91 à 23,14 entre V0 et V2. Face à Codex, elle passe de 25,59 à 17,92. Cela représente des baisses de 22,6 % et 30 %. Les consignes enrichies améliorent l’accord sur ce corpus. Nous n’avons cependant pas de référence experte ni de jeu de test indépendant.

Sources : Notebook §7 bis, cellule 41 ; results/raw_runs.jsonl ; 50 pitchs par version

À montrer : Cellule 41 · définition de la métrique · extrait exact.

```python
def rmse(y, z):
    y, z = np.asarray(y, dtype=float), np.asarray(z, dtype=float)
    return float(np.sqrt(np.mean((y - z) ** 2)))
```

## 11. Lire les écarts et les régressions

**07:20–08:05 · 45 secondes**

La cellule du notebook dessine un nuage de points pour chaque version. En abscisse, la calibration. En ordonnée, Qwen. Le regroupement par palier colore les niveaux du corpus, et la diagonale représente l’accord parfait. La droite orange sur notre visuel est une régression descriptive ajoutée à partir des mêmes résultats : elle n’est pas calculée par l’extrait affiché. Pour V2, sa pente est de 0,43 et son ordonnée à l’origine de 47,2. Cela révèle des notes tassées et une surnotation des pitchs faibles. Le R carré augmente de 0,12 en V0 à 0,43 en V2. Ce diagnostic décrit le corpus observé, sans mesurer une prédiction hors échantillon.

Sources : Notebook §7 bis, cellule 42 ; régression OLS complémentaire depuis results/raw_runs.jsonl

À montrer : Cellule 42 · nuage de points et diagonale · extrait, mise en lignes adaptée.

```python
for tier, group in ratings.groupby('palier'):
    ax.scatter(group['claude_rating'],
               group[column], s=28,
               color=tier_colors[tier], label=tier)
ax.plot([0, 100], [0, 100],
        linestyle='--', color=PLOT_COLORS['muted'])
```

## 12. Contrôler le format et recalculer les totaux

**08:05–08:50 · 45 secondes**

La cellule de test prépare volontairement un total faux, égal à 999. parse_output vérifie la structure, puis computed_total recalcule le score à partir des critères. Le résultat correct du cas de test vaut 79 et l’écart détecté 920. Ce contrôle n’est pas seulement théorique. Sur les résultats V2 enregistrés, les cinquante réponses sont en JSON pur, mais quarante-neuf totaux annoncés diffèrent du calcul pondéré. Nous utilisons donc total_computed pour classer les dossiers. La latence médiane est de 49,7 secondes et le percentile 95 de 65,4 secondes sur le Mac M4 documenté. Un format correct ne garantit ni une arithmétique correcte ni une bonne appréciation métier.

Sources : Notebook §5, cellule 29, et §8 ; src/schemas.py ; docs/ENGINE_CHECKS.md

À montrer : Cellule 29 · validation et recalcul · extrait exact.

```python
parsed = parse_output(json.dumps(example_output))
assert parsed.ok and parsed.valid_json_strict
print('Total annoncé :', parsed.parsed.total_score)
print('Total recalculé :', parsed.parsed.computed_total())
print('Écart détecté :', parsed.parsed.total_drift())
```

## 13. Le code complète la défense du prompt

**08:50–10:00 · 70 secondes**

La première cellule applique notre filtre au texte de chaque pitch. Le filtre détecte des formulations d’injection sans appeler le modèle. Dans le classement historique, la compréhension de dictionnaire conserve uniquement les scores non signalés, puis select classe les dossiers. Pourquoi ajouter ce contrôle au prompt V2 ? Parce que P025 reste à 100 sur 100 malgré les instructions de défense. P049, lui, passe de 100 en V0 à 62 en V2. Le progrès est réel mais partiel. Sur les cas connus, le filtre détecte les cinq pièges avec zéro faux positif sur les quarante-cinq textes sains. Il faut distinguer cette expérience de l’application V1 actuelle, où les alertes sont informatives et les dossiers scorés restent classés. Notre conclusion est que le prompt doit être précis, testé et accompagné de contrôles. Pour généraliser, il faudrait un corpus indépendant et une annotation experte. Nous allons maintenant montrer le produit.

Sources : Notebook §9, cellule 51, et §8, cellule 49 ; src/guard.py ; README.md, décision V1

À montrer : Cellules 51 et 49 · détection puis classement historique · extraits.

```python
for pitch in pitches:
    verdict = scan(pitch['pitch_text'])

scores_by_id = {
    r['pitch_id']: r['total_computed']
    for r in valid_runs if not r.get('guard_flagged')
}
ranked = select(scores_by_id)
```

## 14. Démonstration de notre site

**10:00–12:00 · 120 secondes**

Ouvrir http://127.0.0.1:8502. 0:00–0:25 : vue d’ensemble et priorités. 0:25–1:05 : une fiche, ses cinq critères, une citation et une réserve. Préciser que les notes du corpus viennent de Codex. 1:05–1:35 : comparaison ou shortlist. 1:35–2:00 : zone de dépôt, en expliquant qu’un nouveau dossier utilise Qwen V2 via Ollama. Éviter de lancer un scoring long et ne pas envoyer de message réel. Le parcours est dans les notes, pas sur la diapositive.

Sources : app.py ; README.md ; src/intake.py
