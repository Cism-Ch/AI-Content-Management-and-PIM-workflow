#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de mise à jour des Catégories WooCommerce Usine V3.4 avec les Catégories Officielle du Store
(Categories_produits_du_store.csv).

Met à jour :
1. Les fichiers JSON parents dans product-data/blackview/blackview-*.json
2. Les fichiers JSON de déclinaisons dans products/blackview-all/[variant]/pack-data-*.json
3. Le CSV consolidé global import-v2-blackview-all.csv
"""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE_DIR = Path(__file__).resolve().parents[3]
BLACKVIEW_ALL_DIR = WORKSPACE_DIR / "products" / "blackview-all"
PRODUCT_DATA_DIR = WORKSPACE_DIR / "product-data" / "blackview"
PARENT_MODELS_CSV = BLACKVIEW_ALL_DIR / "blackview_models_parent.csv"
MASTER_IMPORT_CSV = BLACKVIEW_ALL_DIR / "import-v2-blackview-all.csv"

def get_official_store_category(slug, category_type):
    s = slug.lower()
    cat = category_type.lower().strip()
    
    if cat == 'smartphone':
        if 'bl' in s and 'blackview' not in s: series = 'BL Series'
        elif 'bv' in s and ('4800' in s or '7300' in s or '9300' in s or 'bv' in s): series = 'BV Series'
        elif 'color' in s: series = 'Color Series'
        elif 'fort' in s: series = 'Fort Series'
        elif 'hero' in s: series = 'Hero Series'
        elif 'rock' in s: series = 'Rock Series'
        elif 'shark' in s: series = 'Shark Series'
        elif 'wave' in s: series = 'Wave Series'
        elif 'xplore' in s: series = 'Xplore Series'
        elif 'zeno' in s: series = 'Zeno Series'
        else: series = 'A Series'
        return f"Smartphones > Blackview > {series}, Smartphones > Blackview, Smartphones"
        
    elif cat == 'tablet':
        if 'active' in s: series = 'Active Series'
        elif 'link' in s: series = 'Link Series'
        elif 'mega' in s: series = 'Mega Series'
        elif 'zeno' in s: series = 'Zeno Series'
        else: series = 'Tab Series'
        return f"Tablettes > Blackview > {series}, Tablettes > Blackview, Tablettes"
        
    elif cat == 'pc_mini':
        return "Matériels Informatique & Bureautique > Ordinateurs Portable > Mini PC, Matériels Informatique & Bureautique > Ordinateurs Portable, Matériels Informatique & Bureautique"
        
    elif cat == 'laptop':
        return "Matériels Informatique & Bureautique > Ordinateurs Portable, Matériels Informatique & Bureautique"
        
    elif cat == 'screen extender':
        return "Matériels Informatique & Bureautique > Moniteurs Portable, Matériels Informatique & Bureautique"
        
    elif cat == 'smartwatch':
        return "Objets Connectés & Wearables > Montres connectées > Blackview Smartwatches, Objets Connectés & Wearables > Montres connectées, Objets Connectés & Wearables"
        
    elif cat == 'smart glasses':
        return "Objets Connectés & Wearables > Lunettes Connectées, Objets Connectés & Wearables"
        
    elif cat == 'earbuds':
        return "Audio & Hi-fi > Ecouteurs Sans Fil & Ecouteurs Filaire, Audio & Hi-fi"
        
    elif cat == 'speaker':
        return "Audio & Hi-fi > Enceintes Connectées & Bluetooth, Audio & Hi-fi"
        
    elif cat == 'keyboard':
        return "Matériels Informatique & Bureautique > Clavier & Souris, Matériels Informatique & Bureautique"
        
    return "Matériels Informatique & Bureautique > Accessoires Tech, Matériels Informatique & Bureautique"

def patch_categories():
    print("=======================================================")
    print("  MISE À JOUR DES CATÉGORIES WOOCOMMERCE STORE (V3.4)")
    print("=======================================================\n")
    
    # 1. Charger les modèles parents
    with open(PARENT_MODELS_CSV, encoding="utf-8") as f:
        parent_rows = list(csv.DictReader(f))
        
    parent_cat_map = {}
    for r in parent_rows:
        slug = r['model_slug'].strip()
        cat_type = r['category'].strip()
        official_cat = get_official_store_category(slug, cat_type)
        parent_cat_map[slug] = official_cat
        
    print(f"[*] {len(parent_cat_map)} modèles parents cartographiés sur les catégories officielles du store.")

    # 2. Mettre à jour les JSONs parents dans product-data/blackview/
    updated_parents_count = 0
    for slug, official_cat in parent_cat_map.items():
        parent_json = PRODUCT_DATA_DIR / f"blackview-{slug}.json"
        if parent_json.exists():
            try:
                with open(parent_json, encoding="utf-8") as f:
                    pdata = json.load(f)
                pdata["woocommerce_csv"]["Categories"] = official_cat
                with open(parent_json, "w", encoding="utf-8") as f:
                    json.dump(pdata, f, ensure_ascii=False, indent=4)
                updated_parents_count += 1
            except Exception as e:
                print(f"  [!] Erreur sur {parent_json.name}: {e}")
                
    print(f"[*] {updated_parents_count} fichiers JSON parents mis à jour.")

    # 3. Mettre à jour les JSONs de déclinaisons dans products/blackview-all/[variant]/pack-data-*.json
    updated_variants_count = 0
    for v_folder in BLACKVIEW_ALL_DIR.iterdir():
        if v_folder.is_dir():
            v_json = v_folder / f"pack-data-{v_folder.name}.json"
            if v_json.exists():
                try:
                    with open(v_json, encoding="utf-8") as f:
                        vdata = json.load(f)
                    
                    # Retrouver le slug parent
                    parent_slug = vdata.get("metadata", {}).get("target_model_slug", "")
                    if not parent_slug:
                        # Fallback parsing
                        for ps in sorted(parent_cat_map.keys(), key=len, reverse=True):
                            if ps in v_folder.name:
                                parent_slug = ps
                                break
                                
                    if parent_slug in parent_cat_map:
                        vdata["woocommerce_csv"]["Categories"] = parent_cat_map[parent_slug]
                        with open(v_json, "w", encoding="utf-8") as f:
                            json.dump(vdata, f, ensure_ascii=False, indent=4)
                        updated_variants_count += 1
                except Exception as e:
                    print(f"  [!] Erreur sur {v_json.name}: {e}")

    print(f"[*] {updated_variants_count} fichiers JSON de déclinaisons mis à jour.")

    # 4. Mettre à jour le CSV consolidé master import-v2-blackview-all.csv
    with open(MASTER_IMPORT_CSV, encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))
        
    updated_csv_count = 0
    for row in master_rows:
        sku_clean = row['SKU'].lower().replace('-', '').replace(' ', '')
        name_clean = row['Name'].lower().replace('-', '').replace(' ', '')
        matched_cat = None
        for slug, official_cat in sorted(parent_cat_map.items(), key=lambda x: len(x[0]), reverse=True):
            clean_slug = slug.lower().replace('-', '').replace(' ', '').replace('set', '')
            if clean_slug in sku_clean or clean_slug in name_clean:
                matched_cat = official_cat
                break
        if matched_cat:
            row['Categories'] = matched_cat
            updated_csv_count += 1

    fields = master_rows[0].keys()
    with open(MASTER_IMPORT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(master_rows)

    print(f"[*] {updated_csv_count} / {len(master_rows)} lignes du CSV master mis à jour.")

    print("\n=======================================================")
    print("  RÉSULTAT DE LA MISE À JOUR DES CATÉGORIES STORE")
    print("=======================================================")
    print(f"  JSONs Parents Mises à Jour      : {updated_parents_count}")
    print(f"  JSONs Déclinaisons Mises à Jour  : {updated_variants_count}")
    print(f"  CSV Master Lignes Mises à Jour  : {updated_csv_count} / {len(master_rows)}")
    print("=======================================================\n")

if __name__ == "__main__":
    patch_categories()
