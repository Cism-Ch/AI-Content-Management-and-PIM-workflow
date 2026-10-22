---
description: "Workflow Agent QA (Checker). Réalise un audit qualité strict des fiches JSON parents ou variantes et exécute les scripts de validation Python."
---

# 🕵️ Workflow Assurance Qualité (`/audit-product-pack`)

Ce workflow définit le comportement de l'Agent QA. Son rôle est d'agir comme un **inspecteur intransigeant** (Checker) qui vérifie le travail des agents rédacteurs (Makers). 

> **💡 NORME V3.4 (Parent-First)** : L'audit QA doit prioritairement s'exécuter sur les **JSON Parents** (dossier `product-data/`) AVANT la duplication vers les dossiers de variantes physiques (`products/`).

---

## 🚀 Invocation
```
/audit-product-pack [Chemin_du_fichier_JSON_ou_Dossier]
```
*(Ex: `/audit-product-pack product-data/blackview/blackview-a53-pro.json`)*

---

## 🎯 Processus d'Audit (4 Étapes)

### Étape 1 : Vérification Éditoriale et SEO (JSON Parent)
1. Lire le `pack-data-[model].json` du modèle parent dans `product-data/`.
2. Appliquer rigoureusement la checklist du skill `content-quality-validator` :
   - **Formule Meta Title Top Specs** : `Acheter [MARQUE] [MODÈLE] ([RAM]/[ROM]) à Abidjan | My-eStore` (short) et `[MARQUE] [MODÈLE] [ROM] : [Top Spec 1] & [Top Spec 2] | My-eStore` (long). Interdiction formelle du titre générique *"Fiche Technique et Spécifications"*.
   - **Taux de Mots de Transition (AIOSEO)** : Strictement **> 30% et < 50%** (cible optimale 36.5%, soit 15 phrases sur 41).
   - **Orthographe Enseigne** : Écriture exacte **`My-eStore`** (en un mot, sans espace).
   - **Présence LSI** : Minimum 10 mots-clés LSI transactionnels.
   - **Confirmation Obligatoire des Déclinaisons (`paired_variants`) [GATE BLOQUANT]** : Le Gate QA doit impérativement confirmer la présence, la validité et la conformité matérielle du bloc `paired_variants` au niveau racine du JSON parent. Vérifier qu'aucune variation fantôme n'est possible, que chaque SKU suffix est unique, et que les valeurs d'attributs WooCommerce (`Attribute 1, 2, 3`) sont strictement synchronisées avec cette liste. En cas d'absence ou de discordance sur des modèles multi-variantes, statut **FAIL immédiat**.
   - **Formule Enrichie des Tags WooCommerce (10 à 14 Tags)** : Vérifier que `woocommerce_csv.Tags` comporte entre 10 et 14 tags précis et dédoublonnés intégrant les Top Specs matérielles, la typologie, et les tags obligatoires `Abidjan` et `My-eStore` (statut FAIL si tags squelettiques < 8 tags ou tags obligatoires absents).
   - **Fluff & Exagérations** : Proscription absolue des superlatifs ("ultime", "révolutionnaire", "parfait", "exceptionnel", "inégalé").

### Étape 2 : Exécution des Tests Python (Audit QA par Batch)
1. Lancer la suite d'audits en lot (batch) sur l'ensemble du dossier de JSON parents :
   ```bash
   # 1. Audit Approfondi de la Structure JSON Parents V3.4 (Test Structurel Obligatoire)
   python scripts/tools/product_data/audit_json_structure.py --dir "product-data/[marque]"

   # 2. Audit AIOSEO & Lisibilité par Lot
   python scripts/tools/data_processing/audit_batch_aioseo.py --dir "product-data/[marque]"

   # 3. Audit de Structure & Specs Factuelles
   python scripts/tools/product_data/validate_product_data.py --input "product-data/[marque]" --batch

   # 4. Détection des Hyperboles par Lot
   python scripts/copywriting_remediation.py detect --products-dir "product-data/[marque]"
   ```

### Étape 3 : Routage des Erreurs (Maker/Checker)
- **Cas 1 (Erreur Éditoriale, AIOSEO ou Structure V3.4)** : Le QA génère un rapport **FAIL**, cite les phrases ou clés non conformes, et **renvoie le JSON parent au Maker** pour réécriture.
- **Cas 2 (Plantage Script Python)** : Le QA invoque le Spécialiste : `/script-specialist [Nom_du_script]`.

### Étape 4 : Validation Finale & Autorisation de Duplication
- Lorsque toutes les vérifications sont au vert (100% PASS), le QA émet un **PASS** et autorise la duplication du JSON Parent vers la chaîne de déclinaison des variantes.
