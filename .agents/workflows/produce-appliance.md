---
name: produce-appliance
description: "Industrial production of an appliance product pack (LONG + SHORT) under V3.4 Parent-First standards."
---

# ❄️ Workflow Appliance Production (Norme V3.4 — `/produce-appliance`)

Ce workflow automatise la création de fiches produits standardisées et certifiées pour l'électroménager, le froid et la climatisation via la commande `/produce-appliance [Product Name]`.

> [!NOTE]
> Pour une explication détaillée de la nature industrielle et des objectifs de ce workflow, consultez la [Documentation complète](../../Docs/WORKFLOW_PRODUCE_APPLIANCE.md).

---

## 🎯 Étapes Opérationnelles V3.4

### 1. Analyse & Initialisation
* Initialiser les instructions du skill [appliance-factory](../../skills/appliance-factory/SKILL.md) situé dans `.agents/skills/appliance-factory/SKILL.md`.
* Vérifier le [Guide de Taxonomie](../../Docs/WORDPRESS_TAXONOMY_GUIDE.md) pour assurer le classement exact dans l'une des 127 catégories hiérarchiques officielles.

> [!CAUTION]
> **DIRECTIVE IMPÉRATIVE** : Ce workflow est soumis à [`VERIFICATION_IMPERATIVE.md`](../directives/VERIFICATION_IMPERATIVE.md). L'agent ne doit JAMAIS remplir un champ technique (SKU, dimensions, consommation, puissance) depuis sa mémoire interne. Toute donnée DOIT provenir d'une **recherche web vérifiée en temps réel**.

### 2. Recherche & Data Sourcing (Gate 0)
* Avant toute recherche web, vérifier si un fichier JSON vérifié existe dans `product-data/[marque]/[slug].json`.
* Si oui, l'utiliser comme **base de référence certifiée** (specs, SKU constructeur, prix FCFA, coloris).
* Si non, effectuer une **recherche web obligatoire** en priorité sur le site officiel constructeur (Midea, Hisense, Beko, Nasco) puis sur les catalogues distributeurs (Sociam).

### 3. Rédaction 3 Personas V3.4
Appliquer rigoureusement la chaîne cognitive des 3 Personas :

1. **Persona 1 (Copywriter Factualité Dynamique)** :
   * Ton factuel et chaleureux, axé sur le confort domestique, la durabilité et l'économie d'énergie.
   * **Zéro Hyperbole** : Proscription absolue des termes publicitaires pompeux (*révolutionnaire*, *magique*, *exceptionnel*).
   * Paragraphe introductif : **100 mots maximum**, purement centré sur les atouts de l'appareil.
2. **Persona 2 (Expert SEO AIOSEO)** :
   * **Longueur des phrases** : 0% de phrases longues (> 20 mots), viser 12-18 mots.
   * **Transitions** : Formule mathématique 15/41 (36.5% de connecteurs logiques, cible 31-49%).
   * **Structure H2** : 3 sections éditoriales (Performance, Confort d'usage, Fonctions avancées & Sécurité).
   * **Word Count** : 450 à 650 mots de texte visible.
   * **Tags WooCommerce** : 10 à 14 tags précis et géolocalisés.
3. **Persona 3 (Intégrateur Technique)** :
   * Injection des gabarits [TEMPLATE_APPLIANCE_LONG.html](../../../Templates/TEMPLATE_APPLIANCE_LONG.html) et [TEMPLATE_APPLIANCE_SHORT.html](../../../Templates/TEMPLATE_APPLIANCE_SHORT.html).
   * Tableau technique `full_specs` complet avec classes énergétiques (A+, A++), dimensions (HxLxP en mm), gaz réfrigérant (R32, R410A, R600a), volume net en litres.
   * Règle des 3 liens sources neutres.

### 4. Audit Qualité Bloquant (Agent QA)
* Invoquer systématiquement le Checker :
  ```bash
  /audit-product-pack product-data/[marque]/[slug].json
  ```
* En cas d'erreur ou d'échec AIOSEO, corriger immédiatement sur le fichier parent avant toute compilation.

### 5. Compilation & Build
* Générer les rendus HTML et exporter vers le CSV consolidé avec le prix FCFA calibré depuis [Pricing/](../../../Pricing/).
* En cas de dysfonctionnement de script, escalader vers [`/script-specialist`](script-specialist.md).
