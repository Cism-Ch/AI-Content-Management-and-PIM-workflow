---
name: appliance-factory
description: Procédures industrielles et molds structurels (HTML LONG + SHORT) pour le Gros et Petit Électroménager, le Froid et la Climatisation. Moteur exclusif pour /produce-appliance.
---

# SKILL: Appliance Production Factory

This skill defines the operational procedure for generating standardized product description packs (LONG + SHORT) for household appliances. It serves as the **exclusive implementation engine** for the `/produce-appliance` workflow. It treats templates as industrial **molds** that ensure consistency while allowing data-driven flexibility. Do not use any other workflow for this task. Do not use any other skill for this task. Do not invent any other workflow for this task. Do not invent any other skill or procedure for this task.

## Core Directives

0.  **Workflow Identity & Binding**: This skill is **strictly dedicated** to the `/produce-appliance` workflow. - **DO NOT** confuse this skill (procedural instructions) with "linked files" (_fichiers liés_) such as JSON/CSV data sources. - **DO NOT** apply these specific rules to other workflows (e.g., [**production-industrielle-v3**](../../workflows/production-industrielle-v3.md)) to avoid procedural cross-contamination. - This skill defines the industrial process for appliances only.
    0.1 **AI Orchestrator Link**: If you encounter looping errors, template rejections from validation scripts, or any complex issue you cannot resolve in 2 attempts, escalate the problem to the [**Production Orchestrator (orchestrateur_production)**](file:///c:/Users/hanok/wordpress/.agents/skill/orchestrateur_production/orchestrateur.md). It has broader access to the codebase and will guide you to a structural fix.
1.  **Industrial Consistency**: You MUST strictly adhere to the CSS, font-family, colors, and layout defined in the [**Template-Appliance**](file:///C:/Users/hanok/wordpress/Template-Appliance) directory. Never invent new styles or change the theme (Orange #ff4800 / Black #1d1d1f) (TRÈS IMPORTANT).
2.  **Verified Research**: Never hallucinate specifications. Never extrapoler les specs d'un modèle voisin (TRÈS IMPORTANT).
    - Effectuer une **recherche web générale** pour chaque modèle. Une simple recherche Google du nom du produit mène naturellement vers de nombreuses sources fiables.
    - **Sources à exploiter** (ordre recommandé) :
        1. Site officiel du constructeur
        2. Sites de vente en ligne locaux et internationaux (Jumia, Amazon, Alibaba, AliExpress, etc.)
        3. Sous-distributeurs et revendeurs régionaux
        4. Sites de comparaison et fiches produit en ligne
        5. Catalogues PDF de grossistes
    - **Minimum 2 sources distinctes** pour confirmer une donnée technique clé (CRITIQUE ET IMPORTANT).
    - **Si une donnée reste introuvable après recherche exhaustive** : supprimer la ligne du tableau. Ne pas inventer de valeur vague (!important).
2.1 **Taxonomie & Catégories** : Pour toute classification de produit dans le catalogue, vous DEVEZ vous référer au [**Guide de Taxonomie WordPress**](file:///c:/Users/hanok/wordpress/Docs/WORDPRESS_TAXONOMY_GUIDE.md). Ce document est la **source de vérité unique** pour l'arborescence des catégories (Parent > Enfant) lors de la génération des CSV.
3.  **Dynamic Table Extension**: While the mold is fixed, the data content is not.
    - If a product has unique features (e.g., "AI Wash", "Smart Diagnosis"), **ADD** the necessary `<tr>` rows in the corresponding table category.
    - **CRITICAL**: If you add rows, you MUST update the `rowspan` of the first `<td>` of that category to maintain table alignment.
    - **Flexible Sections**: Use the standard 3-section structure (Performance, Confort, Fonctions Avancées or other relevant sections) for all appliances.
4.  **Linguistic Standards**:
    - **Word Count**: LONG description must be between 450 and 700 words (to accommodate the new 3-sections éditoriales h2 structure).
    - **SEO Transitions**: 31% to 72% of sentences must start with a transition word in at least half of the paragraphs.
    - **Tone**: French (Standard), professional, focusing on domestic benefits or professional benefits for professional appliances.

## Operational Workflow

### Phase 1: Data Gathering

> [!TIP]
> **🔗 Pré-vérification Product Intelligence** : Avant de lancer la recherche web, vérifier si un fichier JSON vérifié existe dans `product-data/[brand]/[series]/product-data-[model].json`. Si oui, utiliser ses données (SKU, specs, prix FCFA, coloris) comme base de référence fiable. Si non, procéder à la recherche ci-dessous ou invoquer le workflow [`/generate-product-data`](file:///c:/Users/hanok/wordpress/.agents/workflows/generate-product-data.md) pour le créer. Validation : `python scripts/tools/product_data/validate_product_data.py --input <fichier.json>`.

- Recherche principale : `[Nom du Produit] fiche technique` ou `[Nom du Produit] specifications` sur Google.
- Recherche élargie (si résultats insuffisants) : `[Référence SKU]`, `[Marque] [Modèle] datasheet`, `[Marque] [Modèle] prix`.
- La recherche Google générale est le point d'entrée naturel : elle mène vers les sites constructeurs, de vente, sous-distributeurs et comparateurs sans avoir besoin de filtres spécifiques.
- Extract: Brand, Model, Energy Class, Dimensions (HxLxP), Capacity, Noise, specific technologies, weight, warranty, number of colors, number of functions, number of settings, number of programs, main features, energy efficiency, etc.
- Save a brief JSON log of findings.

### Phase 2: LONG Generator

- Load [**TEMPLATE_APPLIANCE_LONG.html**](file:///C:/Users/hanok/wordpress/Template-Appliance/TEMPLATE_APPLIANCE_LONG.html).
- Inject: Replace all `[VAL]` and placeholders.
- Write: Craft paragraphs for "Performance" and "Confort" sections.
- Validation: Check word count and transition density.

### Phase 3: SHORT Generator

- Load [**TEMPLATE_APPLIANCE_SHORT.html**](file:///C:/Users/hanok/wordpress/Template-Appliance/TEMPLATE_APPLIANCE_SHORT.html).
- Inject: Brand/Model in header.
- List: Select top 4 high-impact benefits found during research.

### Phase 4: Output Path

- Root: `c:/Users/hanok/wordpress/products-appliance/`
- Pattern: `[BRAND]/[MODEL]/[PRODUCT-NAME]-[TYPE].html`

### Phase 5: Workflow Termination (Standard Tools)

Once HTML files are generated and validated, use the following scripts to finalize the pack. Le toolkit unifié [**wc_csv_toolkit.py**](file:///C:/Users/hanok/wordpress/scripts/tools/data_processing/wc_csv_toolkit.py) est désormais **l'outil de référence** pour les corrections post-génération.

### Phase 6: Industrial Remediation & Structural Refactoring (Reprise de Travail)

Cette phase est obligatoire si un fichier existant ne respecte pas la `Quality Check Checklist` ou si la structure HTML est corrompue. Contrairement aux scripts automatiques, l'IA doit ici agir comme un "correcteur chirurgical".

- **Audit d'Intégrité** : Lire le fichier (`view_file`) et identifier les manquements (ex: Paragraphes trop longs > 60 mots (nombre de mots par paragraphe avec tolerance +10% a +15%) ou trop courts < 450 mots (nombre de mots total), manque de transitions, H2 manquants, CSS altéré).
- **Réusinage Éditorial** : Utiliser les outils d'édition de code (`replace_file_content`) pour corriger le fond sans détruire la forme :
    - **Scinder** les blocs de texte denses.
    - **Re-formater** les tableaux techniques si les styles inline ont été perdus.
    - **Enrichir** le contenu si le word count est < 450 mots.
- **Restauration du Moule** : Si le template a dérivé, copier-coller les blocs de styles CSS et les structures de boutons (`CTA`) depuis les fichiers [**Template-Appliance**](file:///C:/Users/hanok/wordpress/Template-Appliance) d'origine.
- **Re-Validation** : Exécuter systématiquement les scripts de validation après chaque intervention manuelle.

1.  **CSV Generation**: [**scripts/generate_appliance_csv.py**](file:///C:/Users/hanok/wordpress/scripts/generate_appliance_csv.py) `--input products-appliance/[BRAND]`
    - _Purpose_: Scans the product folders to create the WooCommerce import CSV.

2.  **Corrections & Enrichissement (Toolkit unifié)**:

    ```bash
    # Passe complète : prix + couleurs + nettoyage des tags
    # CRITICAL: Always use quotes for paths with spaces (e.g. "cuiseur de riz")
    python scripts/tools/data_processing/wc_csv_toolkit.py all \
      --csv "Exports/CSV_Imports/Appliance/votre_fichier.csv" \
      --json "chemin/vers/prices.json" \
      --rules "scripts/tools/data_processing/color_rules_default.json" \
      --remove "Côte d'Ivoire"
    ```

    - **CRITICAL - Format JSON Prix**: Les clés du JSON doivent correspondre EXACTEMENT au SKU du CSV (format: "BRAND-MODEL").
        - Exemple: `"NASCO-NAS-RC1,8WM": "29900"`
    - Sous-commandes disponibles : `prices`, `colors`, `clean-tags`, `all`
    - Documentation complète : [**scripts/tools/data_processing/README.md**](file:///C:/Users/hanok/wordpress/scripts/tools/data_processing/README.md)
    - Fichier de règles couleur : [**Pricing/color_rules_default.json**](file:///C:/Users/hanok/wordpress/Pricing/color_rules_default.json)

## Specialized Utility Library (Tools)

### 🔧 Outils de validation HTML ([**scripts/tools/appliance/**](file:///C:/Users/hanok/wordpress/scripts/tools/appliance/))

- [**analyze_editorial_sections.py**](file:///C:/Users/hanok/wordpress/scripts/tools/appliance/analyze_editorial_sections.py): Mandatory validation for LONG.html structure.
- [**check_csv_colors.py**](file:///C:/Users/hanok/wordpress/scripts/tools/appliance/check_csv_colors.py) / [**check_csv_prices.py**](file:///C:/Users/hanok/wordpress/scripts/tools/appliance/check_csv_prices.py): Post-import CSV verification.

### 🛠️ WooCommerce CSV Toolkit ([**wc_csv_toolkit.py**](file:///C:/Users/hanok/wordpress/scripts/tools/data_processing/wc_csv_toolkit.py))

Outil générique de correction et d'enrichissement des CSV WooCommerce. À utiliser **après** la génération du CSV pour toute correction standard :

| Sous-commande | Usage                                          | Exemple rapide                                                             |
| ------------- | ---------------------------------------------- | -------------------------------------------------------------------------- |
| `prices`      | Injecter les prix depuis un JSON `{SKU: prix}` | `wc_csv_toolkit.py prices --csv X.csv --json prices.json`                  |
| `colors`      | Corriger les attributs Color manquants         | `wc_csv_toolkit.py colors --csv X.csv --rules color_rules_default.json`    |
| `clean-tags`  | Supprimer des mots-clés des tags               | `wc_csv_toolkit.py clean-tags --csv X.csv --remove "Côte d'Ivoire"`        |
| `all`         | Tout en une seule passe                        | `wc_csv_toolkit.py all --csv X.csv --json P.json --remove "Côte d'Ivoire"` |

## Mapping des Catégories de Tableau par Type de Produit

Le template LONG définit un tableau technique extensible. Voici les catégories recommandées selon le type d'appareil. **Minimum 14 lignes** par tableau.

### Groupe 1 : Froid (Réfrigérateur, Congélateur, Congélateur Vertical, Refroidisseur)

| Catégorie   | Lignes min | Exemples de champs                           |
| :---------- | :--------: | :------------------------------------------- |
| Général     |     5      | Marque, Modèle, Type, Dimensions, Coloris    |
| Énergie     |     4      | Classe, Consommation, Tension, Niveau sonore |
| Capacité    |     4      | Volume total, Répartition, Compartiments     |
| Technologie |     4      | Système froid, Dégivrage, Affichage          |

### Groupe 2 : Cuisson (Gazinière, Plaque de Cuisson, Four Encastrable)

| Catégorie          | Lignes min | Exemples de champs                                            |
| :----------------- | :--------: | :------------------------------------------------------------ |
| Général            |     5      | Marque, Modèle, Format, Finition, Usage                       |
| Cuisson            |     5      | Nombre feux, Type gaz, Allumage, Four, Capacité four          |
| Structure          |     4      | Porte, Couvercle, Accessoires, Piétement                      |
| Options & Sécurité |     4      | Allumage intégré, Sécurité thermocouple, Minuterie, Éclairage |

### Groupe 3 : Soin du Linge (Machine à Laver, Sèche-Linge, Soin du Linge)

| Catégorie   | Lignes min | Exemples de champs                        |
| :---------- | :--------: | :---------------------------------------- |
| Général     |     4      | Marque, Modèle, Type, Coloris             |
| Performance |     4      | Capacité, Essorage, Classe énergie, Bruit |
| Dimensions  |     4      | HxLxP, Poids, Type pose                   |
| Programmes  |     4      | Nombre programmes, Fonctions spéciales    |

### Groupe 4 : Extraction (Hotte Aspirante)

| Catégorie                  | Lignes min | Exemples de champs                                                  |
| :------------------------- | :--------: | :------------------------------------------------------------------ |
| Général                    |     4      | Marque, Type, Dimensions, Finition                                  |
| Performance                |     4      | Débit, Vitesses, Bruit, Classe énergie                              |
| Éclairage & Filtres        |     4      | Type lampe, Filtres, Entretien                                      |
| Maintenance & Installation |     4      | Filtres lavables, Type évacuation, Clapet anti-retour, Installation |

### Groupe 5 : Petit Électroménager Cuisine (Micro-Ondes, Mixeur-Blender, Bouilloire, Préparation Culinaire)

| Catégorie            | Lignes min | Exemples de champs                                              |
| :------------------- | :--------: | :-------------------------------------------------------------- |
| Général              |     4      | Marque, Modèle, Type, Coloris                                   |
| Performance          |     4      | Puissance, Capacité, Vitesses, Fonctions                        |
| Construction         |     4      | Matériaux, Dimensions, Poids, Accessoires                       |
| Fonctions & Sécurité |     4      | Protection thermique, Pieds ventouses, Verrouillage, Mode Pulse |

### Groupe 6 : Climatisation (Climatiseur)

| Catégorie  | Lignes min | Exemples de champs                       |
| :--------- | :--------: | :--------------------------------------- |
| Général    |     4      | Marque, Modèle, Type (Split/Mobile), BTU |
| Énergie    |     4      | Classe, EER/COP, Tension, Réfrigérant    |
| Dimensions |     4      | Unité int/ext, Poids, Longueur tuyau     |
| Fonctions  |     4      | Modes, Télécommande, Timer, Connectivité |

### Groupe 7 : Eau & Confort (Chauffe-Eau, Purificateur d'Eau, Distributeur d'Eau)

| Catégorie             | Lignes min | Exemples de champs                                         |
| :-------------------- | :--------: | :--------------------------------------------------------- |
| Général               |     4      | Marque, Modèle, Type, Capacité                             |
| Performance           |     4      | Puissance, Température, Débit, Énergie                     |
| Construction          |     4      | Matériau cuve, Dimensions, Poids, Sécurité                 |
| Sécurité & Protection |     4      | Soupape de sécurité, Anti-corrosion, Voyant LED, Indice IP |

### Groupe 8 : Protection Électrique (Stabilisateur, Protecteur, Rallonge)

| Catégorie             | Lignes min | Exemples de champs                                               |
| :-------------------- | :--------: | :--------------------------------------------------------------- |
| Général               |     4      | Marque, Modèle, Type, Puissance VA                               |
| Spécifications        |     4      | Plage tension, Temps réponse, Prises                             |
| Construction          |     4      | Dimensions, Poids, Protection, Indicateurs                       |
| Système de Protection |     4      | Temps de délai, Protection pics, Coupure auto, Matériau ignifugé |

### Groupe 9 : Ventilation (Ventilateur sur pied, mural, brumisateur)

| Catégorie          | Lignes min | Exemples de champs                                            |
| :----------------- | :--------: | :------------------------------------------------------------ |
| Général            |     4      | Marque, Modèle, Type, Diamètre                                |
| Performance        |     4      | Puissance, Vitesses, Débit air, Bruit                         |
| Construction       |     4      | Matériaux, Hauteur, Poids, Télécommande                       |
| Confort & Réglages |     4      | Oscillation auto, Inclinaison réglable, Minuterie, Type socle |

### Groupe 10 : Nettoyage (Lave-Vaisselle)

| Catégorie            | Lignes min | Exemples de champs                                                  |
| :------------------- | :--------: | :------------------------------------------------------------------ |
| Général              |     4      | Marque, Modèle, Type, Couverts                                      |
| Performance          |     4      | Classe énergie, Consommation eau, Bruit                             |
| Programmes           |     4      | Nombre cycles, Type séchage, Fonctions                              |
| Agencement & Options |     4      | Panier réglable, Sécurité enfant, Indicateurs rinçage, Top amovible |

### Groupe 11 : Audio-Visuel (Téléviseur / Smart TV)

| Catégorie              | Lignes min | Exemples de champs                                                                |
| :--------------------- | :--------: | :-------------------------------------------------------------------------------- |
| Affichage              |     5      | Taille écran, Résolution (4K/HD/HD Ready), Technologie (LED/QLED), Fréquence (Hz) |
| Smart & Audio          |     5      | Système (Android/Tizen), Applications, Puissance Sortie, Wi-Fi, Bluetooth         |
| Réception & Protection |     4      | Tuner (DVB-T2/S2), Régulateur de tension intégré, Enregistrement USB (PVR)        |
| Connectique            |     4      | HDMI (nombre), USB (nombre), Entrée AV/VGA, Sortie Optique/Jack                   |
| Général & Montage      |     4      | Marque, Modèle, Dimensions, Norme VESA (Fixation murale)                          |

## Quality Check Checklist

- [ ] **Zéro Hallucination** : Pas de valeurs "N/A" ou inventées, pas de placeholder. Données recoupées.
- [ ] **Structure & Style** : Tableaux conformes au Template (3 colonnes, styles inline, `rowspan` exact).
- [ ] **Mapping Technique** : Respect du mapping (4 catégories min, extensible à 5) et seuil de 14 lignes.
- [ ] **Hygiène HTML** : Code non-minifié, propre et indenté pour maintenance WordPress.
- [ ] **Sources & Crédibilité** : Liens 100% officiels (Constructeur). **Aucun lien concurrent** (Jumia, Amazon).
- [ ] **Appels à l'Action** : Boutons "Découvrir" et "Panier" présents avec styles officiels.
- [ ] **Français & Transitions** : Seuil de transitions (31-72%) respecté. Pas d'anglicismes inutiles.
- [ ] **Sobriété Rédactionnelle** : Ton factuel professionnel. **Zéro hyperbole marketing**.
- [ ] **SEO (E-commerce)** : Blocs Metadata (Title/Meta Desc/Keywords) présents et structurés selon la norme V2.1 :
  - **Meta Title** : Strictement descriptif (Ex: `Marque Modèle Caractéristique_Clé Capacité/Puissance`).
  - **Meta Description** : Zéro SAV/Garantie commerciale. Focus sur Livraison Abidjan, qualité/prix, facilité de commande, ou garanties technologiques.
  - **LSI Keywords** : Minimum **10 mots-clés** orientés achat et caractéristiques uniques.
  - **Variantes** : Jeux de métadonnées totalement différents entre les blocs SHORT et LONG.
- [ ] **Template** : Respect du template (CRITICAL).
