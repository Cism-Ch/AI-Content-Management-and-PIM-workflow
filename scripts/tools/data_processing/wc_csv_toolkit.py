#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     WooCommerce CSV Toolkit                                  ║
║                     Outils de correction & enrichissement CSV                ║
╚══════════════════════════════════════════════════════════════════════════════╝

SOUS-COMMANDES DISPONIBLES :
  prices      - Met à jour les prix depuis un fichier JSON  {SKU: prix}
  colors      - Corrige les attributs Color manquants via règles SKU/nom
  clean-tags  - Supprime des mots-clés indésirables des tags
  all         - Enchaîne prices + colors + clean-tags en une seule passe

EXEMPLES :
  # Mettre à jour les prix
  python wc_csv_toolkit.py prices --csv products.csv --json prices.json

  # Corriger les couleurs
  python wc_csv_toolkit.py colors --csv products.csv --rules rules.json

  # Nettoyer les tags
  python wc_csv_toolkit.py clean-tags --csv products.csv --remove "Côte d'Ivoire" "LSI Keywords"

  # Tout en une passe
  python wc_csv_toolkit.py all --csv products.csv --json prices.json --rules rules.json --remove "Côte d'Ivoire"
"""

import csv
import json
import re
import argparse
import sys
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------------
# UTILITAIRES COMMUNS
# --------------------------------------------------------------------------------

def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    """Lit un CSV WooCommerce (encodage utf-8-sig pour Excel)."""
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    print(f"  [FILE] Lecture : {path.name} ({len(rows)} lignes)")
    return fieldnames, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]):
    """Écrit un CSV WooCommerce (encodage utf-8-sig pour Excel)."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [FILE] Ecriture : {path.name}")


def make_output_path(input_path: Path, suffix: str, out_arg: Optional[str] = None) -> Path:
    """Génère un nom de fichier de sortie avec suffix si --out n'est pas spécifié."""
    if out_arg:
        return Path(out_arg)
    stem = input_path.stem
    # Évite d'empiler les suffixes si déjà présent
    for known in ("-priced", "-colored", "-cleaned", "-final"):
        stem = stem.replace(known, "")
    return input_path.with_name(stem + suffix + ".csv")


def print_separator(title: str):
    print("\n" + "="*60)
    print(f"  [GEAR] {title}")
    print("="*60)


# --------------------------------------------------------------------------------
# MODULE 1 : MISE À JOUR DES PRIX
# --------------------------------------------------------------------------------

def apply_prices(rows: list[dict], prices: dict, price_col: str = "Regular price") -> int:
    """
    Met à jour la colonne `price_col` des lignes dont le SKU est dans `prices`.
    Retourne le nombre de lignes mises à jour.
    """
    updated = 0
    for row in rows:
        sku = row.get("SKU", "")
        if sku in prices:
            old = row.get(price_col, "")
            row[price_col] = str(prices[sku])
            updated += 1
            label = f"+{prices[sku]}" if not old else f"{old} -> {prices[sku]}"
            print(f"  PRICE [{sku}] {label}")
    return updated


def cmd_prices(args):
    print_separator("Mise à jour des prix")

    csv_path  = Path(args.csv)
    json_path = Path(args.json)
    out_path  = make_output_path(csv_path, "-priced", args.out)

    with open(json_path, "r", encoding="utf-8") as f:
        prices = json.load(f)
    print(f"  [INFO] {len(prices)} prix chargés depuis {json_path.name}")

    fieldnames, rows = read_csv(csv_path)
    updated = apply_prices(rows, prices, args.col)
    write_csv(out_path, fieldnames, rows)

    print(f"\n  [OK] Prix mis à jour : {updated}/{len(rows)}")
    return out_path


# --------------------------------------------------------------------------------
# MODULE 2 : CORRECTION DES COULEURS
# --------------------------------------------------------------------------------

# Règles de fallback keyword -> couleur (cherché dans SKU ou Name)
DEFAULT_COLOR_RULES = [
    # (regex_pattern, couleur_résultante)
    (r"MIRROR",            "Noir Miroir"),
    (r"MIROIR",            "Noir Miroir"),
    (r"BLACK",             "Noir"),
    (r"SILVER|BANDE.SILVER|M24N1-N", "Blanc / Bande Silver"),
    (r"INOX",              "Inox"),
    (r"GRIS",              "Gris"),
]
DEFAULT_COLOR_FALLBACK = "Blanc"


def load_color_rules(rules_path: Optional[str]):
    """
    Charge des règles JSON au format :
    {
      "sku_map": { "SKU-EXACT": "Couleur" },
      "keyword_rules": [ ["REGEX_PATTERN", "Couleur"] ],
      "fallback": "Blanc"
    }
    Si rules_path est None, utilise les règles par défaut codées ci-dessus.
    """
    if rules_path:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sku_map       = data.get("sku_map", {})
        keyword_rules = [(r, c) for r, c in data.get("keyword_rules", [])]
        fallback      = data.get("fallback", DEFAULT_COLOR_FALLBACK)
        print(f"  [INFO] Règles couleur : {len(sku_map)} SKU exacts, {len(keyword_rules)} regex")
    else:
        sku_map       = {}
        keyword_rules = DEFAULT_COLOR_RULES
        fallback      = DEFAULT_COLOR_FALLBACK
        print(f"  [INFO] Règles couleur : règles par défaut ({len(keyword_rules)} regex)")
    return sku_map, keyword_rules, fallback


def infer_color(sku: str, name: str, sku_map: dict, keyword_rules: list, fallback: str) -> str:
    """Déduit la couleur depuis le SKU ou le nom en appliquant les règles dans l'ordre."""
    # 1. Correspondance SKU exacte
    if sku in sku_map:
        return sku_map[sku]
    # 2. Regex sur SKU+Name (combinés)
    combined = f"{sku} {name}".upper()
    for pattern, color in keyword_rules:
        if re.search(pattern.upper(), combined):
            return color
    return fallback


def apply_colors(rows: list[dict], sku_map: dict, keyword_rules: list,
                 fallback: str, attr_idx: int = 1, overwrite: bool = False) -> int:
    """
    Corrige les attributs Color manquants.
    attr_idx : numéro de l'attribut WooCommerce (1 = Attribute 1 name, etc.)
    overwrite : si True, remplace même les valeurs existantes.
    """
    col_name    = f"Attribute {attr_idx} name"
    col_values  = f"Attribute {attr_idx} value(s)"
    col_default = f"Attribute {attr_idx} default"
    col_visible = f"Attribute {attr_idx} visible"

    fixed = 0
    for row in rows:
        has_color = (
            (row.get(col_name)    or "").strip() and
            (row.get(col_values)  or "").strip() and
            (row.get(col_default) or "").strip()
        )
        if has_color and not overwrite:
            continue

        sku   = row.get("SKU", "")
        name  = row.get("Name", "")
        color = infer_color(sku, name, sku_map, keyword_rules, fallback)

        row[col_name]    = "Color"
        row[col_values]  = color
        row[col_default] = color
        row[col_visible] = "1"
        fixed += 1
        print(f"  [COLOR] [{sku}] -> {color}")
    return fixed


def cmd_colors(args):
    print_separator("Correction des couleurs")

    csv_path = Path(args.csv)
    out_path = make_output_path(csv_path, "-colored", args.out)
    sku_map, keyword_rules, fallback = load_color_rules(args.rules)

    fieldnames, rows = read_csv(csv_path)
    fixed = apply_colors(rows, sku_map, keyword_rules, fallback,
                         attr_idx=args.attr, overwrite=args.overwrite)
    write_csv(out_path, fieldnames, rows)

    print(f"\n  [OK] Couleurs corrigées : {fixed}/{len(rows)}")
    return out_path


# --------------------------------------------------------------------------------
# MODULE 3 : NETTOYAGE DES TAGS
# --------------------------------------------------------------------------------

def apply_clean_tags(rows: list[dict], patterns: list[str]) -> int:
    """
    Supprime les patterns (regex) de la colonne Tags.
    Chaque pattern est cherché de manière insensible à la casse.
    La virgule précédant ou suivant le match est également supprimée.
    """
    # Compose un regex qui supprime aussi les virgules/espaces adjacents
    combined_pat = "|".join(
        r",?\s*(?:" + p + r")(\s*,)?" for p in patterns
    )
    cleaned_count = 0

    for row in rows:
        raw  = row.get("Tags", "") or ""
        clean = re.sub(combined_pat, "", raw, flags=re.IGNORECASE)
        # Nettoyage résiduel des virgules doubles / espaces
        clean = re.sub(r",\s*,", ",", clean)
        clean = clean.strip().strip(",").strip()

        if clean != raw:
            row["Tags"] = clean
            cleaned_count += 1

    return cleaned_count


def cmd_clean_tags(args):
    print_separator("Nettoyage des tags")

    csv_path = Path(args.csv)
    out_path = make_output_path(csv_path, "-cleaned", args.out)

    if not args.remove:
        print("  [WARN] Aucun pattern --remove fourni. Rien à faire.")
        return csv_path

    print(f"  [INFO] Patterns à supprimer : {args.remove}")

    fieldnames, rows = read_csv(csv_path)
    cleaned = apply_clean_tags(rows, args.remove)
    write_csv(out_path, fieldnames, rows)

    print(f"\n  [OK] Lignes de tags modifiées : {cleaned}/{len(rows)}")
    return out_path


# --------------------------------------------------------------------------------
# MODULE 4 : PASSE COMPLÈTE (all)
# --------------------------------------------------------------------------------

def cmd_all(args):
    print_separator("Passe complète (prices -> colors -> clean-tags)")

    csv_path = Path(args.csv)
    out_path = make_output_path(csv_path, "-final", args.out)

    fieldnames, rows = read_csv(csv_path)

    # ── Étape 1 : Prix ───────────────────────────────────────────────────────
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            prices = json.load(f)
        print(f"\n  [1/3] [PRICE] Prix ({len(prices)} entrées)")
        updated = apply_prices(rows, prices, args.col)
        print(f"        -> {updated} mis à jour")
    else:
        print("\n  [1/3] [PRICE] Prix — ignoré (--json non fourni)")

    # ── Étape 2 : Couleurs ───────────────────────────────────────────────────
    print(f"\n  [2/3] [COLOR] Couleurs")
    sku_map, keyword_rules, fallback = load_color_rules(args.rules)
    fixed = apply_colors(rows, sku_map, keyword_rules, fallback,
                         attr_idx=args.attr, overwrite=args.overwrite)
    print(f"        -> {fixed} corrigées")

    # ── Étape 3 : Tags ───────────────────────────────────────────────────────
    if args.remove:
        print(f"\n  [3/3] Tags — suppression : {args.remove}")
        cleaned = apply_clean_tags(rows, args.remove)
        print(f"        -> {cleaned} lignes modifiées")
    else:
        print("\n  [3/3] Tags — ignoré (--remove non fourni)")

    write_csv(out_path, fieldnames, rows)
    print(f"\n  [OK] Fichier final : {out_path.name}")
    return out_path


# --------------------------------------------------------------------------------
# POINT D'ENTRÉE CLI
# --------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wc_csv_toolkit",
        description="WooCommerce CSV Toolkit – Correction & enrichissement de fichiers CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── Commun à toutes les sous-commandes ────────────────────────────────────
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--csv",  required=True, help="Chemin vers le CSV WooCommerce d'entrée")
    parent.add_argument("--out",  default=None,  help="Chemin de sortie (auto si absent)")

    # ── prices ────────────────────────────────────────────────────────────────
    p_prices = sub.add_parser("prices", parents=[parent],
                              help="Mettre à jour les prix depuis un JSON {SKU: prix}")
    p_prices.add_argument("--json", required=True, help="Fichier JSON {SKU: prix}")
    p_prices.add_argument("--col",  default="Regular price",
                          help="Nom de la colonne prix (défaut: 'Regular price')")
    p_prices.set_defaults(func=cmd_prices)

    # ── colors ────────────────────────────────────────────────────────────────
    p_colors = sub.add_parser("colors", parents=[parent],
                              help="Corriger les attributs Color manquants")
    p_colors.add_argument("--rules",     default=None,
                          help="JSON de règles {sku_map, keyword_rules, fallback} (optionnel)")
    p_colors.add_argument("--attr",      type=int, default=1,
                          help="Indice de l'attribut WooCommerce (défaut: 1)")
    p_colors.add_argument("--overwrite", action="store_true",
                          help="Remplace les couleurs existantes aussi")
    p_colors.set_defaults(func=cmd_colors)

    # ── clean-tags ────────────────────────────────────────────────────────────
    p_tags = sub.add_parser("clean-tags", parents=[parent],
                             help="Supprimer des mots/patterns des tags")
    p_tags.add_argument("--remove", nargs="+", metavar="PATTERN",
                        help="Patterns regex à supprimer des tags (ex: \"Côte d'Ivoire\")")
    p_tags.set_defaults(func=cmd_clean_tags)

    # ── all ───────────────────────────────────────────────────────────────────
    p_all = sub.add_parser("all", parents=[parent],
                            help="Passe complète : prices + colors + clean-tags")
    p_all.add_argument("--json",    default=None, help="JSON {SKU: prix} (optionnel)")
    p_all.add_argument("--col",     default="Regular price",
                       help="Colonne prix (défaut: 'Regular price')")
    p_all.add_argument("--rules",   default=None, help="JSON de règles de couleur (optionnel)")
    p_all.add_argument("--attr",    type=int, default=1,
                       help="Indice attribut couleur (défaut: 1)")
    p_all.add_argument("--overwrite", action="store_true")
    p_all.add_argument("--remove",  nargs="*", metavar="PATTERN", default=None,
                       help="Patterns tags à supprimer")
    p_all.set_defaults(func=cmd_all)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args   = parser.parse_args()
    result = args.func(args)
    print(f"\n{'='*60}")
    print(f"  [OK] Termine -> {Path(result).name if result else 'OK'}")
    print(f"{'='*60}\n")
