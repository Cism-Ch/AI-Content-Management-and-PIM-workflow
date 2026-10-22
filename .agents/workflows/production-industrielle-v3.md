---
description: '[V3.4 - Master Router] Point d''entrée du workflow de production industrielle My-eStore en version V3.4. Découplé en sous-workflows spécialisés par rôles (Parent-First Audit Gate).'
---

# 🚀 Workflow de Production Industrielle V3.4 (Master Router)

Ce document est le **point d'entrée et de routage** de notre chaîne de production. Il découple l'intelligence de conception de la rigueur technique grâce à des sous-workflows ciblés et à un **Gate d'Audit Qualité sur les Modèles Parents (Parent-First)** avant toute duplication.

> **RÈGLE D'OR** : L'IA ne génère JAMAIS de HTML. Elle remplit un moule JSON Parent. L'Audit Qualité valide le JSON Parent à 100% PASS avant la duplication des variantes et la compilation HTML par le script Python.

---

## 📋 Séquence de Production en 5 Étapes (V3.4)

### 🔗 Phase 0 : Recherche & Extraction (Modèles Parents)
*   **Action** : L'agent DOIT appliquer la directive constitutionnelle de recherche en temps réel : [`VERIFICATION_IMPERATIVE.md`](../directives/VERIFICATION_IMPERATIVE.md).
*   **1. Extraction & Création des JSON Parents** : Générer ou mettre à jour les fichiers JSON parents certified dans `product-data/[marque]/[marque]-[slug].json`.
*   **2. Cadrage des Déclinaisons Exclusives (`paired_variants`) (OBLIGATOIRE AVANT RÉDACTION)** :
    - Vérifier impérativement si les coloris et les configurations RAM/ROM sont couplés de manière exclusive (ex: RedMagic, Axon 60 Ultra, éditions spéciales).
    - Si oui, renseigner formellement le bloc `paired_variants` au niveau racine du JSON parent dès la Phase 0.
    - Synchroniser strictement les métadonnées parents (`Attribute 1, 2, 3 value(s)` dans `woocommerce_csv` et `key_specifications`).
    - *Il est formellement interdit d'engager la Phase A (rédaction) ou la Phase B (audit) sans avoir cadré ces déclinaisons.*
*   **3. Validation des Specs Factuelles (Zero Hallucination)** :
    ```bash
    python scripts/tools/product_data/validate_product_data.py --input "product-data/[marque]/[marque]-[slug].json"
    ```

### ✍️ Phase A : Rédaction Unitaire & Copywriting 3 Personas (Modèles Parents)
*   **Action** : Rédiger le contenu du JSON parent **modèle par modèle (rédaction unitaire)** en appliquant la chaîne séquentielle des **3 Personas** :
    1. **Persona 1 (Copywriter)** : Rédaction factuelle sans hyperbole, axée sur les bénéfices d'usage (0 superlatif).
    2. **Persona 2 (Expert SEO AIOSEO)** : Phrases ≤ 20 mots, **31% à 49% de mots de transition** (formule fixe 15/41 = 36.5%), word count 450-650 mots, orthographe `My-eStore`, meta titles normés, titre H1 Standard B Top Specs (`[MARQUE] [MODÈLE] : [Top Spec 1], [Top Spec 2] et [Top Spec 3]`), et **formule standard de 10 à 14 Tags enrichis** dans `woocommerce_csv.Tags` (Marque, Modèle, Série, Catégorie/OS, Réseau, Écran, Photo, Batterie, Chipset, Points forts, Abidjan, My-eStore — interdiction des tags restreints < 8 tags).
    3. **Persona 3 (Intégrateur V3.4)** : Structure JSON V3.4 avec `full_specs` dans `long_description` au-dessus de `cta`, bloc CTA 2 boutons (Bouton 1 : `top_link` `#` / `"Remonter pour commander"`, Bouton 2 : `boutiques_link` `"https://my-estore.com/boutiques-officielles/"` / `"Nos Boutiques Officielles"`), 3 liens sources neutres, et ordre des 5 attributs normé (Attr 1=Couleur, Attr 2=Stockage, Attr 3=RAM, Attr 4=Processeur [PC], Attr 5=Réseau).

### 🔍 Phase B : Audit Qualité QA sur Modèles Parents (GATE BLOQUANT PARENT)
> **⚠️ RÈGLE DE SÉCURITÉ V3.4** : L'audit de structure JSON V3.4, l'audit AIOSEO, la validation des specs factuelles, la cohérence des déclinaisons `paired_variants` et la remédiation d'hyperboles s'exécutent IMPÉRATIVEMENT en lot (Batch) sur l'ensemble des JSON Parents (`product-data/`) AVANT TOUTE DUPLICATION.
*   **Audit de Structure JSON Parents V3.4 (Test Structurel Approfondi Obligatoire)** :
    ```bash
    python scripts/tools/product_data/audit_json_structure.py --dir "product-data/[marque]"
    ```
*   **Audit AIOSEO & Lisibilité par Lot (Batch)** :
    ```bash
    python scripts/tools/data_processing/audit_batch_aioseo.py --dir "product-data/[marque]"
    ```
*   **Audit de Structure, Specs Factuelles & Paired Variants par Lot (Batch)** :
    ```bash
    python scripts/tools/product_data/validate_product_data.py --input "product-data/[marque]" --batch
    ```
*   **Assainissement des Hyperboles par Lot (Batch)** :
    ```bash
    python scripts/tools/data_processing/copywriting_remediation.py detect --products-dir "product-data/[marque]" --output "hyperboles-[marque].md"
    python scripts/tools/data_processing/copywriting_remediation.py rewrite --products-dir "product-data/[marque]"
    ```
*   *Seuls les JSON Parents ayant obtenu le statut **100% PASS** sur l'ensemble de la suite d'audits sont autorisés à passer en Phase C.*

### ⚙️ Phase C : Compilation HTML du Modèle Parent (Sans Duplication Physique)
> **💡 STRATÉGIE PARENT-ENFANT (V3.4)** : La duplication de sous-dossiers physiques par variante est **désactivée**. La compilation HTML s'exécute directement sur le modèle parent unique.
*   **Compilation HTML Parent** :
    ```bash
    python scripts/build-product-pack-v3.py --data "products/[serie-all]/[slug]/pack-data-[slug].json" --outdir "products/[serie-all]/[slug]" --modele "[slug]" --serie "[serie-all]" --skip-validation
    ```
    * Génère `short-[slug].html` et `long-[slug].html` dans le dossier produit parent `products/[serie-all]/[slug]/`.

### 📊 Phase D : Export CSV WooCommerce & Génération des Déclinaisons Parent-Enfant
*   **Génération Directe du CSV Consolidé (Parent + Variations)** :
    Lancer le script de compilation du catalogue (ex: `rebuild_[marque]_catalog.py` ou `propagate_variants_and_compile_csv.py`) qui lit les JSON parents et génère automatiquement dans `import-v2-[serie-all].csv` :
    - **1 Ligne Parent (`Type=variable`)** : Contient le SKU Parent (`[MARQUE]-[SLUG]`), le titre vendeur enrichi, les descriptions HTML complètes, et la liste globale des couleurs (`Attribute 1 value(s)`).
    - **N Lignes Enfants (`Type=variation`)** : Rattachées au SKU Parent via le champ `Parent`, portant chacune leur couleur spécifique (`Attribute 1 value(s)`), leur SKU unique (`[MARQUE]-[SLUG]-[COULEUR]`), le stock et le prix.
*   **Validation Finale** : Valider l'unicité de 100% des SKUs et la présence du poids en kg (`Attribute 4`).

---

## 📁 Organisation des Fichiers

### 1. Rôles et Workflow
*   🚩 **Master Router** : [production-industrielle-v3.md](production-industrielle-v3.md)
*   ✍️ **Règles Rédaction** : [copywriting_rules_v3.md](sub_workflows/copywriting_rules_v3.md)
*   ⚙️ **Règles Compilation** : [build_remediation_rules_v3.md](sub_workflows/build_remediation_rules_v3.md)

### 2. Dossiers de Production
*   **Fiches Techniques Parents (Source de Vérité)** : [product-data/](../../../product-data/)
*   **Dossiers Déclinaisons Variantes & HTML** : [products/](../../../products/) (regroupés par `[serie-all]/[variante]`)
