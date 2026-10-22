# 🛡️ DIRECTIVE IMPÉRATIVE : Vérification des Données Produits

> **STATUT** : CONSTITUTIONNELLE — Cette directive s'applique à TOUS les workflows de production sans exception.
> Elle est référencée par : `/production-industrielle-v3`, `/generate-product-data`, `/produce-appliance`, `/WORKFLOW_COMPLET`.

---

## ⛔ AVERTISSEMENT CRITIQUE — BASE DE CONNAISSANCE IA

**Les modèles d'IA possèdent des données d'entraînement qui sont SYSTÉMATIQUEMENT obsolètes, incomplètes ou erronées pour les informations produits.**

Cela inclut, sans s'y limiter :
- Les **numéros de modèle / SKU** (ex: variantes régionales, nouveaux produits)
- Les **spécifications techniques** (ex: capacité batterie, dimensions, poids)
- Les **prix** (fluctuent constamment)
- Les **dates de sortie** et disponibilité
- Les **coloris** et configurations disponibles
- Les **noms commerciaux** (ex: confusion entre iPhone 16e et SE 4)

> [!CAUTION]
> **INTERDICTION ABSOLUE** : Un agent IA ne doit JAMAIS remplir un champ technique (SKU, specs, prix) en se basant uniquement sur sa mémoire interne ou ses données d'entraînement. Chaque donnée technique DOIT provenir d'une recherche web vérifiée en temps réel.

---

## 🔒 Protocole de Vérification Obligatoire (PVO)

### Étape 0 : Extraction & Vérification des Specs Réelles (Gate 0 - V3.3)

Avant d'entamer la rédaction ou la modification d'un JSON/CSV, l'agent DOIT extraire et certifier la matrice de spécifications réelles (Nom commercial, SKU officiel, RAM, stockage, processeur, batterie, puissance de charge, étanchéité et coloris).
- **Règle anti-hallucination (V3.3)** : Exécuter le script résilient multi-moteurs (Google + DuckDuckGo + Scraping direct) pour construire ou valider la fiche technique :
  ```bash
  python scripts/tools/product_data/fetch_product_specs.py --product "[Nom du produit]" --category [tech|appliance] --output "product-data/[slug].json"
  ```
- **Validation d'existence complémentaire** :
  ```bash
  python scripts/tools/product_data/check_product_existence.py --product "[Nom complet]" --color "[Coloris]" --category "[Catégorie]"
  ```
- **Règle d'Arbitrage Constructeur & Verrouillage des Coloris (V3.3)** : 
  - En cas de divergence de specs entre sites (ex: 5000 mAh vs 5180 mAh), accorder la **priorité absolue au site officiel constructeur** pour la **zone géographique ciblée (Version Internationale / Global SKU)**.
  - **Plafond Strict des Coloris** : Si la fiche officielle ou la spec table énumère N coloris (ex: 3 coloris `Noir, Orange, Vert`), la liste `colors.standard` est **strictement verrouillée** à ces N coloris. Il est **STRICTEMENT INTERDIT** d'ajouter des couleurs supplémentaires issues de textes secondaires ou de revendeurs tiers pour éviter d'induire en erreur.

### Étape 1 : Recherche Officielle & Dual-Source OBLIGATOIRE

Avant de remplir tout champ technique dans un JSON ou CSV, l'agent DOIT :

1. **Effectuer une recherche web** ciblant le site officiel du constructeur :
   - Apple : `support.apple.com/108044` (Identify your iPhone model)
   - Samsung : `samsung.com/[region]/smartphones/`
   - Xiaomi : `xiaomi.com/[region]/product/`
   - Etc.

2. **Consulter AU MINIMUM 2 sources distinctes** pour toute donnée critique :
   - Source primaire : Site officiel constructeur
   - Source secondaire : GSMArena, DeviceSpecifications, NotebookCheck, Kimovil

3. **Énumération et Tri des Coloris (Spécifique V3.1)** : 
   - L'agent doit rechercher et lister **l'intégralité** des couleurs annoncées par le constructeur.
   - **Distinction CRITIQUE** : L'agent doit séparer les couleurs "Standard / Retail" (vendues partout) des couleurs "Exclusives" (éditions limitées, exclusivités web constructeur).
   - *Règle d'intégration* : **Seules les couleurs "Standard"** doivent être insérées dans les attributs WooCommerce pour générer des variantes de vente. Les couleurs "Exclusives" ne doivent **JAMAIS** générer de variantes (pour éviter des produits impossibles à sourcer), mais peuvent être mentionnées à titre informatif dans la fiche technique.

4. **Documenter les résultats** dans le champ `sourcing.specs_sources` du JSON avec les URLs réelles consultées.

### Étape 2 : Gate Bloquant — Rapport de Vérification

**Aucun remplissage de moule JSON ne peut commencer** sans que l'agent ait produit (au minimum mentalement) un rapport de vérification contenant :

```
═══════════════════════════════════════════════════════════
  🔍 RAPPORT DE VÉRIFICATION — [Nom du Produit]
═══════════════════════════════════════════════════════════
  SKU officiel :     [A3287] — Source : support.apple.com/108044
  Processeur :       [A18 Bionic] — Source : apple.com/iphone-16
  RAM :              [8 Go] — Source : gsmarena.com/...
  Batterie :         [3561 mAh] — Source : gsmarena.com/...
  Prix FCFA :        [550 000] — Source : jumia.ci/...
  Date vérification: [2026-05-13]
═══════════════════════════════════════════════════════════
  ⚠️ Données NON vérifiées : [Liste ou "Aucune"]
═══════════════════════════════════════════════════════════
```

### Étape 3 : Distinction Régionale des SKU

Les constructeurs utilisent des numéros de modèle DIFFÉRENTS par région. Pour le marché My-eStore (Côte d'Ivoire), privilégier :

- **Version Internationale** (Global) : Supporte nano-SIM + eSIM
- **PAS** la version US (eSIM only) ni la version Chine (Dual nano-SIM)

| Constructeur | Nomenclature à rechercher |
|---|---|
| Apple | "Identify your iPhone model" → Variante pour "other countries and regions" |
| Samsung | Suffixe `-B` (International) vs `-U` (US) vs `-N` (Corée) |
| Xiaomi | Suffixe `G` (Global) vs `C` (Chine) |
| BBK (OnePlus/Oppo/Vivo) | Modèles CPHxxxx (Global) vs Pxxx (Chine). Ex: OnePlus 12 = CPH2581 (Global) |
| Google Pixel | Variantes "Rest of World (ROW)" ou "Global/Unlocked" (éviter variantes Japon/Verizon) |
| **Autres Marques** (ZTE, Blackview, etc.) | **Règle Générale** : Chercher explicitement la mention "Global Version" ou "International". Vérifier la présence des services Google (GMS) et la compatibilité des bandes réseaux (B3, B7, B20). Rejeter systématiquement la mention "China ROM" ou "US Carrier". |

---

## 🚫 Liste des Comportements Interdits

1. **Remplir un SKU par mémoire** sans recherche web → INTERDIT
2. **Extrapoler les specs** d'un modèle vers un autre (ex: iPhone 16 → iPhone 16 Pro) → INTERDIT
3. **Utiliser des données de leaks/rumeurs** comme source → INTERDIT
4. **Ignorer les différences régionales** des model numbers → INTERDIT
5. **Laisser un champ vide sans le documenter** → INTERDIT
6. **Affirmer une vérification sans l'avoir réellement effectuée** → INTERDIT
7. **Copier un SKU depuis un message précédent** sans re-vérification → INTERDIT

---

## ✅ Checklist de Conformité (à valider avant chaque build)

- [ ] **Recherche web effectuée** : Au moins 1 recherche web ciblée a été lancée
- [ ] **Site officiel consulté** : Le site du constructeur a été la première source
- [ ] **SKU vérifié** : Le numéro de modèle provient d'une source officielle datée
- [ ] **Variante régionale correcte** : Version Internationale sélectionnée (pas US/Chine)
- [ ] **2+ sources concordantes** : Les specs critiques sont confirmées par 2 sources minimum
- [ ] **Coloris énumérés exhaustivement** : Toutes les couleurs officielles ont été trouvées et listées
- [ ] **Tri des coloris (Standard/Exclusif)** : Les couleurs exclusives web ont été séparées et exclues des attributs WooCommerce
- [ ] **Vérification GMS & Bandes** : Présence des services Google et compatibilité 4G/5G validée (surtout pour les "Autres Marques")
- [ ] **URLs documentées** : Le champ `sourcing.specs_sources` contient les URLs réelles
- [ ] **Aucune hallucination** : Aucun champ n'a été rempli par "intuition" ou mémoire IA

---

## 📝 Cas d'Étude : Incident iPhone SKU (Mai 2026)

### Ce qui s'est passé
Un agent IA a rempli les SKU de toute la gamme iPhone (14 à 17) avec des numéros erronés :
- iPhone 16 : `A3286` (Japon/Canada) au lieu de `A3287` (International)
- iPhone 16 Pro : `A3293` (Chine mainland) au lieu de `A3294` (International)
- iPhone 16e : `A3520` (c'est le SKU de l'iPhone 17 !) au lieu de `A3409`
- iPhone 17 : `A3251` (inexistant) au lieu de `A3520`

### Cause racine
L'agent s'est fié à sa mémoire interne sans effectuer de recherche web vers le support officiel Apple (`support.apple.com/108044`).

### Impact
- Données erronées injectées dans 7 fichiers JSON de production
- CSV d'import WooCommerce générés avec de mauvais identifiants
- Nécessité d'un audit complet et d'une reconstruction totale

### Leçon
**La vérification web officielle n'est pas un luxe — c'est un prérequis absolu.** Un agent IA, aussi avancé soit-il, ne peut pas garantir l'exactitude de données factuelles changeantes sans vérification en temps réel.

---

**Version** : 1.0
**Date de création** : 13 Mai 2026
**Déclencheur** : Incident critique SKU iPhone — Mai 2026
**Applicabilité** : Tous les workflows de production My-eStore
