---
name: copywriting-remediation
description: >-
  Audits and rewrites hyperbolic copywriting (superlatives/PR exaggerations) into neutral, factual French across any product brand folders.
---

# Copywriting Remediation

## Overview
Ce skill permet aux agents d'auditer et d'assainir de façon autonome les textes rédactionnels (descriptions courtes et longues) des packs de produits dans le projet My-eStore. Il garantit la conformité stricte avec la charte rédactionnelle de neutralité V3.2 en éliminant les expressions de sur-marketing publicitaire.

## Dependencies
- Ce skill s'appuie sur le script utilitaire de projet [copywriting_remediation.py](file:///c:/Users/My-eStore-PC2/My-eStore-workspace/wordpress/scripts/tools/data_processing/copywriting_remediation.py).

## Quick Start
Pour vérifier la conformité rédactionnelle d'un dossier de produits d'une marque (ex: Hisense) :

1. **Détection et Rapport** :
   ```bash
   python scripts/tools/data_processing/copywriting_remediation.py detect --products-dir "products/hisense-all" --output "C:\Users\My-eStore-PC2\.gemini\antigravity-ide\brain\56536fd8-5ec1-46d8-999b-12fcd821c733\failing_exaggerations.md"
   ```

2. **Correction des JSON sources** :
   Si le rapport contient des échecs, lancez la réécriture :
   ```bash
   python scripts/tools/data_processing/copywriting_remediation.py rewrite --products-dir "products/hisense-all"
   ```

3. **Recompilation & QA** :
   Recompilez ensuite la marque pour propager les corrections sur les HTML et le CSV WooCommerce consolidé.

## Utility Scripts
Le script [copywriting_remediation.py](file:///c:/Users/My-eStore-PC2/My-eStore-workspace/wordpress/scripts/tools/data_processing/copywriting_remediation.py) propose les commandes suivantes :

### `detect`
Scanne récursivement tous les fichiers `pack-data-*.json` sous `--products-dir` et cherche les correspondances avec les mots-clés d'exagération (ex: *monstrueux*, *majestueusement*, *fièrement*, *merveille*, *pulvérise*, etc.).
- **Arguments requis** :
  - `--products-dir` : chemin absolu ou relatif vers le dossier de la marque.
  - `--output` : chemin absolu pour le fichier de rapport Markdown.

### `rewrite`
Remplace les expressions d'exagération trouvées dans les champs textuels des JSON par des alternatives neutres (ex: *pulvérise les limites* ➔ *dépasse les limites*).
- **Arguments requis** :
  - `--products-dir` : chemin absolu ou relatif vers le dossier de la marque.

## Common Mistakes
- **Oublier la recompilation** : Après avoir exécuté `rewrite`, n'oubliez pas de lancer la compilation de la marque (`rebuild_all_v32.py`), sinon le CSV WooCommerce importé contiendra encore les anciennes phrases exagérées.
- **Chemins incorrects** : Veillez à spécifier le bon dossier de marque (`products/nom-de-la-marque`).
