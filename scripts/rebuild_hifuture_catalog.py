#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Reconstruction & Compilation du Catalogue HiFuture (V3.4).

Formate les noms commerciaux selon la nomenclature officielle My-eStore (format_product_names.py).
Génère le format WooCommerce complet avec relations parent/variation :
  - 1 ligne parent (Type=variable ou simple) avec Nom commercial enrichi (Top Specs) & Short/Long desc
  - N lignes enfants (Type=variation) pour chaque couleur, avec Parent=SKU_PARENT et Nom=[Nom Parent] - [Couleur]
"""

import os
import sys
import json
import re
import csv
import unicodedata
import subprocess

# Ajouter le répertoire racine au PATH pour importer format_product_names
sys.path.insert(0, os.path.abspath("."))
try:
    from scripts.tools.data_processing.format_product_names import get_formatted_name
except ImportError:
    get_formatted_name = None

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE_ROOT = r"c:\Users\My-eStore-PC2\My-eStore-workspace\wordpress"
PRODUCTS_DIR   = os.path.join(WORKSPACE_ROOT, "products", "hifuture-all")
BUILD_SCRIPT   = os.path.join(WORKSPACE_ROOT, "scripts", "build-product-pack-v2.py")
CSV_OUT        = os.path.join(PRODUCTS_DIR, "import-v2-hifuture-all.csv")

# En-têtes WooCommerce avec colonne Parent pour les variations
CSV_HEADERS = [
    "ID", "Type", "SKU", "Name", "Published", "Visibility in catalog",
    "Short description", "Description", "In stock?", "Stock", "Regular price",
    "Categories", "Tags", "Parent",
    "Attribute 1 name", "Attribute 1 value(s)", "Attribute 1 default", "Attribute 1 visible", "Attribute 1 global",
    "Attribute 2 name", "Attribute 2 value(s)", "Attribute 2 default", "Attribute 2 visible", "Attribute 2 global",
    "Attribute 3 name", "Attribute 3 value(s)", "Attribute 3 default", "Attribute 3 visible", "Attribute 3 global",
    "Attribute 4 name", "Attribute 4 value(s)", "Attribute 4 default", "Attribute 4 visible", "Attribute 4 global",
]


def clean_html(html: str) -> str:
    """Nettoie le HTML pour le CSV WooCommerce (0 commentaire, 0 saut de ligne cosmétique)."""
    if not html:
        return ""
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = html.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    html = re.sub(r'\s+', ' ', html)
    return html.strip()


def color_to_sku_suffix(color: str) -> str:
    """Normalise une couleur pour l'inclure dans un SKU (ASCII, MAJ, tirets)."""
    nfkd = unicodedata.normalize('NFKD', color)
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return ascii_str.upper().replace(' ', '-').replace("'", "")


def parse_weight_g_to_kg(raw: str) -> str:
    """Convertit une valeur de poids brute (ex: '2000g', '82g', 'environ 50g') en format kg (ex: '2 kg', '0.082 kg')."""
    if not raw:
        return ""
    m = re.search(r"(\d+(?:\.\d+)?)", raw)
    if not m:
        return ""
    grams = float(m.group(1))
    kg = grams / 1000.0
    if kg >= 1.0:
        return f"{kg:.3f}".rstrip("0").rstrip(".") + " kg"
    else:
        return f"{kg:.3f} kg"


def get_hifuture_categories(data: dict) -> str:
    """Détermine la catégorie officielle Store pour un produit HiFuture."""
    existing = data.get("woocommerce_csv", {}).get("Categories", "").strip()
    if existing:
        return existing
    
    prod_id = data.get("product_identity", {})
    category = prod_id.get("category", "").lower()
    commercial_name = prod_id.get("commercial_name", "").lower()
    slug = prod_id.get("primary_sku", "").lower()
    
    if category == "audio" or "tour" in slug or "box" in slug or "ripple" in slug or "buds" in slug or "air" in slug or "gravity" in slug or "flexclip" in slug or "sonic" in slug or "music" in slug:
        if "tour" in slug:
            return "Audio & Hi-fi > Casques, Audio & Hi-fi"
        elif "musicbox" in slug or "ripple" in slug:
            return "Audio & Hi-fi > Enceintes Connectées & Bluetooth, Audio & Hi-fi"
        else:
            return "Audio & Hi-fi > Ecouteurs Sans Fil & Ecouteurs Filaire, Audio & Hi-fi"
    else:
        return "Objets Connectés & Wearables > Montres connectées > Smart Watch, Objets Connectés & Wearables > Montres connectées, Objets Connectés & Wearables"


def get_hifuture_tags(data: dict) -> str:
    """Génère les tags SEO WooCommerce pour un produit HiFuture."""
    existing = data.get("woocommerce_csv", {}).get("Tags", "").strip()
    if existing:
        return existing

    prod_id = data.get("product_identity", {})
    comm_name = prod_id.get("commercial_name", "HiFuture")
    brand = prod_id.get("brand", "HiFuture")
    category = prod_id.get("category", "").lower()
    slug = prod_id.get("primary_sku", "").lower()
    
    key_specs = data.get("key_specifications", {})
    screen_tech = key_specs.get("screen_technology", "")
    
    tags = [brand, comm_name]
    
    if category == "audio" or "tour" in slug or "box" in slug or "ripple" in slug or "buds" in slug or "air" in slug or "gravity" in slug or "flexclip" in slug or "sonic" in slug or "music" in slug:
        if "musicbox" in slug or "ripple" in slug:
            tags.extend(["Enceinte Bluetooth", "Enceinte Portable", "Audio HD", "TWS", "IPX7", "Abidjan", "My-eStore"])
        elif "tour" in slug:
            tags.extend(["Casque Bluetooth", "Casque ANC", "Audio HD", "Abidjan", "My-eStore"])
        else:
            tags.extend(["Écouteurs sans fil", "Écouteurs TWS", "Bluetooth 5.3", "Audio HD", "Abidjan", "My-eStore"])
    else:
        tags.extend(["Montre connectée", "Smartwatch", "Bluetooth", "Suivi Santé", "IP68", "Abidjan", "My-eStore"])
        if "AMOLED" in str(screen_tech).upper():
            tags.append("Écran AMOLED")
            
    seen = set()
    unique_tags = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique_tags.append(t)
            
    return ", ".join(unique_tags)


def empty_row() -> dict:
    """Retourne une ligne CSV vide (tous les headers à vide)."""
    return {h: "" for h in CSV_HEADERS}


def main():
    print("\n=======================================================")
    print("  REBUILD CATALOGUE HIFUTURE (V3.4)")
    print("  Nomenclature Noms Commerciaux + Parent/Variation")
    print("=======================================================\n")

    if not os.path.isdir(PRODUCTS_DIR):
        print(f"[-] Erreur : dossier products/hifuture-all introuvable : {PRODUCTS_DIR}")
        sys.exit(1)

    parent_csv_path = os.path.join(PRODUCTS_DIR, "hifuture-models-parent.csv")
    parent_data_dir = os.path.join(WORKSPACE_ROOT, "product-data", "hifuture")

    if not os.path.exists(parent_csv_path):
        print(f"[-] Erreur : hifuture-models-parent.csv introuvable : {parent_csv_path}")
        sys.exit(1)

    with open(parent_csv_path, "r", encoding="utf-8") as f_csv_in:
        reader = csv.DictReader(f_csv_in)
        target_models = [row for row in reader if row.get("model_slug", "").strip()]

    print(f"[+] {len(target_models)} modèles parents référencés dans hifuture-models-parent.csv\n")

    csv_rows = []
    success_count = 0
    fail_count = 0

    for item in target_models:
        slug = item["model_slug"].strip()
        official_colors_fr = item.get("official_colors_fr", "").strip()
        weight_g_raw = item.get("weight g", "").strip()
        weight_kg = parse_weight_g_to_kg(weight_g_raw)
        
        parent_json_path = os.path.join(parent_data_dir, f"{slug}.json")

        if not os.path.exists(parent_json_path):
            print(f"  [WARN] Fichier parent JSON manquant pour {slug}")
            continue

        # Chercher le dossier correspondant dans products/hifuture-all/
        existing_dirs = [d for d in os.listdir(PRODUCTS_DIR) if os.path.isdir(os.path.join(PRODUCTS_DIR, d))]
        matching_dir = None
        for d in existing_dirs:
            if d.lower() == slug.lower() or d.lower().replace("-", "") == slug.lower().replace("-", ""):
                matching_dir = d
                break

        if not matching_dir:
            matching_dir = slug
            prod_folder = os.path.join(PRODUCTS_DIR, matching_dir)
            os.makedirs(prod_folder, exist_ok=True)
        else:
            prod_folder = os.path.join(PRODUCTS_DIR, matching_dir)

        pack_data_path = os.path.join(prod_folder, f"pack-data-{slug}.json")

        # Synchroniser depuis product-data/hifuture/
        with open(parent_json_path, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)

        # Synchroniser les couleurs, le poids, les catégories et les tags
        woo_dict = data.setdefault("woocommerce_csv", {})
        if official_colors_fr:
            woo_dict["Attribute 1 name"] = "Couleur"
            woo_dict["Attribute 1 value(s)"] = official_colors_fr
            colors_list = [c.strip() for c in official_colors_fr.split(",") if c.strip()]
            if colors_list:
                woo_dict["Attribute 1 default"] = colors_list[0]
        
        if weight_kg:
            key_specs = data.setdefault("key_specifications", {})
            key_specs["weight"] = weight_kg
            woo_dict["Attribute 4 name"] = "Poids"
            woo_dict["Attribute 4 value(s)"] = weight_kg
            woo_dict["Attribute 4 default"] = weight_kg

        cat_str = get_hifuture_categories(data)
        tag_str = get_hifuture_tags(data)
        woo_dict["Categories"] = cat_str
        woo_dict["Tags"] = tag_str

        # Mettre à jour le fichier parent source
        with open(parent_json_path, "w", encoding="utf-8") as f_p_out:
            json.dump(data, f_p_out, ensure_ascii=False, indent=4)

        # Enregistrer le pack-data JSON produit
        with open(pack_data_path, "w", encoding="utf-8") as f_out:
            json.dump(data, f_out, ensure_ascii=False, indent=4)


        # Lire le pack-data JSON
        try:
            with open(pack_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  [JSON FAIL] {slug}: {e}")
            fail_count += 1
            continue

        woo = data.get("woocommerce_csv", {})
        parent_sku = woo.get("SKU", slug.upper())

        # 1. Extraire les couleurs certifiées officielles depuis Attribute 1
        attr1_name = woo.get("Attribute 1 name", "Couleur")
        attr1_vals = woo.get("Attribute 1 value(s)", "")
        attr1_default = woo.get("Attribute 1 default", "")
        attr1_visible = woo.get("Attribute 1 visible", "1")
        attr1_global  = woo.get("Attribute 1 global",  "1")

        colors = []
        if attr1_vals:
            sep = "|" if "|" in attr1_vals else ","
            colors = [c.strip() for c in attr1_vals.split(sep) if c.strip()]

        attr1_default = attr1_default or (colors[0] if colors else "")

        # 2. Formater le nom commercial selon la nomenclature My-eStore (format_product_names)
        if get_formatted_name:
            formatted_name = get_formatted_name(data, data)
        else:
            formatted_name = data.get("woocommerce_csv", {}).get("Name", slug)

        # S'assurer que le nom parent ne contient ni liste de couleurs ni mémoire MB inutile à la fin
        clean_parent_name = re.sub(r'\s*-\s*(?:[A-ZÀ-ÿa-z]+(?:\s*,\s*|\s*\|\s*|\s+)){1,}[A-ZÀ-ÿa-z]+\s*$', '', formatted_name)
        clean_parent_name = re.sub(r'\s*-\s*(?:N/A|Standard|\d+\s*(?:Mo|MB))\s*$', '', clean_parent_name, flags=re.IGNORECASE).strip()

        # 3. Synchroniser les JSON (products/hifuture-all/ et product-data/hifuture/)
        if "woocommerce_csv" in data:
            data["woocommerce_csv"]["Name"] = clean_parent_name
            data["woocommerce_csv"]["Stock"] = "10"

        try:
            with open(pack_data_path, "w", encoding="utf-8") as f_out:
                json.dump(data, f_out, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"  [WARN] Impossible de maj pack-data pour {slug}: {e}")

        # Synchroniser également product-data/hifuture/[slug].json si existant
        parent_json_path = os.path.join(WORKSPACE_ROOT, "product-data", "hifuture", f"{slug}.json")
        if os.path.exists(parent_json_path):
            try:
                with open(parent_json_path, "r", encoding="utf-8") as f_p:
                    p_data = json.load(f_p)
                if "woocommerce_csv" in p_data:
                    p_data["woocommerce_csv"]["Name"] = clean_parent_name
                    p_data["woocommerce_csv"]["Stock"] = "10"
                with open(parent_json_path, "w", encoding="utf-8") as f_p_out:
                    json.dump(p_data, f_p_out, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"  [WARN] Impossible de maj product-data pour {slug}: {e}")

        # 4. Compiler via build-product-pack-v2.py avec --serie hifuture-all
        cmd = [
            sys.executable, BUILD_SCRIPT,
            "--data", pack_data_path,
            "--outdir", prod_folder,
            "--modele", slug,
            "--serie", "hifuture-all",
            "--skip-validation",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode != 0:
            print(f"  [BUILD FAIL] {matching_dir}: {res.stderr[:300]}")
            fail_count += 1
            continue

        # Lire et nettoyer les HTML générés
        short_html_path = os.path.join(prod_folder, f"short-{slug}.html")
        long_html_path  = os.path.join(prod_folder, f"long-{slug}.html")
        raw_short = open(short_html_path, "r", encoding="utf-8").read() if os.path.exists(short_html_path) else ""
        raw_long  = open(long_html_path,  "r", encoding="utf-8").read() if os.path.exists(long_html_path)  else ""
        clean_short = clean_html(raw_short)
        clean_long  = clean_html(raw_long)

        product_type = "variable" if colors else "simple"

        # ─── LIGNE PARENT ─────────────────────────────────────────────────────
        parent_row = empty_row()
        parent_row["ID"]                     = woo.get("ID", "")
        parent_row["Type"]                   = product_type
        parent_row["SKU"]                    = parent_sku
        parent_row["Name"]                   = clean_parent_name
        parent_row["Published"]              = woo.get("Published", "1")
        parent_row["Visibility in catalog"]  = woo.get("Visibility in catalog", "visible")
        parent_row["Short description"]      = clean_short
        parent_row["Description"]            = clean_long
        parent_row["In stock?"]              = woo.get("In stock?", "1")
        parent_row["Stock"]                  = "10"
        parent_row["Regular price"]          = woo.get("Regular price", "")
        parent_row["Categories"]             = woo.get("Categories", "")
        parent_row["Tags"]                   = woo.get("Tags", "")
        parent_row["Parent"]                 = ""

        if attr1_name:
            parent_row["Attribute 1 name"]       = attr1_name
            parent_row["Attribute 1 value(s)"]   = attr1_vals
            parent_row["Attribute 1 default"]    = attr1_default
            parent_row["Attribute 1 visible"]    = attr1_visible
            parent_row["Attribute 1 global"]     = attr1_global

        for i in (2, 3):
            n = woo.get(f"Attribute {i} name", "")
            if n:
                parent_row[f"Attribute {i} name"]     = n
                parent_row[f"Attribute {i} value(s)"] = woo.get(f"Attribute {i} value(s)", "")
                parent_row[f"Attribute {i} default"]  = woo.get(f"Attribute {i} default", "")
                parent_row[f"Attribute {i} visible"]  = woo.get(f"Attribute {i} visible", "1")
                parent_row[f"Attribute {i} global"]   = woo.get(f"Attribute {i} global", "1")

        parent_row["Attribute 4 name"]      = woo.get("Attribute 4 name", "Poids")
        parent_row["Attribute 4 value(s)"]  = woo.get("Attribute 4 value(s)", "")
        parent_row["Attribute 4 default"]   = woo.get("Attribute 4 default", "")
        parent_row["Attribute 4 visible"]   = woo.get("Attribute 4 visible", "1")
        parent_row["Attribute 4 global"]    = woo.get("Attribute 4 global", "1")

        csv_rows.append(parent_row)
        print(f"  [PARENT OK] {product_type.upper()} — {clean_parent_name}")

        # ─── LIGNES VARIATION ENFANTS (1 par couleur) ─────────────────────────
        if colors:
            for color in colors:
                color_suffix = color_to_sku_suffix(color)
                variation_sku  = f"{parent_sku}-{color_suffix}"
                variation_name = f"{clean_parent_name} - {color}"

                var_row = empty_row()
                var_row["Type"]                  = "variation"
                var_row["SKU"]                   = variation_sku
                var_row["Name"]                  = variation_name
                var_row["Published"]             = "1"
                var_row["Visibility in catalog"] = "visible"
                var_row["Short description"]     = ""
                var_row["Description"]           = ""
                var_row["In stock?"]             = "1"
                var_row["Stock"]                 = "10"
                var_row["Regular price"]         = woo.get("Regular price", "")
                var_row["Parent"]                = parent_sku

                var_row["Attribute 1 name"]      = attr1_name
                var_row["Attribute 1 value(s)"]  = color
                var_row["Attribute 1 default"]   = color
                var_row["Attribute 1 visible"]   = attr1_visible
                var_row["Attribute 1 global"]    = attr1_global

                var_row["Attribute 4 name"]      = woo.get("Attribute 4 name", "Poids")
                var_row["Attribute 4 value(s)"]  = woo.get("Attribute 4 value(s)", "")
                var_row["Attribute 4 default"]   = woo.get("Attribute 4 default", "")
                var_row["Attribute 4 visible"]   = woo.get("Attribute 4 visible", "1")
                var_row["Attribute 4 global"]    = woo.get("Attribute 4 global", "1")

                csv_rows.append(var_row)
                print(f"    ↳ [VARIATION] {variation_name} ({variation_sku})")

        success_count += 1

    # Écrire le CSV consolidé propre
    print(f"\n[+] Écriture du CSV consolidé : {CSV_OUT}")
    with open(CSV_OUT, "w", encoding="utf-8-sig", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(csv_rows)

    total_rows = len(csv_rows)
    parent_rows = sum(1 for r in csv_rows if r["Type"] in ("variable", "simple"))
    variation_rows = sum(1 for r in csv_rows if r["Type"] == "variation")

    print(f"\n=======================================================")
    print(f"  BILAN REBUILD HIFUTURE V3.4")
    print(f"  Produits parents : {success_count} / {len(target_models)}")
    print(f"  Lignes CSV totales : {total_rows}")
    print(f"    → Parents (variable/simple) : {parent_rows}")
    print(f"    → Variations enfants        : {variation_rows}")
    print(f"  CSV : {CSV_OUT}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    main()
