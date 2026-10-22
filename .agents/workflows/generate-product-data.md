---
description: "Workflow agentique de génération de fiches produits JSON vérifiées (Tech & Appliance). Mode batch supporté. Source de vérité pour les données produits."
---

# 🔍 Workflow Product Intelligence (`/generate-product-data`)

Ce workflow génère des **fichiers JSON de référence** contenant des données produits vérifiées et structurées. Il sert de **source de vérité** pour la vérification manuelle ou automatique des fiches produits.

> [!CAUTION]
> **DIRECTIVE IMPÉRATIVE** : Ce workflow est soumis à [`VERIFICATION_IMPERATIVE.md`](../../.agents/directives/VERIFICATION_IMPERATIVE.md). L'agent ne doit JAMAIS remplir un champ technique (SKU, specs, prix) depuis sa mémoire interne. Toute donnée technique DOIT provenir d'une **recherche web vérifiée en temps réel** vers les sites officiels des constructeurs. La base de connaissance IA est systématiquement obsolète pour les données produits.

> **⚠️ RÈGLE D'OR** : Ce workflow ne génère ni HTML, ni CSV. Il produit des fichiers JSON de données produits pures, stockés dans `product-data/`.

> **🔗 INDÉPENDANT** : Ce workflow est autonome et ne s'enchaîne PAS automatiquement avec les workflows `production-industrielle-v3` ou `produce-appliance`. Il peut être utilisé comme source de vérification.

---

## 📋 Prérequis

1. Initialiser le skill [`PRODUCT_INTELLIGENCE_SKILL.md`](../skills/product-intelligence/SKILL.md) — contient les règles opérationnelles complètes.
2. Les templates JSON sont dans [`Templates/`](../../Templates/) :
   - `Template_ProductData_tech.json` (smartphones, tablettes, PC, audio, wearables, stockage)
   - `Template_ProductData_appliance.json` (électroménager)

---

## 🚀 Invocation

```
/generate-product-data [Nom du produit ou de la série]
```

### Exemples

| Commande | Comportement |
|----------|-------------|
| `/generate-product-data Samsung Galaxy S25 Series` | Batch : identifie S25, S25+, S25 Ultra, S25 FE → 4 fichiers JSON |
| `/generate-product-data iPhone 16 Pro` | Unitaire : 1 fichier JSON pour le 16 Pro uniquement |
| `/generate-product-data Hisense réfrigérateurs 2024` | Batch : identifie tous les modèles de réfrigérateurs Hisense 2024 |
| `/generate-product-data Oraimo SmartWatch` | Batch : identifie les variantes de montres Oraimo |

---

## 🎯 Pipeline (5 Stages)

### Stage 1 : Identification & Énumération

1. **Analyser la demande** pour identifier le(s) produit(s) cible(s).
2. **Vérifier l'existence en ligne (Gate 0)** : Pour chaque produit ou variante demandée, exécuter le script de vérification :
   ```bash
   python scripts/tools/product_data/check_product_existence.py --product "[Nom du produit]" --color "[Coloris]" --category "[Catégorie]"
   ```
   *Si la vérification en ligne échoue (ex: configuration de stockage, RAM, connectivité ou coloris introuvable), stopper le processus et demander confirmation à l'utilisateur.*
3. **Rechercher les variantes** de la série sur le site constructeur.
4. **Lister les model numbers** (SKU) pour chaque variante identifiée.
5. **Présenter la liste** à l'utilisateur pour confirmation en mode batch :
   ```
   📋 Variantes identifiées pour Samsung Galaxy S25 :
   1. Galaxy S25       → SM-S931B
   2. Galaxy S25+      → SM-S936B  
   3. Galaxy S25 Ultra → SM-S938B
   4. Galaxy S25 FE    → SM-S72xB (à confirmer)
   
   ▶ Je procède avec les 4 variantes ?
   ```
6. **Valider** : Chaque produit doit avoir un SKU et une existence confirmés avant de passer au Stage 2.

> **🛡️ RÉSILIENCE** : Si plusieurs produits portent des noms similaires (ex: Redmi Note 14 / 14 Pro / 14 Pro+ / 14 Pro Max), TOUJOURS les distinguer par leur SKU officiel. Documenter les risques de confusion dans `disambiguation_notes`.

---

### Stage 2 : Recherche Approfondie — VÉRIFICATION WEB OBLIGATOIRE

> [!WARNING]
> **RAPPEL CRITIQUE** : La mémoire interne de l'IA est INSUFFISANTE pour cette étape. Les données d'entraînement sont souvent obsolètes, incomplètes ou erronées (cf. incident SKU iPhone Mai 2026). Chaque champ ci-dessous DOIT être rempli à partir de résultats de recherche web réels, jamais depuis la mémoire IA.

> [!CAUTION]
> **VÉRIFICATION STRICTE DES COLORIS & SPECS** :
> Pour éviter les variations manquantes ou erronées (cf. incident montres Blackview Juillet 2026), l'IA ne doit JAMAIS se fier uniquement à des listes de stocks locales, des fichiers JSON d'entrée non validés ou des sites marchands tiers (ex: boutiques Jumia incomplètes, revendeurs secondaires).
> Toute liste de coloris et de spécifications DOIT être vérifiée auprès de :
> 1. Le site constructeur officiel (ex: apple.com, blackview.hk).
> 2. Des bases de données de specs réputées et exhaustives (ex: GSMArena, DeviceSpecifications).
> Si un décalage majeur de spécifications est détecté pour un modèle donné (ex: taille d'écran ou batterie différente), bloquer le processus et alerter immédiatement car cela signale un mélange de modèles dans les sources d'entrée.

Pour CHAQUE produit identifié au Stage 1 :

1. **Extraction de la Matrice de Specs (Script Auto V3.3)** :
   - Lancer l'extraction résiliente multi-moteurs :
     ```bash
     python scripts/tools/product_data/fetch_product_specs.py --product "[Nom du produit]" --category [tech|appliance] --output "product-data/[slug].json"
     ```
   - **Règle des 2 sources** : Toute donnée technique critique doit être confirmée par 2+ sources web consultées en temps réel et archivées dans `sources`.
   - **Arbitrage SKU** : En cas de divergence, accorder la priorité au site officiel constructeur pour la variante Internationale / Global SKU.

2. **Prix local (Côte d'Ivoire)** :
   - Rechercher sur Jumia CI (`jumia.ci`)
   - Compléter via autres marketplaces ouest-africaines
   - Documenter la fourchette min/max par configuration
   - Renseigner la date du relevé de prix

3. **Coloris & Configurations (Déclinaisons Exclusives / Paired Variants)** :
   - Lister les coloris standard et exclusifs (ex: Samsung Online Shop exclusives, coloris transparents RedMagic)
   - Identifier si des coloris spécifiques sont restreints à certains stockages ou couples RAM/ROM
   - **OBLIGATION PAIRED_VARIANTS** : Si les configurations ne sont pas un produit cartésien aveugle (toutes les RAM x tous les stockages x toutes les couleurs), formaliser impérativement la matrice exacte sous le tableau `paired_variants` dès ce stade.
   - Pour les appliances : capacités, puissances, voltages

4. **INTERDIT** : Extrapoler les specs d'un modèle vers un autre. Chaque produit fait l'objet d'une recherche INDÉPENDANTE.

---

### Stage 3 : Assemblage JSON

1. **Charger le template** :
   - Tech → `Templates/Template_ProductData_tech.json`
   - Appliance → `Templates/Template_ProductData_appliance.json`

2. **Remplir le JSON** selon les données du Stage 2 :
   - `product_identity` → Identité commerciale
   - `model_numbers` → SKU vérifié + sources + disambiguation
   - `paired_variants[]` → Matrice officielle des couples exclusifs (Coloris, RAM, ROM, Prix, Suffixe SKU) si applicable
   - `variants[]` → Une entrée par configuration avec prix individuel
   - `colors` → Standard + exclusifs + défaut
   - `key_specifications` → Données techniques (cf. [`category_specs_map.json`](../../scripts/tools/product_data/category_specs_map.json))
   - `woocommerce_csv.Tags` → Générer impérativement entre **10 et 14 tags enrichis** (Marque, Modèle, Série, Catégorie/OS, Réseau, Écran, Photo, Batterie, Processeur, Feature clé, Abidjan, My-eStore). Interdiction formelle des tags squelettiques (< 8 tags).
   - `sources[]` → Toutes les sources consultées

3. **Sauvegarder** dans :
   ```
   product-data/[brand-slug]/[series-slug]/product-data-[model-slug].json
   ```

---

### Stage 4 : Validation Automatique

```bash
# Validation d'un fichier unitaire
python scripts/tools/product_data/validate_product_data.py \
  --input "product-data/[brand]/[series]/product-data-[model].json"

# Validation batch (toute la série)
python scripts/tools/product_data/validate_product_data.py \
  --input "product-data/[brand]/[series]/" --batch

# Mode strict (warnings = erreurs)
python scripts/tools/product_data/validate_product_data.py \
  --input "product-data/[brand]/[series]/" --batch --strict
```

- **🔴 FATAL** → Corriger et re-valider (max 3 tentatives)
- **🟡 WARNING** → Corriger si possible, documenter sinon
- **✅ PASS** → Passer au Stage 5

---

### Stage 5 : Rapport de Production

Produire un résumé structuré :

```
═══════════════════════════════════════════════════
  📊 RAPPORT — Samsung Galaxy S25 Series
═══════════════════════════════════════════════════
  ✅ Galaxy S25       | SM-S931B | product-data-s25.json       | high
  ✅ Galaxy S25+      | SM-S936B | product-data-s25-plus.json  | high
  ✅ Galaxy S25 Ultra | SM-S938B | product-data-s25-ultra.json | high
  ⚠️ Galaxy S25 FE    | SM-S72xB | product-data-s25-fe.json    | medium
═══════════════════════════════════════════════════
  Fichiers : product-data/samsung/galaxy-s25/
  Avertissements : 1 (prix S25 FE non disponible localement)
═══════════════════════════════════════════════════
```

---

## 📁 Structure de Sortie

```
product-data/
├── samsung/
│   ├── galaxy-s25/
│   │   ├── product-data-s25.json
│   │   ├── product-data-s25-plus.json
│   │   ├── product-data-s25-ultra.json
│   │   └── product-data-s25-fe.json
│   └── galaxy-a56/
│       └── product-data-a56.json
├── apple/
│   └── iphone-16/
│       ├── product-data-iphone-16.json
│       ├── product-data-iphone-16-plus.json
│       ├── product-data-iphone-16-pro.json
│       └── product-data-iphone-16-pro-max.json
└── hisense/
    └── refrigerateurs/
        ├── product-data-rd-49dc4sb.json
        └── product-data-rr-220d4agn.json
```

---

## 🔗 Ressources

| Ressource | Chemin |
|-----------|--------|
| **Skill** | [PRODUCT_INTELLIGENCE_SKILL.md](../skills/product-intelligence/SKILL.md) |
| **Template Tech** | [Template_ProductData_tech.json](../../Templates/Template_ProductData_tech.json) |
| **Template Appliance** | [Template_ProductData_appliance.json](../../Templates/Template_ProductData_appliance.json) |
| **Category Map** | [category_specs_map.json](../../scripts/tools/product_data/category_specs_map.json) |
| **Validation Script** | [validate_product_data.py](../../scripts/tools/product_data/validate_product_data.py) |
| **Orchestrateur** | [orchestrateur.md](master-orchestrator.md) |

---

**Version** : 1.0
**Dernière mise à jour** : 09 Mai 2026
**Auteur** : Workflow Product Intelligence (Source de Vérité)
