#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wc_json_attributes_fixer.py
============================
Outil GENERAL de correction des attributs WooCommerce dans les JSON de pack produit.
Compatible avec toutes les series/marques du projet (Blackview, Samsung, Xiaomi, etc.)

Corrections appliquees :
  1. Renommage d'attributs errones  (ex: "Capacite" -> "Stockage")
  2. Normalisation des valeurs       (ex: "256Go" -> "256 Go", "1TB" -> "1 To")
  3. Injection des attributs manquants depuis full_specs (ex: RAM)
  4. Detection intelligente des accessoires (pas de RAM sur Airbuds/Montres/Moniteurs)

Usage :
  python wc_json_attributes_fixer.py --products-dir products/blackview-all
  python wc_json_attributes_fixer.py --products-dir products/samsung-galaxy-a-all --fix-mode stockage
  python wc_json_attributes_fixer.py --products-dir products/xiaomi-redmi-14-all --dry-run --verbose
  python wc_json_attributes_fixer.py --products-dir products/blackview-all --config path/to/custom.json

Arguments :
  --products-dir  Dossier contenant les sous-dossiers produits (chacun avec un pack-data-*.json)
  --fix-mode      stockage | ram | all  (defaut: all)
  --config        Chemin vers le fichier de config JSON (defaut: wc_json_fix_config.json dans le meme dossier)
  --dry-run       Simulation sans ecriture fichier
  --verbose       Affichage detaille de chaque action
  --no-backup     Desactiver la creation de fichiers .bak (non recommande)
"""

import os
import re
import sys
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
#  CONFIG LOADER
# ══════════════════════════════════════════════════════════════

def load_config(config_path: str) -> dict:
    """Charge et valide le fichier de configuration JSON."""
    if not os.path.isfile(config_path):
        print(f"[ERROR] Fichier de config introuvable : {config_path}")
        print(f"        Generez-le depuis : scripts/tools/data_processing/wc_json_fix_config.json")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════
#  NORMALISATION
# ══════════════════════════════════════════════════════════════

def normalize_value(raw: str, patterns: list) -> str:
    """
    Applique les patterns de normalisation definis dans la config.
    Ex: "256Go" -> "256 Go" grace au pattern { regex: "(\\d+)\\s*(GB|Go)", output: "{n} Go" }
    """
    separator = None
    if "|" in raw:
        separator = " | "
        parts = [p.strip() for p in raw.split("|") if p.strip()]
    elif "," in raw:
        separator = ", "
        parts = [p.strip() for p in raw.split(",") if p.strip()]
    else:
        parts = [raw]

    normalized_parts = []
    for part in parts:
        found = False
        for p in patterns:
            m = re.search(p["regex"], part, re.IGNORECASE)
            if m:
                normalized_parts.append(p["output"].replace("{n}", m.group(1)))
                found = True
                break
        if not found:
            normalized_parts.append(part.strip())

    if separator:
        return separator.join(normalized_parts)
    return normalized_parts[0] if normalized_parts else raw.strip()


def normalize_storage(raw: str, config: dict) -> str:
    """Normalise une valeur de stockage selon les regles de config."""
    if not config.get("storage_normalize", {}).get("enabled", True):
        return raw
    patterns = config["storage_normalize"].get("patterns", [])
    return normalize_value(raw, patterns)


def normalize_ram(raw: str, config: dict) -> str:
    """Normalise une valeur RAM selon les regles de config."""
    patterns = config.get("ram_normalize_patterns", [])
    return normalize_value(raw, patterns)


# ══════════════════════════════════════════════════════════════
#  DETECTION ACCESSOIRES
# ══════════════════════════════════════════════════════════════

def is_accessory(data: dict, config: dict) -> bool:
    """
    Detecte si le produit est un accessoire sans RAM (airbuds, montre, moniteur, etc.)
    en se basant sur les mots-cles definis dans la config.
    """
    acc_cfg = config.get("accessory_detection", {})
    keywords = [kw.lower() for kw in acc_cfg.get("keywords", [])]
    check_fields = acc_cfg.get("check_fields", ["Name", "Categories", "Tags"])
    woo = data.get("woocommerce_csv", {})

    # Verifier les champs texte (Name, Categories, Tags)
    for field in check_fields:
        field_val = woo.get(field, "").lower()
        for kw in keywords:
            if kw in field_val:
                return True

    # Verifier les valeurs "Non applicable" dans full_specs Performances
    non_applicable = [v.lower() for v in acc_cfg.get("full_specs_non_applicable_values", [])]
    for section in data.get("full_specs", {}).get("sections", []):
        if "performance" in section.get("name", "").lower():
            for row in section.get("rows", []):
                if any(lbl in row.get("label", "").lower() for lbl in ["memoire vive", "mémoire vive", "ram"]):
                    val = row.get("valeur", "").lower()
                    if any(na in val for na in non_applicable):
                        return True
    return False


# ══════════════════════════════════════════════════════════════
#  EXTRACTION VALEUR DEPUIS JSON
# ══════════════════════════════════════════════════════════════

def extract_attribute_value(data: dict, attr_cfg: dict, config: dict) -> str | None:
    """
    Extrait la valeur d'un attribut selon les sources definies dans la config.
    Retourne la valeur normalisee ou None si non trouvee / non valide.
    """
    woo = data.get("woocommerce_csv", {})
    valid_regex = attr_cfg.get("valid_value_regex", "")

    for source in attr_cfg.get("sources", []):
        src_type = source.get("type", "")
        value = None

        # ── Source 1 : Attribut WooCommerce existant ──────────
        if src_type == "woo_attribute":
            target_name = source.get("attr_name", "").upper()
            for n in range(1, 6):
                if woo.get(f"Attribute {n} name", "").strip().upper() == target_name:
                    v = woo.get(f"Attribute {n} value(s)", "").strip()
                    if v:
                        value = v
                        break

        # ── Source 2 : Ligne dans full_specs ──────────────────
        elif src_type == "full_specs_row":
            section_kw = source.get("section_contains", "").lower()
            label_kws  = [lbl.lower() for lbl in source.get("label_contains", [])]
            for section in data.get("full_specs", {}).get("sections", []):
                if section_kw in section.get("name", "").lower():
                    for row in section.get("rows", []):
                        row_label = row.get("label", "").lower()
                        if any(lkw in row_label for lkw in label_kws):
                            v = row.get("valeur", "").strip()
                            if v:
                                value = v
                            break
                    if value:
                        break

        # ── Source 3 : Regex dans Tags ─────────────────────────
        elif src_type == "tags_regex":
            tags = woo.get("Tags", "")
            m = re.search(source.get("regex", ""), tags, re.IGNORECASE)
            if m:
                value = m.group(1) + " Go"

        # ── Source 4 : Regex full text ─────────────────────────
        elif src_type == "full_text_regex":
            all_text = json.dumps(data, ensure_ascii=False)
            m = re.search(source.get("regex", ""), all_text, re.IGNORECASE)
            if m:
                value = m.group(1) + " Go"

        # Valider et normaliser
        if value:
            normalized = normalize_ram(value, config)
            if valid_regex and not re.match(valid_regex, normalized, re.IGNORECASE):
                continue  # Valeur non valide, essayer la source suivante
            return normalized

    return None


# ══════════════════════════════════════════════════════════════
#  AUDIT D'UN JSON
# ══════════════════════════════════════════════════════════════

def audit_json(json_path: str, config: dict, fix_mode: str) -> dict:
    """
    Analyse un JSON et retourne un rapport complet des problemes detectes.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    woo  = data.get("woocommerce_csv", {})
    sku  = woo.get("SKU") or data.get("sourcing", {}).get("official_sku", "UNKNOWN")

    result = {
        "sku":          sku,
        "path":         json_path,
        "data":         data,
        "issues":       [],
        "fixes":        [],
        "needs_fix":    False,
        "is_accessory": is_accessory(data, config),
    }

    # Lire les attributs existants
    attrs = {}
    for n in range(1, 6):
        name = woo.get(f"Attribute {n} name", "").strip()
        val  = woo.get(f"Attribute {n} value(s)", "").strip()
        if name:
            attrs[n] = {"name": name, "value": val}
    result["attrs"] = attrs

    # ── Verifier les regles de renommage ──────────────────────
    if fix_mode in ("stockage", "all"):
        for n, a in attrs.items():
            for rule in config.get("rename_rules", []):
                if a["name"] == rule["from"]:
                    new_val = normalize_storage(a["value"], config)
                    result["issues"].append(
                        f"Attr{n} '{rule['from']}' -> '{rule['to']}' (valeur: {new_val})"
                    )
                    result["fixes"].append({
                        "type": "rename",
                        "attr_n": n,
                        "new_name": rule["to"],
                        "new_value": new_val,
                    })
                    result["needs_fix"] = True
                    break

        # Normalisation des valeurs Stockage existantes
        for n, a in attrs.items():
            if a["name"] == "Stockage":
                raw = a["value"]
                normalized = normalize_storage(raw, config)
                if normalized != raw:
                    result["issues"].append(f"Attr{n} Stockage valeur '{raw}' -> '{normalized}'")
                    result["fixes"].append({
                        "type": "normalize_value",
                        "attr_n": n,
                        "new_value": normalized,
                    })
                    result["needs_fix"] = True

        # Normalisation des valeurs RAM existantes
        for n, a in attrs.items():
            if a["name"] == "RAM":
                raw = a["value"]
                normalized = normalize_ram(raw, config)
                if normalized != raw:
                    result["issues"].append(f"Attr{n} RAM valeur '{raw}' -> '{normalized}'")
                    result["fixes"].append({
                        "type": "normalize_value",
                        "attr_n": n,
                        "new_value": normalized,
                    })
                    result["needs_fix"] = True

    # ── Verifier les attributs a injecter ─────────────────────
    if fix_mode in ("ram", "all") and not result["is_accessory"]:
        for attr_cfg in config.get("attributes_to_inject", []):
            attr_name = attr_cfg.get("name", "")
            # Deja present avec une valeur valide ?
            already_present = False
            valid_regex = attr_cfg.get("valid_value_regex", "")
            for n, a in attrs.items():
                if a["name"].upper() == attr_name.upper():
                    if valid_regex and re.match(valid_regex, a["value"], re.IGNORECASE):
                        already_present = True
                    break

            if not already_present:
                value = extract_attribute_value(data, attr_cfg, config)
                if value:
                    result["issues"].append(f"Attribut '{attr_name}' manquant -> injecter: {value}")
                    result["fixes"].append({
                        "type":       "inject",
                        "attr_name":  attr_name,
                        "attr_value": value,
                    })
                    result["needs_fix"] = True
                else:
                    result["issues"].append(
                        f"Attribut '{attr_name}' manquant mais valeur introuvable dans full_specs"
                    )

    return result


# ══════════════════════════════════════════════════════════════
#  APPLICATION DES CORRECTIONS
# ══════════════════════════════════════════════════════════════

def apply_fixes(audit: dict, config: dict, dry_run: bool, no_backup: bool, verbose: bool) -> bool:
    """
    Applique les corrections au JSON. Retourne True si des changements ont ete effectues.
    """
    if not audit["needs_fix"]:
        return False

    data     = audit["data"]
    woo      = data["woocommerce_csv"]
    sku      = audit["sku"]
    json_path = audit["path"]

    for fix in audit["fixes"]:
        fix_type = fix["type"]

        # ── Renommage attribut ────────────────────────────────
        if fix_type == "rename":
            n = fix["attr_n"]
            woo[f"Attribute {n} name"]     = fix["new_name"]
            woo[f"Attribute {n} value(s)"] = fix["new_value"]
            woo[f"Attribute {n} default"]  = fix["new_value"]
            if verbose:
                print(f"    [FIX] Attr{n}: '{audit['attrs'][n]['name']}' -> '{fix['new_name']}' = '{fix['new_value']}'")

        # ── Normalisation valeur ──────────────────────────────
        elif fix_type == "normalize_value":
            n = fix["attr_n"]
            woo[f"Attribute {n} value(s)"] = fix["new_value"]
            woo[f"Attribute {n} default"]  = fix["new_value"]
            if verbose:
                print(f"    [FIX] Attr{n} valeur: '{audit['attrs'][n]['value']}' -> '{fix['new_value']}'")

        # ── Injection nouvel attribut ─────────────────────────
        elif fix_type == "inject":
            # Trouver le prochain slot libre (1-5)
            used_slots = set()
            for n in range(1, 6):
                if woo.get(f"Attribute {n} name", "").strip():
                    used_slots.add(n)
            next_slot = next((n for n in range(1, 6) if n not in used_slots), None)

            if next_slot is None:
                print(f"    [WARN] {sku}: Pas de slot libre pour injecter '{fix['attr_name']}' !")
                continue

            woo[f"Attribute {next_slot} name"]     = fix["attr_name"]
            woo[f"Attribute {next_slot} value(s)"] = fix["attr_value"]
            woo[f"Attribute {next_slot} default"]  = fix["attr_value"]
            woo[f"Attribute {next_slot} visible"]  = "1"
            woo[f"Attribute {next_slot} global"]   = "1"
            if verbose:
                print(f"    [FIX] Attr{next_slot} (nouveau): '{fix['attr_name']}' = '{fix['attr_value']}'")

    if not dry_run:
        # Backup
        if not no_backup:
            ext = config.get("backup_extension", ".bak")
            backup_path = json_path + ext + f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(json_path, backup_path)
        # Ecriture
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if verbose:
            print(f"    [SAVED] {os.path.basename(json_path)}")

    return True


# ══════════════════════════════════════════════════════════════
#  POINT D'ENTREE
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Outil general de correction des attributs WooCommerce dans les JSON pack produit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python wc_json_attributes_fixer.py --products-dir products/blackview-all
  python wc_json_attributes_fixer.py --products-dir products/samsung-galaxy-a-all --fix-mode ram
  python wc_json_attributes_fixer.py --products-dir products/xiaomi-redmi-14-all --dry-run --verbose
        """
    )
    parser.add_argument("--products-dir", required=True,
                        help="Dossier contenant les sous-dossiers produits")
    parser.add_argument("--fix-mode", choices=["stockage", "ram", "all"], default="all",
                        help="Mode de correction (defaut: all)")
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="Chemin vers le fichier de config JSON")
    parser.add_argument("--dry-run",  action="store_true", help="Simulation sans ecriture")
    parser.add_argument("--verbose",  action="store_true", help="Affichage detaille")
    parser.add_argument("--no-backup", action="store_true", help="Desactiver les backups .bak")
    args = parser.parse_args()

    # Resoudre le chemin relatif products-dir par rapport a la racine workspace
    products_dir = args.products_dir
    if not os.path.isabs(products_dir):
        # Chercher d'abord relatif au CWD, puis relatif au workspace
        if os.path.isdir(products_dir):
            products_dir = os.path.abspath(products_dir)
        else:
            alt = os.path.join(WORKSPACE_ROOT, products_dir)
            if os.path.isdir(alt):
                products_dir = alt
            else:
                print(f"[ERROR] Dossier introuvable : {args.products_dir}")
                sys.exit(1)

    config = load_config(args.config)

    print("=" * 70)
    print("  WC JSON ATTRIBUTES FIXER — Outil General")
    print("=" * 70)
    print(f"  Products dir : {products_dir}")
    print(f"  Fix mode     : {args.fix_mode}")
    print(f"  Config       : {args.config}")
    print(f"  Mode         : {'DRY-RUN' if args.dry_run else 'ECRITURE REELLE'}")
    print("=" * 70)

    prefix = config.get("json_file_prefix", "pack-data-")
    suffix = config.get("json_file_suffix", ".json")

    stats    = {"total": 0, "fixed": 0, "ok": 0, "accessory": 0, "no_fix": 0}
    to_fix   = []

    # ── STEP 1 : Audit ────────────────────────────────────────
    print("\n[STEP 1] Audit des JSON...")
    for folder in sorted(os.listdir(products_dir)):
        folder_path = os.path.join(products_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        json_files = [
            f for f in os.listdir(folder_path)
            if f.startswith(prefix) and f.endswith(suffix)
        ]
        if not json_files:
            continue

        json_path = os.path.join(folder_path, json_files[0])
        stats["total"] += 1

        try:
            audit = audit_json(json_path, config, args.fix_mode)
        except Exception as e:
            print(f"  [ERROR] {folder}: {e}")
            continue

        sku = audit["sku"]

        if audit["is_accessory"]:
            stats["accessory"] += 1
            if args.verbose:
                print(f"  [SKIP] {sku:45s} - Accessoire")
            continue

        if not audit["needs_fix"]:
            stats["ok"] += 1
            if args.verbose:
                print(f"  [OK]   {sku:45s} - Format correct")
            continue

        to_fix.append(audit)
        print(f"  [ISSUE] {sku}")
        for issue in audit["issues"]:
            print(f"          - {issue}")

    print(f"\n[STEP 1] {len(to_fix)} a corriger | {stats['ok']} OK | {stats['accessory']} accessoires")

    if not to_fix:
        print("\n[DONE] Aucune correction necessaire.")
        return

    # ── STEP 2 : Application ─────────────────────────────────
    print(f"\n[STEP 2] Application des corrections...")
    for audit in to_fix:
        sku = audit["sku"]
        print(f"\n  >> {sku}")
        fixed = apply_fixes(audit, config, args.dry_run, args.no_backup, verbose=True)
        if fixed:
            stats["fixed"] += 1
            label = "SIMULE" if args.dry_run else "CORRIGE"
            print(f"     [{label}] OK")
        else:
            stats["no_fix"] += 1
            print(f"     [SKIP] Pas de modification")

    # ── Resume ───────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  RESUME")
    print("=" * 70)
    print(f"  JSON scannes          : {stats['total']}")
    print(f"  Deja corrects         : {stats['ok']}")
    print(f"  Accessoires (ignores) : {stats['accessory']}")
    mode_label = "simules" if args.dry_run else "appliques"
    print(f"  Corrections {mode_label:8s} : {stats['fixed']}")
    print(f"  Non modifiables       : {stats['no_fix']}")
    print("=" * 70)

    if stats["fixed"] > 0:
        if args.dry_run:
            print(f"\n[DONE] {stats['fixed']} JSON seraient corriges.")
            print("       Relancez sans --dry-run pour appliquer.")
        else:
            print(f"\n[DONE] {stats['fixed']} JSON corriges avec succes !")
    else:
        print("\n[DONE] Aucune modification appliquee.")


if __name__ == "__main__":
    main()
