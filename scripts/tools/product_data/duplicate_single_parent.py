#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duplique un modèle parent V3.4 validé (PASS) vers ses dossiers de variantes physiques sous products/blackview-all/
et lance la compilation HTML avec build-product-pack-v2.py.
"""

import json
import os
import csv
import re
import copy
import sys
import subprocess

base_dir = r"c:\Users\My-eStore-PC2\My-eStore-workspace\wordpress"
csv_parent_path = os.path.join(base_dir, "products", "blackview-all", "blackview_models_parent.csv")
parent_data_dir = os.path.join(base_dir, "product-data", "blackview")
out_products_dir = os.path.join(base_dir, "products", "blackview-all")
builder_script = os.path.join(base_dir, "scripts", "build-product-pack-v2.py")

def slugify(text):
    if not text: return ""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', str(text))
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    clean = re.sub(r'[^a-zA-Z0-9]', '-', ascii_str.lower())
    clean = re.sub(r'-+', '-', clean).strip('-')
    return clean

def sku_clean(text):
    if not text: return ""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', str(text))
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    clean = re.sub(r'[^a-zA-Z0-9]', '', ascii_str.upper())
    return clean

def duplicate_parent_model(target_slug):
    with open(csv_parent_path, encoding="utf-8") as f:
        parent_models = list(csv.DictReader(f))
        
    parent_row = next((r for r in parent_models if r['model_slug'].strip() == target_slug), None)
    if not parent_row:
        print(f"[-] Erreur: Modèle {target_slug} non trouvé dans blackview_models_parent.csv")
        sys.exit(1)
        
    parent_json_path = os.path.join(parent_data_dir, f"blackview-{target_slug}.json")
    if not os.path.exists(parent_json_path):
        print(f"[-] Erreur: JSON parent introuvable : {parent_json_path}")
        sys.exit(1)
        
    with open(parent_json_path, encoding="utf-8") as pf:
        parent_json = json.load(pf)
        
    colors_fr = [c.strip() for c in parent_row['official_colors_fr'].split(',') if c.strip()]
    if not colors_fr: colors_fr = ["Noir"]
    
    def is_invalid_mem(val):
        if not val: return True
        v = val.strip().upper()
        return v in ["N/A", "N / A", "NA", "N", "A", "NONE", "NULL", "UNDEFINED", ""]

    ram_rom_raw = parent_row.get('ram&rom_options', '').strip()
    
    configs = []
    if not is_invalid_mem(ram_rom_raw):
        ram_rom_list = [opt.strip() for opt in ram_rom_raw.split(',') if opt.strip()]
        for opt in ram_rom_list:
            if is_invalid_mem(opt):
                continue
            if "/" in opt:
                parts = opt.split("/")
                ram_val = "" if is_invalid_mem(parts[0]) else parts[0].strip()
                rom_val = "" if is_invalid_mem(parts[1]) else parts[1].strip()
                if ram_val or rom_val:
                    configs.append((ram_val, rom_val))
            else:
                configs.append(("", opt.strip()))
            
    if not configs:
        configs = [("", "")]
        
    created_variants = 0
    compiled_htmls = 0
    
    print(f"[Phase C] Duplication des variantes pour {target_slug}...")
    
    for color in colors_fr:
        for (ram, rom) in configs:
            parts = [target_slug]
            if ram and not is_invalid_mem(ram): parts.append(slugify(ram))
            if rom and not is_invalid_mem(rom): parts.append(slugify(rom))
            if color and not is_invalid_mem(color): parts.append(slugify(color))
            folder_name = "-".join(parts)
            
            variant_dir = os.path.join(out_products_dir, folder_name)
            os.makedirs(variant_dir, exist_ok=True)
            
            v_data = copy.deepcopy(parent_json)
            brand = v_data.get("metadata", {}).get("target_brand", "Blackview")
            model_name = v_data.get("metadata", {}).get("target_model", target_slug)
            full_model = model_name if model_name.lower().startswith(brand.lower()) else f"{brand} {model_name}"
            
            sku_parts = ["BV", sku_clean(target_slug)]
            if rom and not is_invalid_mem(rom): sku_parts.append(sku_clean(rom))
            if ram and not is_invalid_mem(ram): sku_parts.append(sku_clean(ram))
            if color and not is_invalid_mem(color): sku_parts.append(sku_clean(color))
            variant_sku = "-".join(sku_parts)
            
            woo = v_data["woocommerce_csv"]
            woo["SKU"] = variant_sku
            woo["Attribute 1 value(s)"] = color
            woo["Attribute 1 default"] = color
            
            # Formatage automatique du nom commercial vendeur V3.4 (Nomenclature enrichie)
            try:
                from scripts.tools.data_processing.format_product_names import get_formatted_name
                woo["Name"] = get_formatted_name(parent_json, v_data)
            except Exception:
                woo["Name"] = f"{full_model} - {color}" if color else full_model
            
            if rom and not is_invalid_mem(rom):
                woo["Attribute 2 value(s)"] = rom
                woo["Attribute 2 default"] = rom
            else:
                woo.pop("Attribute 2 name", None)
                woo.pop("Attribute 2 value(s)", None)
                woo.pop("Attribute 2 default", None)

            if ram and not is_invalid_mem(ram):
                woo["Attribute 3 value(s)"] = ram
                woo["Attribute 3 default"] = ram
            else:
                woo.pop("Attribute 3 name", None)
                woo.pop("Attribute 3 value(s)", None)
                woo.pop("Attribute 3 default", None)
                
            v_json_path = os.path.join(variant_dir, f"pack-data-{folder_name}.json")
            with open(v_json_path, "w", encoding="utf-8") as vf:
                json.dump(v_data, vf, ensure_ascii=False, indent=4)
                
            created_variants += 1
            
            cmd = [
                sys.executable, builder_script,
                "--data", v_json_path,
                "--outdir", variant_dir,
                "--modele", folder_name,
                "--no-csv"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                compiled_htmls += 1
                print(f"   [OK] Variante {folder_name} compilée (HTML)")
            else:
                print(f"   [!] Échec compilation {folder_name}: {res.stderr[:200]}")
                
    print(f"[OK] {compiled_htmls}/{created_variants} déclinaisons compilées avec succès pour {target_slug}.")

if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "a53-pro"
    duplicate_parent_model(slug)
