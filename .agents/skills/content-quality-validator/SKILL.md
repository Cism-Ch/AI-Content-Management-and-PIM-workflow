---
name: content-quality-validator
description: Détecte automatiquement les erreurs de qualité dans les fiches produits (conformité AIOSEO, longueurs de phrases, SKUs, styles proscrits) pour le gate d'audit QA /audit-product-pack.
---

# Skill: Content Quality Validator

## Description

Ce skill permet de détecter automatiquement les erreurs de qualité dans les fichiers de description de produits (long-*.html et short-*.html) et de générer un rapport de correction détaillé. L'agent utilisera ce rapport pour appliquer les corrections via les outils d'édition.

## Types d'erreurs détectées

### 🔴 Erreurs Critiques (Doivent être corrigées immédiatement)

1. **Présence de N/A dans les spécifications**
   - Détection : Rechercher "N/A" dans les tableaux specs et textes
   - Impact : Violation des standards de qualité

2. **Erreurs grammaticales**
   - "Le cette" → Doit être "Cette"
   - "Sa cette" → Doit être "Cette"
   - "Les la" → Doit être "La"
   - "Ce cet" → Doit être "Cet"
   - "Sa la" → Doit être "La"
   - Etc. (toutes les erreurs de double déterminant ou accord)

3. **Confusion RAM/Stockage**
   - "256 Go de RAM" → Doit être "12 Go de RAM et 256 Go de stockage"
   - "512 Go de RAM" → Doit être "16 Go de RAM et 512 Go de stockage"
   -etc. (toutes les erreurs où la quantité de RAM est confondue avec le stockage)

4. **Incohérences techniques**
   - Processeur différent entre texte et tableau
   - Spécifications contradictoires
   - etc.

5. **Présence d'hyperboles et superlatifs excessifs (CRITIQUE — V3.2)**
   - Détection : Utilisation de termes marketing emphatiques non justifiés (ex: "incroyable", "révolutionnaire", "séduction fatale", "colossal", "sublime").
   - Règle : Interdiction absolue. Le ton doit rester purement factuel, sobre et haut de gamme. Tout mot interdit déclenchera un FAIL de l'audit.

### 🟡 Problèmes de Fluidité (À améliorer)

1. **Répétitions excessives de transitions**
   - Plus de 2 utilisations de "De plus" par section
   - Plus de 2 utilisations de "Ensuite" dans le fichier
   - etc.

2. **Structures répétitives**
   - "[Sujet], le [Produit]..." utilisé plus de 2 fois
   - Manque de pronoms pour créer du lien
   - manque de variation dans les introductions de sections
   - manque de connecteurs logiques variés (Par ailleurs, D'ailleurs, À noter, etc.)

3. **Rythme des phrases (CRITIQUE — AIOSEO)**
   - Plus de 25% des phrases contenant plus de 20 mots (seuil bloquant AIOSEO)
   - Plus de 3 phrases courtes consécutives (moins de 10 mots)
   - Manque de variation dans la longueur des phrases

4. **Taux de transitions (CRITIQUE — AIOSEO)**
   - Moins de 30% des phrases contenant un mot de transition
   - Les transitions peuvent être n'importe où dans la phrase, pas seulement au début

### 🟠 Problèmes de Ton Naturel (À améliorer)

1. **Noms génériques**
   - "Le 70", "Le Pro", "Le Pro+", "Le X"
   - Doit être remplacé par le nom complet ou des pronoms

2. **Formules toutes faites et Fluff**
   - "Avec sa conception..."
   - "Grâce à sa technologie..."
   - "Doté de..."
   - "Le summum de la technologie", "Incroyable", "Révolutionnaire" (Aucune hyperbole générique autorisée).
   - "Le smartphone propose..." (si répété)

3. **Verbes peu variés**
   - Répétition excessive de "dispose de", "possède", "embarque"

### 🔵 Erreurs SEO E-Commerce (Critique V2.1)

1. **Meta Title non descriptif**
   - Absence de la RAM, du Stockage, ou de la Taille d'Écran dans le Titre.
   
2. **Meta Description hors sujet**
   - Présence des mots "SAV" ou "Garantie commerciale".
   - Absence de la mention "Livraison Abidjan" (ou variantes locales).

3. **LSI Keywords insuffisants**
   - Moins de 10 mots-clés dans la liste.
   - Présence de mots-clés informatifs ("test", "avis", "comment ça marche") au lieu de mots transactionnels ("prix", "acheter").

4. **Copier-Coller des Variantes (CRITIQUE)**
   - Le bloc `seo` de la section Short est identique ou quasi-identique au bloc `seo` de la section Long. L'IA a triché.

## Procédure d'utilisation

### Étape 1 : Analyse du fichier cible

```markdown
Action: Lire le fichier long ou short à analyser
Commande: read
Paramètre: filePath du fichier à vérifier
```

### Étape 2 : Détection des erreurs

Pour chaque type d'erreur, effectuer les recherches suivantes :

#### 2.1 Détection N/A
- Rechercher : "N/A" dans tout le contenu
- Noter : Ligne exacte, contexte, valeur suggérée

#### 2.2 Détection erreurs grammaticales
- Rechercher : "Le cette", "Sa cette", "Les la", "Ce cet", "Sa la", etc.
- Noter : Chaque occurrence avec ligne exacte

#### 2.3 Détection RAM/Stockage
- Rechercher : "Go de RAM" précédé de 256, 512, 1024
- Vérifier : Si c'est bien de la RAM ou du stockage

#### 2.4 Détection répétitions
- Compter : Occurrences de connecteurs logiques "De plus", "Ensuite", "Par ailleurs", etc.
- Identifier : Structures répétitives "[Sujet], le [Produit]"

#### 2.5 Détection noms génériques
- Rechercher : "Le 70", "Le Pro", "Le Pro+", "Le X", "Le Mate", etc.
- Noter : Lignes où le nom complet devrait être utilisé

### Étape 3 : Génération du rapport d'Audit (PASS / FAIL)

Créer un fichier markdown avec cette structure exacte, qui sera renvoyé à l'Orchestrateur ou à l'Agent de production :

```markdown
# 📋 Rapport de Contrôle Qualité - [Nom du Produit]
**Fichier:** [chemin/vers/fichier.json ou .html]
**Statut de l'Audit:** ❌ FAIL (ou ✅ PASS si aucune erreur détectée)
**Agent:** content-quality-validator

---

## 🔴 Erreurs Critiques (Correction Obligatoire)

### 1. Erreurs SEO E-Commerce
| Ligne | Erreur Détectée | Règle Violée |
|-------|-----------------|--------------|
| X | Titre sans la RAM | Le Meta Title doit inclure toutes les specs techniques |
| Y | Présence du mot "SAV" | La Meta Description ne doit parler que de livraison Abidjan/Qualité |
| Z | 6 mots-clés | Minimum 10 mots-clés requis |
| W | SEO Identique | Le SEO du Short est identique au Long (Copier-coller IA détecté) |

### 2. Valeurs N/A
| Ligne | Erreur | Correction suggérée |
|-------|--------|---------------------|
| X | Processeur: N/A | [Valeur correcte] |
| Y | Batterie: N/A | [Valeur correcte] |
ou toutes les autres occurrences de N/A

**Corrections à appliquer :**

**Ligne X - Processeur N/A:**
```
OLD: <td style="...">N/A</td>
NEW: <td style="...">[Valeur correcte]</td>
```

### 2. Erreurs Grammaticales
| Ligne | Erreur | Correction |
|-------|--------|------------|
| Y | Le cette | Cette |
| Z | Les la | La |
ou toutes les autres erreurs grammaticales détectées

**Corrections à appliquer :**

**Ligne Y - Double déterminant:**
```
OLD: Le cette configuration
NEW: Cette configuration
```

**Ligne Z - Double déterminant + accord:**
```
OLD: Les la gestion
NEW: La gestion
```

### 3. Erreurs RAM/Stockage
| Ligne | Erreur | Correction |
|-------|--------|------------|
| W | 256 Go de RAM | 12 Go de RAM et 256 Go de stockage |

**Corrections à appliquer :**

**Ligne W - Confusion RAM/Stockage:**
```
OLD: Le smartphone propose 256 Go de RAM
NEW: Le smartphone propose 12 Go de RAM et 256 Go de stockage
```

### 4. Hyperboles et Mots Interdits
| Ligne/Champ | Mot Détecté | Règle Violée |
|-------------|--------------|--------------|
| short_description.teaser | révolutionne | Interdiction absolue de recourir au vocabulaire publicitaire excessif |

**Corrections à appliquer :**

**Champ short_description.teaser - Hyperbole:**
```
OLD: Le spectaculaire Blackview DCM6 révolutionne absolument le fastidieux travail nomade
NEW: Le Blackview DCM6 simplifie le travail nomade
```

---

## 🟡 Problèmes de Fluidité

### Répétitions excessives
- **"De plus" utilisé X fois** (max recommandé: 2 par section)
  - Ligne A, B, C, D
  - **Suggestions:** Remplacer par "Par ailleurs", "D'ailleurs", "À noter"

**Corrections suggérées :**

**Ligne B:**
```
OLD: De plus, l'écran...
NEW: Par ailleurs, l'écran...
```

### Structures répétitives
- **Pattern "[Sujet], le [Produit]" détecté X fois**
  - Lignes: E, F, G

**Corrections suggérées :**

**Ligne E:**
```
OLD: Les performances, le Huawei Nova 13 bénéficie...
NEW: Côté performances, il bénéficie...
```

---

## 🟠 Problèmes de Ton Naturel

### Noms génériques à remplacer
| Ligne | Générique | Correction |
|-------|-----------|------------|
| H | Le 70 | Le Huawei Pura 70 |
| I | Le Pro | Ce modèle |

**Corrections à appliquer :**

**Ligne H:**
```
OLD: Le 70 adopte...
NEW: Le Pura 70 adopte...
```

---

## ✅ Checklist de correction

- [ ] Tous les N/A corrigés
- [ ] Toutes les erreurs grammaticales corrigées
- [ ] Erreurs RAM/Stockage corrigées
- [ ] Répétitions de transitions variées
- [ ] Noms génériques remplacés
- [ ] Structure fluide vérifiée
- [ ] Ton naturel amélioré
- [ ] informations techniques cohérentes
- [ ] Aucune hyperbole/mot interdit présent dans les textes

---

## 📊 Statistiques

- **Erreurs critiques:** X
- **Problèmes de fluidité:** Y
- **Problèmes de ton:** Z
- **Total erreurs détectées:** X+Y+Z
- **Total corrections:** X+Y+Z
```

### Étape 4 : Application des corrections

L'agent doit :
1. Lire le rapport de correction généré
2. Pour chaque correction listée :
   - Localiser l'oldString exact dans le fichier source
   - Utiliser `edit` avec oldString/newString
   - Vérifier que la correction est appliquée
3. Continuer jusqu'à épuisement des corrections

## Exemple complet d'utilisation

### Scénario : Correction du fichier long d'un produit

**Étape 1 : Analyse**
```
User: "Vérifie la qualité du fichier products/huawei-nova-all/nova-13/long-nova-13.html"
```

**Étape 2 : Détection**
```
Action: read filePath="products/huawei-nova-all/nova-13/long-nova-13.html"
Résultat: Détection de :
- 1 N/A (Processeur)
- 0 erreurs grammaticales
- 4 répétitions "De plus"
- 4 structures "[Sujet], le [Produit]"
```

**Étape 3 : Génération rapport**
```
Action: write filePath="Docs/correction-report-nova-13.md"
Contenu: Rapport structuré avec oldString/newString
```

**Étape 4 : Correction**
```
Pour chaque entrée du rapport:
  Action: edit filePath="..." oldString="..." newString="..."
```

## Bonnes pratiques

1. **Toujours lire le fichier complet** avant de générer le rapport
2. **Noter les numéros de ligne exacts** pour faciliter la correction
3. **Fournir le contexte** (lignes avant/après) pour chaque oldString
4. **Prioriser les erreurs critiques** avant les problèmes de fluidité
5. **Vérifier la cohérence** entre texte et tableau des spécifications

## Limitations connues

- Ce skill ne détecte pas les erreurs de mise en page HTML
- Les erreurs de style (inline styles) ne sont pas vérifiées ici mais peuvent être détectées par un autre skill de formatage ou via les scripts de validations validate_html_template.py ; validate_product_pack.ps1
- La détection du ton naturel est indicative et nécessite une relecture humaine
- Les suggestions de remplacement pour les transitions sont des recommandations, non des obligations

## Ressources

- **Rapport d'exemple** : Voir `Docs/rapport_audit_huawei_long_files.md` pour un exemple de détection complète
- **Skill de formatage** : Se référer à `PRODUCT_FORMATTING_SKILL.md` pour les standards de référence