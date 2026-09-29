# Unicornext — Design System

Source de vérité visuelle de l'app Streamlit (`app.py`). Les jetons vivent dans `assets/unicornext.css` (`:root`), les primitives dans `src/ui.py`, et `scripts/ui_showcase.py` les montre dans tous leurs états. Aucune couleur, taille ou durée n'est écrite en dur hors de ce fichier : on ajoute d'abord le jeton ici.

Références utilisées : `motherduck.md` (canevas crème chaud, une couleur signature employée avec retenue, hiérarchie par le contenu) et les principes du skill `dashboard` (grille 8 pt, états explicites, accessibilité WCAG 2.2 AA). La palette bleue et IBM Plex de ce dernier n'ont pas été reprises : elles contredisent l'identité Unicornext, dont la couleur principale est le **violet licorne**.

## 1. Atmosphère et identité

Un poste de pilotage calme, posé sur du papier. Une barre latérale à l'encre où vit le logo clair, un canevas crème, des surfaces blanches séparées par des filets fins plutôt que par des cadres épais. Le contenu est la donnée : les scores sont les plus gros éléments de la page. Derrière tout cela, un fond qui vit : un champ de points d'où partent des anneaux, comme un sonar (section 7).

**Signature : l'anneau de score, en violet licorne.** Le violet n'est jamais décoratif, c'est un signal : il marque le dossier en tête, l'onglet actif, l'action principale, le score qui compte. Une seule touche de fantaisie : un dégradé violet vers magenta, réservé à l'accroche de la vue d'ensemble et au dossier en tête. Chaque score s'affiche dans un anneau qui se remplit à l'arrivée, et les chiffres clés comptent jusqu'à leur valeur (CSS pur, sans JavaScript).

Le ton est celui d'un outil d'investisseur : dense quand il le faut, aéré sinon, jamais ludique.

## 2. Couleur

Thème clair pour le contenu, sombre pour la barre latérale. Pas de bascule de thème.

| Rôle | Jeton | Valeur | Usage |
|---|---|---|---|
| Encre | `--ink-900` | `#14171A` | Barre latérale, texte fort, boutons primaires |
| Encre relevée | `--ink-800` | `#1D2226` | Surfaces sur fond encre |
| Encre survol | `--ink-700` | `#2A3136` | Survol sur fond encre |
| Filet sur encre | `--ink-line` | `#FFFFFF14` | Séparateurs dans la barre latérale |
| Texte sur encre | `--on-ink` | `#F3F2EC` | Texte de la barre latérale |
| Texte 2 sur encre | `--on-ink-2` | `#B7BEB8` | Légendes de la barre latérale (contraste 9:1) |
| Canevas | `--canvas` | `#F3F2EC` | Fond de l'app |
| Surface | `--surface` | `#FFFFFF` | Cartes, champs |
| Surface 2 | `--surface-2` | `#F8F7F2` | Zones en creux dans une carte |
| Creux | `--sunken` | `#E9E8DF` | Fond des contrôles segmentés |
| Filet | `--line` | `#14171A17` | Bordure par défaut (9 %) |
| Filet fort | `--line-strong` | `#14171A29` | Bordure au survol, champs |
| Texte | `--text` | `#14171A` | Titres et corps |
| Texte 2 | `--text-2` | `#4B5550` | Texte secondaire (contraste 7:1 sur canevas) |
| Texte 3 | `--text-3` | `#5F6963` | Légendes, méta (contraste 5,1:1 sur canevas) |
| Violet licorne | `--violet-500` | `#7C4DFF` | Couleur principale : bouton primaire, onglet actif, carte KPI signal (texte blanc, 4,8:1) |
| Violet données | `--violet-600` | `#6538E0` | Données, liens, anneaux et focus sur fond clair (6,6:1) ; survol du bouton primaire |
| Violet profond | `--violet-700` | `#4F2AB8` | Appui du bouton primaire, texte du tag « priorité élevée » (7:1 sur violet pâle) |
| Violet clair | `--violet-400` | `#A77BFF` | Signal sur fond encre : anneau, surtitre, focus (5,9:1 sur l'encre) |
| Violet doux | `--violet-300` | `#C9B0FF` | Halo et texte accentué sur fond encre |
| Violet pâle | `--violet-100` | `#EFE8FF` | Fond du tag « priorité élevée », survol de nav claire |
| Magenta | `--magenta-600` | `#B6339A` | Fin du dégradé licorne, texte seulement (4,8:1 sur canevas) |
| Ambre | `--amber-500` | `#E0A030` | Anneau « à approfondir » |
| Ambre pâle | `--amber-100` | `#FFF1CC` | Fond d'alerte et de tag |
| Ambre texte | `--amber-700` | `#6B4400` | Texte d'alerte (contraste 8:1 sur ambre pâle) |
| Danger | `--danger-600` | `#B42318` | Erreur |
| Danger pâle | `--danger-100` | `#FDECEA` | Fond d'erreur |
| Succès | `--success-600` | `#1F7A45` | Texte de confirmation (5,6:1 sur succès pâle) |
| Succès pâle | `--success-100` | `#E4F4EA` | Fond de confirmation |
| Pierre | `--stone-400` | `#B9B8AD` | Anneau « non prioritaire », piste des anneaux |

### Rampe de score (histogramme, du plus faible au plus fort)

`--ramp-1 #CDCAD6` → `--ramp-2 #BFB1EA` → `--ramp-3 #A48CF0` → `--ramp-4 #7C55EE` → `--ramp-5 #5230C2`

### Niveaux de score

Les seuils sont ceux du produit (`docs/UNICORNEXT_V1.md`) : **haute priorité ≥ 75**, **à approfondir 50–74**, **non prioritaire < 50**.

| Niveau | Anneau | Tag |
|---|---|---|
| `high` | `--violet-600` (`--violet-400` sur fond encre) | `--violet-100` / `--violet-700` |
| `mid` | `--amber-500` | `--amber-100` / `--amber-700` |
| `low` | `--stone-400` | `--sunken` / `--text-2` |
| `none` | pas d'anneau | `--sunken` / `--text-3` |

### Règles

- Le violet `--violet-500` porte du texte **blanc**, jamais du texte sombre. Sur fond clair, le violet est utilisé en `--violet-600`, jamais `--violet-500` ni `--violet-400` (contraste insuffisant en petit).
- Le dégradé licorne (`--unicorn`, `#6538E0 → #B6339A`) est réservé au texte de l'accroche et au filet du dossier en tête. Aucun rose pastel sous du texte.
- Un dossier signalé par le filtre est en **ambre**, jamais en rouge : l'alerte est informative, pas une exclusion.
- Aucune couleur hors de ce tableau. Le rouge est réservé aux erreurs système.
- Les alertes Streamlit suivent le sens, pas la teinte par défaut : info = violet pâle, avertissement = ambre, succès = vert, erreur = rouge.

## 3. Typographie

Une seule famille : **Geist** (celle des projets shadcn récents, le même rendu que la démo du fond). Les titres se distinguent par la graisse (600) et un approche serrée, pas par une autre police. Si Geist ne se charge pas (hors ligne), `system-ui` prend le relais sans casser la mise en page.

| Niveau | Police | Taille | Graisse | Interligne | Approche | Usage |
|---|---|---|---|---|---|---|
| Display | Geist | `clamp(32px, 4vw, 44px)` | 600 | 1,08 | −0,035em | Accroche de la vue d'ensemble |
| H1 | Geist | `clamp(26px, 3vw, 32px)` | 600 | 1,15 | −0,03em | Titre de page |
| H2 | Geist | 22px | 600 | 1,25 | −0,03em | Titre de section |
| H3 | Geist | 17px | 600 | 1,3 | −0,01em | Titre de carte |
| Corps | Geist | 15px | 400 | 1,6 | 0 | Texte courant |
| Petit | Geist | 13px | 400 | 1,5 | 0 | Description de carte, aide |
| Légende | Geist | 12px | 500 | 1,4 | 0,01em | Méta, notes |
| Surtitre | Geist | 11px | 600 | 1,3 | 0,08em, majuscules | Étiquettes de section |
| Chiffre XL | Geist | 56px | 500 | 1 | −0,045em | Valeur d'une carte KPI |
| Chiffre L | Geist | 40px | 400 | 1 | −0,03em | Score d'un dossier en tête |
| Chiffre M | Geist | 26px | 600 | 1 | −0,02em | Score au centre d'un anneau |

Règles : le corps ne descend jamais sous 14px (les légendes 12px sont des métadonnées, jamais du contenu). Les chiffres alignés en colonne utilisent `font-variant-numeric: tabular-nums`. Un titre qui passe sur 4 lignes est trop grand.

## 4. Espacement et mise en page

Base **4px**. Aucun espacement hors de cette échelle.

| Jeton | Valeur | Usage |
|---|---|---|
| `--space-1` | 4px | Icône et libellé |
| `--space-2` | 8px | Éléments d'un groupe |
| `--space-3` | 12px | Padding d'un champ, écart de tags |
| `--space-4` | 16px | Padding compact, écart de grille mobile |
| `--space-5` | 20px | Écart de grille |
| `--space-6` | 24px | Padding de carte |
| `--space-8` | 32px | Entre groupes de cartes |
| `--space-10` | 40px | Entre sections |
| `--space-12` | 48px | Marge latérale du contenu (bureau) |
| `--space-16` | 64px | Bas de page |

**Rayons.** `--r-sm` 8px (champs, boutons), `--r-md` 12px (tags carrés, barres), `--r-lg` 16px (cartes), `--r-xl` 20px (grandes cartes), `--r-pill` 999px (tags, contrôles segmentés).

**Grille.** Contenu limité à 1280px. Barre latérale fixe de 264px, collée aux bords, pleine hauteur. Cartes de dossiers : 3 colonnes au-dessus de 1100px, 2 entre 640 et 1100px, 1 en dessous. Cartes KPI : 4 colonnes, 2 sous 1100px.

**Points de rupture.** 640px (mobile), 1100px (tablette).

Cibles tactiles : 44px minimum pour tout élément interactif.

## 5. Composants

Les primitives sont dans `src/ui.py` et se voient toutes, dans tous leurs états, avec `streamlit run scripts/ui_showcase.py`. Chacune renvoie du HTML dont **tout texte dynamique est échappé** : les noms d'entreprise et les extraits de pitchs viennent de fondateurs inconnus (Telegram, e-mail).

### Tag (`ui.tag`)
- **Structure** : `<span class="tag tag--{tone}">` avec un point optionnel.
- **Variantes** : `high`, `mid`, `low`, `warning`, `neutral`.
- **États** : statique. Pas de survol (n'est pas interactif).
- **Accessibilité** : la couleur n'est jamais seule, le libellé porte le sens. Contraste ≥ 4,5:1.

### Anneau de score (`ui.score_ring`)
- **Structure** : `<div class="ring ring--{tier}" role="img" aria-label="Score 82 sur 100">` avec le chiffre au centre.
- **Variantes** : tailles `sm` (64px), `md` (88px), `lg` (120px) ; fond `light` ou `dark`.
- **États** : `none` (score absent) = anneau en pointillés et « — ».
- **Mouvement** : se remplit de 0 à la valeur en 900ms (`--ease-emph`), le chiffre compte en même temps.
- **Accessibilité** : le sens est porté par `aria-label` ; le chiffre animé est décoratif.

### Carte KPI (`ui.stat_card`)
- **Structure** : icône, libellé, valeur (Chiffre XL), note.
- **Variantes** : `default`, `signal` (fond violet licorne, texte blanc, une seule par rangée).
- **États** : survol = remontée de 2px. Pas de clic.
- **Mouvement** : entrée décalée de 60ms par carte, valeur qui compte.

### Carte de dossier (`ui.dossier_card`, dans un conteneur Streamlit `card_*`)
- **Structure** : tag d'état et anneau, titre (H3), description (3 lignes max), méta secteur et identifiant, avis, puis deux boutons Streamlit.
- **États** : repos, survol (remontée de 2px, ombre élevée), focus clavier sur les boutons, signalé (tag ambre), sans score (anneau vide, tag neutre).
- **Bords** : titre long = retour à la ligne ; description vide = phrase de repli ; identifiant long = coupé.
- **Mouvement** : entrée décalée, survol 240ms.

### Ligne de barre (`ui.bar_row`)
- **Structure** : libellé, valeur, piste et remplissage.
- **Mouvement** : le remplissage s'étire de 0 à sa largeur (`transform: scaleX`, 600ms).
- **Accessibilité** : `role="meter"` avec `aria-valuenow/min/max` et `aria-label`.

### Histogramme (`ui.distribution`)
- **Structure** : 5 colonnes, une par tranche de score, colorées par la rampe.
- **Mouvement** : les barres montent (`scaleY`), décalées.
- **États** : vide = message, aucune barre trompeuse.

### État vide (`ui.empty_state`)
- **Structure** : icône, titre, description. Bordure en pointillés.
- **Rôle** : `status`. Toujours accompagné d'une action quand il en existe une.

### En-tête de page (`ui.page_header`)
- **Structure** : surtitre, titre, sous-titre. Variante `hero` pour la vue d'ensemble.

### Dossier en tête (`ui.featured`, dans le conteneur Streamlit `featured_company`)
- **Structure** : surtitre, nom (Geist 600, 28px), secteur, anneau `lg` sur fond encre, description (4 lignes max), puis un bouton primaire Streamlit.
- **Surface** : carte à l'encre, halo violet, filet supérieur en dégradé licorne (section 7).
- **États** : sans dossier scoré, l'anneau est vide et le bouton mène à « Déposer un pitch ».

### En-tête de fiche (`ui.profile_header`)
- **Structure** : tag d'état, nom (H1), idée (16px), puces de contexte (secteur, canal, date), anneau `lg` à droite.
- **Mobile** : l'anneau passe au-dessus du texte (`column-reverse`).

### Titre de section (`ui.section_head`)
- **Structure** : H2 22px et légende optionnelle 13px. Utilisé partout à la place des `st.subheader` pour garder un rythme constant.

### Icône (`ui.icon`)
- **Structure** : `<span class="ico ico--{nom}">`, dessinée par un masque CSS qui prend la couleur du texte (`currentColor`). Jeu Lucide (ISC), trait 1,75.
- **Pourquoi pas du `<svg>`** : le sanitiseur de Streamlit retire les `<svg>` en ligne. Les masques sont injectés une fois par `ui.icons_css()`.

### Contrôles Streamlit restylés (CSS uniquement)
Boutons `primary` (encre), `secondary` (blanc, filet), `tertiary` (texte) ; champs texte et zone de texte ; liste déroulante ; radio horizontal en **contrôle segmenté** ; radio de la barre latérale en **navigation** avec icônes ; tableau ; expander ; alertes ; métrique ; formulaire ; téléversement.
Chaque bouton et champ a survol, appui, focus visible (anneau 2px + décalage 2px), désactivé. Chargement : spinner Streamlit en `--violet-600`.

## 6. Mouvement et interaction

| Type | Durée | Courbe | Usage |
|---|---|---|---|
| Micro | 120ms | `--ease-out` | Appui bouton, survol de nav |
| Standard | 240ms | `--ease-out` | Survol de carte, changement d'onglet |
| Emphase | 600–900ms | `--ease-emph` | Remplissage d'anneau, barres, entrée de page |

`--ease-out: cubic-bezier(.2, .8, .2, 1)` ; `--ease-emph: cubic-bezier(.16, 1, .3, 1)`.

Règles :
- On anime `transform` et `opacity`. Les ombres d'élévation sont une couche pseudo-élément dont on anime l'`opacity`.
- Les exceptions sont les deux propriétés enregistrées (`--p` de l'anneau et `--n` du compteur), qui ne déclenchent ni mise en page ni recalcul de flux.
- Entrée de page : 8px de translation et fondu en 320ms. Les cartes et KPI entrent avec un décalage de 50ms par élément, plafonné à 6.
- Chaque élément interactif a survol, appui et focus visible.
- `prefers-reduced-motion: reduce` : plus aucune animation, les valeurs finales s'affichent immédiatement.

**Fond vivant.** Un anneau part tout seul toutes les 3,2 secondes ; un clic n'importe où en lance un à l'endroit touché (5 anneaux au plus). Il se met en veille sans anneau, onglet caché, ou si le système demande moins de mouvement (la grille reste alors immobile).

**Moment signature** : à l'ouverture de la vue d'ensemble, les KPI comptent, l'histogramme monte et l'anneau du dossier en tête se referme sur son score.

## 7. Profondeur et surface

Stratégie **mixte** : filet fin + ombre en couches, sans cadre épais.

| Niveau | Valeur | Usage |
|---|---|---|
| Repos | `0 1px 2px #14171A0D` | Cartes, champs |
| Élevé | `0 1px 2px #14171A0A, 0 12px 24px -16px #14171A29` | Carte au survol (couche `::after`) |
| Prononcé | `0 2px 4px #14171A0D, 0 28px 48px -24px #14171A47` | Menus déroulants, toasts |

**Fond : le champ sonar** (`assets/sonar.js`, port du composant SonarGrid). Une grille de points de 26px, rayon 1,3px, à 20 % d'opacité en `--violet-600`, fixe derrière toute l'app. Sur le front d'un anneau, les points montent jusqu'à 100 % d'opacité et grossissent jusqu'à 3,9× (amplitude 2,2), largeur de front 90px, vitesse 260px/s. L'app est transparente au-dessus (`.stApp`, `stMain`), seules les surfaces blanches et la barre encre sont opaques.

**Halo.** Par-dessus, un halo violet très doux en haut à droite, avec une pointe de rose (`radial-gradient`).

**Lisibilité.** Le texte posé directement sur le fond (en-tête, titres de section) a un voile `--canvas` derrière lui ; les anneaux passent sous les cartes, jamais sur le texte.

**Carte à l'encre** (dossier en tête, tête de classement). Dégradé `#1D2226 → #14171A`, halo violet en haut à droite, filet supérieur en dégradé licorne, filet interne clair de 1px (`inset 0 1px 0 #FFFFFF14`).

## Contraintes de Streamlit à connaître

- **Aucun chevron `<` dans le CSS.** Streamlit passe le CSS par DOMPurify, qui supprime tout le bloc de style dès qu'il y trouve un `<` brut : toute l'app apparaît alors sans style. Les propriétés typées `@property` s'écrivent donc `syntax: "\3C number\3E"`. Le test `test_icones_sont_des_masques_css…` protège les icônes ; pour le fichier CSS, vérifier `grep -c "<" assets/unicornext.css` = 0.
- **Aucun `<svg>` en ligne** : voir `ui.icon`.
- **Le fond est un script, pas du CSS.** Streamlit interdit `<script>` dans `st.html`. `ui.sonar_html` génère un iframe de hauteur 0 (`components.html`) qui recopie `assets/sonar.js` dans la page principale, une seule fois (garde `window.__unicornextSonar`). C'est un contournement : il dépend du fait que l'iframe de Streamlit partage l'origine de la page.
- **Ne jamais mettre `position` sur `#root`.** Streamlit y ancre `.stApp` ; `#root` prendrait alors 0px de haut et l'app disparaîtrait sous le canvas. Le `z-index` se met sur `.stApp`.
- **Les tests parcourent l'app avec `AppTest`** : les clés de widgets (`page`, `open_*`, `save_*`, `featured_open`, `next_profile`, `active_pitch`) sont un contrat, ne pas les renommer.

## Dette assumée

- Streamlit relance le script à chaque clic : pas de vraies transitions entre pages, l'animation d'entrée les simule.
- Les icônes de navigation sont des masques CSS sur les éléments `label` du radio Streamlit ; elles dépendent de l'ordre des cinq pages et de la structure DOM de Streamlit 1.50.
- Le chargement de Geist demande un accès réseau ; hors ligne, `system-ui` s'affiche.
- Streamlit conserve la position de défilement d'une page à l'autre : changer de page ne remonte pas en haut.
- Le compteur animé et l'anneau reposent sur `@property` (Chrome, Safari 16.4+, Firefox 128+). Ailleurs, la valeur finale s'affiche sans animation.
