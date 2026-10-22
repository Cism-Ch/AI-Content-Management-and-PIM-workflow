#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wc_csv_attr_patcher.py
=======================
Outil GENERAL de patch des attributs manquants dans un CSV WooCommerce.
Lit les donnees depuis les JSON de pack produit et les injecte dans le CSV.

Compatible avec toutes les series/marques du projet (Blackview, Samsung, Xiaomi, etc.)

Cas d'usage type :
  - Le CSV a ete genere depuis des JSON sans attribut RAM
  - On veut patcher le CSV directement depuis les JSON sources
  - Alternative au re-build complet de la serie

Usage :
  python wc_csv_attr_patcher.py \\
    --csv products/blackview-all/import-v2-blackview-all.csv \\
    --json-dir products/blackview-all \\
    --attr RAM

  python wc_csv_attr_patcher.py \\
    --csv products/samsung-galaxy-a-all/import-v2-samsung-galaxy-a-all.csv \\
    --json-dir products/samsung-galaxy-a-all \\
    --attr RAM --dry-run --verbose

Arguments :
  --csv           Chemin vers le fichier CSV WooCommerce a patcher
  --json-dir      Dossier contenant les sous-dossiers produits (avec pack-data-*.json)
  --attr          Nom de l'attribut a verifier/injecter (ex: RAM, Stockage, Couleur)
  --config        Chemin vers la config JSON (defaut: wc_json_fix_config.json)
  --dry-run       Simulation sans ecriture
  --verbose       Affichage detaille
  --no-backup     Desactiver la creation du backup CSV (.bak)
  --skip-types    Types de lignes a ignorer (defaut: variation)
"""

import os
import re
import sys
import csv
import json
import shutil
import argparse
from datetime import datetime

# ──────────────────────────────────────────────────────────────
#  Chemins par defaut
# ──────────────────────────────────────────────────────────────
SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG  = os.path.join(SCRIPT_DIR, "wc_json_fix_config.json")
WORKSPACE_ROOT  = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))


# ══════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════

def load_config(config_path: str) -> dict:
    if not os.path.isfile(config_path):
        print(f"[ERROR] Fichier de config introuvable : {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════
#  EXTRACTION VALEUR DEPUIS JSON
# ══════════════════════════════════════════════════════════════

def normalize_value(raw: str, patterns: list) -> str:
    """Applique les patterns de normalisation."""
    for p in patterns:
        m = re.search(p["regex"], raw, re.IGNORECASE)
        if m:
            return p["output"].replace("{n}", m.group(1))
    return raw.strip()


def extract_attr_from_json(json_path: str, attr_name: str, config: dict) -> str | None:
    """
    Extrait la valeur d'un attribut depuis un JSON de pack produit.
    Cherche dans :
      1. woocommerce_csv > Attribute N name == attr_name
      2. full_specs > sections[Performances] > rows matching attr_name
      3. Tags regex
      4. Full text regex
    Retourne la valeur normalisee ou None.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [WARN] Impossible de lire {json_path}: {e}")
        return None

    woo = data.get("woocommerce_csv", {})

    # Trouver la config pour cet attribut
    attr_cfg = next(
        (a for a in config.get("attributes_to_inject", [])
         if a.get("name", "").upper() == attr_name.upper()),
        None
    )

    # Config generique si pas dans attributes_to_inject
    if attr_cfg is None:
        attr_cfg = {
            "name": attr_name,
            "valid_value_regex": "",
            "sources": [
                {"type": "woo_attribute", "attr_name": attr_name},
                {
                    "type": "full_specs_row",
                    "section_contains": "performance",
                    "label_contains": [attr_name.lower()]
                },
                {"type": "tags_regex", "regex": f"(\\d+)\\s*Go\\s*{attr_name}"},
            ]
        }

    valid_regex  = attr_cfg.get("valid_value_regex", "")
    ram_patterns = config.get("ram_normalize_patterns", [])

    for source in attr_cfg.get("sources", []):
        src_type = source.get("type", "")
        value    = None

        if src_type == "woo_attribute":
            target = source.get("attr_name", attr_name).upper()
            for n in range(1, 6):
                if woo.get(f"Attribute {n} name", "").strip().upper() == target:
                    v = woo.get(f"Attribute {n} value(s)", "").strip()
                    if v:
                        value = v
                        break

        elif src_type == "full_specs_row":
            sec_kw     = source.get("section_contains", "").lower()
            label_kws  = [lbl.lower() for lbl in source.get("label_contains", [])]
            for section in data.get("full_specs", {}).get("sections", []):
                if sec_kw and sec_kw not in section.get("name", "").lower():
                    continue
                for row in section.get("rows", []):
                    row_label = row.get("label", "").lower()
                    if any(lkw in row_label for lkw in label_kws):
                        v = row.get("valeur", "").strip()
                        if v:
                            value = v
                        break
                if value:
                    break

        elif src_type == "tags_regex":
            tags = woo.get("Tags", "")
            m    = re.search(source.get("regex", ""), tags, re.IGNORECASE)
            if m:
                value = m.group(1) + " Go"

        elif src_type == "full_text_regex":
            all_text = json.dumps(data, ensure_ascii=False)
            m        = re.search(source.get("regex", ""), all_text, re.IGNORECASE)
            if m:
                value = m.group(1) + " Go"

        if value:
            normalized = normalize_value(value, ram_patterns) if ram_patterns else value.strip()
            # Verifier validite
            if valid_regex and not re.match(valid_regex, normalized, re.IGNORECASE):
                continue
            return normalized

    return None


def is_accessory_by_sku_data(json_path: str, config: dict) -> bool:
    """Detecte si un produit est un accessoire via son JSON."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False

    acc_cfg  = config.get("accessory_detection", {})
    keywords = [kw.lower() for kw in acc_cfg.get("keywords", [])]
    woo      = data.get("woocommerce_csv", {})

    for field in acc_cfg.get("check_fields", ["Name", "Categories", "Tags"]):
        fval = woo.get(field, "").lower()
        if any(kw in fval for kw in keywords):
            return True

    non_app = [v.lower() for v in acc_cfg.get("full_specs_non_applicable_values", [])]
    for section in data.get("full_specs", {}).get("sections", []):
        if "performance" in section.get("name", "").lower():
            for row in section.get("rows", []):
                if any(lbl in row.get("label", "").lower() for lbl in ["memoire vive", "mémoire vive", "ram"]):
                    if any(na in row.get("valeur", "").lower() for na in non_app):
                        return True
    return False


# ══════════════════════════════════════════════════════════════
#  CONSTRUCTION DU MAPPING  SKU -> VALEUR
# ══════════════════════════════════════════════════════════════

def build_sku_map(json_dir: str, attr_name: str, config: dict, verbose: bool) -> dict:
    """
    Parcourt les sous-dossiers de json_dir, extrait la valeur de attr_name pour chaque produit.
    Retourne dict { SKU: valeur }.
    """
    mapping  = {}
    skipped  = []
    prefix   = config.get("json_file_prefix", "pack-data-")
    suffix   = config.get("json_file_suffix", ".json")

    for folder in sorted(os.listdir(json_dir)):
        folder_path = os.path.join(json_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        json_files = [
            f for f in os.listdir(folder_path)
            if f.startswith(prefix) and f.endswith(suffix)
        ]
        if not json_files:
            continue

        json_path = os.path.join(folder_path, json_files[0])

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        woo = data.get("woocommerce_csv", {})
        sku = woo.get("SKU") or data.get("sourcing", {}).get("official_sku", "")
        if not sku:
            skipped.append(folder)
            continue

        # Accessoire ?
        if is_accessory_by_sku_data(json_path, config):
            skipped.append(f"{sku} (accessoire)")
            if verbose:
                print(f"  [SKIP] {sku} - Accessoire")
            continue

        value = extract_attr_from_json(json_path, attr_name, config)
        if value:
            mapping[sku] = value
            if verbose:
                print(f"  [MAP]  {sku:40s} -> {attr_name}={value}")
        else:
            skipped.append(f"{sku} (valeur {attr_name} non trouvee)")
            if verbose:
                print(f"  [MISS] {sku} - {attr_name} introuvable")

    return mapping, skipped


# ══════════════════════════════════════════════════════════════
#  PATCH DU CSV
# ══════════════════════════════════════════════════════════════

def find_col(headers: list, attr_n: int, field: str) -> int:
    """Retourne l'index de 'Attribute N field' dans les headers."""
    try:
        return headers.index(f"Attribute {attr_n} {field}")
    except ValueError:
        return -1


def patch_csv(csv_path: str, sku_map: dict, attr_name: str, config: dict,
              skip_types: list, dry_run: bool, no_backup: bool, verbose: bool) -> dict:
    """
    Lit le CSV WooCommerce, injecte l'attribut manquant pour chaque SKU du mapping.
    Ecrit le fichier corrige (avec backup automatique).
    """
    stats = {"total": 0, "patched": 0, "already_ok": 0,
             "no_data": 0, "skipped_type": 0, "invalid_value": 0}

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        print("[ERROR] CSV vide !")
        return stats

    headers  = rows[0]
    sku_idx  = headers.index("SKU")  if "SKU"  in headers else -1
    type_idx = headers.index("Type") if "Type" in headers else -1

    if sku_idx < 0:
        print("[ERROR] Colonne SKU introuvable dans le CSV !")
        return stats

    # Index des attributs 1 à 4
    attr_info = {}
    for n in range(1, 5):
        attr_info[n] = {
            "name":    find_col(headers, n, "name"),
            "value":   find_col(headers, n, "value(s)"),
            "default": find_col(headers, n, "default"),
            "visible": find_col(headers, n, "visible"),
            "global":  find_col(headers, n, "global"),
        }

    patched_rows = [headers]
    valid_regex  = ""
    for ac in config.get("attributes_to_inject", []):
        if ac.get("name", "").upper() == attr_name.upper():
            valid_regex = ac.get("valid_value_regex", "")
            break

    for row_num, row in enumerate(rows[1:], start=2):
        stats["total"] += 1

        # Etendre si necessaire
        while len(row) < len(headers):
            row.append("")

        sku      = row[sku_idx].strip() if sku_idx < len(row) else ""
        row_type = row[type_idx].strip().lower() if type_idx >= 0 and type_idx < len(row) else ""

        # Ignorer les types a sauter (ex: "variation")
        if row_type in [t.lower() for t in skip_types]:
            patched_rows.append(row)
            stats["skipped_type"] += 1
            continue

        # Chercher si attribut deja present avec une valeur valide
        attr_present_n   = None
        attr_present_val = ""
        for n in range(1, 5):
            ni = attr_info[n]["name"]
            vi = attr_info[n]["value"]
            if ni >= 0 and ni < len(row) and row[ni].strip().upper() == attr_name.upper():
                attr_present_n   = n
                attr_present_val = row[vi].strip() if vi >= 0 and vi < len(row) else ""
                break

        if attr_present_n and attr_present_val:
            if not valid_regex or re.match(valid_regex, attr_present_val, re.IGNORECASE):
                stats["already_ok"] += 1
                if verbose:
                    print(f"  [OK]   Row {row_num} {sku} - {attr_name} deja = {attr_present_val}")
                patched_rows.append(row)
                continue

        # Chercher la valeur dans le mapping
        value = sku_map.get(sku)
        if not value:
            # Tentative sans prefixe
            alt_sku = re.sub(r"^[A-Z]{2}-", "", sku)
            value   = sku_map.get(alt_sku)

        if not value:
            stats["no_data"] += 1
            if verbose:
                print(f"  [???]  Row {row_num} {sku} - Pas de data dans les JSON")
            patched_rows.append(row)
            continue

        # Valider la valeur
        if valid_regex and not re.match(valid_regex, value, re.IGNORECASE):
            stats["invalid_value"] += 1
            if verbose:
                print(f"  [INV]  Row {row_num} {sku} - Valeur non valide: '{value}'")
            patched_rows.append(row)
            continue

        # Determiner le slot cible
        if attr_present_n:
            target_n = attr_present_n  # Slot existe mais valeur vide/invalide
        else:
            # Trouver le premier slot libre
            target_n = None
            for n in range(1, 5):
                ni = attr_info[n]["name"]
                if ni >= 0 and ni < len(row) and not row[ni].strip():
                    target_n = n
                    break

            if target_n is None:
                if verbose:
                    print(f"  [FULL] Row {row_num} {sku} - Attributs pleins, impossible d'injecter")
                stats["no_data"] += 1
                patched_rows.append(row)
                continue

        # Injection
        ai = attr_info[target_n]
        if ai["name"]    >= 0: row[ai["name"]]    = attr_name
        if ai["value"]   >= 0: row[ai["value"]]   = value
        if ai["default"] >= 0: row[ai["default"]] = value
        if ai["visible"] >= 0: row[ai["visible"]] = "1"
        if ai["global"]  >= 0: row[ai["global"]]  = "1"

        stats["patched"] += 1
        print(f"  [PATCH] Row {row_num} {sku:40s} -> {attr_name}={value} (Attr{target_n})")
        patched_rows.append(row)

    # ── Ecriture ─────────────────────────────────────────────
    if not dry_run:
        if not no_backup:
            bak = csv_path + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(csv_path, bak)
            print(f"\n[BACKUP] {os.path.basename(bak)}")

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerows(patched_rows)
        print(f"[WRITE]  CSV mis a jour : {csv_path}")
    else:
        print("\n[DRY-RUN] Aucun fichier ecrit.")

    return stats


# ══════════════════════════════════════════════════════════════
#  POINT D'ENTREE
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Patch les attributs manquants dans un CSV WooCommerce depuis les JSON sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python wc_csv_attr_patcher.py --csv products/blackview-all/import-v2-blackview-all.csv \\
      --json-dir products/blackview-all --attr RAM --dry-run

  python wc_csv_attr_patcher.py --csv products/samsung-galaxy-a-all/import-v2-samsung-galaxy-a-all.csv \\
      --json-dir products/samsung-galaxy-a-all --attr RAM
        """
    )
    parser.add_argument("--csv",      required=True, help="Chemin vers le CSV WooCommerce")
    parser.add_argument("--json-dir", required=True, help="Dossier des sous-dossiers produits JSON")
    parser.add_argument("--attr",     required=True, help="Nom de l'attribut a patcher (ex: RAM)")
    parser.add_argument("--config",   default=DEFAULT_CONFIG, help="Config JSON")
    parser.add_argument("--dry-run",  action="store_true", help="Simulation sans ecriture")
    parser.add_argument("--verbose",  action="store_true", help="Affichage detaille")
    parser.add_argument("--no-backup", action="store_true", help="Desactiver backup .bak")
    parser.add_argument("--skip-types", nargs="+", default=["variation"],
                        help="Types de lignes a ignorer (defaut: variation)")
    args = parser.parse_args()

    # Resoudre les chemins relatifs
    def resolve_path(p):
        if os.path.isabs(p):
            return p
        if os.path.exists(p):
            return os.path.abspath(p)
        alt = os.path.join(WORKSPACE_ROOT, p)
        if os.path.exists(alt):
            return alt
        return p

    csv_path = resolve_path(args.csv)
    json_dir = resolve_path(args.json_dir)

    if not os.path.isfile(csv_path):
        print(f"[ERROR] CSV introuvable : {csv_path}")
        sys.exit(1)
    if not os.path.isdir(json_dir):
        print(f"[ERROR] JSON dir introuvable : {json_dir}")
        sys.exit(1)

    config = load_config(args.config)

    print("=" * 70)
    print("  WC CSV ATTR PATCHER — Outil General")
    print("=" * 70)
    print(f"  CSV        : {csv_path}")
    print(f"  JSON dir   : {json_dir}")
    print(f"  Attribut   : {args.attr}")
    print(f"  Config     : {args.config}")
    print(f"  Mode       : {'DRY-RUN' if args.dry_run else 'ECRITURE REELLE'}")
    print("=" * 70)

    # STEP 1 : Mapping SKU -> valeur
    print(f"\n[STEP 1] Scan des JSON pour '{args.attr}'...")
    sku_map, skipped = build_sku_map(json_dir, args.attr, config, args.verbose)
    print(f"  -> {len(sku_map)} produits avec {args.attr} trouve")
    if skipped and args.verbose:
        for s in skipped:
            print(f"      - {s}")

    if not sku_map:
        print(f"\n[DONE] Aucun produit avec {args.attr} trouve. Rien a patcher.")
        return

    # STEP 2 : Patch CSV
    print(f"\n[STEP 2] Application du patch sur le CSV...")
    stats = patch_csv(
        csv_path, sku_map, args.attr, config,
        args.skip_types, args.dry_run, args.no_backup, args.verbose
    )

    # Resume
    print("\n" + "=" * 70)
    print("  RESUME")
    print("=" * 70)
    print(f"  Lignes traitees      : {stats['total']}")
    print(f"  Deja corrects        : {stats['already_ok']}")
    print(f"  Lignes patchees      : {stats['patched']}")
    print(f"  Sans data JSON       : {stats['no_data']}")
    print(f"  Valeur invalide      : {stats['invalid_value']}")
    print(f"  Types ignores        : {stats['skipped_type']}")
    print("=" * 70)

    if stats["patched"] > 0 and not args.dry_run:
        print(f"\n[DONE] {stats['patched']} ligne(s) patchee(s) avec succes !")
    elif args.dry_run:
        print(f"\n[DONE] Simulation : {stats['patched']} ligne(s) seraient patchees.")
    else:
        print("\n[DONE] Aucune modification necessaire.")


if __name__ == "__main__":
    main()
