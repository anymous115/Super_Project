# Gabarit de rédaction — P006

Modèle de référence pour les 50 pitchs. **À lire avant d'écrire le premier.**

Quatre personnes rédigeant sans étalon commun produiront quatre structures différentes, et cette hétérogénéité se retrouvera dans les scores sans qu'on puisse la distinguer du signal. Ce document existe pour éviter ça.

Le pitch complet est dans `data/pitches.jsonl`, champ `pitch_text` de P006.

## Pourquoi P006 comme gabarit

C'est le **premier recalé** : 78, un point sous P005 qui ferme la sélection. C'est le test central du jeu de données.

Commencer par lui plutôt que par un pitch faible donne le bon étalon. Un gabarit calé sur un mauvais pitch apprend à écrire mal ; celui-ci oblige à produire un dossier réellement solide, et c'est le niveau d'exigence qu'il faut tenir sur les douze pitchs du palier fort.

- **Société source** : Flock Freight (mutualisation de fret LTL)
- **Société fictive** : Remorq
- **Longueur** : 656 mots, plafond 800

## Comment le texte atteint 78

| Critère | Note | Poids | Points | Ce qui, dans le texte, produit cette note |
|---|:-:|---:|---:|---|
| Équipe | **5** | 20 | 20 | Neuf ans à diriger 1 200 départs quotidiens chez un top-5 européen ; le second fondateur a construit l'optimisation d'itinéraires d'une plateforme dans onze pays ; dix-huit mois de travail commun avant de créer la société. Spécifique et directement pertinent. |
| Marché | **4** | 25 | 20 | 38 Md€ chiffrés, dont 14 Md€ adressables, avec la raison du découpage. Crédible et borné — mais marché mature et disputé, pas une catégorie neuve. |
| Produit | **3** | 15 | 9 | La solution fonctionne et est décrite précisément, **mais le texte reconnaît qu'elle n'est pas inimitable**. L'avantage vient de la densité du carnet, pas de la technologie. |
| Traction | **4** | 25 | 20 | Chiffres réels et vérifiables : 4,1 M€, +11 %/mois, 71 % de rétention, 84 % de remplissage contre 63 % pour le secteur. Solide — mais le volume absolu reste modeste. |
| Business model | **3** | 15 | 9 | 14 % brut, 6,2 points nets, en progression. **Le texte dit lui-même que la marge est mince** et qu'elle n'est pas prouvée au-delà de trois corridors. |
| | | | **78** | |

## Ce que P006 doit à P005 — et l'inverse

P005 vise 79, P006 vise 78. Un point d'écart, mais des **formes différentes** :

| | Équipe | Marché | Produit | Traction | BM | Total |
|---|:-:|:-:|:-:|:-:|:-:|---:|
| P005 (cybersecurity) | 3 | 4 | **5** | 4 | 4 | **79** |
| P006 (logistics) | **5** | 4 | 3 | 4 | 3 | **78** |

P005 a un produit remarquable porté par une équipe ordinaire. P006 a une équipe exceptionnelle sur un produit banal.

C'est volontaire, et c'est ce qui rend la coupure difficile : un modèle ne peut pas les départager en comparant des magnitudes, il doit **pondérer équipe contre produit** comme le fait la grille. Un modèle qui surévalue systématiquement les équipes brillantes fera remonter P006 et écartera P005.

## Structure à suivre

Dans cet ordre, sections nommées en majuscules :

```
LE PROBLÈME       ce qui ne va pas aujourd'hui, chiffré
NOTRE SOLUTION    ce que fait le produit, avec un exemple concret
LE MARCHÉ         taille, périmètre adressable, justification du découpage
LA CONCURRENCE    qui occupe le terrain, et ce qui nous distingue
L'ÉQUIPE          parcours des fondateurs, taille actuelle
TRACTION          liste à puces de chiffres
MODÈLE ÉCONOMIQUE comment l'argent rentre, et ce qu'il en reste
GO-TO-MARKET      canal de vente, cycle, coût d'acquisition
FINANCEMENT       montant levé et usage
```

Un pitch peut **omettre une section** : c'est même prévu pour douze slots marqués ␀ dans la grille. L'omission doit alors être franche — la section absente, pas remplacée par du vide habillé.

## Règles de rédaction

**Écrire au niveau visé, pas au-dessus.** Le score cible se tient par le contenu, pas par le ton. Un pitch à 43 n'est pas un pitch à 78 écrit avec moins d'enthousiasme : c'est un dossier qui a réellement moins à montrer.

**Mettre la faiblesse dans le texte, pas dans le sous-entendu.** Si le business model est fragile, les chiffres doivent le dire. Un annotateur doit pouvoir pointer la phrase qui justifie sa note. Sans ça, deux annotateurs diverge et la référence devient instable.

**Ne pas caricaturer.** Un pitch faible reste un pitch qu'un fondateur a écrit en y croyant. C'est tout l'intérêt de partir de post-mortems : la société existait vraiment et y croyait vraiment.

**Chiffrer.** Des nombres précis et plausibles, jamais ronds au point de sonner faux. « 71 % de rétention » vaut mieux que « une excellente rétention ».

**Changer le nom, le pays si besoin, les chiffres et les fondateurs.** On reprend la structure d'un dossier réel, jamais ses phrases. Aucun nom de fondateur réel, aucune coordonnée.

**Renseigner `source_url` et `accessed_at`** avec ce qu'on a réellement ouvert, à la date où on l'a ouvert.

**Plafond de 800 mots, pas une cible.** Les pitchs faibles sont courts par nature. P046 doit être très court, P050 creux.

## Le piège principal

Le devenir réel de la société source **ne fixe pas la note**. Flock Freight vaut 1 Md$ ; ça n'impose pas que P006 soit excellent. On sait comment l'histoire finit en rédigeant, et la tentation est de noter l'entreprise plutôt que le pitch.

C'est l'erreur la plus facile à commettre sans s'en apercevoir.

## Décision en attente

**Dans quelle langue écrit-on les 50 pitchs ?**

Le produit rend ses analyses en français et en anglais, mais ça ne dit rien de la langue du corpus. Un corpus mélangé ajoute une variable non contrôlée : si les pitchs anglais obtiennent des scores différents, on ne saura pas distinguer l'effet de langue de l'effet de qualité.

Deux options tenables :

- **corpus monolingue** — tous les pitchs en français, restitution testée dans les deux langues ;
- **corpus dédoublé** — les mêmes pitchs traduits, ce qui permet de *mesurer* l'effet de langue, mais double la rédaction.

P006 est écrit en français en attendant l'arbitrage.

## Avant de soumettre un pitch

- [ ] ≤ 800 mots
- [ ] sections dans l'ordre ci-dessus, omissions assumées
- [ ] chaque note visée est justifiable par une phrase précise du texte
- [ ] les informations marquées ␀ dans la grille sont réellement absentes
- [ ] nom, pays, chiffres et fondateurs modifiés par rapport à la source
- [ ] aucun nom réel de fondateur, aucune coordonnée
- [ ] `company_name`, `source_url`, `accessed_at`, `written_by` renseignés
