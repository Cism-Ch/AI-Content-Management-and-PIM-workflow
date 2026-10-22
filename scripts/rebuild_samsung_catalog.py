#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Reconstruction & Compilation Industrielle du Catalogue Samsung (V3.4).

Standardise l'arborescence et génère le format WooCommerce complet avec relations Parent-Enfant :
  - Sous-dossier par modèle : products/[series-all]/[model-slug]/ contenant :
      * pack-data-[model-slug].json
      * long-[model-slug].html
      * short-[model-slug].html
  - CSV WooCommerce Consolidé Global : products/[series-all]/import-v2-[series-all].csv
      * 1 ligne parent (Type=variable) avec nomenclature multi-variantes (ex: (8 Go|16 Go & 256 Go|512 Go)),
        descriptions HTML complètes et attributs globaux avec espace (ex: '128 Go, 512 Go')
      * N lignes enfants (Type=variation) pour chaque combinaison couleur / RAM / Stockage reliées par SKU Parent
"""

import os
import sys
import json
import re
import csv
import unicodedata
import subprocess
import argparse
import shutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCT_DATA_DIR = os.path.join(WORKSPACE_ROOT, "product-data", "samsung")
PARENT_CSV_PATH = os.path.join(PRODUCT_DATA_DIR, "samsung_models_parent.csv")
BUILD_SCRIPT = os.path.join(WORKSPACE_ROOT, "scripts", "build-product-pack-v3.py")

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


def clean_mem_for_sku(mem: str) -> str:
    """Convertit la mémoire en notation internationale (GB, TB, MB) pour les SKUs."""
    if not mem:
        return ""
    val = normalize_ascii(mem)
    val = val.replace("GO", "GB").replace("TO", "TB").replace("MO", "MB")
    return re.sub(r'[^A-Z0-9-]', '', val)


def format_memory_with_space(mem_str: str) -> str:
    """Normalise l'écriture de la mémoire avec un espace obligatoire entre le chiffre et l'unité (ex: '128 Go', '1.5 Go', '1 To')."""
    if not mem_str:
        return ""
    val = str(mem_str).strip()
    val = val.replace("GB", "Go").replace("TB", "To").replace("MB", "Mo")
    val = re.sub(r'(\d+(?:\.\d+)?)\s*(Go|To|Mo)', r'\1 \2', val)
    return val.strip()


def parse_mem_to_gb(mem_str: str) -> float:
    """Convertit une chaîne mémoire (Go, To, Mo, GB, TB, MB) en valeur numérique en Go."""
    if not mem_str:
        return 0.0
    s = mem_str.strip().upper()
    m = re.search(r'(\d+(?:\.\d+)?)\s*(TO|TB|GO|GB|MO|MB)?', s)
    if not m:
        return 0.0
    val = float(m.group(1))
    unit = m.group(2) or 'GO'
    if unit in ['TO', 'TB']:
        return val * 1024.0
    elif unit in ['MO', 'MB']:
        return val / 1024.0
    else:
        return val


def round_to_5000(val: float) -> int:
    """Arrondit un montant au multiple de 5 000 FCFA le plus proche."""
    return int(round(val / 5000.0) * 5000)


def compute_samsung_tier_price(base_price_val: int, tier_index: int) -> int:
    """Calcule le prix par palier de 30% depuis la configuration la plus basse (Tier 0)."""
    return round_to_5000(base_price_val * (1.0 + 0.30 * tier_index))


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

    # Pattern correspondant à une mention de RAM/ROM existante (ex: 8Go/128Go, 8 Go/128 Go, (8 Go & 128 Go), 1.5 Go, 128Go, etc.)
    pattern = r'(?:\(\s*[\w\.\s\|&/]+\s*\)|\d+(?:\.\d+)?\s*(?:Go|GB|To|TB|Mo|MB)\s*\/\s*\d+(?:\.\d+)?\s*(?:Go|GB|To|TB|Mo|MB)|\d+(?:\.\d+)?\s*(?:Go|GB|To|TB|Mo|MB))'

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


def get_series_output_dir(serie_name: str) -> str:
    """Détermine le dossier de sortie selon la série Samsung."""
    s = serie_name.lower().strip()
    if "galaxy s" in s or s == "s" or "samsung-s" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-s-all")
    elif "galaxy z" in s or s == "z" or "fold" in s or "flip" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-z-all")
    elif "galaxy a" in s or s == "a" or "samsung-a" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-a-all")
    elif "galaxy m" in s or s == "m" or "samsung-m" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-m-all")
    elif "watch" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-watch-all")
    elif "tab s" in s or "tab-s" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-tab-s-all")
    elif "tab a" in s or "tab-a" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-tab-a-all")
    elif "tab active" in s or "tab-active" in s:
        return os.path.join(WORKSPACE_ROOT, "products", "samsung-galaxy-tab-active-all")
    else:
        return os.path.join(WORKSPACE_ROOT, "products", f"samsung-{s.replace(' ', '-')}-all")


def collect_all_parent_jsons():
    """Collecte l'ensemble des JSON parents présents dans product-data/samsung/."""
    json_map = {}
    for root, dirs, files in os.walk(PRODUCT_DATA_DIR):
        for f in files:
            if f.endswith(".json") and not f.startswith("hyp_"):
                slug = f[:-5]
                json_map[slug] = os.path.join(root, f)
    return json_map


def process_series(target_series: str):
    """Traite et consolide une série Samsung spécifique."""
    print(f"\n=======================================================")
    print(f"  TRAITEMENT CATALOGUE SAMSUNG : {target_series.upper()}")
    print(f"=======================================================\n")

    parent_jsons = collect_all_parent_jsons()

    csv_info_map = {}
    if os.path.isfile(PARENT_CSV_PATH):
        with open(PARENT_CSV_PATH, "r", encoding="utf-8") as f_csv:
            reader = csv.DictReader(f_csv)
            for row in reader:
                slug = row.get("model_slug", "").strip()
                if slug:
                    csv_info_map[slug] = row

    # Filtrer les modèles de la série ciblée
    target_clean = target_series.lower().strip()
    selected_slugs = []

    for slug, json_path in parent_jsons.items():
        if target_clean in ["all", "tout"]:
            selected_slugs.append(slug)
        elif target_clean in ["s", "galaxy-s", "galaxy s"] and ("galaxy-s" in slug or slug.startswith("samsung-galaxy-s") or slug.startswith("samsung-s")):
            selected_slugs.append(slug)
        elif target_clean in ["z", "galaxy-z", "galaxy z"] and ("galaxy-z" in slug or "fold" in slug or "flip" in slug):
            selected_slugs.append(slug)
        elif target_clean in ["a", "galaxy-a", "galaxy a"] and ("galaxy-a" in slug or slug.startswith("samsung-galaxy-a")):
            selected_slugs.append(slug)
        elif target_clean in ["m", "galaxy-m", "galaxy m"] and ("galaxy-m" in slug or slug.startswith("samsung-galaxy-m")):
            selected_slugs.append(slug)
        elif target_clean in ["watch", "galaxy-watch", "galaxy watch"] and "watch" in slug:
            selected_slugs.append(slug)
        elif target_clean in ["tab-s", "galaxy-tab-s", "galaxy tab s", "tab-s-all", "galaxy-tab-s-all"] and ("tab-s" in slug or "-tab-s" in slug):
            selected_slugs.append(slug)
        elif target_clean in ["tab-a", "galaxy-tab-a", "galaxy tab a", "tab-a-all", "galaxy-tab-a-all", "tab-active"] and ("tab-a" in slug or "tab-active" in slug):
            selected_slugs.append(slug)
        elif target_clean in ["tab", "galaxy-tab", "galaxy tab"] and "tab" in slug:
            selected_slugs.append(slug)

    selected_slugs = sorted(list(set(selected_slugs)))

    if not selected_slugs:
        print(f"[-] Aucun modèle trouvé pour la série : {target_series}")
        return

    print(f"[+] {len(selected_slugs)} modèles JSON parents identifiés dans la série.")

    # Regrouper par dossier de sortie
    outdir = get_series_output_dir(target_series)
    os.makedirs(outdir, exist_ok=True)
    series_folder_name = os.path.basename(outdir)
    csv_out_path = os.path.join(outdir, f"import-v2-{series_folder_name}.csv")

    csv_rows = []
    all_skus = set()
    success_count = 0
    fail_count = 0

    for slug in selected_slugs:
        parent_json_path = parent_jsons[slug]

        # Créer le sous-dossier modèle dédié
        model_dir = os.path.join(outdir, slug)
        os.makedirs(model_dir, exist_ok=True)

        with open(parent_json_path, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)

        # Enregistrer le pack-data dans le sous-dossier modèle
        pack_data_path = os.path.join(model_dir, f"pack-data-{slug}.json")
        with open(pack_data_path, "w", encoding="utf-8") as f_out:
            json.dump(data, f_out, ensure_ascii=False, indent=4)

        # Compiler via build-product-pack-v3.py vers model_dir
        cmd = [
            sys.executable, BUILD_SCRIPT,
            "--data", pack_data_path,
            "--outdir", model_dir,
            "--modele", slug,
            "--skip-validation",
            "--no-csv"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode != 0:
            print(f"  [BUILD FAIL] {slug}: {res.stderr[:300]}")
            fail_count += 1
            continue

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
        categories = woo.get("Categories", "Smartphones > Samsung")
        tags = woo.get("Tags", "Samsung, Smartphone")

        csv_row_info = csv_info_map.get(slug, {})

        # Si paired_variants est présent, c'est la source de vérité absolue (modèle ZTE)
        if "paired_variants" in data and data["paired_variants"]:
            colors = []
            all_roms = []
            all_rams = []
            ram_rom_pairs = []
            for pv in data["paired_variants"]:
                c_val = pv.get("color_fr") or pv.get("color", "")
                r_val = pv.get("storage") or pv.get("rom", "")
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
            # Récupérer les attributs officiels
            colors_str = csv_row_info.get("official_colors_fr", "").strip() or woo.get("Attribute 1 value(s)", "").strip()
            ram_rom_str = csv_row_info.get("paired_variantes", "").strip() or csv_row_info.get("ram&rom_options", "").strip()

            # Parsing des couleurs (dédoublonnées)
            colors = list(dict.fromkeys([c.strip() for c in colors_str.split(",") if c.strip()]))

            # Parsing des options RAM/ROM
            ram_rom_pairs = []
            if ram_rom_str:
                for pair in ram_rom_str.split(","):
                    p = pair.strip()
                    if "/" in p:
                        parts = p.split("/")
                        ram_rom_pairs.append((format_memory_with_space(parts[0]), format_memory_with_space(parts[1])))
                    else:
                        ram_rom_pairs.append(("", format_memory_with_space(p)))
            else:
                # Fallback sur les attributs du JSON
                stockage_val = woo.get("Attribute 2 value(s)", "")
                ram_val = woo.get("Attribute 3 value(s)", "")
                stockages = [format_memory_with_space(s) for s in stockage_val.split(",") if s.strip()]
                rams = [format_memory_with_space(r) for r in ram_val.split(",") if r.strip()]
                if rams and stockages:
                    for r in rams:
                        for s in stockages:
                            ram_rom_pairs.append((r, s))
                elif stockages:
                    for s in stockages:
                        ram_rom_pairs.append(("", s))

            # Stockage & RAM consolidés pour la fiche parent avec espace obligatoire
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

        # Construction du nom Parent multi-variantes
        ram_rom_group_str = build_parent_ram_rom_group(all_rams, all_roms)
        formatted_parent_name = inject_parent_ram_rom_in_name(raw_parent_name, ram_rom_group_str)
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

        # Attribut 2 : Stockage (avec espace, ex: '128 Go, 512 Go')
        if all_roms:
            parent_row["Attribute 2 name"] = "Stockage"
            parent_row["Attribute 2 value(s)"] = ", ".join(all_roms)
            parent_row["Attribute 2 default"] = all_roms[0]
            parent_row["Attribute 2 visible"] = "1"
            parent_row["Attribute 2 global"] = "1"

        # Attribut 3 : RAM (avec espace, ex: '8 Go, 12 Go')
        if all_rams:
            parent_row["Attribute 3 name"] = "RAM"
            parent_row["Attribute 3 value(s)"] = ", ".join(all_rams)
            parent_row["Attribute 3 default"] = all_rams[0]
            parent_row["Attribute 3 visible"] = "1"
            parent_row["Attribute 3 global"] = "1"

        # Attribut 4 : Poids (IGNORÉ POUR SAMSUNG SUIVANT DIRECTIVE OFFICIELLE)

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
        print(f"  [PARENT OK] {product_type.upper()} — {formatted_parent_name} (SKU: {parent_sku})")

        # ─── LIGNES VARIATION ENFANTS (MODÈLE ZTE - SANS CARTÉSIEN & PALIERS 30%) ──
        if is_variable:
            combinations = []
            clean_bp = re.sub(r'[^\d]', '', str(regular_price))
            base_price_int = int(clean_bp) if clean_bp else 150000

            if "paired_variants" in data and data["paired_variants"]:
                # Établir les paliers de prix (+30% par palier de configuration)
                unique_configs = []
                seen_cfgs = set()
                for pv in data["paired_variants"]:
                    cfg = (pv.get("ram", ""), pv.get("storage") or pv.get("rom", ""))
                    if cfg not in seen_cfgs:
                        seen_cfgs.add(cfg)
                        unique_configs.append(cfg)
                unique_configs.sort(key=lambda x: (parse_mem_to_gb(x[1]), parse_mem_to_gb(x[0])))

                config_price_map = {}
                for k, cfg in enumerate(unique_configs):
                    config_price_map[cfg] = str(compute_samsung_tier_price(base_price_int, k))

                for pv in data["paired_variants"]:
                    c_val = pv.get("color_fr") or pv.get("color", "")
                    r_val = pv.get("storage") or pv.get("rom", "")
                    ram_val = pv.get("ram", "")
                    cfg = (ram_val, r_val)
                    # Privilégier le prix stocké dans paired_variants ou le prix calculé du palier
                    price_val = pv.get("price") or config_price_map.get(cfg, str(base_price_int))
                    sku_suf = pv.get("sku_suffix", "")
                    combinations.append((ram_val, r_val, c_val, price_val, sku_suf))
            else:
                active_pairs = ram_rom_pairs if ram_rom_pairs else [("", "")]
                active_colors = colors if colors else [""]
                unique_cfgs = sorted(active_pairs, key=lambda x: (parse_mem_to_gb(x[1]), parse_mem_to_gb(x[0])))
                config_price_map = {}
                for k, cfg in enumerate(unique_cfgs):
                    config_price_map[cfg] = str(compute_samsung_tier_price(base_price_int, k))

                for ram, rom in active_pairs:
                    cfg_price = config_price_map.get((ram, rom), str(base_price_int))
                    for color in active_colors:
                        combinations.append((ram, rom, color, cfg_price, ""))

            base_model_title = formatted_parent_name.split(" - ")[0]

            for ram, rom, color, price_val, sku_suf in combinations:
                var_row = empty_row()
                var_row["Type"] = "variation"
                var_row["Published"] = "1"
                var_row["Visibility in catalog"] = "visible"
                var_row["Short description"] = ""
                var_row["Description"] = ""
                var_row["In stock?"] = "1"
                var_row["Stock"] = "10"
                var_row["Regular price"] = price_val or regular_price
                var_row["Parent"] = parent_sku

                # Construire le SKU Enfant avec anti-collision (Notation internationale GB/TB)
                sku_base = re.sub(r'-MASTER$', '', parent_sku, flags=re.IGNORECASE)
                if sku_suf:
                    clean_suf = sku_suf.replace("-GO", "-GB").replace("-TO", "-TB").replace("-MO", "-MB")
                    var_sku = f"{sku_base}-{clean_suf}".upper()
                else:
                    sku_parts = [sku_base]
                    if ram and rom:
                        sku_parts.append(f"{clean_mem_for_sku(ram)}-{clean_mem_for_sku(rom)}")
                    elif rom:
                        sku_parts.append(clean_mem_for_sku(rom))
                    elif ram:
                        sku_parts.append(clean_mem_for_sku(ram))

                    if color:
                        sku_parts.append(normalize_ascii(color))

                    var_sku = "-".join([p for p in sku_parts if p]).upper()

                # Anti-collision SKU
                counter = 1
                orig_sku = var_sku
                while var_sku in all_skus:
                    counter += 1
                    var_sku = f"{orig_sku}-V{counter}"
                all_skus.add(var_sku)

                name_suffixes = []
                if ram and rom:
                    name_suffixes.append(f"{ram}/{rom}")
                elif rom:
                    name_suffixes.append(rom)
                elif ram:
                    name_suffixes.append(ram)
                if color:
                    name_suffixes.append(color)

                var_name = f"{base_model_title} - " + " - ".join(name_suffixes) if name_suffixes else formatted_parent_name
                var_row["SKU"] = var_sku
                var_row["Name"] = var_name

                # Attributs de la variation avec espace
                if color:
                    var_row["Attribute 1 name"] = "Couleur"
                    var_row["Attribute 1 value(s)"] = color
                    var_row["Attribute 1 default"] = color
                    var_row["Attribute 1 visible"] = "1"
                    var_row["Attribute 1 global"] = "1"

                if rom:
                    var_row["Attribute 2 name"] = "Stockage"
                    var_row["Attribute 2 value(s)"] = rom
                    var_row["Attribute 2 default"] = rom
                    var_row["Attribute 2 visible"] = "1"
                    var_row["Attribute 2 global"] = "1"

                if ram:
                    var_row["Attribute 3 name"] = "RAM"
                    var_row["Attribute 3 value(s)"] = ram
                    var_row["Attribute 3 default"] = ram
                    var_row["Attribute 3 visible"] = "1"
                    var_row["Attribute 3 global"] = "1"

                # Attribut 4 : Poids (IGNORÉ POUR SAMSUNG SUIVANT DIRECTIVE OFFICIELLE)

                if net_val:
                    var_row["Attribute 5 name"] = "Réseau"
                    var_row["Attribute 5 value(s)"] = net_val
                    var_row["Attribute 5 default"] = net_val
                    var_row["Attribute 5 visible"] = "1"
                    var_row["Attribute 5 global"] = "1"

                csv_rows.append(var_row)
                print(f"    ↳ [VARIATION] {var_name} ({var_sku})")

        success_count += 1

    # Écrire le CSV consolidé de la série
    print(f"\n[+] Écriture du CSV consolidé : {csv_out_path}")
    with open(csv_out_path, "w", encoding="utf-8-sig", newline="") as f_out_csv:
        writer = csv.DictWriter(f_out_csv, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(csv_rows)

    # Nettoyage des dossiers groupés obsolètes ou fichiers plats dans outdir
    for item_name in os.listdir(outdir):
        item_path = os.path.join(outdir, item_name)
        if os.path.isdir(item_path):
            if item_name.startswith("samsung-s") and item_name not in selected_slugs:
                shutil.rmtree(item_path, ignore_errors=True)
        elif os.path.isfile(item_path) and item_name != f"import-v2-{series_folder_name}.csv":
            if item_name.startswith("long-") or item_name.startswith("short-") or item_name.startswith("import-v2-") or item_name.startswith("prix-"):
                try:
                    os.remove(item_path)
                except Exception:
                    pass

    total_rows = len(csv_rows)
    parent_rows = sum(1 for r in csv_rows if r["Type"] in ("variable", "simple"))
    variation_rows = sum(1 for r in csv_rows if r["Type"] == "variation")

    print(f"\n=======================================================")
    print(f"  BILAN SÉRIE {series_folder_name.upper()}")
    print(f"  Produits parents traités : {success_count} / {len(selected_slugs)}")
    print(f"  Lignes CSV totales       : {total_rows}")
    print(f"    → Parents (variable)   : {parent_rows}")
    print(f"    → Variations enfants   : {variation_rows}")
    print(f"  Fichier CSV final        : {csv_out_path}")
    print(f"=======================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Rebuild and consolidate Samsung catalog V3.4")
    parser.add_argument("--series", default="all", help="Série à traiter (galaxy-s, galaxy-z, galaxy-a, galaxy-m, galaxy-watch, galaxy-tab, all)")
    args = parser.parse_args()

    target = args.series.lower().strip()
    if target in ["all", "tout"]:
        for s in ["galaxy-s", "galaxy-z", "galaxy-a", "galaxy-m", "galaxy-tab-s", "galaxy-tab-a", "galaxy-watch"]:
            process_series(s)
    else:
        process_series(target)


if __name__ == "__main__":
    main()
