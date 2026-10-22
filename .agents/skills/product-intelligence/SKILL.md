---
name: product-intelligence
description: Moteur de recherche et d'extraction certifiée des spécifications techniques pour les fiches produits JSON parents (Tech & Appliance). Source de vérité pour /generate-product-data et /produce-appliance.
---

# SKILL: Product Intelligence — Recherche & Génération de Fiches Produits JSON

Ce skill définit la procédure opérationnelle pour **rechercher, structurer et valider** des données produits Tech et Appliance sous forme de fichiers JSON standardisés. Il sert de **moteur d'exécution exclusif** pour le workflow `/generate-product-data`.

> [!CAUTION]
> **DIRECTIVE IMPÉRATIVE** : Ce skill est soumis à [`VERIFICATION_IMPERATIVE.md`](../../.agents/directives/VERIFICATION_IMPERATIVE.md). **AUCUNE donnée technique ne doit provenir de la mémoire interne de l'IA.** Les données d'entraînement sont systématiquement obsolètes, incomplètes ou erronées pour les specs produits, SKU et prix. Chaque champ technique DOIT être rempli à partir de résultats de recherche web en temps réel.

> **⚠️ RÈGLE D'OR** : Ce workflow est une **source de vérité** pour les données produits. Il ne génère ni HTML ni CSV. Il produit des fichiers JSON de référence qui peuvent être utilisés pour vérifier d'autres workflows ou comme base de données produit.

---

## Directives Fondamentales

### 0. Identité & Liaison Workflow

- Ce skill est **strictement dédié** au workflow `/generate-product-data`.
- **NE PAS** confondre avec les workflows `production-industrielle-v3` ou `produce-appliance` qui génèrent du HTML/CSV.
- **NE PAS** mélanger les schémas JSON de ce workflow avec les `Template_Pack_v3_*.json` existants.
- Les fichiers générés sont stockés dans `product-data/` (séparé de `products/` et `products-appliance/`).

### 1. Précision Absolue des Model Numbers (CRITIQUE)

- Le model number (SKU constructeur) est **le champ le plus important** du fichier JSON.
- **INTERDIT** : Inventer, deviner ou extrapoler un SKU depuis un modèle voisin.
- **OBLIGATOIRE** : Vérifier le SKU sur le site officiel du constructeur ou sur 2+ sources fiables.
- **EXEMPLES de confusions fréquentes** (SKU Internationaux vérifiés en Mai 2026) :
  - Samsung Galaxy S24 (`SM-S921B`) ≠ S24+ (`SM-S926B`) ≠ S24 Ultra (`SM-S928B`)
  - iPhone 16 (`A3287`) ≠ iPhone 16 Plus (`A3291`) ≠ iPhone 16 Pro (`A3294`) ≠ iPhone 16 Pro Max (`A3296`)
  - iPhone 17 (`A3520`) ≠ iPhone 17 Pro (`A3523`) ≠ iPhone 17 Pro Max (`A3526`)
  - Xiaomi Redmi Note 14 (`24108RN14G`) ≠ Redmi Note 14 Pro (`24108RN14PG`)
  - ⚠️ **ATTENTION** : Ces exemples peuvent devenir obsolètes. TOUJOURS re-vérifier via recherche web.
- Toujours renseigner le champ `disambiguation_notes` quand un risque de confusion existe.

### 2. Recherche Vérifiée & Sources — RECHERCHE WEB OBLIGATOIRE

> [!WARNING]
> **NE JAMAIS utiliser la mémoire IA comme source de données techniques.** Les modèles d'IA ont des données d'entraînement avec un décalage de plusieurs mois à années. Des produits peuvent avoir été renommés, des SKU réassignés, des specs modifiées depuis la date de cutoff.

- **Hiérarchie des sources** (par ordre de priorité) :
  1. 🥇 **Site officiel du constructeur** (samsung.com, apple.com, xiaomi.com...) — **OBLIGATOIRE en première intention**
  2. 🥈 Bases de données techniques (GSMArena, DeviceSpecifications, NotebookCheck, Kimovil)
  3. 🥉 Sites de vente locaux (Jumia CI, marchés ouest-africains)
  4. 4️⃣ Revendeurs internationaux (Amazon, AliExpress, B&H Photo)
  5. 5️⃣ Catalogues PDF constructeur / sous-distributeurs

- **Minimum 2 sources web distinctes** pour confirmer une donnée technique critique.
- **La mémoire IA ne compte PAS comme une source** — seules les recherches web en temps réel sont valides.
- **INTERDIT** : Sites de leaks, rumeurs, données non vérifiées, forums non modérés, données issues de la mémoire IA.
- **SI une donnée est introuvable** : Laisser le champ vide plutôt qu'inventer une valeur.

### 3. Pricing Local (Marché Côte d'Ivoire)

- **Source principale** : Jumia CI (jumia.ci), puis autres marketplaces ouest-africaines.
- **Format** : Fourchette de prix en FCFA (`market_price_range_fcfa.min` / `max`).
- **Plusieurs variantes** → Plusieurs prix (un par configuration RAM/Stockage).
- **Prix introuvable** : Renseigner `"price_source": "Non disponible localement"` plutôt que `null` silencieux.
- **Date du prix** : Toujours renseigner `price_date` au format `YYYY-MM`.

### 4. Gestion des Variantes (Résilience)

- Quand l'utilisateur mentionne une **série** (ex: "Samsung Galaxy S25"), le workflow DOIT :
  1. Énumérer TOUTES les variantes connues de la série
  2. Confirmer la liste avec l'utilisateur (ou traiter toutes en batch)
  3. Générer UN fichier JSON PAR variante
- Chaque variante a ses propres : SKU, configurations, prix, coloris.
- **INTERDIT** : Copier-coller les specs d'un modèle vers un autre modèle de la même série.

### 5. Zéro Placeholder, Zéro Hallucination

- Aucune valeur `""`, `"N/A"`, `"TBD"`, `"TODO"`, `"???"` n'est acceptée dans les champs obligatoires.
- Si une information n'est pas trouvée et qu'elle est optionnelle : **supprimer le champ** du JSON.
- Si une information n'est pas trouvée et qu'elle est obligatoire : **documenter l'absence** dans `generation_metadata.notes`.

---

## Procédure Opérationnelle (Pipeline)

### Stage 1 : Identification des Produits

**Objectif** : Transformer la demande utilisateur en une liste précise de produits à traiter.

1. **Parser la demande** :
   - "Samsung Galaxy S25" → Identifier la série S25
   - "iPhone 16 Pro" → Identifier un modèle spécifique
   - "Hisense réfrigérateurs" → Identifier une catégorie de marque

2. **Énumérer les variantes** :
   - Rechercher sur le site constructeur toutes les variantes de la série
   - Lister les model numbers officiels pour chaque variante
   - Documenter les différences clés entre variantes

3. **Confirmer le périmètre** (mode batch) :
   - Présenter la liste complète à l'utilisateur
   - Exemple : "J'ai identifié 4 variantes : S25 (SM-S931B), S25+ (SM-S936B), S25 Ultra (SM-S938B), S25 FE (SM-S72xB). Je procède avec les 4 ?"

4. **Sortie attendue** : Liste structurée `[{name, sku, category, sub_category}]`

### Stage 2 : Recherche Approfondie

**Objectif** : Collecter les données vérifiées pour chaque produit identifié.

1. **Recherche web systématique** (pour CHAQUE produit de la liste) :
   - `"[Nom exact du produit] specifications"` → Site constructeur + GSMArena
   - `"[SKU] fiche technique"` → Confirmation du SKU
   - `"[Nom du produit] prix Jumia Côte d'Ivoire"` → Prix local FCFA
   - `"[Nom du produit] coloris disponibles"` → Palette de couleurs

2. **Extraction des données** :
   - Spécifications techniques complètes
   - Configurations disponibles (RAM × Stockage pour tech, Capacité × Puissance pour appliance)
   - Coloris standard et exclusifs
   - Prix par configuration et par source
   - Model numbers régionaux si pertinent

3. **Cross-validation** :
   - Chaque donnée technique critique doit apparaître dans 2+ sources
   - Si une donnée ne peut être confirmée, ajouter `"confidence_level": "low"` dans les metadata
   - Comparer les prix entre sources pour établir une fourchette réaliste

4. **Sortie attendue** : Notes de recherche brutes (mentales, pas de fichier intermédiaire)

### Stage 3 : Assemblage du JSON

**Objectif** : Structurer les données dans le schéma JSON standardisé.

1. **Charger le bon template** selon le type de produit :
   - Tech → `Templates/Template_ProductData_tech.json`
   - Appliance → `Templates/Template_ProductData_appliance.json`

2. **Remplir les sections** dans l'ordre :
   - `product_identity` → Identité commerciale et catégorisation
   - `model_numbers` → SKU primaire, variantes régionales, disambiguation
   - `variants` → Une entrée par configuration (RAM/Stockage ou Capacité)
   - `colors` → Standard, exclusifs, défaut
   - `key_specifications` → Données techniques vérifiées
   - `sources` → Toutes les sources consultées avec URLs et dates

3. **Remplir les métadonnées** :
   - `generation_metadata.generated_date` → Date du jour (YYYY-MM-DD)
   - `generation_metadata.confidence_level` → "high", "medium" ou "low"
   - `generation_metadata.batch_id` → Identifiant du batch si applicable

4. **Sauvegarder** dans le répertoire approprié :
   ```
   product-data/[brand-slug]/[series-slug]/product-data-[model-slug].json
   ```
   - Exemple : `product-data/samsung/galaxy-s25/product-data-s25-plus.json`

### Stage 4 : Validation Automatique

**Objectif** : Vérifier la conformité du JSON via le script de validation.

1. **Exécuter le script** :
   ```bash
   # Validation unitaire
   python scripts/tools/product_data/validate_product_data.py \
     --input "product-data/[brand]/[series]/product-data-[model].json"

   # Validation batch (toute la série)
   python scripts/tools/product_data/validate_product_data.py \
     --input "product-data/[brand]/[series]/" --batch
   ```

2. **Interpréter les résultats** :
   - 🔴 **FATAL** : Corriger immédiatement et re-valider
   - 🟡 **WARNING** : Corriger si possible, documenter si non

3. **Boucle de correction** :
   - Maximum 3 tentatives de correction
   - Si échec après 3 tentatives : escalader vers l'utilisateur
   - Toujours re-valider après chaque correction

### Stage 5 : Rapport de Production

**Objectif** : Notifier l'utilisateur du résultat final.

1. **Résumé par produit** :
   | Produit | SKU | Fichier | Statut | Confiance |
   |---------|-----|---------|--------|-----------|
   | Galaxy S25+ | SM-S936B | product-data-s25-plus.json | ✅ | high |

2. **Fichiers générés** : Lister les chemins complets
3. **Avertissements résiduels** : Lister les warnings non résolus
4. **Prochaine étape** : Indiquer que les fichiers sont prêts pour vérification manuelle ou comme source de référence

---

## Mapping des Catégories

Le fichier [`category_specs_map.json`](../../scripts/tools/product_data/category_specs_map.json) définit :
- Les champs de spécifications **obligatoires** et **optionnels** par catégorie
- Les **fourchettes de prix réalistes** en FCFA par catégorie
- Les **patterns regex** des model numbers par constructeur

### Catégories Tech supportées

| Catégorie | Template | Exemples |
|-----------|----------|----------|
| `smartphone` | tech | iPhone 17, Galaxy S25, Redmi Note 14 |
| `tablet` | tech | iPad Pro, Galaxy Tab S10, Xiaomi Pad 7 |
| `laptop` | tech | MacBook Pro, HP Pavilion, ThinkPad |
| `pc_desktop` | tech | iMac, HP ProDesk, Dell OptiPlex |
| `audio` | tech | AirPods Pro, Sony WH-1000XM5, JBL Flip |
| `wearable` | tech | Apple Watch, Galaxy Watch, Xiaomi Band |
| `storage` | tech | SSD Samsung 990 Pro, Clé USB SanDisk |
| `printer` | tech | HP LaserJet, Epson EcoTank, Canon PIXMA |
| `peripheral` | tech | Clavier Logitech, Souris Razer, Webcam |

### Catégories Appliance supportées

| Catégorie | Template | Exemples |
|-----------|----------|----------|
| `appliance_refrigerator` | appliance | Hisense RD-49DC, Beko RDNE |
| `appliance_washer` | appliance | Samsung WW80, Beko WTE |
| `appliance_cooker` | appliance | Unionaire C6060, Toshiba TS-698 |
| `appliance_ac` | appliance | Carrier 42KHL, TCL TAC |
| `appliance_tv` | appliance | Hisense 43A4K, TCL 55P745 |
| `appliance_small` | appliance | Philips GC1742, Galaxy Mixeur |
| `appliance_fan` | appliance | Toshiba F-LSD10, Nasco NAS-FD |
| `appliance_water` | appliance | Nasco WD-100, Hisense YLR |

---

## Quality Check Checklist

- [ ] **SKU Vérifié** : Le model number correspond exactement à celui du constructeur officiel
- [ ] **Zéro Confusion** : Les specs de ce produit ne sont PAS celles d'un modèle voisin
- [ ] **Variants Complets** : Chaque configuration (RAM/Stockage ou Capacité) a son entrée
- [ ] **Prix Documentés** : Au moins une source de prix renseignée par variante
- [ ] **Couleurs Listées** : Couleurs standard et exclusives identifiées
- [ ] **2+ Sources** : Minimum 2 sources distinctes avec URLs valides
- [ ] **Pas de Placeholder** : Aucun champ obligatoire avec valeur vide ou "N/A"
- [ ] **Date Renseignée** : `generated_date` et `price_date` remplis
- [ ] **Validation Script** : `validate_product_data.py` retourne exit code 0

---

## Outils et Ressources

| Outil | Chemin | Usage |
|-------|--------|-------|
| Template Tech | [`Templates/Template_ProductData_tech.json`](../../Templates/Template_ProductData_tech.json) | Schéma pour produits tech |
| Template Appliance | [`Templates/Template_ProductData_appliance.json`](../../Templates/Template_ProductData_appliance.json) | Schéma pour électroménager |
| Category Map | [`scripts/tools/product_data/category_specs_map.json`](../../scripts/tools/product_data/category_specs_map.json) | Mapping specs par catégorie |
| Validation Script | [`scripts/tools/product_data/validate_product_data.py`](../../scripts/tools/product_data/validate_product_data.py) | Validation automatique JSON |
| Orchestrateur | [`.agents/skill/orchestrateur_production/orchestrateur.md`](orchestrateur_production/orchestrateur.md) | Escalade en cas de blocage |

---

**Version** : 1.0
**Dernière mise à jour** : 09 Mai 2026
**Binding** : Workflow `/generate-product-data` exclusivement
