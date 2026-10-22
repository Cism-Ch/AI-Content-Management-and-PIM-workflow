# 🚀 Pipeline de Production HiFuture V3.4 (Parent-First Audit Gate & Modèle Parent-Enfant)

Ce pipeline standardise le processus de création, d'audit, de compilation HTML et de génération du CSV WooCommerce avec relations **Parent-Enfant (Variable + Variation)** pour les 21 modèles de la marque **HiFuture**.

---

## 📋 Pré-requis et Structure des Fichiers

Avant de démarrer la production ou la mise à jour du catalogue HiFuture, s'assurer de disposer de la structure suivante :
1. **Fichier Source de Vérité** : `hifuture_models_parent.csv` situé à la racine de `product-data/` répertoriant les modèles officiels avec leurs caractéristiques :
   * `model_slug`, `commercial_name`, `category`, `ram_options`, `rom_options`, `official_colors_fr`, `official_colors_en`, `certification_status`, `official_source_url`.
2. **Dossier de Stockage JSON Parents** : `product-data/hifuture/` pour stocker les 21 fichiers JSON de configuration parents certifiés.
3. **Dossier de Sortie Produit & CSV** : `products/hifuture-all/` contenant les 21 sous-dossiers produits et le CSV d'importation consolidé `import-v2-hifuture-all.csv`.

---

## 🛠️ Étapes du Pipeline de Production HiFuture

### Étape 1 : Sourcing Web en Direct & Création du Fichier Parent (JSON)
Extraire en temps réel (via recherche Web en direct `search_web` sur les sites officiels HiFuture et fiches certifiées) les données techniques officielles du produit et créer le fichier parent :
📂 `product-data/hifuture/hifuture-[slug].json`

S'assurer que :
* **Règle Stricte des 3 Liens Sources** :
  - **Source 1** : `"HiFuture Official Store"` -> Lien officiel du constructeur (`https://hifuturegroup.com/products/[slug]`).
  - **Source 2** : `"Recherche Générique"` -> `https://www.google.com/search?q=HiFuture+[MODELE]`.
  - **Source 3** : `"Recherche Spécialisée IA"` -> `https://www.google.com/search?q=HiFuture+[MODELE]+specifications`.
* **Noms de Couleurs Certifiées (`official_colors_fr` & `official_colors_en`)** : 
  - Conserver fidèlement les dénominations officielles du constructeur HiFuture présentées dans `hifuture_models_parent.csv` (`official_colors_fr`: ex: `Noir, Blanc, Bleu, Rose`, `Noir, Silver`, `Noir, Vert, Camo`, `Noir, Gris, Orange`).
  - Générer les suffixes des SKUs des variantes en majuscules ASCII normalisées d'après les termes certifiés (`HIFUTURE-[MODELE]-NOIR`, `HIFUTURE-[MODELE]-BLANC`, `HIFUTURE-[MODELE]-SILVER`, `HIFUTURE-[MODELE]-TITANIUM`, etc.).
* Le tableau `full_specs` (ou `full_specs_table`) est imbriqué **à l'intérieur de `long_description`**, immédiatement au-dessus de la clé `cta`.
* Le bloc `cta` est configuré avec les 2 boutons d'action officiels :
  - `top_link`: `"#"` | `top_label`: `"Remonter pour commander"`
  - `boutiques_link`: `"https://my-estore.com/boutiques-officielles/"` | `boutiques_label`: `"Nos Boutiques Officielles"`
* Le bloc `woocommerce_csv` contient les attributs ordonnés selon la norme V3.4 :
  - `Stock`: `"10"` (Valeur de stock par défaut fixée à 10 unités par déclinaison).
  - `Attribute 1 name`: `"Couleur"`, `Attribute 1 value(s)`: Liste de toutes les couleurs (ex: `"Noir, Blanc, Bleu, Rose"`).
  - `Attribute 2 name`: `"Stockage"` (ou `"Connexion"`)
  - `Attribute 3 name`: `"RAM"` (ou `"Autonomie"`)
  - `Attribute 4 name`: `"Processeur"` *(uniquement pour PC / Ordinateurs Laptops & Desktops)*
  - `Attribute 5 name`: `"Réseau"` *(ex: `5G`, `4G`, `Wi-Fi 7`)*

---

### Étape 2 : Rédaction & Optimisation (3 Personas)

#### ✍️ Copywriting Factuel (Persona 1)
* **Zéro Hyperbole** : Proscrire les adjectifs promotionnels subjectifs (*ultime*, *révolutionnaire*, *parfaite*, *colossale*, *exceptionnelle*).
* **Bénéfice Usage** : Expliquer l'utilité réelle de chaque composant technique pour le client.

#### 🔍 Expert SEO AIOSEO (Persona 2) — Formule Mathématique Fixe (15/41 - 36.5%)
* **Formule Mathématique Fixe 15/41** : Viser exactement **15 phrases avec transition sur 41 phrases au total** pour obtenir systématiquement 36.5% de score AIOSEO :
  - Paragraphe d'intro : 5 phrases (exactement 3 phrases avec mot de transition).
  - 3 Sections H2 (6 paragraphes de 6 phrases) : 4 phrases avec mot de transition par section (2 par paragraphe).
* **Longueur des phrases** : Scinder systématiquement toute phrase pour maintenir une longueur strictement comprise entre **12 et 18 mots maximum** (0% de phrases > 20 mots).
* **Marque Enseigne** : Toujours orthographier **`My-eStore`** en un seul mot.
* **Sous-Titre Tableau Specs** : Formuler `full_specs.header.subtitle` **SANS LE MOT "certifiées"** (ex: `"Spécifications matérielles du [MODÈLE]."`).
* **Formule des Meta Titles** :
  * Dans `short_description.seo.meta_title` (Intention locale) :
    👉 `Acheter [MARQUE] [MODÈLE] à Abidjan | My-eStore`
  * Dans `long_description.seo.meta_title` (Top Spécifications) :
    👉 `[MARQUE] [MODÈLE] : [Top Spec 1] & [Top Spec 2] | My-eStore`

#### ⚙️ Intégrateur & Auditeur (Persona 3)
* Valider que les SKUs des variantes respecteront le format standard : `HIFUTURE-[MODELE]-SKU` (ex: `HIFUTURE-COLORBUDS2` pour le parent, `HIFUTURE-COLORBUDS2-NOIR` pour la déclinaison).

---

### Étape 3 : Audit de Qualité & Conformité (Gate QA sur Parent)
Exécuter impérativement les scripts d'audit AIOSEO et de conformité des spécifications sur la fiche parent avant toute compilation :
```bash
python scripts/tools/product_data/validate_product_data.py --input "product-data/hifuture/hifuture-[slug].json"
python scripts/tools/data_processing/audit_aioseo_sentences.py "products/hifuture-all/hifuture-[slug]/pack-data-hifuture-[slug].json"
```
* **Contrôles de l'Audit Gate** :
  1. Validation ProductData à 0 erreur (au moins 2 sources URLs profondes réelles documentées).
  2. Contexte éditorial sans hyperbole, 0 phrase > 20 mots, et score de transition AIOSEO exact de 36.5%.
  3. Présence obligatoire du poids technique.
* **Si un test échoue** : Corriger immédiatement le JSON parent et relancer les audits jusqu'à obtenir le statut **PASS**.

---

### Étape 4 : Formatage des Noms Commerciaux Vendeurs & Compilation HTML
* **Attribution des Noms Commerciaux Vendeurs (`format_product_names.py`)** :
  - **Produit Parent (`variable` / `simple`)** : Titre vendeur enrichi avec Top Specs, **SANS énumération de couleurs et SANS mémoire système MB interne à la fin**.
    *(Exemple)* : `HiFuture ColorBuds 2 - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 10mm - Boîtier 300mAh - IPX5`
  - **Déclinaisons Enfants (`variation`)** : Nom parent propre + **uniquement la couleur individuelle représentée**.
    *(Exemple)* : `HiFuture ColorBuds 2 - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 10mm - Boîtier 300mAh - IPX5 - Noir`

* **Compilation des Fiches HTML (`build-product-pack-v2.py`)** :
  ```bash
  python scripts/build-product-pack-v2.py --data "products/hifuture-all/hifuture-[slug]/pack-data-hifuture-[slug].json" --outdir "products/hifuture-all/hifuture-[slug]" --modele [slug] --serie hifuture-all --skip-validation
  ```
  * Génère les fichiers HTML rendus nettoyés (0 commentaire, 0 saut de ligne cosmétique) :
    - `short-[slug].html`
    - `long-[slug].html`

---

### Étape 5 : Consolidation du CSV WooCommerce Global (Modèle Parent-Enfant)
Exécuter le script orchestrateur dédié HiFuture pour compiler les 21 produits et leurs 58 variations dans le fichier d'importation unique :
```bash
python scripts/rebuild_hifuture_catalog.py
```

* **Structure des Lignes dans le CSV Consolidé (`import-v2-hifuture-all.csv`)** :
  - **Ligne Parent (`Type=variable`)** :
    - `SKU`: `HIFUTURE-[SLUG]`
    - `Name`: Nom commercial propre avec Top Specs (SANS liste de couleurs)
    - `Short description` & `Description`: Descriptions HTML complètes
    - `Parent`: (champ vide)
    - `Attribute 1 value(s)`: Liste de toutes les couleurs (ex: `"Noir, Blanc, Bleu, Rose"`)
  - **Lignes Enfants (`Type=variation`)** :
    - `SKU`: `HIFUTURE-[SLUG]-[COULEUR]`
    - `Name`: `[Nom Parent Propre] - [Couleur]` (ex: `... - IPX5 - Noir`)
    - `Short description` & `Description`: (vides — héritées du parent sur WooCommerce)
    - `Parent`: `HIFUTURE-[SLUG]` (pointe vers le SKU Parent)
    - `Attribute 1 value(s)`: Couleur unique (ex: `"Noir"`)

📂 **Emplacement du CSV Final** : `products/hifuture-all/import-v2-hifuture-all.csv` (79 lignes : 21 parents + 58 variations).

---

## 📊 Tableau de Suivi de Production HiFuture (21 Modèles — 100% COMPLET)

| # | Slug Modèle | Nom Commercial Parent | Type WC | SKUs Parent / Variantes | Status QA & HTML | Status CSV |
| :-: | :--- | :--- | :-: | :--- | :-: | :-: |
| **1** | `hifuture-colorbuds2` | HiFuture ColorBuds 2 - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 10mm - Boîtier 300mAh - IPX5 | `variable` | `HIFUTURE-COLORBUDS2` (+4 variantes) | ✅ PASS | ✅ INCLUS |
| **2** | `hifuture-flex-2` | HiFuture Flex 2 Smartwatch - Écran IPS - 1.39" - 280mAh | `variable` | `HIFUTURE-FLEX-2` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **3** | `hifuture-flexclip` | HiFuture FlexClip - Écouteurs Open-Ear - Bluetooth 5.4 - Autonomie 30h - IPX5 | `variable` | `HIFUTURE-FLEXCLIP` (+2 variantes) | ✅ PASS | ✅ INCLUS |
| **4** | `hifuture-flybuds3` | HiFuture FlyBuds 3 - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 10mm - Boîtier 400mAh - IPX5 | `variable` | `HIFUTURE-FLYBUDS3` (+4 variantes) | ✅ PASS | ✅ INCLUS |
| **5** | `hifuture-futurego-mix-2` | HiFuture FutureGo Mix 2 Smartwatch - Écran AMOLED - 1.43" - 400mAh | `variable` | `HIFUTURE-FUTUREGO-MIX-2` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **6** | `hifuture-futurego-pro` | HiFuture FutureGo Pro Smartwatch - Écran IPS - 1.32" - 430mAh | `variable` | `HIFUTURE-FUTUREGO-PRO` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **7** | `hifuture-futuremate-2-pro` | HiFuture FutureMate 2 Pro - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 4mm - Boîtier 500mAh - IPX5 | `variable` | `HIFUTURE-FUTUREMATE-2-PRO` (+2 variantes) | ✅ PASS | ✅ INCLUS |
| **8** | `hifuture-go-pro-2` | HiFuture GO PRO 2 Smartwatch - Écran AMOLED - 1.32" - 430mAh | `variable` | `HIFUTURE-GO-PRO-2` (+2 variantes) | ✅ PASS | ✅ INCLUS |
| **9** | `hifuture-gravity` | HiFuture Gravity - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Boîtier 4000mAh - IPX7 | `variable` | `HIFUTURE-GRAVITY` (+2 variantes) | ✅ PASS | ✅ INCLUS |
| **10** | `hifuture-musicbox` | HiFuture MusicBox - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 78mm - Boîtier 12000mAh - IPX7 | `simple` | `HIFUTURE-MUSICBOX` | ✅ PASS | ✅ INCLUS |
| **11** | `hifuture-olymbuds3` | HiFuture OlymBuds 3 - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 6mm - Boîtier 350mAh - IPX5 | `variable` | `HIFUTURE-OLYMBUDS3` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **12** | `hifuture-ripple` | HiFuture Ripple - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Boîtier 4000mAh - IPX7 | `variable` | `HIFUTURE-RIPPLE` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **13** | `hifuture-sonicair` | HiFuture SonicAir - Écouteurs Sans Fil TWS - Bluetooth 5.3 - Drivers 10mm - Boîtier 450mAh - IPX5 | `variable` | `HIFUTURE-SONICAIR` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **14** | `hifuture-ultra3-pro` | HiFuture Ultra3 Pro Smartwatch - Écran AMOLED - 2.04" - 350mAh | `variable` | `HIFUTURE-ULTRA3-PRO` (+2 variantes) | ✅ PASS | ✅ INCLUS |
| **15** | `hifuture-zone-2` | HiFuture Zone 2 Smartwatch - Écran IPS - 1.96" - 300mAh | `variable` | `HIFUTURE-ZONE-2` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **16** | `hifuture-active` | HiFuture Active Smartwatch - Écran AMOLED - 1.43" - 400mAh | `variable` | `HIFUTURE-ACTIVE` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **17** | `hifuture-altair` | HiFuture Altair Smartwatch - Écran AMOLED - 1.32" - 260mAh | `variable` | `HIFUTURE-ALTAIR` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **18** | `hifuture-apex` | HiFuture Apex Smartwatch - Écran AMOLED - 2.04" - 350mAh | `variable` | `HIFUTURE-APEX` (+3 variantes) | ✅ PASS | ✅ INCLUS |
| **19** | `hifuture-aurora` | HiFuture Aurora Smartwatch - Écran AMOLED - 1.43" - 300mAh | `variable` | `HIFUTURE-AURORA` (+3 variantes) | ✅ PASS | ✅ INCLUS |

---
*Ce pipeline constitue la référence officielle V3.4 pour la marque HiFuture dans le workspace My-eStore.*
