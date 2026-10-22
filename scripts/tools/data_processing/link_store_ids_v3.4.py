#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Liaison et Résolution des ID WooCommerce Store (V3.4)
Rapproche les ID WooCommerce du store (Blackview-product-export-from-wc-29-7-2026.csv)
avec le fichier certifié usine import-v2-blackview-all.csv.

Garantit :
1. Unicité stricte des ID (0 doublon).
2. Remplacement intégral des données corrompues du store par les données certifiées V3.4.
3. Propagation dans le CSV global et les JSONs de déclinaisons.
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Chemins des fichiers
WORKSPACE_DIR = Path(__file__).resolve().parents[3]
BLACKVIEW_ALL_DIR = WORKSPACE_DIR / "products" / "blackview-all"
STORE_EXPORT_CSV = BLACKVIEW_ALL_DIR / "Blackview-product-export-from-wc-29-7-2026.csv"
MASTER_IMPORT_CSV = BLACKVIEW_ALL_DIR / "import-v2-blackview-all.csv"
PARENT_MODELS_CSV = BLACKVIEW_ALL_DIR / "blackview_models_parent.csv"

# Dictionnaire bilingue complet des couleurs EN -> FR
COLOR_MAP = {
    'BLUE': 'BLEU', 'SKY BLUE': 'BLEU', 'STARRY BLUE': 'BLEU', 'GALAXY BLUE': 'BLEU', 'DAYBREAK BLUE': 'BLEU',
    'GREY': 'GRIS', 'GRAY': 'GRIS', 'SPACE GREY': 'GRIS', 'SPACE GRAY': 'GRIS',
    'BLACK': 'NOIR', 'MIDNIGHT BLACK': 'NOIR', 'POLAR NIGHT BLACK': 'NOIR',
    'WHITE': 'BLANC', 'ORANGE': 'ORANGE', 'GREEN': 'VERT', 'JAUNE': 'JAUNE',
    'YELLOW': 'JAUNE', 'GOLD': 'OR', 'BLAZE GOLD': 'OR', 'SPLENDID GOLD': 'OR', 'FLASH GOLD': 'OR',
    'PURPLE': 'VIOLET', 'METEOR PURPLE': 'VIOLET', 'PINK': 'ROSE', 'SILVER': 'ARGENT',
    'RED': 'ROUGE', 'CLEAR': 'CLAIR', 'SUN GLASS': 'CLAIR'
}

def norm_slug(slug):
    if not slug: return ''
    s = slug.lower().replace('-', '').replace(' ', '')
    if s.startswith('blackview'): s = s[9:]
    elif s.startswith('bv') and not s.startswith('bvk1'): s = s[2:]
    return s

def extract_store_attrs(row, parent_slugs):
    ugs = row.get('UGS', '').upper()
    nom = row.get('Nom', '').upper()
    full_text = f"{ugs} {nom}"
    clean_text = re.sub(r'[^A-Z0-9]', '', full_text)
    
    # 1. Modèle parent
    found_model = None
    for slug in sorted(parent_slugs, key=lambda x: len(norm_slug(x)), reverse=True):
        cs = norm_slug(slug)
        if cs in clean_text.lower():
            found_model = slug
            break
            
    # 2. Stockage (ROM)
    rom = None
    mem_matches = re.findall(r'(\d+)\s*(GO|GB|TB|TO)', full_text)
    for val, unit in mem_matches:
        if unit in ['TB', 'TO'] or int(val) >= 32:
            rom = f"{val} Go" if unit in ['GB', 'GO'] else f"{val} To"
            
    # 3. Couleur
    color = None
    for en, fr in COLOR_MAP.items():
        if re.search(rf'\b{en}\b', full_text):
            color = fr
            break
            
    return found_model, rom, color, ugs, nom

def extract_master_attrs(row, parent_slugs):
    sku = row.get('SKU', '')
    name = row.get('Name', '')
    found_model = None
    for slug in sorted(parent_slugs, key=lambda x: len(norm_slug(x)), reverse=True):
        cs = norm_slug(slug)
        if cs in norm_slug(sku) or cs in norm_slug(name):
            found_model = slug
            break
    rom = row.get('Attribute 2 value(s)', '').strip()
    color = row.get('Attribute 1 value(s)', '').strip().upper()
    return found_model, rom, color

def run_linking_pipeline():
    print("=======================================================")
    print("  LIAISON ET RESOLUTION DES ID WOOCOMMERCE STORE (V3.4)")
    print("=======================================================\n")
    
    # Charger les modèles parents
    with open(PARENT_MODELS_CSV, encoding="utf-8") as f:
        parent_slugs = [r['model_slug'].strip() for r in csv.DictReader(f)]
        
    # Charger l'export du store
    with open(STORE_EXPORT_CSV, encoding="utf-8-sig") as f:
        store_rows = list(csv.DictReader(f))
        
    # Lecture du CSV Master avec utf-8-sig pour éliminer la BOM \ufeffID
    with open(MASTER_IMPORT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        raw_fieldnames = list(reader.fieldnames or [])
        raw_rows = list(reader)

    # Nettoyage et dédoublonnage des noms de colonnes
    fields = []
    seen = set()
    for fn in raw_fieldnames:
        clean_fn = fn.replace('\ufeff', '').strip()
        if clean_fn not in seen:
            seen.add(clean_fn)
            fields.append(clean_fn)

    master_rows = []
    for r in raw_rows:
        new_r = {}
        for k, v in r.items():
            if k is None: continue
            clean_k = k.replace('\ufeff', '').strip()
            if clean_k == 'ID':
                if v and not new_r.get('ID'):
                    new_r['ID'] = str(v).strip()
                elif 'ID' not in new_r:
                    new_r['ID'] = ''
            else:
                new_r[clean_k] = str(v).strip() if v is not None else ''
        master_rows.append(new_r)
        
    print(f"[*] Export Store : {len(store_rows)} lignes avec ID WooCommerce")
    print(f"[*] Usine Certifiée : {len(master_rows)} déclinaisons V3.4\n")
    
    used_store_ids = set()
    used_master_skus = set()
    matches = {} # master_sku -> store_id
    
    # --- PHASE 1 : Match Exact / Normalisé sur SKU / UGS ---
    print("[Phase 1] Recherche de correspondances exactes par SKU...")
    phase1_count = 0
    for m in master_rows:
        m_sku = m['SKU']
        m_norm_sku = re.sub(r'[^A-Z0-9]', '', m_sku.upper())
        for s in store_rows:
            s_id = s['ID']
            if s_id in used_store_ids: continue
            s_ugs = s.get('UGS', '')
            s_norm_ugs = re.sub(r'[^A-Z0-9]', '', s_ugs.upper())
            if m_norm_sku and s_norm_ugs and (m_norm_sku == s_norm_ugs or m_norm_sku in s_norm_ugs or s_norm_ugs in m_norm_sku):
                matches[m_sku] = s_id
                used_store_ids.add(s_id)
                used_master_skus.add(m_sku)
                phase1_count += 1
                break
            
    print(f"   -> {phase1_count} correspondances trouvées en Phase 1.\n")

    # --- PHASE 2 : Match par Modèle + ROM + Couleur ---
    print("[Phase 2] Match strict par Modèle + ROM + Couleur...")
    phase2_count = 0
    
    for s_row in store_rows:
        s_id = s_row['ID']
        if s_id in used_store_ids:
            continue
            
        s_mod, s_rom, s_col, _, _ = extract_store_attrs(s_row, parent_slugs)
        if not s_mod or not s_col:
            continue
            
        best_m = None
        for m in master_rows:
            if m['SKU'] in used_master_skus:
                continue
            m_mod, m_rom, m_col = extract_master_attrs(m, parent_slugs)
            if m_mod == s_mod and m_col == s_col:
                if s_rom is None or m_rom == s_rom:
                    best_m = m
                    break
                    
        if best_m:
            matches[best_m['SKU']] = s_id
            used_store_ids.add(s_id)
            used_master_skus.add(best_m['SKU'])
            phase2_count += 1
            
    print(f"   -> {phase2_count} correspondances ajoutées en Phase 2.\n")

    # --- PHASE 3 : Résolution des Variantes Store Corrompues (Fallback Modèle + Couleur) ---
    print("[Phase 3] Résolution des variantes store corrompues (Fallback Modèle + Couleur)...")
    phase3_count = 0
    
    for s_row in store_rows:
        s_id = s_row['ID']
        if s_id in used_store_ids:
            continue
            
        s_mod, s_rom, s_col, _, _ = extract_store_attrs(s_row, parent_slugs)
        if not s_mod or not s_col:
            continue
            
        best_m = None
        for m in master_rows:
            if m['SKU'] in used_master_skus:
                continue
            m_mod, m_rom, m_col = extract_master_attrs(m, parent_slugs)
            if m_mod == s_mod and m_col == s_col:
                best_m = m
                break
                    
        if best_m:
            matches[best_m['SKU']] = s_id
            used_store_ids.add(s_id)
            used_master_skus.add(best_m['SKU'])
            phase3_count += 1

    print(f"   -> {phase3_count} variantes corrompues remédiées en Phase 3.\n")

    # --- PHASE 4 : Application des ID & Verification d'Unicite ---
    print("[Phase 4] Application des ID sur le CSV Master et dans les JSONs de variantes...")
    
    updated_csv_count = 0
    new_products_count = 0
    
    for row in master_rows:
        m_sku = row['SKU']
        if m_sku in matches:
            assigned_id = str(matches[m_sku]).strip()
            row['ID'] = assigned_id
            updated_csv_count += 1
        else:
            if not row.get('ID'):
                row['ID'] = ""
            if not row['ID']:
                new_products_count += 1
            else:
                updated_csv_count += 1
            
        # Propagation dans le fichier JSON physique de la variante s'il existe
        v_sku = row['SKU']
        for v_folder in BLACKVIEW_ALL_DIR.iterdir():
            if v_folder.is_dir():
                v_json = v_folder / f"pack-data-{v_folder.name}.json"
                if v_json.exists():
                    try:
                        with open(v_json, encoding="utf-8") as vf:
                            vdata = json.load(vf)
                        if vdata.get("woocommerce_csv", {}).get("SKU") == v_sku:
                            vdata["woocommerce_csv"]["ID"] = row['ID']
                            with open(v_json, "w", encoding="utf-8") as vfw:
                                json.dump(vdata, vfw, ensure_ascii=False, indent=4)
                    except Exception:
                        pass

    # Réécriture propre du CSV Master sans BOM ni doublons de colonnes
    with open(MASTER_IMPORT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(master_rows)

    # --- VÉRIFICATION DE SÉCURITÉ ---
    assigned_ids_list = [r['ID'] for r in master_rows if r['ID']]
    is_unique = (len(assigned_ids_list) == len(set(assigned_ids_list)))

    print("=======================================================")
    print("  RÉSULTAT DE LA SYNCHRONISATION DES ID WOOCOMMERCE")
    print("=======================================================")
    print(f"  Total Lignes Master V3.4     : {len(master_rows)}")
    print(f"  Produits Existants Liés (ID) : {updated_csv_count} / {len(store_rows)} du store")
    print(f"  Nouveaux Produits (ID Vide)  : {new_products_count}")
    print(f"  Unicité Stricte des ID       : {'[OK] 100% UNIQUE (0 Doublon)' if is_unique else '[ERREUR] Doublons Détectés'}")
    print(f"  Fichier Master CSV Mis à jour: {MASTER_IMPORT_CSV}")
    print("=======================================================\n")

if __name__ == "__main__":
    run_linking_pipeline()
