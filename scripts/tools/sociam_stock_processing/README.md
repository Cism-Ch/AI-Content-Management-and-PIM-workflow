# Outils Universels de Traitement du Stock (Sociam)

Ces outils permettent d'extraire et d'appliquer automatiquement les prix et les couleurs pour **n'importe quelle marque** (Midea, Nasco, Samsung, LG, etc.) à partir du fichier Excel de stock global.

## Structure

- `stock_extractor.py` : Scanne l'Excel pour créer des maps JSON universelles (Prix, Couleurs).
- `stock_applier.py` : Parcourt les fichiers CSV d'importation WooCommerce et applique les données en utilisant une correspondance par SKU intelligente.
- `stock_search.py` : Outil de recherche universelle par mots-clés (marque, catégorie, etc.).
- `stock_details.py` : Outil pour obtenir les détails (prix, couleur, désignation) d'une liste spécifique de SKUs.
- `data/` : Contient les fichiers JSON générés.

## Utilisation

### 1. Recherche de modèles

Utilisez cet outil pour trouver les modèles correspondants à une marque ou une catégorie :

```bash
python scripts/sociam_stock_processing/stock_search.py MIDEA CONGELATEUR
```

### 2. Obtention des détails (Prix/Couleurs)

Utilisez cet outil pour préparer vos listes de prix avant production :

```bash
python scripts/sociam_stock_processing/stock_details.py SKU1 SKU2 SKU3
```

### 3. Extraction et Application massive

1. Mettez à jour les bases JSON :
    ```bash
    python scripts/sociam_stock_processing/stock_extractor.py
    ```
2. Appliquez les données à tous les CSV concernés :
    ```bash
    python scripts/sociam_stock_processing/stock_applier.py
    ```

## Points Forts

- **Multi-Marques** : Plus de limitation à Midea. Fonctionne pour tout le catalogue Sociam.
- **SKU Intelligent** : Gère les préfixes (MIDEA-, NASCO-, GAZ\_, etc.) et les variations de format (tirets, slashs).
- **Extensible** : Vous pouvez ajouter de nouveaux mots-clés de couleurs dans `stock_extractor.py`.
