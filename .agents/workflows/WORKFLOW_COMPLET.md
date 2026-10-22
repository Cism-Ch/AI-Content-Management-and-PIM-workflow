---
name: WORKFLOW_COMPLET
description: "Carte d'État-Major de l'usine agentique (Architecture V3.4 Parent-First Audit Gate). Cartographie des 5 agents autonomes."
---

# 🚀 Écosystème des Agents Autonomes (Architecture V3.4 — Parent-First Audit Gate)

Ce document constitue la **carte d'état-major** de l'usine de production e-commerce. La production repose sur un écosystème de **5 Agents Spécialisés** qui collaborent de manière déterministe sous la supervision du Chef d'Atelier ([/master-orchestrator](master-orchestrator.md)).

> **💡 INNOVATION ARCHITECTURALE V3.4** : Tous les audits éditoriaux (AIOSEO, Lisibilité, Zero Hyperbole) et techniques (`paired_variants`) sont réalisés **sur les Modèles Parents (`product-data/`) AVANT toute duplication**. Cela garantit la perfection absolue des contenus sources et élimine 100% de la réplication d'erreurs sur les déclinaisons.

---

## 🗺️ Cartographie des 5 Agents Spécialisés

| Agent | Rôle & Persona | Commande / Workflow |
| :--- | :--- | :--- |
| **1. Orchestrateur** | Le "Chef d'Atelier V3.4". Point d'entrée unique. Pilote la chaîne bout-en-bout. | [`/master-orchestrator [Produit]`](master-orchestrator.md) |
| **2. Investigateur** | L'Agent Data. Récupère et certifie les specs techniques constructeurs. | [`/generate-product-data`](generate-product-data.md) |
| **3. Maker (Tech / Appliance)** | Le Rédacteur. Rédaction unitaire 3 Personas (Copywriter, SEO AIOSEO, Intégrateur). | [`/production-industrielle-v3`](production-industrielle-v3.md) ou [`/produce-appliance`](produce-appliance.md) |
| **4. Checker (QA)** | L'Inspecteur Qualité. Exécute la suite d'audits Python et valide le Gate Parent bloquant. | [`/audit-product-pack`](audit-product-pack.md) |
| **5. Script Specialist** | Le Gardien Python. Seul agent habilité à modifier ou déboguer les scripts système. | [`/script-specialist`](script-specialist.md) |

---

## 🎯 Le Flux de Travail Industriel (V3.4 Parent-First)

```
                    [VOUS] → /master-orchestrator
                                   ↓
        1. /generate-product-data (Extraction JSON Technique Parent Certifié)
                                   ↓
        2. /production-industrielle-v3 (Rédaction 3 Personas V3.4 sur JSON Parent)
                                   ↓
        3. /audit-product-pack (GATE AUDIT QUALITÉ QA SUR PARENT)
           ├─ (Échec QA) ──> Ré-écriture par le Maker sur le Parent
           └─ (Statut 100% PASS) ──> Autorisation de Compilation & Export
                                   ↓
        4. Compilation HTML Parent (Sans Duplication Physique de Dossiers)
                                   ↓
        5. Build CSV WooCommerce Final (Ligne Variable Parent + Lignes Variations Enfants)
```

---

## 📏 Règles Absolues & Contraintes Normatives V3.4

> [!CAUTION]
> **DIRECTIVE IMPÉRATIVE** : Aucun agent ne doit générer de specs techniques depuis sa mémoire interne.
> Tous les workflows de production sont soumis à [`VERIFICATION_IMPERATIVE.md`](../directives/VERIFICATION_IMPERATIVE.md).

| Métrique / Règle | Norme V3.4 | Cible & Standard |
| :--- | :--- | :--- |
| **Audit Gate** | Parent-First | 100% des tests validés sur `product-data/` avant compilation. |
| **Déclinaisons** | `paired_variants` | Couples réels constructeur uniquement (0% d'erreur cartésienne). |
| **SEO Meta Title (Short)** | Intention d'Achat Locale | `Acheter [MARQUE] [MODÈLE] ([RAM]/[ROM]) à Abidjan \| My-eStore` (50-60 car.) |
| **SEO Meta Title (Long)** | Top Specs & Atouts Majeurs | `[MARQUE] [MODÈLE] [ROM] : [Top Spec 1] & [Top Spec 2] \| My-eStore` |
| **Accroche H1** | Standard B Top Specs | `[MARQUE] [MODÈLE] : [Top Spec 1], [Top Spec 2] et [Top Spec 3]` |
| **Tags WooCommerce** | Enrichis & Géolocalisés | **10 à 14 Tags** précis (Marque, Modèle, Réseau, SoC, Batterie, Abidjan, My-eStore). |
| **Mots de Transition** | Formule Fixe 15/41 | **36.5%** de transitions (cible stricte 31% à 49%). |
| **Longueur des Phrases** | Seuil AIOSEO Stricte | **0% de phrases > 20 mots** (phrases de 12 à 18 mots). |
| **Poids** | Normalisé en kilogrammes | Renseigné sous `Attribute 4` (ex: `0.195 kg` ou `1.250 kg`). |
| **Liens Sources** | Règle des 3 Liens Neutres | 1 boutique officielle constructeur + 2 requêtes neutres (0 lien concurrent). |

---

## ▶️ Pour Commencer

Une seule commande permet d'orchestrer la production d'un modèle ou d'une gamme entière :
👉 **`/master-orchestrator [Nom du Produit ou de la Gamme]`**

---

**Version** : 3.4 (Parent-First Audit Gate)  
**Norme de référence** : [AGENTS.md](../../AGENTS.md)  
