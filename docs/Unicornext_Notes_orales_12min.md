# Unicornext — présentation de 12 minutes

10 minutes de diapositives, puis 2 minutes de démonstration. Les diapositives 14 à 16 sont des annexes pour les questions, hors temps prévu. Le minutage est une cible à vérifier par répétition.

## Déroulé

| Diapositive | Sujet | Passage | Durée |
|---|---|---|---|
| 1 | Le premier tri des pitchs d’un fonds VC | 00:00–00:45 | 45 s |
| 2 | La structure du projet | 00:45–01:20 | 35 s |
| 3 | Un corpus construit pour tester le tri | 01:20–02:05 | 45 s |
| 4 | Le classement calibré fixe les cas à tester | 02:05–02:50 | 45 s |
| 5 | Qui attribue réellement les notes ? | 02:50–03:30 | 40 s |
| 6 | V0, V1, V2 : ce que nous changeons | 03:30–04:45 | 75 s |
| 7 | Le contexte et la grille encadrent la réponse | 04:45–05:35 | 50 s |
| 8 | La RMSE diminue avec les prompts enrichis | 05:35–06:35 | 60 s |
| 9 | Les régressions montrent des notes tassées | 06:35–07:30 | 55 s |
| 10 | Un JSON valide peut contenir un total faux | 07:30–08:25 | 55 s |
| 11 | Le prompt V2 réduit certains pièges | 08:25–09:20 | 55 s |
| 12 | Ce que le projet permet de conclure | 09:20–10:00 | 40 s |
| 13 | Démonstration d’Unicornext | 10:00–12:00 | 120 s |

## Préparer la démonstration

- Lancer `.venv/bin/streamlit run app.py --server.port 8502` depuis la racine du dépôt et ouvrir http://127.0.0.1:8502 avant le passage.
- Préouvrir la vue d’ensemble et choisir une fiche du corpus dont les citations et les réserves sont faciles à commenter.
- Montrer les résultats enregistrés. La latence médiane de Qwen V2 est de 49,7 s sur la machine documentée : ne pas attendre un nouveau scoring pendant les deux minutes.
- Les notes du corpus affichées par le produit viennent de Codex. Les nouveaux dépôts utilisent Qwen V2 via Ollama.
- Aucun envoi réel d’e-mail ni de message de suivi n’est nécessaire pour cette démonstration.
- Si le site ne répond pas, utiliser les diapositives 5, 10 et 11 pour expliquer les notes, la fiabilité et les limites.

## Notes orales

### 1. Le premier tri des pitchs d’un fonds VC

Durée cible : 45 s.

Un fonds reçoit des dossiers par plusieurs canaux. Avant de décider dans quelle entreprise investir, il faut déjà savoir quels dossiers lire en priorité. Notre use case est ce premier tri. Unicornext centralise les pitchs, leur applique une même grille et rend les éléments de l’analyse consultables. La valeur recherchée est une lecture plus homogène et une file de dossiers plus facile à explorer. Nous n’avons pas mesuré un gain de temps chez un fonds réel. Nous avons construit un prototype, puis étudié comment les instructions données au modèle modifient ses notes. C’est ce travail de prompt engineering que nous allons expliquer avant une démonstration du site.

Source : CONTEXT.md ; README.md ; phases/01_cadrage/

### 2. La structure du projet

Durée cible : 35 s.

Le projet partait d’un benchmark qualité-coût. Avec l’accord du professeur, le périmètre a évolué vers un produit utilisant un moteur local. Le notebook reste notre laboratoire : il décrit les données, les prompts et les résultats. L’application est la restitution destinée à l’investisseur. Les dépôts entrent par le site, Telegram ou e-mail. Le pipeline extrait le texte, détecte des tentatives d’injection, appelle Qwen et recalcule le score. Les résultats alimentent ensuite la file et les fiches. Le modèle ne remplace donc qu’une partie du système.

Source : CONTEXT.md, historique du 23 septembre ; README.md ; src/intake.py ; Input_Telegram_Mail/input_listener.py

### 3. Un corpus construit pour tester le tri

Durée cible : 45 s.

Nous travaillons sur cinquante pitchs fictifs en anglais. Trente-sept sont dérivés de sources documentées, treize sont synthétiques. Cela ne signifie pas que nous avons cinquante véritables dossiers investisseurs. Le corpus couvre vingt et un secteurs, avec seulement un à trois pitchs par secteur : on ne peut donc pas conclure sur une performance sectorielle. La longueur moyenne est de 477 mots, avec un écart-type de 124 mots. Les paliers comportent douze pitchs faibles, vingt-six moyens et douze forts. Cinq pitchs incluent volontairement une injection. Ces statistiques décrivent les cas de test, sans représenter statistiquement le flux réel d’un fonds.

Source : Notebook §2, cellules 7, 9 et 11 (positions, base 1) ; data/pitches.jsonl ; data/calibration.jsonl

### 4. Le classement calibré fixe les cas à tester

Durée cible : 45 s.

Avant la notation du modèle, nous avons fixé des cibles de rédaction pour obtenir une échelle de qualité. La courbe présente ces cinquante cibles ordonnées. Le cinquième dossier est à 79, le sixième à 77 : c’est une frontière intéressante pour tester la précision du classement. La règle de sélection garde au moins cinq dossiers, puis dix pour cent du volume, avec un plafond de cinquante. Mais le top cinq calibré est une intention de conception du corpus. Il ne constitue pas un jugement expert indépendant. L’intérêt est de vérifier si le moteur retrouve les grands écarts de qualité, puis d’examiner les désaccords.

Source : Notebook §2, cellules 13 et 15 ; data/calibration.jsonl ; src/metrics.py

### 5. Qui attribue réellement les notes ?

Durée cible : 40 s.

Il faut distinguer les trois colonnes. Le notebook utilise le nom Claude pour les cibles de calibration. La documentation indique que Claude a participé à la rédaction du corpus, mais cette colonne n’est pas un nouvel appel indépendant à Claude pendant le benchmark. Codex a ensuite évalué directement les cinquante textes, avec des justifications par critère. Qwen 2.5 14B est le modèle local évalué avec les trois prompts. Ollama est le logiciel qui l’exécute. Pour P001, la cible vaut 92, Codex donne 76 et Qwen V2 donne 75. La référence choisie change donc l’interprétation de l’écart.

Source : Notebook §7 bis ; data/calibration.jsonl ; data/assessments/unicornext_v1.jsonl ; results/raw_runs.jsonl ; docs/VALIDATION_BATCH1_REPORT.md

### 6. V0, V1, V2 : ce que nous changeons

Durée cible : 75 s.

V0 est notre point de départ : noter cinq critères de zéro à cinq et répondre en JSON. C’est une demande courte, mais elle ne définit pas vraiment ce qu’est une bonne note. V1 ajoute un rôle d’analyste VC et surtout une échelle explicite : zéro si le pitch ne dit rien, quatre pour une preuve précise et cinq pour une preuve exceptionnelle. Il exige des citations, interdit d’inventer des chiffres ou des clients et demande de signaler les informations absentes. V2 conserve V1 et ajoute une frontière de confiance : le texte du fondateur est une donnée non fiable, pas une instruction. Un rappel placé après le pitch répète cette règle. Les versions ne changent donc pas seulement en longueur. Elles modifient la précision de la tâche, le niveau de preuve attendu et la résistance aux instructions malveillantes. Nous gardons le même modèle et le même corpus pour comparer ces choix.

Source : Notebook §4, cellules 23, 25 et 27 ; src/prompts.py, V0, V1, INJECTION_DEFENCE, POST_PITCH_REMINDER

### 7. Le contexte et la grille encadrent la réponse

Durée cible : 50 s.

Le message système porte le rôle, les critères et les règles. Le message utilisateur contient seulement l’identifiant et le texte entre des marqueurs PITCH. Les cibles de calibration et l’indicateur de piège restent hors de l’entrée du modèle. En V2, le rappel arrive après le texte. Les cinq critères ont des poids fixes : équipe 20 %, marché 25 %, produit 15 %, traction 25 % et modèle économique 15 %. Le total vaut la somme des notes divisées par cinq, multipliées par ces poids. Le code recalcule ce total. Ollama contraint aussi la sortie par un schéma JSON. La validité du format dépend donc du pipeline autant que du prompt.

Source : Notebook §4–5, cellules 27 et 29 ; src/prompts.py::build_prompt ; src/config.py::WEIGHTS ; src/score_pitch.py ; src/schemas.py

### 8. La RMSE diminue avec les prompts enrichis

Durée cible : 60 s.

Nous avons cent cinquante résultats enregistrés : cinquante pitchs pour chaque version, avec Qwen 2.5 14B et une température de zéro. La RMSE est la racine de la moyenne des écarts au carré. Elle s’exprime ici en points sur cent et pénalise fortement les gros désaccords. Face à la calibration, elle passe de 29,91 à 26,47 puis 23,14. Face à Codex, elle passe de 25,59 à 21,44 puis 17,92. Cela représente une baisse de 22,6 % et de 30,0 % entre V0 et V2. Le résultat soutient l’intérêt des instructions enrichies sur ce corpus. Il ne prouve pas une précision universelle : nous n’avons ni jeu de test indépendant, ni référence experte. Les cinq injections restent incluses dans cette comparaison.

Source : Notebook §7 bis, cellules 38 à 43 ; results/raw_runs.jsonl ; calcul sur 50 pitchs par prompt, injections incluses

### 9. Les régressions montrent des notes tassées

Durée cible : 55 s.

Nous avons ajouté une régression linéaire descriptive aux données du notebook. En abscisse, la cible de calibration. En ordonnée, la note de Qwen. La diagonale représente l’accord parfait. Avec V0, la droite ajustée vaut environ 0,23 fois la cible plus 62,6. Avec V2, la pente monte à 0,43 et le R carré à 0,43. Les notes varient donc davantage avec la qualité prévue, mais la pente reste loin de un et l’ordonnée à l’origine reste élevée. Les pitchs faibles sont encore surnotés. La corrélation de rang de Spearman passe de 0,35 à 0,73 sur les cinquante pitchs. Attention : ce R carré mesure l’ajustement de la droite sur ce corpus, pas une précision de prédiction sur de nouveaux dossiers.

Source : Analyse complémentaire OLS recalculée depuis results/raw_runs.jsonl et data/calibration.jsonl ; même base que notebook §7 bis ; 50 pitchs, injections incluses

### 10. Un JSON valide peut contenir un total faux

Durée cible : 55 s.

La fiabilité a plusieurs dimensions. En V2, les cinquante réponses sont du JSON pur et aucune n’est tronquée. Mais le total annoncé par le modèle diffère du total pondéré quarante-neuf fois sur cinquante. Sur P001, le modèle annonce 3,84 alors que le calcul pondéré donne 75 sur cent. La sortie structurée ne garantit donc pas la justesse arithmétique. Nous confions les notes par critère au modèle, puis le calcul au code. La latence médiane est de 49,7 secondes et le percentile 95 de 65,4 secondes sur la machine documentée. Pour la démo, nous montrerons les dossiers déjà évalués : le lancement d’un nouveau scoring ne doit pas bloquer le déroulé. Si Ollama est indisponible, l’interface doit montrer l’échec sans inventer une note.

Source : Notebook §5 et §8 ; results/raw_runs.jsonl ; docs/ENGINE_CHECKS.md ; README.md, machine M4 16 Go

### 11. Le prompt V2 réduit certains pièges

Durée cible : 55 s.

P049 illustre un progrès : sa note passe de 100 en V0 à 62 en V2. Mais P025 reste à 100 malgré la défense. Un prompt plus explicite ne suffit donc pas à assurer la sécurité. Notre filtre déterministe détecte cinq pièges sur cinq sans faux positif sur les quarante-cinq autres textes du corpus. Dans le benchmark historique, on retire ces cinq pièges du classement : Spearman atteint 0,753 et deux dossiers du top cinq calibré sont retrouvés. Il faut distinguer cela de l’application actuelle. Depuis la décision V1, les alertes sont informatives, les dossiers scorés restent classés et aucune validation humaine obligatoire ne bloque l’accès. Nous montrons donc un prototype avec des limites de sécurité explicites, pas une décision d’investissement automatisée.

Source : Notebook §9 ; src/guard.py ; results/raw_runs.jsonl ; docs/ENGINE_CHECKS.md ; README.md, Défense du benchmark historique ; docs/UNICORNEXT_V1.md

### 12. Ce que le projet permet de conclure

Durée cible : 40 s.

Le principal apprentissage est que le prompt fait partie d’un système mesurable. Préciser la grille et le niveau de preuve réduit les écarts sur notre corpus. Séparer les instructions des données améliore certaines réponses, mais laisse des injections réussir. Le code doit garantir le format et les calculs. Pour aller plus loin, il faudrait des pitchs réels tenus à l’écart de la conception, une annotation experte indépendante et une nouvelle évaluation des règles de classement et des alertes. Nous passons maintenant au site pour montrer comment ces résultats deviennent une expérience investisseur, en gardant visible la provenance des notes.

Source : Synthèse du notebook §12 ; README.md ; docs/UNICORNEXT_V1.md

### 13. Démonstration d’Unicornext

Durée cible : 120 s.

0:00 à 0:25 : ouvrir la vue d’ensemble et montrer les dossiers prioritaires. Dire que les cinquante notes du corpus proviennent des évaluations directes Codex. 0:25 à 1:05 : ouvrir une fiche, lire les cinq critères, une citation et une réserve. Montrer la provenance, sans assimiler ces notes au benchmark Qwen. 1:05 à 1:35 : montrer la comparaison de dossiers ou la shortlist existante. 1:35 à 2:00 : ouvrir la zone de dépôt et expliquer qu’un nouveau texte ou PDF utilisera Qwen V2 via Ollama. Ne pas lancer de traitement long pendant le temps de parole. Ne pas envoyer d’e-mail ni de message de suivi. Conclure : notre travail relie une tâche métier, des prompts comparables et un produit qui expose les justifications. Secours : revenir aux diapositives 5, 10 et 11 si le site ne répond pas.

Source : app.py ; README.md ; src/intake.py ; démonstration locale http://127.0.0.1:8502

### 14. Annexe : choix du moteur local

Annexe, hors déroulé principal.

Ces mesures correspondent aux essais historiques du 23 septembre documentés dans le README. Elles ne viennent pas de la matrice actuelle des 150 appels, qui contient uniquement Qwen 14B. DeepSeek a été arrêté après 18 essais. Les latences historiques sont distinctes de celles du passage final V2. Les scores des modèles frontière ne sont pas disponibles dans un benchmark contrôlé équivalent.

Source : README.md, Historique du choix du moteur local ; CONTEXT.md

### 15. Annexe : les deux références et le classement

Annexe, hors déroulé principal.

Les régressions sont ajustées sur les mêmes 50 points qui servent à leur diagnostic. Y désigne Qwen, X la référence. Aucun calibrage correctif n’a été appliqué aux notes en production. Le classement hors injections concerne le benchmark historique. Les notes Codex servent de seconde référence IA et ne sont pas des annotations expertes indépendantes. Le top 5 Qwen V2 hors injections est P022, P005, P016, P028, P002. Le top 5 calibré est P001, P002, P003, P004, P005. L’intersection est donc de deux sur cinq.

Source : results/raw_runs.jsonl ; data/calibration.jsonl ; data/assessments/unicornext_v1.jsonl ; docs/ENGINE_CHECKS.md

### 16. Annexe : retrouver les cellules et les preuves

Annexe, hors déroulé principal.

Les positions sont celles du notebook versionné au commit 754b982, en comptant toutes les cellules à partir de un. Les numéros In[] changent selon l’ordre d’exécution et ne constituent pas un repère stable. Les régressions de la diapositive 9 sont une analyse complémentaire des résultats enregistrés. Aucun nouveau modèle n’a été appelé pour préparer cette présentation.

Source : 08_quality_vs_cost_benchmark.ipynb ; commit 754b982 ; scripts et fichiers mentionnés sur la diapositive

## Points à formuler précisément

- **Calibration** : cibles de rédaction. Le nom `claude_rating` du notebook ne prouve pas une notation indépendante de Claude pendant le benchmark.
- **Codex** : évaluations directes enregistrées. Le dépôt ne permet pas d’attribuer ici un modèle sous-jacent précis à ces évaluations.
- **Ollama / Qwen** : Ollama est le logiciel d’exécution, Qwen 2.5 14B est le modèle.
- **RMSE** : écart aux références, en points sur 100. Une RMSE plus faible signifie un meilleur accord avec la référence choisie, sans certifier la justesse métier.
- **Régression** : ajustement descriptif de Qwen en fonction de la référence sur les mêmes 50 pitchs. Les droites sont une analyse complémentaire aux graphiques du notebook, sans évaluation hors échantillon.
- **Spearman** : accord des rangs. 0,733 sur les 50 pitchs en V2 ; 0,753 sur les 45 après exclusion des injections dans le benchmark historique.
- **Fiabilité** : JSON valide et total correct sont deux contrôles différents. Le score utilisé est recalculé à partir des cinq critères.
- **Sécurité actuelle** : dans le produit V1, les alertes sont informatives et ne déclenchent plus une exclusion automatique des dossiers scorés.

Version des sources : commit `754b982`. Calculs sur les fichiers JSONL du dépôt. Aucun nouvel appel au modèle pour préparer ce support.
