---
name: aioseo-verification
description: Guide technique de vérification AIOSEO TruSEO. Définit la formule mathématique des connecteurs logiques 15/41 (36.5%), la limite stricte de 0% de phrases longues (>20 mots) et les méta-titres Standard B.
---

# Guide de Vérification AIOSEO & Génération de Contenu

Ce guide définit les standards de rédaction pour les fiches produits WordPress, alignés sur les algorithmes TruSEO d'AIOSEO et les principes de conversion Big Tech.

---

## 📋 CHECKLIST DE VÉRIFICATION AIOSEO (TruSEO)

### 1. Analyse du Titre & Meta
- [ ] **SEO Title Length :** Entre 50 et 60 caractères. Le mot-clé principal doit être au début.
- [ ] **Meta Description Length :** Entre 155 et 160 caractères. Doit inclure l'USP (Unique Selling Proposition) et un appel à l'action (CTA).

### 2. Structure du Contenu (Suivre les Templates)
- [ ] **Content Length :** Minimum 500 mots (texte visible) pour une description longue (marge de sécurité de production, seuil strict de 450).
- [ ] **Subheading Distribution :** Un titre (H2) pour chaque bloc.
- [ ] **Short Description TAGS :** Doit inclure une conclusion en italique via la balise `<em>`.
- [ ] **HTML Hygiene :** Ne pas utiliser de `<div>` ou de styles CSS personnalisés dans les descriptions courtes (SEO WordPress).
- [ ] **Internal Links :** Au moins 1 lien vers un accessoire ou une catégorie parente.
- [ ] **External Links :** Au moins 1 lien vers une source d'autorité (ex: fiche constructeur) ou un test indépendant.
- [ ] **Images/Videos :** Présence de médias avec des attributs `alt` descriptifs incluant le mot-clé.

### 3. Lisibilité (Facteurs TruSEO)
- [ ] **Paragraph Word Count (CRITICAL - BLOCKING):**
  - **Note de calcul** : Compter uniquement le **texte visible** (balises HTML supprimées). Le script `validate_html_template.py` fait autorité pour le calcul du nombre de mots. Alternativement, L'Agent effectue ce comptage lors de son auto-audit.
  - **Paragraphe introductif** : ≤ 100 mots (présentation factuelle du produit)
  - **Tous les autres paragraphes** : ≤ 60 mots par paragraphe (flexible 45-60 selon longueur tableau specs)
  - **Section "Fiche technique sommaire"** : Le H2 + tableau ajoute environ 50-60 mots au total
  - **Description longue totale** : 500-650 mots (Viser 500 mots minimum de sécurité - STRICT - Interdiction de descendre sous 450 ou dépasser 650)
  - **Vérification du calcul** : Compter TOUS les mots visibles incluant H2 "Fiche technique" et contenu du tableau (hors balises)
- [ ] **Paragraphs Length :** Aucun paragraphe ne doit dépasser 60 mots (introductif max 100). Ajuster selon tableau.
- [ ] **Sentences Length (CRITIQUE — BLOQUANT) :** Maximum **25% des phrases** peuvent dépasser 20 mots (cible : ≤20%). Privilégier des phrases de 12-18 mots. L'IA Rédactrice scinde systématiquement toute phrase atteignant 18 mots par un point.
- [ ] **Sentence Structure (Vigilance) :** Les descriptions techniques complexes doivent être divisées en deux phrases distinctes plutôt que d'utiliser des virgules excessives.
- [ ] **Passive Voice :** Maximum 10% de phrases à la voix passive. Privilégier la voix active (ex: "Le processeur booste" au lieu de "Les performances sont boostées par").
- [ ] **Transition Words (par PHRASE, pas par paragraphe) :** Au moins **30% des phrases** doivent contenir un mot de transition (zone optimale 30-70%). AIOSEO cherche les transitions **n'importe où dans la phrase**, pas uniquement au début. Limiter les transitions en début de paragraphe à un maximum de 4 sur 7 pour éviter un style trop lourd. Validé par `audit_aioseo_sentences.py`.
- [ ] **Consecutive Sentences :** Ne jamais commencer 3 phrases consécutives par le même mot.
- [ ] **Flesch Reading Ease :** Score cible entre 60 et 70 (Lisibilité "Standard").

### 4. Qualité Grammaticale et Ton (CRITICAL)
- [ ] **Grammaire Standard :** Utiliser UNIQUEMENT le français standard correct. Pas de constructions alambiquées, de syntaxe artificielle ou de ton "robotique".
- [ ] **Articles & Déterminants :** Toujours utiliser les articles corrects (le, la, les, un, une, des) devant les noms pour produire des phrases grammaticalement justes.
- [ ] **Fluidité Native :** Le texte doit se lire naturellement. Éviter les répétitions de structures de phrases (ex: "Il dispose de... Il possède... Il est équipé...").
- [ ] **Pas de Verbosité :** Éviter les phrases trop descriptives ou le langage fleuri. Privilégier la clarté et la concision.
- [ ] **Ton Factuel :** Écrire dans un ton direct et factuel, inspiré des fiches techniques professionnelles (style Samsung/Apple).
- [ ] **Pas d'Adjectifs Excessifs :** Limiter les superlatifs et adjectifs emphatiques ("incroyable", "révolutionnaire"). Préférer les faits mesurables.
- [ ] **Correction Orthographique :** Vérifier l'orthographe de tous les mots, notamment les termes techniques et les noms de marque.
- [ ] **Cohérence Temporelle :** Utiliser le présent de l'indicatif de manière cohérente pour décrire les caractéristiques du produit.

---

## 🔝 LISTE DES MOTS DE TRANSITION (POUR TRUSEO)

Utilisez ces termes de manière variée pour maintenir le taux de 30-70% **par phrase** (pas par paragraphe). AIOSEO cherche ces mots **n'importe où dans la phrase** :
- **Addition :** De plus, En outre, Par ailleurs, Également, De surcroît, et, Ainsi que.
- **Contrast / Opposition :** Cependant, Toutefois, Néanmoins, En revanche, Pourtant, Alors que, Bien que.
- **Cause / Justification :** En effet, Car, Étant donné que, Puisque, Parce que, Grâce à.
- **Conséquence / Conclusion :** Par conséquent, Ainsi, C’est pourquoi, Dès lors, En conséquence, En résumé, En conclusion, En bref, Finalement.
- **Temps / Ordre :** D’abord, Ensuite, Enfin, Puis, Premiérement, Secondairement, Toisiémement, Dans un premier temps, Dans un second temps, Pour finir.
- **Illustration :** Par exemple, Notamment, En particulier, Spécifiquement, Comme.
- **Alternative :** Soit... soit, Tantôt... Tantôt, d'un côté de l'autre.

---

## 🤖 DIRECTIVES DE GÉNÉRATION (Framework AIOSEO - Professional Copywriting)

**APPROCHE : RÉDACTEUR PROFESSIONNEL TECH**

Le système doit fonctionner comme un rédacteur professionnel qui écrit du contenu varié et naturel basé sur les spécifications techniques Vrai.

### Méthodologie de Rédaction Professionnelle

**✅ EXEMPLE D'APPROCHE CORRECTE - Rédaction Naturelle :**
```
Specs: {"processeur": "MediaTek Helio G99", "batterie": "5500 mAh", "écran": "AMOLED 120Hz"}
Rédaction: "Le Redmi Note 14 4G embarque le processeur MediaTek Helio G99 gravé en 6nm, 
offrant des performances équilibrées pour le multitâche et le gaming léger. Sa batterie 
de 5500 mAh garantit une autonomie de plus de 12 heures en utilisation intensive. L'écran 
AMOLED de 6.67 pouces avec rafraîchissement 120Hz fluidifie chaque interaction."
```

**❌ APPROCHE INCORRECTE - Substitution Rigide :**
```
Template rigide: "Le [PROCESSEUR] offre [QUALIFICATIF]."
Résultat: Texte répétitif et peu naturel
```

### Instructions pour l'Agent IA

**LIMITES STRICTES DE WORD COUNT À RESPECTER TOUJOURS:**
- **Note** : Le calcul se fait sur le **texte visible uniquement** (balises HTML exclues).
- **Paragraphe introductif** : **MAXIMUM 100 mots**
- **Tous les autres paragraphes** : **MAXIMUM 60 mots** par paragraphe
- **Description longue totale** : **500-650 mots** (cible de sécurité pour la génération ; le validateur accepte le pack dès 450 mots pour des raisons de compatibilité, mais viser 500 mots évite tout rejet).
- **À valider AVANT création du fichier** - Échouer le checkpoint si dépassé

**Lors de la Phase 2 (LONG) et Phase 3 (SHORT) :**

1. **Analyser les Specs**
   - Lire le fichier specs-[variant].html complètement
   - Identifier les caractéristiques clés et différenciantes
   - Noter les données techniques exactes (capacités, modèles, technologies)
   - Les Specs doivent correspondre et etre vrai

2. **Rédiger Naturellement**
   - Écrire comme un rédacteur tech professionnel
   - Varier les structures de phrases
   - Utiliser les mots de transition de manière naturelle
   - Expliquer les specs techniques de façon accessible
   - Connecter les caractéristiques techniques aux bénéfices réels

3. **Standards de Qualité**
   - **Grammaire** : Français standard impeccable
   - **Ton** : Factuel, professionnel, style Samsung/Apple
   - **Précision** : Toutes les données techniques doivent correspondre exactement aux specs
   - **Clarté** : Phrases courtes (≤20 mots, scission systématique à 18 mots), paragraphes concis
   - **Naturel** : Le texte doit se lire fluidement, pas comme un formulaire rempli

4. **Ce qu'il faut FAIRE**
   - ✅ Varier les débuts de phrases
   - ✅ Utiliser des synonymes appropriés
   - ✅ Créer des transitions fluides entre les sections
   - ✅ Expliquer les termes techniques quand nécessaire
   - ✅ Maintenir un ton cohérent et professionnel
   - ✅ Utilisations d'adjectifs Utile et précis

5. **Ce qu'il faut ÉVITER**
   - ❌ Inventer des spécifications ou approximer les chiffres
   - ❌ Utiliser un langage marketing excessif ou des superlatifs non justifiés
   - ❌ Répéter les mêmes structures de phrases
   - ❌ Écrire de manière verbeuse ou complexe
   - ❌ Utiliser un ton artificiel ou robotique
   - ❌ Pas de d'excès d'adjectifs pour pas alourdir inutilement le texte

**Contraintes de rédaction (STRICTES) :**
1. **Longueur :** 500-650 mots pour LONG (cible de sécurité), <60 mots teaser pour SHORT
2. **Structure HTML :** Suivre la structure du template (H1, H2, paragraphes, listes)
3. **Lisibilité TruSEO :**
   - Phrases courtes (≤20 mots, max 25% peuvent dépasser)
   - Paragraphes de 2-4 phrases
   - Mots de transition dans **30-70% des phrases** (pas des paragraphes)
   - Voix active privilégiée
   - Variation des débuts de phrases
4. **SEO :**
   - Mot-clé focus dans H1, premier paragraphe, et au moins un H2
   - SEO Title (50-60 car.) et Meta Description (155-160 car.)
5. **Style :** Ton factuel, technique mais accessible, style premium (Samsung/Apple)
6. **Exactitude :** TOUTES les données techniques doivent correspondre exactement aux specs

---

## 🛠 OUTILS DE VALIDATION RAPIDE

| Point de contrôle | Outil / Méthode | Objectif |
| :--- | :--- | :--- |
| Longueur | `wc -w` ou compteur en ligne | > 450 mots |
| Phrases >20 mots | `audit_aioseo_sentences.py` | ≤ 25% |
| Voix Passive | Analyseur de texte | < 10% |
| Transition/phrase | `audit_aioseo_sentences.py` | 30-70% |
| Flesch Score | Hemingway App / AIOSEO | 60-70 |

---

## 📝 EXEMPLE DE STRUCTURE OPTIMISÉE

Se référé toujours aux Templates.
---

## 🔑 GESTION DES MOTS-CLÉS (KEYWORDS)

Lors de chaque génération ou révision, une liste de mots-clés doit être annexée en bas du document sous forme de commentaire HTML. Cela permet de vérifier rapidement la densité et la pertinence sans impacter le rendu final.

### Structure des Keywords à ajouter :
1. **Focus Keyword :** Le mot-clé principal visé.
2. **LSI Keywords (Latent Semantic Indexing) :** 5 à 8 termes sémantiquement proches (ex: caractéristiques techniques, synonymes).

*Consultez cette liste lors de l'intégration dans WordPress pour remplir les champs AIOSEO correspondants.*