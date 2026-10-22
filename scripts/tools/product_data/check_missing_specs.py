#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_missing_specs.py — Script d'audit pour identifier les spécifications manquantes
(poids pour tous les produits, classe énergétique pour les appliances) dans product-data/ (JSON)
et products-appliance/ (HTML).
"""

import os
import json
import sys
import re
from pathlib import Path

# Configurer UTF-8 sur Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PLACEHOLDERS = ["", "n/a", "tbd", "todo", "???", "placeholder", "null", "undefined", "non applicable", "not applicable"]

def is_missing(val):
    if val is None:
        return True
    if isinstance(val, str) and val.strip().lower() in PLACEHOLDERS:
        return True
    if isinstance(val, list) and len(val) == 0:
        return True
    return False

def find_weight_in_full_specs(data):
    for section in data.get("full_specs", {}).get("sections", []):
        for row in section.get("rows", []):
            if row.get("label", "").strip().lower() in ["poids", "weight"]:
                val = row.get("valeur", "").strip()
                if not is_missing(val):
                    return val
    return None

def check_html_file(file_path):
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return None, None

    # Chercher la classe énergétique
    # 1. Dans la table HTML (TD contenant un libellé clé)
    has_energy = False
    energy_labels = ["classe énergétique", "classe d'efficacité", "classe energetique", "energy class", "classe d'énergie", "classe d'energie", "efficacité énergétique", "efficacite energetique"]
    for label in energy_labels:
        pattern = rf'<td[^>]*>\s*(?:<[^>]+>)*\s*{re.escape(label)}\s*(?:<[^>]+>)*\s*</td>\s*<td[^>]*>\s*([\s\S]*?)\s*</td>'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            val = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if val and not is_missing(val):
                has_energy = True
                break

    # 2. Chercher le poids dans la table HTML
    has_weight = False
    pattern = r'<td[^>]*>\s*(?:<[^>]+>)*\s*Poids\s*(?:<[^>]+>)*\s*</td>\s*<td[^>]*>\s*([\s\S]*?)\s*</td>'
    match = re.search(pattern, content, re.IGNORECASE)
    if match:
        val = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        if val and not is_missing(val):
            has_weight = True

    return has_energy, has_weight

def main():
    root_dir = Path(__file__).parent.parent.parent.parent
    product_data_dir = root_dir / "product-data"
    products_appliance_dir = root_dir / "products-appliance"
    
    print(f"=== Audit des Spécifications (V3.2) ===")
    
    # 1. Audit des JSON (product-data)
    print(f"Scan du dossier JSON : {product_data_dir.resolve()}")
    json_files = list(product_data_dir.glob("**/*.json")) if product_data_dir.exists() else []
    
    missing_weight_count = 0
    missing_energy_count = 0
    appliance_count = 0
    total_json_count = 0
    issues = []

    for jf in json_files:
        if jf.name.startswith("Template"):
            continue
            
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            continue

        total_json_count += 1
        prod_type = data.get("product_type", "")
        identity = data.get("product_identity", {})
        category = identity.get("category", "")
        sub_cat = identity.get("sub_category", "")
        comm_name = identity.get("commercial_name", jf.stem)
        brand = identity.get("brand", "")
        
        weight_key = data.get("key_specifications", {}).get("weight") or data.get("key_specifications", {}).get("weight_kg")
        weight_full = find_weight_in_full_specs(data)
        
        wc_data = data.get("woocommerce_csv", {})
        wc_att4_name = wc_data.get("Attribute 4 name", "").strip()
        wc_att4_val = wc_data.get("Attribute 4 value(s)", "").strip()
        has_wc_weight = (wc_att4_name.lower() == "poids" and not is_missing(wc_att4_val))
        
        has_weight = (not is_missing(weight_key) or not is_missing(weight_full)) and has_wc_weight
        
        is_appliance = prod_type == "appliance" or category == "appliance" or "appliance" in str(sub_cat).lower() or "appliance" in str(category).lower()
        has_energy = True
        
        if is_appliance:
            appliance_count += 1
            energy = data.get("key_specifications", {}).get("energy_class")
            if is_missing(energy):
                has_energy = False
                missing_energy_count += 1
        
        if not has_weight:
            missing_weight_count += 1
            
        if not has_weight or not has_energy:
            issues.append({
                "type": "JSON",
                "file": jf,
                "brand": brand,
                "name": comm_name,
                "is_appliance": is_appliance,
                "missing_weight": not has_weight,
                "missing_energy": is_appliance and not has_energy
            })

    # 2. Audit des HTML (products-appliance)
    print(f"Scan du dossier HTML Appliance : {products_appliance_dir.resolve()}")
    html_files = list(products_appliance_dir.glob("**/*-LONG.html")) if products_appliance_dir.exists() else []
    
    total_html_count = len(html_files)
    missing_html_weight = 0
    missing_html_energy = 0
    
    for hf in html_files:
        has_energy, has_weight = check_html_file(hf)
        if has_energy is None:
            continue
            
        # Par convention, tous les HTML dans products-appliance sont des appliances
        if not has_energy or not has_weight:
            brand = hf.parent.parent.name
            name = hf.parent.name
            
            if not has_weight:
                missing_html_weight += 1
            if not has_energy:
                # Exclure les catégories qui n'ont typiquement pas de classe énergétique réglementaire (ex: hotte, petite cuisine, distributeur eau)
                # Mais les splits, réfrigerateurs, lave-linges doivent absolument l'avoir!
                path_lower = str(hf).lower()
                is_mandatory_energy = any(x in path_lower for x in ["split", "climatiseur", "refrigerateur", "congelateur", "machine", "lave-linge", "washer", "dryer"])
                if is_mandatory_energy:
                    missing_html_energy += 1
                    issues.append({
                        "type": "HTML",
                        "file": hf,
                        "brand": brand,
                        "name": name,
                        "is_appliance": True,
                        "missing_weight": not has_weight,
                        "missing_energy": True
                    })
                elif not has_weight:
                    issues.append({
                        "type": "HTML",
                        "file": hf,
                        "brand": brand,
                        "name": name,
                        "is_appliance": True,
                        "missing_weight": True,
                        "missing_energy": False
                    })

    # Affichage des résultats
    print(f"\nSTATISTIQUES DE L'AUDIT :")
    print(f"  - Total JSONs scannés (Tech) : {total_json_count}")
    print(f"    * Sans poids : {missing_weight_count}")
    print(f"  - Total HTMLs scannés (Appliances) : {total_html_count}")
    print(f"    * Sans poids : {missing_html_weight}")
    print(f"    * Sans classe énergétique (obligatoire) : {missing_html_energy}\n")

    if issues:
        print("=== DÉTAILS DES ANOMALIES DÉTECTEES ===")
        for iss in issues:
            details = []
            if iss["missing_weight"]:
                details.append("Poids manquant")
            if iss["missing_energy"]:
                details.append("Classe énergétique manquante")
            
            try:
                rel_path = iss["file"].relative_to(root_dir)
            except Exception:
                rel_path = iss["file"]
            print(f"- [{iss['type']}] [{iss['brand']}] {iss['name']} ({rel_path}) : {', '.join(details)}")
    else:
        print("[FÉLICITATIONS] Aucune anomalie détectée ! Tous les produits ont un poids et toutes les appliances ont leur classe énergétique.")

if __name__ == "__main__":
    main()
