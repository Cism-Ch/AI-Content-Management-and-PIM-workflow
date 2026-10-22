---
name: build_remediation_rules_v3
description: "[V3.4 - Rôle Technique] Instructions de compilation V3.4, gestion des déclinaisons paired_variants, prix FCFA et build CSV WooCommerce."
---

# ⚙️ Sous-Workflow : Technique, Build & Compilation CSV (Norme V3.4)

Ce document rassemble les instructions pour le **Spécialiste Script & Build Technique**. Il régit l'exécution des outils de compilation et la génération des exports CSV WooCommerce sous la norme **V3.4 Parent-First**.

*   **Lien vers le Master Router** : [production-industrielle-v3.md](../production-industrielle-v3.md)
*   **Compilateur Maître** : [build-product-pack-v3.py](../../../scripts/build-product-pack-v3.py)
*   **Répertoire des Tarifs FCFA** : [Pricing/](../../../Pricing/)

---

## 1. Principe Fondamental V3.4 : Parent-First & Paired Variants

> [!IMPORTANT]
> **Interdiction Formelle du Produit Cartésien Aveugle** :
> Les anciennes approches combinatoires ($N \text{ Couleurs} \times M \text{ RAM} \times P \text{ ROM}$) sont formellement proscrites car elles créent des variations fantômes inexistantes chez le fabricant.
> Toutes les déclinaisons matérielles d'un produit sont déclarées dès la création du modèle parent via le tableau **`paired_variants`** :

```json
"paired_variants": [
    {
        "color_fr": "Noir",
        "color_en": "Obsidian Black",
        "color_code": "NOIR",
        "ram": "12 Go",
        "storage": "512 Go",
        "price": "550000",
        "sku_suffix": "512GB-12GB-NOIR"
    }
]
```

---

## 2. Compilation HTML du Modèle Parent (Sans Duplication Physique)

Sous la norme V3.4, la création de sous-dossiers physiques individuels par variante est **désactivée**. La compilation HTML s'exécute directement sur le modèle parent :

```bash
python scripts/build-product-pack-v3.py \
  --data "product-data/[marque]/[slug].json" \
  --outdir "products/[slug]" \
  --modele "[slug]" \
  --skip-validation
```

Ce script génère les fichiers `long-[slug].html` et `short-[slug].html` directement à partir des données validées du parent.

---

## 3. Génération du CSV WooCommerce Hiérarchisé (Parent-Enfant)

L'export CSV consolidé est généré via les scripts de catalogue (ex: `rebuild_[marque]_catalog.py` ou `propagate_variants_and_compile_csv.py`) :

1. **Ligne Parent (`Type = variable`)** :
   * Porte le SKU Parent : `[MARQUE]-[SLUG]`
   * Contient la description longue complète avec son tableau `full_specs` et la description courte.
   * Agrège l'ensemble des valeurs autorisées pour les attributs dans `Attribute 1 value(s)` (Couleur), `Attribute 2 value(s)` (Stockage), `Attribute 3 value(s)` (RAM).
2. **N Lignes Enfants (`Type = variation`)** :
   * Chaque ligne enfant est rattachée au SKU Parent via la colonne `Parent`.
   * SKU Enfant déterministe : `[MARQUE]-[SLUG]-[ROM]-[RAM]-[COULEUR]`.
   * Valeurs d'attributs individuelles (`Attribute 1 value(s) = Couleur`, etc.).
   * Prix en Francs CFA (FCFA) calibré depuis la grille [Pricing/](../../../Pricing/).
   * Statut du stock : `In stock` avec quantité par défaut (50).
3. **Poids Normalisé en Kilogrammes (`Attribute 4`)** :
   * Injecté sous `Attribute 4 name = "Poids"`, `Attribute 4 value(s) = "{poids} kg"`.
   * Obligatoirement numérique et réaliste (rejet automatique de tout poids aberrant).

---

## 4. Réconciliation Déterministe des Identifiants Store

Avant tout import sur une boutique en production, lancer le script de liaison pour préserver l'historique SEO et éviter les doublons :

```bash
python scripts/link_store_ids_v3.4.py --csv "products/import-v2-[marque].csv"
```
Ce script applique un matching à 4 niveaux (SKU exact, Modèle + ROM + Couleur, remédiation ancienne, réinjection d'ID).
