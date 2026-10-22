# 🛠️ Pipeline de Liaison et Réconciliation des ID WooCommerce Store & Usine V3.4

Ce document constitue le **guide opérationnel officiel** pour lier, réconcilier et synchroniser de façon déterministe les `ID` WooCommerce d'un store en production avec un catalogue d'import usine certifié **V3.4**.

---

## 📌 1. Objectif & Enjeux Stratégiques

Lorsqu'un catalogue produit existe déjà sur WooCommerce avec des variations potentiellement corrompues ou des SKUs désynchronisés, **l'importation directe sans `ID` crée des doublons**.

Ce pipeline résout ce problème en :
1. **Attribuant les `ID` du store** aux déclinaisons usine certifiées V3.4.
2. **Garantissant l'unicité stricte (0 doublon d'ID)** sur tout le catalogue.
3. **Remédiant aux anciennes variantes corrompues** sur le store en écrasant leurs données par les fiches certifiées V3.4 (textes AIOSEO sans hyperbole, spécifications certifiées, prix confirmés Jumia).
4. **Laissant les `ID` vides (`""`)** pour les déclinaisons totalement nouvelles afin que WooCommerce les crée proprement.
5. **Propagant les `ID`** à la fois dans le CSV global et dans chaque fichier JSON de déclinaison (`pack-data-*.json`).

---

## 📂 2. Entrées et Fichiers Requis

| Rôle | Fichier / Chemin | Description |
| :--- | :--- | :--- |
| **Export Store WooCommerce** | `products/[marque]-all/Blackview-product-export-from-wc-[date].csv` | Export d'origine avec colonnes `ID`, `UGS`, `Nom`. |
| **Master CSV Usine V3.4** | `products/[marque]-all/import-v2-[marque]-all.csv` | Fichier consolidé de 261 variantes certifiées V3.4. |
| **Modèles Parents** | `products/[marque]-all/[marque]_models_parent.csv` | Source de vérité des slugs modèles parents. |
| **Packs JSON Déclinaisons** | `products/[marque]-all/[variant_slug]/pack-data-*.json` | Données locales de chaque déclinaison. |

---

## ⚙️ 3. Algorithme de Liaison à 4 Niveaux de Détection

L'opération repose sur l'exécution du script `scripts/tools/data_processing/link_store_ids_v3.4.py` qui applique un matching multi-critères :

```
[Store Row Export] ──> [Niveau 1: Match Exact SKU/UGS]
                            ↓ (si non trouvé)
                         [Niveau 2: Match Strict Modèle + ROM + Couleur]
                            ↓ (si non trouvé)
                         [Niveau 3: Fallback Remédiation Erreurs Store]
                            ↓ (si non trouvé)
                         [Niveau 4: Contrôle d'Unicité & Propagation JSON]
```

### 🔹 Niveau 1 : Match Exact / Normalisé sur SKU/UGS
- Nettoyage des préfixes (`BV-`, `BLACKVIEW-`, `-4G-`, `-5G-`).
- Si `m_norm_sku == s_norm_ugs` ➔ **Association immédiate de l'ID**.

### 🔹 Niveau 2 : Match Strict par Modèle + ROM + Couleur (Bilingue EN/FR)
- Extraction du slug modèle parent le plus long correspondant.
- Extraction de la ROM/Stockage (`64 Go`, `128 Go`, `256 Go`, `512 Go`, `1 To`).
- Traduction de la couleur via dictionnaire bilingue :
  * `Blue` / `Sky Blue` / `Starry Blue` / `Galaxy Blue` ➔ `BLEU`
  * `Black` / `Midnight Black` / `Polar Night Black` ➔ `NOIR`
  * `Grey` / `Gray` / `Space Grey` ➔ `GRIS`
  * `White` ➔ `BLANC` | `Orange` ➔ `ORANGE` | `Green` ➔ `VERT`
  * `Yellow` / `Jaune` ➔ `JAUNE` | `Gold` / `Blaze Gold` ➔ `OR`
  * `Purple` / `Meteor Purple` ➔ `VIOLET` | `Pink` ➔ `ROSE` | `Silver` ➔ `ARGENT`
- Si Modèle + ROM + Couleur correspondent ➔ **Association de l'ID**.

### 🔹 Niveau 3 : Résolution des Erreurs/Décalages du Store (Fallback Modèle)
- Si l'ancienne variante du store comportait une ROM ou RAM erronée (ex: RAM virtuelle comptée comme physique), le script effectue un fallback par **Modèle + Couleur** pour réattribuer l'ID à la variante certifiée la plus proche.

### 🔹 Niveau 4 : Application, Unicité & Propagation JSON
- Écriture des `ID` dans `import-v2-[marque]-all.csv`.
- Écriture des `ID` dans chaque `pack-data-[variant].json` sous `woocommerce_csv.ID`.
- Contrôle de sécurité d'unicité : `len(assigned_ids) == len(set(assigned_ids))`.

---

## 🚀 4. Exécution du Pipeline

Pour exécuter la liaison sur n'importe quel catalogue de marque, lancer la commande suivante :

```bash
python scripts/tools/data_processing/link_store_ids_v3.4.py
```

### 📋 Sortie Console Attendue (Audit de Succès) :

```text
=======================================================
  LIAISON ET RESOLUTION DES ID WOOCOMMERCE STORE (V3.4)
=======================================================

[*] Export Store : 200 lignes avec ID WooCommerce
[*] Usine Certifiée : 261 déclinaisons V3.4

[Phase 1] Recherche de correspondances exactes par SKU...
   -> 3 correspondances trouvées en Phase 1.

[Phase 2] Match strict par Modèle + ROM + Couleur...
   -> 157 correspondances ajoutées en Phase 2.

[Phase 3] Résolution des variantes store corrompues (Fallback Modèle + Couleur)...
   -> 5 variantes corrompues remédiées en Phase 3.

[Phase 4] Application des ID sur le CSV Master et dans les JSONs de variantes...
=======================================================
  RÉSULTAT DE LA SYNCHRONISATION DES ID WOOCOMMERCE
=======================================================
  Total Lignes Master V3.4     : 261
  Produits Existants Liés (ID) : 165 / 200 du store
  Nouveaux Produits (ID Vide)  : 96
  Unicité Stricte des ID       : [OK] 100% UNIQUE (0 Doublon)
  Fichier Master CSV Mis à jour: products/blackview-all/import-v2-blackview-all.csv
=======================================================
```

---

## ✅ 5. Points de Contrôle QA & Validation Finale

1. **0 Doublon d'ID** : Le verdict `[OK] 100% UNIQUE (0 Doublon)` doit impérativement apparaître à la fin de l'exécution.
2. **Vérification du CSV Consolidé** : Les lignes des produits existants possèdent leur `ID` WooCommerce numérique, tandis que les nouveaux modèles (`Mega 12`, `Active 12 Pro`, `Table 10`, `Table 9`, etc.) conservent un `ID` vide `""`.
3. **Mise à Jour Intégrale WooCommerce** : Lors de l'import dans WooCommerce, cocher la case **"Mettre à jour les produits existants"**. WooCommerce utilisera la colonne `ID` pour écraser les anciennes fiches corrompues par le contenu certifié V3.4 sans créer de doublons.
