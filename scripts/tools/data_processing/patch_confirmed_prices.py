#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Mise à Jour des Prix Confirmés Jumia (V3.4).
Lit products/blackview-all/Confirmed_Price_list_Blackview.csv,
extrait la RAM physique (en ignorant le +extension_ram) et le Stockage,
met à jour le prix dans le CSV WooCommerce global (products/blackview-all/import-v2-blackview-all.csv)
ainsi que dans les fichiers JSON parents et déclinaisons.
"""

import os
import sys
import csv
import re
import json
from pathlib import Path

BASE_DIR = Path(os.path.abspath("."))
CONFIRMED_CSV = BASE_DIR / "products" / "blackview-all" / "Confirmed_Price_list_Blackview.csv"
GLOBAL_CSV = BASE_DIR / "products" / "blackview-all" / "import-v2-blackview-all.csv"
PRODUCT_DATA_DIR = BASE_DIR / "product-data" / "blackview"
BLACKVIEW_ALL_DIR = BASE_DIR / "products" / "blackview-all"

def parse_confirmed_prices():
    if not CONFIRMED_CSV.exists():
        print(f"[-] Fichier prix introuvable: {CONFIRMED_CSV}")
        return []

    with open(CONFIRMED_CSV, encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if r and any(r)]

    confirmed_items = []
    current_cat = ""

    for r in rows:
        first = r[0].strip()
        if not first.isdigit() and "PRICE LIST" not in first and "N°" not in first:
            current_cat = first
            continue

        if len(r) >= 3 and first.isdigit():
            num = first
            raw_name = r[1].strip()
            price_str = r[2].strip()
            clean_price = re.sub(r'[^\d]', '', price_str)
            if not clean_price:
                continue

            price = int(clean_price)

            # Extraction RAM Physique et Stockage
            # Format: (RAM+EXTENSION/ROM) ex: (4+8/64), (16+32/1T), (2/32), 16+512, 16 + 1T
            ram_val = None
            rom_val = None

            # Pattern pour extraire RAM physique et ROM
            mem_match = re.search(r'\(?(\d+)(?:\+\d+)?\s*[\/\+]\s*(\d+T|\d+Go|\d+GB|\d+)\)?', raw_name, re.IGNORECASE)
            if mem_match:
                ram_num = mem_match.group(1)
                rom_raw = mem_match.group(2).upper()

                ram_val = f"{ram_num} Go"
                if rom_raw == "1T":
                    rom_val = "1 To"
                elif rom_raw.isdigit():
                    if int(rom_raw) <= 2:
                        rom_val = f"{rom_raw} To"
                    else:
                        rom_val = f"{rom_raw} Go"
                else:
                    rom_val = rom_raw.replace("GB", " Go").replace("TB", " To")

            confirmed_items.append({
                "category": current_cat,
                "num": num,
                "raw_name": raw_name,
                "price": price,
                "ram": ram_val,
                "rom": rom_val
            })

    return confirmed_items

def main():
    items = parse_confirmed_prices()
    print(f"[+] Total prix confirmés extraits de Confirmed_Price_list_Blackview.csv : {len(items)}")

    if not GLOBAL_CSV.exists():
        print(f"[-] CSV global introuvable : {GLOBAL_CSV}")
        return

    with open(GLOBAL_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated_rows_count = 0
    matched_items_count = 0

    for item in items:
        raw_name = item["raw_name"]
        target_price = str(item["price"])
        item_ram = item["ram"]
        item_rom = item["rom"]

        # Nettoyer la chaîne pour recherche de modèle
        clean_search = raw_name.split('(')[0]
        clean_search = re.sub(r'INTEL.*', '', clean_search, flags=re.IGNORECASE)
        clean_search = re.sub(r'Smart Watch', '', clean_search, flags=re.IGNORECASE)
        clean_search = re.sub(r'Laptop Extender', '', clean_search, flags=re.IGNORECASE)
        clean_search = re.sub(r'Portable Monitor', '', clean_search, flags=re.IGNORECASE)
        clean_search = re.sub(r'Smart Glasses', '', clean_search, flags=re.IGNORECASE)
        clean_search = re.sub(r'Set', '', clean_search, flags=re.IGNORECASE)
        clean_search = re.sub(r'with dock', '', clean_search, flags=re.IGNORECASE)
        clean_search = clean_search.replace('Blackview', '').strip().lower()

        # Alias spécifiques
        if "rock 3" in clean_search: clean_search = "rock 3"
        elif "tab kids 3" in clean_search: clean_search = "tab 3 kids"
        elif "scm6" in raw_name.lower() or "dual screen" in clean_search: clean_search = "scm6"
        elif "dcm6" in raw_name.lower() or "triple screen" in clean_search: clean_search = "dcm6"
        elif "mp 100" in clean_search or "mp100" in clean_search: clean_search = "mp100"
        elif "wireless keyboard" in clean_search or "keyboard" in clean_search: clean_search = "k1"
        elif "mega 1" in clean_search and "mega 12" not in clean_search: clean_search = "mega 1"

        matching_rows = []
        for r in rows:
            r_name = r["Name"].lower()
            r_sku = r["SKU"].lower()
            r_ram = r.get("Attribute 3 value(s)", "").strip()
            r_rom = r.get("Attribute 2 value(s)", "").strip()

            c_norm = re.sub(r'[^a-zA-Z0-9]', '', clean_search)
            name_norm = re.sub(r'[^a-zA-Z0-9]', '', r_name)
            sku_norm = re.sub(r'[^a-zA-Z0-9]', '', r_sku)

            # Match strict : si c_norm est très court (ex: k1), on vérifie le SKU avec séparateurs
            is_match = False
            if c_norm == "k1":
                is_match = "bv-k1" in r_sku or r_sku.startswith("k1") or "k1" in r_name.split()
            elif len(c_norm) <= 3:
                is_match = f"-{c_norm}-" in f"-{r_sku}-" or c_norm in r_name.split()
            else:
                is_match = (c_norm in name_norm or c_norm in sku_norm)

            if is_match:
                # Vérifier la correspondance de ROM si spécifiée
                if item_rom and "mega 1" not in clean_search:
                    i_rom_norm = re.sub(r'[^a-zA-Z0-9]', '', item_rom.lower())
                    r_rom_norm = re.sub(r'[^a-zA-Z0-9]', '', r_rom.lower())
                    if i_rom_norm != r_rom_norm:
                        continue
                matching_rows.append(r)

        if matching_rows:
            matched_items_count += 1
            for mr in matching_rows:
                mr["Regular price"] = target_price
                updated_rows_count += 1

                # Mettre à jour également les JSONs des variantes physiques si elles existent
                v_sku = mr["SKU"]
                # Trouver le dossier de la variante
                for v_folder in BLACKVIEW_ALL_DIR.iterdir():
                    if v_folder.is_dir():
                        v_json_path = v_folder / f"pack-data-{v_folder.name}.json"
                        if v_json_path.exists():
                            try:
                                with open(v_json_path, encoding="utf-8") as vf:
                                    vdata = json.load(vf)
                                if vdata.get("woocommerce_csv", {}).get("SKU") == v_sku:
                                    vdata["woocommerce_csv"]["Regular price"] = target_price
                                    vdata["sourcing"]["pricing_reference"] = target_price
                                    with open(v_json_path, "w", encoding="utf-8") as vfw:
                                        json.dump(vdata, vfw, ensure_ascii=False, indent=4)
                            except Exception:
                                pass

            print(f"  [OK] '{raw_name}' -> {target_price} FCFA appliqué à {len(matching_rows)} ligne(s) CSV (ex: {matching_rows[0]['SKU']})")
        else:
            print(f"  [!] Non trouvé dans le CSV : '{raw_name}' (RAM={item_ram}, ROM={item_rom})")

    # Écrire le CSV WooCommerce mis à jour
    with open(GLOBAL_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n=======================================================")
    print(f"  RÉSULTAT DE LA MISE À JOUR DES PRIX CONFIRMÉS")
    print(f"  Articles Confirmés Appariés : {matched_items_count} / {len(items)}")
    print(f"  Lignes WooCommerce Mises à Jour : {updated_rows_count} / {len(rows)}")
    print(f"  Fichier CSV Mis à jour : {GLOBAL_CSV}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
