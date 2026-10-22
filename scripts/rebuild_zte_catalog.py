#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Reconstruction & Compilation Industrielle du Catalogue ZTE (V3.4).

Standardise l'arborescence et génère le format WooCommerce complet avec relations Parent-Enfant :
  - Sous-dossier par modèle : products/zte-all/[model-slug]/ contenant :
      * pack-data-[model-slug].json
      * long-[model-slug].html
      * short-[model-slug].html
  - CSV WooCommerce Consolidé Global : products/zte-all/import-v2-zte-all.csv
      * 1 ligne parent (Type=variable) avec nomenclature multi-variantes (ex: (8 Go|16 Go & 256 Go|512 Go)),
        descriptions HTML complètes et attributs globaux (Couleur, Stockage, RAM, Poids, Réseau)
      * N lignes enfants (Type=variation) pour chaque combinaison couleur / RAM / Stockage reliées par SKU Parent
"""

import os
import sys
import json
import re
import csv
import unicodedata
import subprocess

# Ajouter le répertoire racine au PATH pour importer format_product_names
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, WORKSPACE_ROOT)

try:
    from scripts.tools.data_processing.format_product_names import get_formatted_name
except ImportError:
    get_formatted_name = None

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PRODUCT_DATA_DIR = os.path.join(WORKSPACE_ROOT, "product-data", "zte")
PARENT_CSV_PATH = os.path.join(PRODUCT_DATA_DIR, "zte_models_parent.csv")
PRODUCTS_DIR = os.path.join(WORKSPACE_ROOT, "products", "zte-all")
BUILD_SCRIPT = os.path.join(WORKSPACE_ROOT, "scripts", "build-product-pack-v3.py")
CSV_OUT_PATH = os.path.join(PRODUCTS_DIR, "import-v2-zte-all.csv")

CSV_HEADERS = [
    "ID", "Type", "SKU", "Name", "Published", "Visibility in catalog",
    "Short description", "Description", "In stock?", "Stock", "Regular price",
    "Categories", "Tags", "Parent",
    "Attribute 1 name", "Attribute 1 value(s)", "Attribute 1 default", "Attribute 1 visible", "Attribute 1 global",
    "Attribute 2 name", "Attribute 2 value(s)", "Attribute 2 default", "Attribute 2 visible", "Attribute 2 global",
    "Attribute 3 name", "Attribute 3 value(s)", "Attribute 3 default", "Attribute 3 visible", "Attribute 3 global",
    "Attribute 4 name", "Attribute 4 value(s)", "Attribute 4 default", "Attribute 4 visible", "Attribute 4 global",
    "Attribute 5 name", "Attribute 5 value(s)", "Attribute 5 default", "Attribute 5 visible", "Attribute 5 global",
]


def clean_html(html: str) -> str:
    """Nettoie le HTML pour le CSV WooCommerce (0 commentaire, 0 saut de ligne parasite)."""
    if not html:
        return ""
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = html.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    html = re.sub(r'\s+', ' ', html)
    return html.strip()


def normalize_ascii(val: str) -> str:
    """Normalise une chaîne pour SKU (ASCII, majuscules, sans espaces ni caractères spéciaux)."""
    if not val:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(val))
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return ascii_str.upper().strip().replace(' ', '-').replace("'", "").replace('/', '-')


def clean_color_for_sku(color: str) -> str:
    if not color:
        return ""
    return normalize_ascii(color)


def clean_mem_for_sku(mem: str) -> str:
    if not mem:
        return ""
    val = normalize_ascii(mem)
    val = val.replace("GO", "GB").replace("TO", "TB").replace("MO", "MB")
    return re.sub(r'[^A-Z0-9-]', '', val)


def format_memory_with_space(mem_str: str) -> str:
    """Normalise l'écriture de la mémoire avec un espace obligatoire (ex: '128 Go', '1 To')."""
    if not mem_str:
        return ""
    val = str(mem_str).strip()
    val = val.replace("GB", "Go").replace("TB", "To").replace("MB", "Mo")
    val = re.sub(r'(\d+(?:\.\d+)?)\s*(Go|To|Mo)', r'\1 \2', val)
    return val.strip()


def build_parent_ram_rom_group(all_rams: list, all_roms: list) -> str:
    """Construit la chaîne de nomenclature multi-variantes pour le parent, ex: (8 Go|16 Go & 256 Go|512 Go)."""
    rams_clean = [format_memory_with_space(r) for r in all_rams if r]
    roms_clean = [format_memory_with_space(r) for r in all_roms if r]

    rams_unique = list(dict.fromkeys(rams_clean))
    roms_unique = list(dict.fromkeys(roms_clean))

    if rams_unique and roms_unique:
        return f"({'|'.join(rams_unique)} & {'|'.join(roms_unique)})"
    elif roms_unique:
        return f"({'|'.join(roms_unique)})"
    elif rams_unique:
        return f"({'|'.join(rams_unique)})"
    return ""


def inject_parent_ram_rom_in_name(base_name: str, ram_rom_group_str: str) -> str:
    """Remplace la mention de RAM/ROM unique dans le nom parent par la nomenclature groupée multi-variantes."""
    if not ram_rom_group_str or ram_rom_group_str in base_name:
        return base_name

    # Pattern ciblant précisément la RAM/ROM (ex: 8Go/128Go, 8 Go/128 Go, (8 Go & 128 Go), 128Go, etc.)
    # Ne matche JAMAIS les parenthèses SIM sans unité mémoire comme (Nano) ou (eSIM/Nano)
    pattern = r'(?:\(\s*[\w\.\s\|&/]*(?:Go|GB|To|TB|Mo|MB)[\w\.\s\|&/]*\s*\)|\d+(?:\.\d+)?\s*(?:Go|GB|To|TB|Mo|MB)\s*\/\s*\d+(?:\.\d+)?\s*(?:Go|GB|To|TB|Mo|MB)|\d+(?:\.\d+)?\s*(?:Go|GB|To|TB|Mo|MB))'

    if re.search(pattern, base_name, flags=re.IGNORECASE):
        new_name = re.sub(pattern, ram_rom_group_str, base_name, count=1, flags=re.IGNORECASE)
        return new_name
    else:
        parts = base_name.split(" - ")
        if len(parts) >= 2:
            parts.insert(2, ram_rom_group_str)
            return " - ".join(parts)
        else:
            return f"{base_name} - {ram_rom_group_str}"


def empty_row() -> dict:
    """Retourne une ligne CSV avec tous les champs initialisés à vide."""
    return {h: "" for h in CSV_HEADERS}


def collect_all_parent_jsons():
    """Collecte l'ensemble des 30 JSON parents certifiés sous zte-axon, zte-blade, zte-nubia."""
    json_map = {}
    subdirs = ["zte-axon", "zte-blade", "zte-nubia"]
    for sdir in subdirs:
        dirpath = os.path.join(PRODUCT_DATA_DIR, sdir)
        if os.path.isdir(dirpath):
            for f in os.listdir(dirpath):
                if f.endswith(".json") and not f.startswith("hyp_"):
                    slug = f[:-5]
                    json_map[slug] = os.path.join(dirpath, f)
    return json_map


def main():
    print("=======================================================")
    print("  RECONSTRUCTION DU CATALOGUE ZTE V3.4 (PARENTS & VARIATIONS)")
    print("=======================================================\n")

    parent_jsons = collect_all_parent_jsons()
    print(f"[+] {len(parent_jsons)} fichiers JSON parents détectés.")

    csv_info_map = {}
    if os.path.isfile(PARENT_CSV_PATH):
        with open(PARENT_CSV_PATH, "r", encoding="utf-8") as f_csv:
            reader = csv.DictReader(f_csv)
            for row in reader:
                slug = row.get("model_slug", "").strip()
                if slug:
                    csv_info_map[slug] = row

    os.makedirs(PRODUCTS_DIR, exist_ok=True)

    csv_rows = []
    success_count = 0
    fail_count = 0
    total_variations = 0

    all_skus = set()

    for slug in sorted(parent_jsons.keys()):
        parent_json_path = parent_jsons[slug]

        # Créer le sous-dossier modèle dédié dans products/zte-all/[slug]/
        model_dir = os.path.join(PRODUCTS_DIR, slug)
        os.makedirs(model_dir, exist_ok=True)

        with open(parent_json_path, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)

        # Enregistrer le pack-data dans le sous-dossier modèle
        pack_data_path = os.path.join(model_dir, f"pack-data-{slug}.json")
        with open(pack_data_path, "w", encoding="utf-8") as f_out:
            json.dump(data, f_out, ensure_ascii=False, indent=4)

        # Compiler via build-product-pack-v3.py
        cmd = [
            sys.executable, BUILD_SCRIPT,
            "--data", pack_data_path,
            "--outdir", model_dir,
            "--modele", slug,
            "--serie", "zte-all",
            "--skip-validation",
            "--no-csv"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode != 0:
            print(f"  [BUILD FAIL] {slug}: {res.stderr[:300]}")
            fail_count += 1
            continue
        else:
            success_count += 1

        # Lire et nettoyer les HTML générés
        short_html_path = os.path.join(model_dir, f"short-{slug}.html")
        long_html_path = os.path.join(model_dir, f"long-{slug}.html")
        raw_short = open(short_html_path, "r", encoding="utf-8").read() if os.path.exists(short_html_path) else ""
        raw_long = open(long_html_path, "r", encoding="utf-8").read() if os.path.exists(long_html_path) else ""
        clean_short = clean_html(raw_short)
        clean_long = clean_html(raw_long)

        woo = data.get("woocommerce_csv", {})
        raw_parent_sku = woo.get("SKU", slug.upper())
        parent_sku = re.sub(r'-MASTER$', '', raw_parent_sku, flags=re.IGNORECASE)
        raw_parent_name = woo.get("Name", slug)
        regular_price = woo.get("Regular price", "150000")
        categories = woo.get("Categories", "Smartphones > ZTE, Smartphones")
        tags = woo.get("Tags", "ZTE, Smartphone")

        csv_row_info = csv_info_map.get(slug, {})

        # Si paired_variants est présent, c'est la source de vérité absolue
        if "paired_variants" in data and data["paired_variants"]:
            colors = []
            all_roms = []
            all_rams = []
            ram_rom_pairs = []
            for pv in data["paired_variants"]:
                c_val = pv.get("color_fr") or pv.get("color", "")
                r_val = pv.get("rom") or pv.get("storage", "")
                ram_val = pv.get("ram", "")
                if c_val and c_val not in colors:
                    colors.append(c_val)
                if r_val and r_val not in all_roms:
                    all_roms.append(r_val)
                if ram_val and ram_val not in all_rams:
                    all_rams.append(ram_val)
                pair = (ram_val, r_val)
                if pair not in ram_rom_pairs:
                    ram_rom_pairs.append(pair)
        else:
            # Attributs officiels
            colors_str = csv_row_info.get("official_colors_fr", "").strip() or woo.get("Attribute 1 value(s)", "").strip()
            ram_rom_str = csv_row_info.get("ram&rom_options", "").strip()
            # Parsing couleurs
            colors = [c.strip() for c in re.split(r'[,|]', colors_str) if c.strip()]

            # Parsing RAM/ROM
            ram_rom_pairs = []
            if ram_rom_str:
                for pair in re.split(r'[,|]', ram_rom_str):
                    p = pair.strip()
                    if "/" in p:
                        parts = p.split("/")
                        ram_rom_pairs.append((format_memory_with_space(parts[0]), format_memory_with_space(parts[1])))
                    else:
                        ram_rom_pairs.append(("", format_memory_with_space(p)))
            else:
                stockage_val = woo.get("Attribute 2 value(s)", "")
                ram_val = woo.get("Attribute 3 value(s)", "")
                stockages = [format_memory_with_space(s) for s in re.split(r'[,|]', stockage_val) if s.strip()]
                rams = [format_memory_with_space(r) for r in re.split(r'[,|]', ram_val) if r.strip()]
                if rams and stockages:
                    for r in rams:
                        for s in stockages:
                            ram_rom_pairs.append((r, s))
                elif stockages:
                    for s in stockages:
                        ram_rom_pairs.append(("", s))

            # Consolidations pour le parent
            all_roms = []
            all_rams = []
            for ram, rom in ram_rom_pairs:
                rom_clean = format_memory_with_space(rom)
                ram_clean = format_memory_with_space(ram)
                if rom_clean and rom_clean not in all_roms:
                    all_roms.append(rom_clean)
                if ram_clean and ram_clean not in all_rams:
                    all_rams.append(ram_clean)

        weight_str = csv_row_info.get("official_weight", "").strip()
        if not weight_str and "key_specifications" in data:
            weight_str = data["key_specifications"].get("weight", "")
        if not weight_str and "Attribute 4 value(s)" in woo:
            weight_str = woo.get("Attribute 4 value(s)", "")

        # Construction du nom Parent
        if get_formatted_name:
            base_formatted_name = get_formatted_name(data, data)
        else:
            base_formatted_name = raw_parent_name

        ram_rom_group_str = build_parent_ram_rom_group(all_rams, all_roms)
        formatted_parent_name = inject_parent_ram_rom_in_name(base_formatted_name, ram_rom_group_str)
        if colors:
            color_pat = r'\s*-\s*(?:' + '|'.join(re.escape(c) for c in colors) + r')\s*$'
            formatted_parent_name = re.sub(color_pat, '', formatted_parent_name, flags=re.IGNORECASE)

        is_variable = bool(colors or ram_rom_pairs)
        product_type = "variable" if is_variable else "simple"

        # ─── LIGNE PARENT ─────────────────────────────────────────────────────
        parent_row = empty_row()
        parent_row["Type"] = product_type
        parent_row["SKU"] = parent_sku
        parent_row["Name"] = formatted_parent_name
        parent_row["Published"] = "1"
        parent_row["Visibility in catalog"] = "visible"
        parent_row["Short description"] = clean_short
        parent_row["Description"] = clean_long
        parent_row["In stock?"] = "1"
        parent_row["Stock"] = "10"
        parent_row["Regular price"] = regular_price
        parent_row["Categories"] = categories
        parent_row["Tags"] = tags
        parent_row["Parent"] = ""

        # Attribut 1 : Couleur
        if colors:
            parent_row["Attribute 1 name"] = "Couleur"
            parent_row["Attribute 1 value(s)"] = ", ".join(colors)
            parent_row["Attribute 1 default"] = colors[0]
            parent_row["Attribute 1 visible"] = "1"
            parent_row["Attribute 1 global"] = "1"

        # Attribut 2 : Stockage
        if all_roms:
            parent_row["Attribute 2 name"] = "Stockage"
            parent_row["Attribute 2 value(s)"] = ", ".join(all_roms)
            parent_row["Attribute 2 default"] = all_roms[0]
            parent_row["Attribute 2 visible"] = "1"
            parent_row["Attribute 2 global"] = "1"

        # Attribut 3 : RAM
        if all_rams:
            parent_row["Attribute 3 name"] = "RAM"
            parent_row["Attribute 3 value(s)"] = ", ".join(all_rams)
            parent_row["Attribute 3 default"] = all_rams[0]
            parent_row["Attribute 3 visible"] = "1"
            parent_row["Attribute 3 global"] = "1"

        # Attribut 4 : Poids
        if weight_str:
            w_kg = weight_str
            if "g" in str(weight_str).lower() and "kg" not in str(weight_str).lower():
                m_w = re.search(r"(\d+(?:\.\d+)?)", str(weight_str))
                if m_w:
                    w_kg = f"{float(m_w.group(1))/1000.0:.3f} kg"
            parent_row["Attribute 4 name"] = "Poids"
            parent_row["Attribute 4 value(s)"] = w_kg
            parent_row["Attribute 4 default"] = w_kg
            parent_row["Attribute 4 visible"] = "1"
            parent_row["Attribute 4 global"] = "1"

        # Attribut 5 : Réseau
        net_val = woo.get("Attribute 5 value(s)", "5G")
        if net_val:
            parent_row["Attribute 5 name"] = "Réseau"
            parent_row["Attribute 5 value(s)"] = net_val
            parent_row["Attribute 5 default"] = net_val
            parent_row["Attribute 5 visible"] = "1"
            parent_row["Attribute 5 global"] = "1"

        csv_rows.append(parent_row)
        all_skus.add(parent_sku)
        print(f"  [PARENT OK] {slug} -> {formatted_parent_name} (SKU: {parent_sku})")

        # ─── LIGNES VARIATIONS ENFANTS ────────────────────────────────────────
        if is_variable:
            combinations = []
            if "paired_variants" in data and data["paired_variants"]:
                for pv in data["paired_variants"]:
                    c_val = pv.get("color_fr") or pv.get("color", "")
                    r_val = pv.get("rom") or pv.get("storage", "")
                    ram_val = pv.get("ram", "")
                    price_val = pv.get("price") or regular_price
                    sku_suf = pv.get("sku_suffix", "")
                    combinations.append((ram_val, r_val, c_val, price_val, sku_suf))
            else:
                active_pairs = ram_rom_pairs if ram_rom_pairs else [("", "")]
                active_colors = colors if colors else [""]
                for ram, rom in active_pairs:
                    for color in active_colors:
                        combinations.append((ram, rom, color, regular_price, ""))

            for ram, rom, color, price_val, sku_suf in combinations:
                # Construction SKU Enfant
                sku_base = re.sub(r'-MASTER$', '', parent_sku, flags=re.IGNORECASE)
                if sku_suf:
                    var_sku = f"{sku_base}-{sku_suf}".upper()
                else:
                    sku_parts = [sku_base]
                    if ram:
                        sku_parts.append(clean_mem_for_sku(ram))
                    if rom:
                        sku_parts.append(clean_mem_for_sku(rom))
                    if color:
                        sku_parts.append(clean_color_for_sku(color))
                    var_sku = "-".join([p for p in sku_parts if p]).upper()

                # Déduplication SKU
                counter = 1
                orig_sku = var_sku
                while var_sku in all_skus:
                    counter += 1
                    var_sku = f"{orig_sku}-V{counter}"
                all_skus.add(var_sku)

                # Nom Variation Enfant via nomenclature officielle V3.4
                if get_formatted_name:
                    var_data_mock = json.loads(json.dumps(data))
                    if color:
                        var_data_mock["woocommerce_csv"]["Attribute 1 value(s)"] = color
                    if rom:
                        var_data_mock["woocommerce_csv"]["Attribute 2 value(s)"] = rom
                    if ram:
                        var_data_mock["woocommerce_csv"]["Attribute 3 value(s)"] = ram
                    var_name = get_formatted_name(data, var_data_mock)
                else:
                    var_specs = [s for s in [f"{ram}/{rom}" if ram and rom else (rom or ram), color] if s]
                    var_name = f"{base_formatted_name} - {' - '.join(var_specs)}" if var_specs else base_formatted_name

                var_row = empty_row()
                var_row["Type"] = "variation"
                var_row["SKU"] = var_sku
                var_row["Name"] = var_name
                var_row["Published"] = "1"
                var_row["Visibility in catalog"] = "visible"
                var_row["In stock?"] = "1"
                var_row["Stock"] = "10"
                var_row["Regular price"] = price_val or regular_price
                var_row["Categories"] = categories
                var_row["Tags"] = tags
                var_row["Parent"] = parent_sku

                if color:
                    var_row["Attribute 1 name"] = "Couleur"
                    var_row["Attribute 1 value(s)"] = color
                    var_row["Attribute 1 default"] = ""
                    var_row["Attribute 1 visible"] = "1"
                    var_row["Attribute 1 global"] = "1"

                if rom:
                    var_row["Attribute 2 name"] = "Stockage"
                    var_row["Attribute 2 value(s)"] = rom
                    var_row["Attribute 2 default"] = ""
                    var_row["Attribute 2 visible"] = "1"
                    var_row["Attribute 2 global"] = "1"

                if ram:
                    var_row["Attribute 3 name"] = "RAM"
                    var_row["Attribute 3 value(s)"] = ram
                    var_row["Attribute 3 default"] = ""
                    var_row["Attribute 3 visible"] = "1"
                    var_row["Attribute 3 global"] = "1"

                if weight_str:
                    var_row["Attribute 4 name"] = "Poids"
                    var_row["Attribute 4 value(s)"] = w_kg
                    var_row["Attribute 4 default"] = ""
                    var_row["Attribute 4 visible"] = "1"
                    var_row["Attribute 4 global"] = "1"

                if net_val:
                    var_row["Attribute 5 name"] = "Réseau"
                    var_row["Attribute 5 value(s)"] = net_val
                    var_row["Attribute 5 default"] = ""
                    var_row["Attribute 5 visible"] = "1"
                    var_row["Attribute 5 global"] = "1"

                csv_rows.append(var_row)
                total_variations += 1

    # Écriture du CSV global consolidé
    with open(CSV_OUT_PATH, "w", newline="", encoding="utf-8-sig") as f_csv_out:
        writer = csv.DictWriter(f_csv_out, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(csv_rows)

    print("\n=======================================================")
    print("  RAPPORT FINAL CATALOGUE ZTE V3.4")
    print("=======================================================")
    print(f"  [+] Modèles parents compilés avec succès : {success_count} / {len(parent_jsons)}")
    print(f"  [+] Déclinaisons / variations générées  : {total_variations}")
    print(f"  [+] Lignes totales dans le CSV final    : {len(csv_rows)}")
    print(f"  [+] Fichier CSV produit                 : {CSV_OUT_PATH}")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
