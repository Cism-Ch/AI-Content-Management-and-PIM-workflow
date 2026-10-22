# 🛠️ Pipeline de Mise à Jour & Harmonisation des Catégories Store (V3.4)

Ce document constitue le **guide opérationnel officiel** pour harmoniser l'ensemble des catégories WooCommerce du catalogue Usine V3.4 sur l'arborescence officielle du store ([Categories_produits_du_store.csv](file:///c:/Users/My-eStore-PC2/My-eStore-workspace/wordpress/Categories_produits_du_store.csv)).

---

## 📌 1. Objectif & Principes Techniques

Afin d'éviter la création de catégories doublons ou d'arborescences non désirées lors de l'importation WooCommerce, **tous les produits usine V3.4 doivent impérativement réutiliser les catégories exactes préexistantes sur le store**.

### 💡 Fonctionnement de l'Importation WooCommerce CSV
1. **Hiérarchie avec `>`** : `Parent > Enfant > Petit-Enfant` indique l'arborescence exacte de la catégorie.
2. **Virgule `,` = Attribution Multiple** : Sépare les différentes catégories attribuées au même produit (ex: `Audio & Hi-fi > Enceintes Connectées & Bluetooth, Audio & Hi-fi`).
3. **Recherche par Chaîne de Caractères** : WooCommerce compare le texte exact. Si la catégorie existe déjà sur le site, il coche la case existante **sans créer de nouvelle catégorie**.

---

## 📂 2. Entrées et Fichiers Requis

| Rôle | Fichier / Chemin | Description |
| :--- | :--- | :--- |
| **Source Officielle Store** | `Categories_produits_du_store.csv` | Liste complète des catégories existantes sur WooCommerce. |
| **Modèles Parents** | `products/[marque]-all/[marque]_models_parent.csv` | Source de vérité des slugs et types de produits. |
| **JSONs Parents** | `product-data/[marque]/[marque]-*.json` | Fichiers JSON sources V3.4. |
| **JSONs Déclinaisons** | `products/[marque]-all/[variant]/pack-data-*.json` | Données de chaque variante physique. |
| **Master Import CSV** | `products/[marque]-all/import-v2-[marque]-all.csv` | Fichier d'importation global consolidé. |

---

## ⚙️ 3. Cartographie Officielle des Catégories par Famille

### 📱 3.1 Smartphones (par Séries d'Origine)
* **Série A** : `Smartphones > Blackview > A Series, Smartphones > Blackview, Smartphones`
* **Série BL** : `Smartphones > Blackview > BL Series, Smartphones > Blackview, Smartphones`
* **Série BV** : `Smartphones > Blackview > BV Series, Smartphones > Blackview, Smartphones`
* **Série Color** : `Smartphones > Blackview > Color Series, Smartphones > Blackview, Smartphones`
* **Série Fort** : `Smartphones > Blackview > Fort Series, Smartphones > Blackview, Smartphones`
* **Série Hero** : `Smartphones > Blackview > Hero Series, Smartphones > Blackview, Smartphones`
* **Série Rock** : `Smartphones > Blackview > Rock Series, Smartphones > Blackview, Smartphones`
* **Série Shark** : `Smartphones > Blackview > Shark Series, Smartphones > Blackview, Smartphones`
* **Série Wave** : `Smartphones > Blackview > Wave Series, Smartphones > Blackview, Smartphones`
* **Série Xplore** : `Smartphones > Blackview > Xplore Series, Smartphones > Blackview, Smartphones`
* **Série Zeno** : `Smartphones > Blackview > Zeno Series, Smartphones > Blackview, Smartphones`

### 📱 3.2 Tablettes (par Séries d'Origine)
* **Série Active** : `Tablettes > Blackview > Active Series, Tablettes > Blackview, Tablettes`
* **Série Link** : `Tablettes > Blackview > Link Series, Tablettes > Blackview, Tablettes`
* **Série Mega** : `Tablettes > Blackview > Mega Series, Tablettes > Blackview, Tablettes`
* **Série Tab** : `Tablettes > Blackview > Tab Series, Tablettes > Blackview, Tablettes`
* **Série Zeno Tablette** : `Tablettes > Blackview > Zeno Series, Tablettes > Blackview, Tablettes`

### 💻 3.3 Informatique & Périphériques
* **Mini PC** : `Matériels Informatique & Bureautique > Ordinateurs Portable > Mini PC, Matériels Informatique & Bureautique > Ordinateurs Portable, Matériels Informatique & Bureautique`
* **Laptops** : `Matériels Informatique & Bureautique > Ordinateurs Portable, Matériels Informatique & Bureautique`
* **Moniteurs Portables** : `Matériels Informatique & Bureautique > Moniteurs Portable, Matériels Informatique & Bureautique`
* **Claviers** : `Matériels Informatique & Bureautique > Clavier & Souris, Matériels Informatique & Bureautique`

### ⌚ 3.4 Wearables & Audio
* **Smartwatches** : `Objets Connectés & Wearables > Montres connectées > Blackview Smartwatches, Objets Connectés & Wearables > Montres connectées, Objets Connectés & Wearables`
* **Lunettes Connectées** : `Objets Connectés & Wearables > Lunettes Connectées, Objets Connectés & Wearables`
* **Écouteurs Sans Fil** : `Audio & Hi-fi > Ecouteurs Sans Fil & Ecouteurs Filaire, Audio & Hi-fi`
* **Enceintes Bluetooth** : `Audio & Hi-fi > Enceintes Connectées & Bluetooth, Audio & Hi-fi`

---

## 🚀 4. Exécution du Script d'Harmonisation

La mise à jour tripartite (JSONs Parents + JSONs Déclinaisons + Master CSV) s'exécute avec la commande :

```bash
python scripts/tools/data_processing/patch_store_categories.py
```

### 📋 Sortie Console Attendue :

```text
=======================================================
  MISE À JOUR DES CATÉGORIES WOOCOMMERCE STORE (V3.4)
=======================================================

[*] 83 modèles parents cartographiés sur les catégories officielles du store.
[*] 83 fichiers JSON parents mis à jour.
[*] 261 fichiers JSON de déclinaisons mis à jour.
[*] 261 / 261 lignes du CSV master mis à jour.

=======================================================
  RÉSULTAT DE LA MISE À JOUR DES CATÉGORIES STORE
=======================================================
  JSONs Parents Mises à Jour      : 83
  JSONs Déclinaisons Mises à Jour  : 261
  CSV Master Lignes Mises à Jour  : 261 / 261
=======================================================
```

---

## ✅ 5. Points de Contrôle QA & Validation

1. **100% de Taux de Couverture** : Les 83 JSONs parents et 261 déclinaisons CSV doivent être mis à jour sans omission.
2. **Vérification Post-Traitement** : Après exécution de `patch_store_categories.py`, ré-exécuter systématiquement :
   - `patch_confirmed_prices.py` (pour garantir les tarifs confirmés Jumia).
   - `link_store_ids_v3.4.py` (pour garantir l'unicité stricte des ID WooCommerce store).
