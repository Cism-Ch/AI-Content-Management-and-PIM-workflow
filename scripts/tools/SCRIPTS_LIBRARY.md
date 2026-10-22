# 🧰 Bibliothèque Officielle des Scripts Usine (Standard V3.4)

Ce document constitue la **source de vérité et l'inventaire officiel** de l'ensemble des scripts de production, d'audit qualité et d'outillage technique du catalogue WordPress / WooCommerce Usine V3.4.

Tous les scripts anciens, doublons ou obsolètes ont été assainis. Seuls les composants actifs et strictement conformes à la norme V3.4 sont maintenus.

---

## 🗺️ Cartographie & Organisation

```text
scripts/
├── build-product-pack-v3.py        # Compilateur Maître Tech (JSON -> HTML Long/Short + CSV)
├── generate_appliance_csv.py       # Compilateur Maître Électroménager (CSV d'import consolidé)
├── validate_html_template.py       # Validateur structurel des templates HTML
├── check_duplicates.py             # Détecteur de doublons de modèles et dossiers
│
├── rebuild_blackview_catalog.py    # Reconstructeur officiel Blackview
├── rebuild_hifuture_catalog.py     # Reconstructeur officiel HiFuture
├── rebuild_honor_catalog.py        # Reconstructeur officiel Honor
├── rebuild_oukitel_catalog.py      # Reconstructeur officiel Oukitel
├── rebuild_samsung_catalog.py      # Reconstructeur officiel Samsung
├── rebuild_xiaomi_catalog.py       # Reconstructeur officiel Xiaomi / POCO / Redmi
├── rebuild_zte_catalog.py          # Reconstructeur officiel ZTE / Nubia / RedMagic
│
└── tools/
    ├── product_data/               # Gates QA Qualité V3.4 Parents & Extraction
    ├── data_processing/            # AIOSEO, Copywriting, Store IDs & Toolkit CSV
    ├── appliance/                  # Contrôle éditorial & conformité Électroménager
    ├── extraction/                 # Scrapers de spécifications certifiées (GSMArena)
    ├── sociam_stock_processing/    # Pipeline d'intégration des stocks/prix Sociam
    └── analysis/                   # Analyse syntaxique des balises et sections
```

---

## 🚀 1. Compilateurs Maîtres & Reconstructeurs de Catalogues (`scripts/`)

| Script | Rôle & Usage | Commande d'Exécution |
| :--- | :--- | :--- |
| **`build-product-pack-v3.py`** | Compilateur unifié V3.4 : injecte les spécifications techniques du JSON dans les templates HTML `LONG` et `SHORT`, et génère la ligne WooCommerce CSV. | `python scripts/build-product-pack-v3.py --data <path_json> --outdir <out_dir> --modele <slug>` |
| **`generate_appliance_csv.py`** | Générateur maître CSV pour l'électroménager (Froid, Lavage, Cuisson, Climatisation) en lisant directement les données dans `Pricing/`. | `python scripts/generate_appliance_csv.py --category refrigerateur --brand beko` |
| **`validate_html_template.py`** | Validation stricte de conformité du balisage HTML pour éviter les balises orphelines ou mal fermées. | `python scripts/validate_html_template.py --file <path_to_html>` |
| **`rebuild_[marque]_catalog.py`** | Reconstructeurs officiels par marque : régénèrent l'intégralité du catalogue d'une marque en s'appuyant sur les JSON parents validés. | `python scripts/rebuild_xiaomi_catalog.py`<br>`python scripts/rebuild_samsung_catalog.py` |

---

## 🛡️ 2. Gates Qualité QA & Validation V3.4 (`scripts/tools/product_data/`)

Ces scripts constituent le cœur du Gate QA Parent-First (`/audit-product-pack`) :

| Script | Rôle & Usage | Commande d'Exécution |
| :--- | :--- | :--- |
| **`audit_json_structure.py`** | ⭐ **[Gate Structurel Obligatoire V3.4]** Audit approfondi de la structure des JSON parents (`long_description`, positionnement de `full_specs`, disclaimer officiel, `paired_variants`, attributs WooCommerce). | `python scripts/tools/product_data/audit_json_structure.py --dir product-data/<marque>` |
| **`validate_product_data.py`** | ⭐ **[Gate Technique Obligatoire]** Valide la présence et le bon typage des spécifications matérielles certifiées. | `python scripts/tools/product_data/validate_product_data.py --dir product-data/<marque>` |
| **`check_missing_specs.py`** | Détecte les clés ou spécifications manquantes dans les fiches produits. | `python scripts/tools/product_data/check_missing_specs.py` |
| **`check_product_existence.py`** | Pré-check d'existence d'un modèle pour éviter les doublons avant rédaction. | `python scripts/tools/product_data/check_product_existence.py --model "Nom Du Modèle"` |
| **`duplicate_single_parent.py`** | Duplique un modèle parent validé (statut PASS) vers ses déclinaisons physiques en respectant strictement les `paired_variants`. | `python scripts/tools/product_data/duplicate_single_parent.py --parent <path_json>` |
| **`fetch_product_specs.py`** | Extraction et structuration automatique des données produits. | `python scripts/tools/product_data/fetch_product_specs.py` |
| **`cleanup_n_a_variants.py`** | Nettoie les anciens dossiers orphelins ou mal nommés portant la mention `-n-a`. | `python scripts/tools/product_data/cleanup_n_a_variants.py` |

---

## ✍️ 3. Rédaction, AIOSEO & Liaisons Store (`scripts/tools/data_processing/`)

| Script | Rôle & Usage | Commande d'Exécution |
| :--- | :--- | :--- |
| **`audit_aioseo_sentences.py`** | Audit unitaire AIOSEO TruSEO : contrôle la formule mathématique des transitions (cible 36.5%, règle 15/41) et garantit 0% de phrases > 20 mots. | `python scripts/tools/data_processing/audit_aioseo_sentences.py --file <path_json>` |
| **`audit_batch_aioseo.py`** | Audit AIOSEO batch : scanne tous les fichiers JSON d'une marque et génère un rapport de conformité. | `python scripts/tools/data_processing/audit_batch_aioseo.py --dir product-data/<marque>` |
| **`copywriting_remediation.py`** | Détecte et réécrit les tournures hyperboliques et superlatifs publicitaires pour garantir un ton factuel axé sur l'usage quotidien. | `python scripts/tools/data_processing/copywriting_remediation.py detect --products-dir product-data/<marque>` |
| **`auto_fix_seo_rules.py`** | Scinde automatiquement les phrases dépassant 20 mots en 2 phrases concises. | `python scripts/tools/data_processing/auto_fix_seo_rules.py --file <path_json>` |
| **`link_store_ids_v3.4.py`** | Résout et injecte les identifiants uniques WooCommerce (`ID`) depuis les exports du store pour permettre la mise à jour sans écrasement. | `python scripts/tools/data_processing/link_store_ids_v3.4.py` |
| **`propagate_variants_and_compile_csv.py`** | Propage les déclinaisons matérielles et compile le CSV final consolidé pour l'import. | `python scripts/tools/data_processing/propagate_variants_and_compile_csv.py` |
| **`wc_csv_toolkit.py`** | ⭐ **[Toolkit CSV Unifié]** 4 sous-commandes : `prices` (mise à jour des prix), `colors` (correction couleurs), `clean-tags` (nettoyage balises), `all` (passe globale). | `python scripts/tools/data_processing/wc_csv_toolkit.py --help` |
| **`wc_json_attributes_fixer.py`** | Normalisation des attributs WooCommerce directement dans les JSON parents. | `python scripts/tools/data_processing/wc_json_attributes_fixer.py` |
| **`wc_csv_attr_patcher.py`** | Injection d'attributs manquants (RAM, Stockage) dans un CSV consolidé depuis les JSON sources. | `python scripts/tools/data_processing/wc_csv_attr_patcher.py` |
| **`patch_store_categories.py`** | Harmonise les catégories WooCommerce sur l'arborescence officielle du store. | `python scripts/tools/data_processing/patch_store_categories.py` |
| **`patch_disclaimer_and_energy.py`** | Met à jour le disclaimer officiel V3.4 et la classe énergétique sur l'ensemble des JSON. | `python scripts/tools/data_processing/patch_disclaimer_and_energy.py` |
| **`patch_confirmed_prices.py`** | Applique les prix confirmés du marché ivoirien. | `python scripts/tools/data_processing/patch_confirmed_prices.py` |
| **`normalize_product_colors.py`** | Uniformise les noms des coloris (FR/EN) selon la nomenclature officielle. | `python scripts/tools/data_processing/normalize_product_colors.py` |
| **`format_product_names.py`** | Formate les libellés commerciaux selon les normes WooCommerce. | `python scripts/tools/data_processing/format_product_names.py` |

---

## 🏠 4. Contrôle Électroménager (`scripts/tools/appliance/`)

| Script | Rôle & Usage | Commande d'Exécution |
| :--- | :--- | :--- |
| **`analyze_editorial_sections.py`** | Scanne les fichiers `LONG.html` électroménager pour s'assurer de la présence d'au moins 3 sections H2 et de 2 paragraphes par section. | `python scripts/tools/appliance/analyze_editorial_sections.py` |
| **`check_csv_colors.py`** | Valide la conformité de l'extraction des couleurs dans les exports CSV. | `python scripts/tools/appliance/check_csv_colors.py --csv <fichier.csv>` |
| **`check_csv_prices.py`** | Contrôle la présence et la cohérence de la colonne Regular price dans le CSV. | `python scripts/tools/appliance/check_csv_prices.py --csv <fichier.csv>` |

---

## 🔍 5. Extraction, Stocks Sociam & Analyse

- **`scripts/tools/extraction/scrape-gsmarena-specs.py`** : Scraper certifié pour extraire les fiches complètes depuis GSMArena.
- **`scripts/tools/extraction/extract_html_colors.py`** : Extraction des coloris depuis les templates HTML existants.
- **Suite Sociam Stocks (`scripts/tools/sociam_stock_processing/`)** :
  - `stock_extractor.py` : Extraction des tarifs et stocks depuis l'inventaire Excel.
  - `stock_applier.py` : Application des prix extraits aux CSV WooCommerce.
  - `stock_search.py` : Recherche interactive de références dans les inventaires.
  - `stock_details.py` : Consultation détaillée par référence SKU.
- **Analyse (`scripts/tools/analysis/`)** :
  - `analyze_csv_sections.py` : Comptage des sections H2 dans la description CSV.
  - `analyze_sections.py` : Contrôle des balises dans les fichiers HTML.
  - `debug_tags.py` : Diagnostic des balises HTML mal formées.

---

## 📂 6. Centralisation des Fichiers de Données & Prix

Tous les fichiers de référence tarifaire (`price_map_*.json`), grilles de prix et règles de détection de couleurs sont désormais unifiés à la racine dans le dossier dédié :
👉 [**Pricing/**](file:///c:/Users/hanok/wordpress/Pricing/)
