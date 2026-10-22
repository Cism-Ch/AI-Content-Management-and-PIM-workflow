# 🧰 WooCommerce CSV Toolkit

Scripts utilitaires pour corriger et enrichir les fichiers CSV d'import WooCommerce.

---

## 📂 Fichiers Associés

| Fichier | Rôle |
|---|---|
| `wc_csv_toolkit.py` | **Outil principal** – toolkit unifié avec 4 sous-commandes |
| `../../Pricing/color_rules_default.json` | Règles de couleur par défaut (extensibles par projet) |
| `../../Pricing/nasco_ac_prices.json` | Exemple de fichier de prix pour les climatiseurs NASCO |
| `wc_json_fix_config.json` | Configuration pour le correcteur d'attributs JSON |
| `wc_json_attributes_fixer.py` | Normalisateur d'attributs JSON |
| `wc_csv_attr_patcher.py` | Injecteur d'attributs manquants dans les CSV |

---

## 🚀 Utilisation

### Syntaxe générale

```bash
python wc_csv_toolkit.py <sous-commande> --csv <fichier.csv> [options]
```

---

### 1️⃣ `prices` — Mise à jour des prix

Met à jour la colonne **Regular price** de chaque ligne dont le SKU correspond à une entrée du fichier JSON.

```bash
python wc_csv_toolkit.py prices \
  --csv products.csv \
  --json prices.json
```

**Format du JSON :**
```json
{
  "BRAND-SKU-001": "149900",
  "BRAND-SKU-002": "269900"
}
```

**Options :**
| Option | Défaut | Description |
|---|---|---|
| `--csv` | *(requis)* | Chemin vers le CSV d'entrée |
| `--json` | *(requis)* | Fichier JSON `{SKU: prix}` |
| `--col` | `Regular price` | Nom de la colonne à remplir |
| `--out` | `<stem>-priced.csv` | Fichier de sortie |

---

### 2️⃣ `colors` — Correction des couleurs manquantes

Remplit les colonnes `Attribute N name/value(s)/default` pour les lignes sans couleur.

```bash
# Avec les règles par défaut
python wc_csv_toolkit.py colors --csv products.csv

# Avec un fichier de règles personnalisé
python wc_csv_toolkit.py colors --csv products.csv --rules color_rules_default.json

# Forcer l'écrasement des couleurs existantes
python wc_csv_toolkit.py colors --csv products.csv --overwrite
```

**Options :**
| Option | Défaut | Description |
|---|---|---|
| `--rules` | *(intégré)* | JSON de règles personnalisées |
| `--attr` | `1` | Indice de l'attribut WooCommerce (1, 2, 3…) |
| `--overwrite` | `False` | Remplace aussi les couleurs déjà renseignées |
| `--out` | `<stem>-colored.csv` | Fichier de sortie |

**Format du JSON de règles :**
```json
{
  "sku_map": {
    "BRAND-SKU-MIRROR-12": "Noir Miroir"
  },
  "keyword_rules": [
    ["MIRROR",  "Noir Miroir"],
    ["SILVER",  "Blanc / Bande Silver"],
    ["INOX",    "Inox"]
  ],
  "fallback": "Blanc"
}
```

> Les règles `keyword_rules` sont des **regex** cherchées dans `SKU + Name` (insensible à la casse).  
> Les règles sont évaluées dans l'ordre ; la première qui matche gagne.

---

### 3️⃣ `clean-tags` — Nettoyage des tags

Supprime les patterns indésirables de la colonne **Tags** (virgules résiduelles nettoyées automatiquement).

```bash
python wc_csv_toolkit.py clean-tags \
  --csv products.csv \
  --remove "Côte d'Ivoire" "LSI Keywords"
```

**Options :**
| Option | Défaut | Description |
|---|---|---|
| `--remove` | *(requis)* | Un ou plusieurs patterns regex à supprimer |
| `--out` | `<stem>-cleaned.csv` | Fichier de sortie |

---

### 4️⃣ `all` — Passe complète

Enchaîne les 3 opérations en une seule lecture/écriture : **prices → colors → clean-tags**.

```bash
python wc_csv_toolkit.py all \
  --csv products.csv \
  --json prices.json \
  --rules color_rules_default.json \
  --remove "Côte d'Ivoire"
```

**Options :** toutes les options des 3 commandes précédentes sont disponibles.

---

## 💡 Exemples concrets

### Climatiseurs NASCO (tout en une passe)
```bash
python wc_csv_toolkit.py all \
  --csv "c:/Users/hanok/wordpress/Exports/CSV_Imports/Appliance/products-import-appliance-climatiseurs-20260325.csv" \
  --json "c:/Users/hanok/wordpress/scripts/tools/data_processing/nasco_ac_prices.json" \
  --rules "c:/Users/hanok/wordpress/scripts/tools/data_processing/color_rules_default.json" \
  --remove "Côte d'Ivoire"
```

### Nettoyer uniquement les tags d'un CSV existant
```bash
python wc_csv_toolkit.py clean-tags \
  --csv import-produits.csv \
  --remove "Côte d'Ivoire" "LSI Keywords" "Focus Keyword"
```

### Corriger les couleurs avec un attribut 2 (si Attribute 1 = Taille)
```bash
python wc_csv_toolkit.py colors \
  --csv import-vetements.csv \
  --attr 2 \
  --rules color_rules_vetements.json
```

---

## 📝 Notes

- Tout fichier de sortie est encodé en **UTF-8 BOM** (`utf-8-sig`) pour la compatibilité Excel.
- Le nom du fichier de sortie est généré automatiquement (suffixe `-priced`, `-colored`, `-cleaned`, `-final`) sauf si `--out` est précisé.
- Le mode `all` produit directement un suffixe `-final` sans fichiers intermédiaires.
