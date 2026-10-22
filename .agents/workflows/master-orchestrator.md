---
description: "Le Chef d'Atelier. Workflow maître (V3.4) qui orchestre l'ensemble de la chaîne de production : Data -> Rédaction Parents -> Audit Parents QA -> Duplication Variantes -> CSV."
---

# 👑 Workflow Master Orchestrator (V3.4 - `/master-orchestrator`)

Ce workflow est le **point d'entrée unique** de l'usine de production de My-eStore. L'Orchestrateur pilote les autres agents IA, gère les transferts de données entre eux, et s'assure que le **Gate d'Audit Qualité sur les Modèles Parents (Parent-First)** est strictement validé avant la duplication.

---

## 🚀 Invocation
```
/master-orchestrator [Nom de la série ou du produit]
```
*(Ex: `/master-orchestrator Blackview All`)*

---

## 🎯 Séquence d'Orchestration V3.4 (Parent-First)

### Étape 1 : Collecte des Données Brutes, Pré-check & Cadrage des Déclinaisons (L'Investigateur)
- L'Orchestrateur lance la collecte et vérification des spécifications parentes :
  `python scripts/tools/product_data/check_product_existence.py --product "[Produit]"`
- Il invoque l'Agent Data pour générer les fichiers JSON techniques parents certified dans `product-data/[marque]/`.
- **Règle d'Or préalable** : L'Investigateur DOIT obligatoirement identifier si les configurations matérielles sont dépendantes (couples spécifiques RAM/ROM/Couleurs). Si oui, il renseigne formellement le tableau `paired_variants` à la racine du JSON parent dès cette étape, et synchronise `Attribute 1, 2, 3` avant tout passage en rédaction.

### Étape 2 : Rédaction 3 Personas sur Modèles Parents (Les Makers)
- L'Orchestrateur confie la rédaction des JSON parents aux 3 personas séquentiels (Copywriter > SEO > Intégrateur V3.4).
- Il s'assure que le bloc `full_specs` est positionné dans `long_description` au-dessus de `cta`.

### Étape 3 : Audit Qualité QA sur Modèles Parents (Le Checker — GATE PARENT)
- Dès qu'un JSON parent est créé dans `product-data/`, l'Orchestrateur invoque l'Inspecteur : `/audit-product-pack product-data/[marque]/[parent_json]`.
- L'Inspecteur valide :
  1. Structure JSON Parents V3.4 (`audit_json_structure.py`).
  2. AIOSEO & Lisibilité (<20 mots/phrase, 31-49% transitions via `audit_batch_aioseo.py`).
  3. Zéro hyperbole (`copywriting_remediation.py`).
  4. Cohérence absolue des déclinaisons `paired_variants` avec les attributs WooCommerce parents.
- **Boucle de correction** : En cas d'échec, le Maker réécrit uniquement le JSON parent jusqu'à l'obtention du statut **100% PASS**.

### Étape 4 : Compilation HTML sur Modèle Parent (Sans Duplication Physique)
- La duplication vers des sous-dossiers physiques par variante est **désactivée**.
- L'Orchestrateur exécute la compilation HTML directement sur le modèle parent : `python scripts/build-product-pack-v3.py --data "products/[serie-all]/[slug]/pack-data-[slug].json" --outdir "products/[serie-all]/[slug]" --modele [slug] --serie [serie-all] --skip-validation`.

### Étape 5 : Export CSV WooCommerce & Génération Parent-Enfant
- L'Orchestrateur lance le script de compilation finale qui génère le CSV consolidé `import-v2-[serie-all].csv` avec les relations **Parent-Enfant (Ligne `variable` Parent + N Lignes `variation` Enfants)**.
- Validation de l'unicité de 100% des SKUs et de la présence du poids en kg dans `Attribute 4`.
