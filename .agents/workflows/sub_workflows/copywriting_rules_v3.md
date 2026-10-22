---
name: copywriting_rules_v3
description: "[V3.4 - Rôle Rédacteur] Règles éditoriales, gabarits et consignes SEO (AIOSEO Standard B) pour la rédaction des fiches produits V3.4."
---

# ✍️ Sous-Workflow : Règles de Rédaction & SEO (Norme V3.4)

Ce document contient les instructions opérationnelles pour l'**IA Rédactrice (Maker)**. Il régit la création des descriptions, l'optimisation SEO (AIOSEO TruSEO) et le choix des moules JSON sous la norme **V3.4 Parent-First**.

*   **Lien vers le Master** : [production-industrielle-v3.md](../production-industrielle-v3.md)
*   **Gabarit d'écriture source** : [TEMPLATE_LONG.html](../../../Templates/TEMPLATE_LONG.html)
*   **Guide technique AIOSEO** : [SKILL.md](../../skills/aioseo-verification/SKILL.md)

---

## 1. Choix du Moule JSON (TECH & APPLIANCE)

Avant d'engager la rédaction unitaire sur le modèle parent, l'agent doit sélectionner le gabarit normé V3.4 dans le répertoire [Templates/](../../../Templates/) :

| Typologie de Produit | Fichier Gabarit JSON V3.4 | Exemples Types |
| :--- | :--- | :--- |
| **Smartphone / Tablette** | [Template_Pack_v3_smartphone.json](../../../Templates/Template_Pack_v3_smartphone.json) | Galaxy S24 Ultra, iPhone 16 Pro, Poco F7, Redmi Pad 2 |
| **PC Portable (Laptop)** | [Template_Pack_v3_pc_portable.json](../../../Templates/Template_Pack_v3_pc_portable.json) | MacBook Pro, HP Pavilion, Blackview AceBook |
| **PC Bureau / Mini PC / AIO** | [Template_Pack_v3_pc_bureau.json](../../../Templates/Template_Pack_v3_pc_bureau.json) | iMac, Dell OptiPlex, Mini PC MP200 |
| **Périphérique & Accessoire** | [Template_Pack_v3_peripherique.json](../../../Templates/Template_Pack_v3_peripherique.json) | Clavier Logitech, Souris sans fil, Chargeurs |
| **Stockage Amovible / SSD** | [Template_Pack_v3_stockage.json](../../../Templates/Template_Pack_v3_stockage.json) | SSD NVMe Samsung, Clé SanDisk, MicroSD |
| **Imprimante & Scanner** | [Template_Pack_v3_imprimante.json](../../../Templates/Template_Pack_v3_imprimante.json) | HP LaserJet, Canon MegaTank, Epson EcoTank |
| **Audio (Écouteurs, Casques, Enceintes)** | [Template_Pack_v3_audio.json](../../../Templates/Template_Pack_v3_audio.json) | AirPods Pro, HiFuture FutureMate, JBL Flip |
| **Wearable (Montres & Bracelets)** | [Template_Pack_v3_wearable.json](../../../Templates/Template_Pack_v3_wearable.json) | Apple Watch, Galaxy Watch Ultra, HiFuture Aura |
| **Électroménager & Froid** | [Template_Pack_v3_appliance.json](../../../Templates/Template_Pack_v3_appliance.json) | Réfrigérateurs Nasco/Hisense, Climatiseurs Midea |

---

## 2. Le Processus des 3 Personas Industriels

Pour garantir l'excellence et éradiquer le texte générique ou paresseux, la rédaction applique séquentiellement 3 personas :

### ✍️ Persona 1 : Copywriter Factualité Dynamique & Usage Quotidien
*   **Zéro Hyperbole / Exagération** : Proscription formelle de tout superlatif publicitaire :
    *   *Mots strictement interdits (détectés par script d'audit)* : *incroyable, révolutionnaire, le summum, chef-d'œuvre, époustouflant, inégalé, sans précédent, spectaculaire, phénoménal, exceptionnel, extraordinaire, magique, sublime, ultime, parfait, fabuleux, formidable, merveilleux, prodigieux, monstrueux, colossal, vertigineux, inestimable, magistral, sensationnel, invulnérable, rutilant, impitoyable, insolence, terrible, somptueux, luxueux, coûteux, décupler, panoramique inédit*.
*   **Calibrage par Gamme** : Le ton met en valeur les bénéfices concrets dans son **usage quotidien** selon la catégorie de prix :
    *   *Entrée de gamme* : Fiabilité pratique, simplicité d'accès, autonomie rassurante, robustesse et maîtrise du budget.
    *   *Milieu de gamme* : Polyvalence, réactivité, confort multimédia (90Hz/120Hz), rapport performance/prix.
    *   *Flagship / Premium* : Haute précision des composants, puissance de calcul, durabilité des finitions (verre trempé, titane, IP68).
*   **Pureté de l'Introduction (`intro_paragraph`)** : Focus 100% produit. Interdiction formelle d'y insérer des mentions promotionnelles de réassurance boutique.

### 🔍 Persona 2 : Expert SEO AIOSEO (TruSEO)
*   **Longueur des Phrases** : **0% de phrases longues (> 20 mots)**. Viser des phrases courtes et rythmées de 12 à 18 mots.
*   **Transitions & Formule Fixe 15/41 (36.5%)** :
    *   Score de mots de transition strictement **> 30% et < 50%** (cible idéale 31% à 49%).
    *   Formule fixe : Viser 15 phrases avec connecteur sur 41 (3 dans l'intro, 4 dans chaque section H2).
    *   **Fluidité syntaxique** : Insérer harmonieusement les connecteurs au cœur de la phrase (*"...assure ainsi..."*, *"...garantit en outre..."*) plutôt que de débuter systématiquement par *"En effet,... De plus,..."*.
*   **Titres SEO Standard B (Top Specs & Intent)** :
    *   `short_description.seo.meta_title` : `Acheter [MARQUE] [MODÈLE] ([RAM]/[ROM]) à Abidjan | My-eStore` (50-60 car.)
    *   `long_description.seo.meta_title` : `[MARQUE] [MODÈLE] [ROM] : [Top Spec 1] & [Top Spec 2] | My-eStore`
    *   `long_description.h1` : `[MARQUE] [MODÈLE] : [Top Spec 1], [Top Spec 2] et [Top Spec 3]`
*   **Bloc de Tags WooCommerce Enrichis (10 à 14 Tags)** :
    *   Ordre normé : `[MARQUE]`, `[MODÈLE]`, `[SÉRIE]`, `[TYPOLOGIE/OS]`, `[RÉSEAU]`, `[ÉCRAN]`, `[PHOTO]`, `[BATTERIE]`, `[SOC]`, `[ATOUT]`, `Abidjan`, `My-eStore`.

### ⚙️ Persona 3 : Intégrateur & Contrôleur de Structure V3.4
*   **Emplacement de `full_specs`** : Le tableau technique complet doit être impérativement positionné **à l'intérieur de `long_description`**, immédiatement au-dessus du bloc `cta`.
*   **Bloc CTA Standardisé** :
    ```json
    "cta": {
        "top_link": "#",
        "top_label": "Remonter pour commander",
        "boutiques_link": "https://my-estore.com/boutiques-officielles/",
        "boutiques_label": "Nos Boutiques Officielles"
    }
    ```
*   **Règle des 3 Liens Sources Neutres** : 1 boutique constructeur + 2 requêtes génériques Google. Zéro lien concurrent sortant.
*   **Ordre Officiel des Attributs WooCommerce** :
    1. `Couleur` | 2. `Stockage` | 3. `RAM` | 4. `Processeur` *(PC)* ou `Poids` *(format `X.XXX kg`)* | 5. `Réseau`.

---

## 3. Limites de Longueur & Word Count

*   **Description Longue Globale** : **450 à 650 mots** de texte visible.
*   **Paragraphe d'Introduction** : Maximum **100 mots**.
*   **Paragraphes des Sections H2** : **45 à 60 mots** par paragraphe.
*   **Description Courte** : Résumé direct en HTML pur (paragraphe d'accroche ≤60 mots, 4 puces caractéristiques fortes, slogan de conclusion en `<em>`, 0 balise `<div>` ou styles CSS inline).
