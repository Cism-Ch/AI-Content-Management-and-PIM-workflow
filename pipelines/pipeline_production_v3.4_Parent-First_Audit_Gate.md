# 🚀 Pipeline de Production Industrielle V3.4 (Parent-First Audit Gate)

Ce pipeline standardise le processus de création, d'audit, de duplication et de compilation de fiches produits pour WooCommerce. Il est réutilisable pour n'importe quelle marque de High-Tech ou d'Électroménager.

---

## 📋 Pré-requis et Structure des Fichiers

Avant de démarrer la production d'une marque, s'assurer de disposer de la structure suivante :
1. **Fichier Source de Vérité** : Un fichier CSV nommé `[marque]_models_parent.csv` situé dans `products/[marque]-all/` répertoriant les modèles officiels avec leurs caractéristiques :
   * `model_slug`, `commercial_name`, `category`, `ram&rom_options`, `official_colors_fr`, `official_battery`, `official_weight`, `official_dimensions`, `official_screen_size`, `official_source_url`.
2. **Dossier de Stockage JSON** : `product-data/[marque]/` pour stocker les fichiers de configuration parents certifiés.
3. **Dossier de Sortie** : `products/[marque]-all/` pour générer les déclinaisons et fichiers d'importation.

---

## 🛠️ Étapes du Pipeline de Production

### Étape 1 : Sourcing Web en Direct & Création du Fichier Parent (JSON)
Extraire en temps réel (via recherche Web en direct `search_web` sur les sites officiels constructeurs et fiches distributeurs agréées) les données techniques officielles du produit et créer le fichier parent :
📂 `product-data/[marque]/[marque]-[slug].json`

S'assurer que :
* **Règle Stricte des 3 Liens Sources** :
  - **Source 1** : `"[MARQUE] Official Store"` -> Lien officiel du constructeur (`https://[official_store]/products/[slug]`).
  - **Source 2** : `"Recherche Générique"` -> `https://www.google.com/search?q=[MARQUE]+[MODELE]`.
  - **Source 3** : `"Recherche Spécialisée IA"` -> `https://www.google.com/search?q=[MARQUE]+[MODELE]+specifications`.
  - (Aucune URL vers un site de test tiers ou concurrent ne doit figurer dans les liens sortants des JSON ou HTML).
* **Noms de Couleurs Certifiées (`official_colors_fr` & `official_colors_en`)** : 
  - Conserver fidèlement les dénominations officielles du constructeur documentées dans `[marque]_models_parent.csv` (`official_colors_fr`: ex: `Noir, Blanc, Bleu, Rose`, `Noir, Silver`, `Or, Silver, Noir`).
  - Générer les suffixes des SKUs des variantes en majuscules ASCII normalisées d'après les termes certifiés (`BLACK`->`NOIR`, `WHITE`->`BLANC`, `SILVER`, `TITANIUM`, etc.).
* Le tableau `full_specs` (ou `full_specs_table`) est imbriqué **à l'intérieur de `long_description`**, immédiatement au-dessus de la clé `cta`.
* Le bloc `cta` est configuré avec les 2 boutons d'action officiels :
  - `top_link`: `"#"` | `top_label`: `"Remonter pour commander"`
  - `boutiques_link`: `"https://my-estore.com/boutiques-officielles/"` | `boutiques_label`: `"Nos Boutiques Officielles"`
* Le bloc `woocommerce_csv` contient les attributs standard ordonnés selon la norme V3.4 :
  - `Stock`: `"10"` (Valeur de stock par défaut fixée à 10 unités par déclinaison).
  - `Attribute 1 name`: `"Couleur"` (ou `"Color"`)
  - `Attribute 2 name`: `"Stockage"`
  - `Attribute 3 name`: `"RAM"`
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
    👉 `Acheter [MARQUE] [MODÈLE] ([RAM]/[ROM]) à Abidjan | My-eStore`
  * Dans `long_description.seo.meta_title` (Top Spécifications) :
    👉 `[MARQUE] [MODÈLE] [ROM] : [Top Spec 1] & [Top Spec 2] | My-eStore`

#### ⚙️ Intégrateur & Auditeur (Persona 3)
* Valider que les SKUs des variantes respecteront le format standard : `[MARQUE]-[MODELE]-SKU`.

---

### Étape 3 : Audit de Qualité & Conformité (Gate QA sur Parent)
Exécuter impérativement les scripts d'audit AIOSEO et de conformité des spécifications sur la fiche parent avant toute duplication ou compilation :
```bash
python scripts/tools/product_data/validate_product_data.py --input "product-data/[marque]/[marque]-[slug].json"
python scripts/tools/data_processing/audit_aioseo_sentences.py "products/[marque]-all/[folder]/pack-data-[slug].json"
```
* **Contrôles de l'Audit Gate** :
  1. Validation ProductData à 0 erreur (au moins 2 sources URLs profondes réelles documentées).
  2. Contexte éditorial sans hyperbole, 0 phrase > 20 mots, et score de transition AIOSEO exact de 36.5%.
  3. Présence obligatoire du poids technique.
* **Si un test échoue** : Corriger immédiatement le JSON parent et relancer les audits jusqu'à obtenir le statut **PASS**.

---

### Étape 4 : Compilation HTML sur Modèle Parent Unique (Sans Duplication Physique)
* **Duplication Physique Désactivée** : La création de sous-dossiers physiques par variante est désactivée.
* **Compilation HTML Directe** : Générer les descriptions HTML sur le modèle parent unique :
  ```bash
  python scripts/build-product-pack-v2.py --data "products/[marque]-all/[slug]/pack-data-[slug].json" --outdir "products/[marque]-all/[slug]" --modele [slug] --serie [marque]-all --skip-validation
  ```
  * Génère `short-[slug].html` et `long-[slug].html` dans le dossier parent `products/[marque]-all/[slug]/`.

---

### Étape 5 : Consolidation du CSV WooCommerce Global (Génération Parent-Enfant)
Compiler l'ensemble du catalogue de la marque en générant directement les relations **Parent-Enfant (Variable + Variations)** dans le CSV final :
```bash
python scripts/rebuild_[marque]_catalog.py
# ou
python scripts/tools/data_processing/propagate_variants_and_compile_csv.py
```
* **Structure des Lignes générées dans `import-v2-[marque]-all.csv`** :
  - **Ligne Parent (`Type=variable`)** : Contient le SKU Parent (`[MARQUE]-[SLUG]`), le titre vendeur enrichi avec Top Specs, les descriptions HTML complètes, et la liste de toutes les couleurs (`Attribute 1 value(s)`: ex `"Noir, Blanc, Bleu"`).
  - **Lignes Enfants (`Type=variation`)** : Rattachées au SKU Parent via le champ `Parent`, portant chacune leur couleur spécifique (`Attribute 1 value(s)`: ex `"Noir"`), leur SKU unique (`[MARQUE]-[SLUG]-[COULEUR]`), le stock et le prix.

📂 **Emplacement du CSV Final** : `products/[marque]-all/import-v2-[marque]-all.csv`

