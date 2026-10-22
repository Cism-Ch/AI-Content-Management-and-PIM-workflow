import os
import sys
import json
import re
import csv
import unicodedata
import subprocess

# Assurer la résolution de l'import aussi bien pour l'IDE que pour l'exécution directe
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DP_DIR = os.path.join(SCRIPT_DIR, "tools", "data_processing")
if TOOLS_DP_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DP_DIR)

try:
    from tools.data_processing.format_product_names import get_formatted_name
except ImportError:
    from format_product_names import get_formatted_name

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pd_dir = os.path.join(WORKSPACE_ROOT, "product-data", "blackview")
products_dir = os.path.join(WORKSPACE_ROOT, "products", "blackview-all")
build_script = os.path.join(WORKSPACE_ROOT, "scripts", "build-product-pack-v3.py")
master_csv_path = os.path.join(products_dir, "import-v2-blackview-all.csv")

CSV_HEADERS = [
    "ID", "Type", "SKU", "Name", "Published", "Visibility in catalog",
    "Short description", "Description", "In stock?", "Stock", "Regular price",
    "Categories", "Tags",
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

def clean_mem_for_sku(val):
    if not val or val.upper() in ["N/A", "STANDARD", "NON APPLICABLE"]:
        return ""
    val = val.upper().strip().replace(" ", "")
    val = val.replace("GO", "GB").replace("TO", "TB").replace("MO", "MB")
    return re.sub(r'[^A-Z0-9-]', '', val)

def clean_color_for_sku(color):
    if not color or color.upper() in ["N/A", "STANDARD", "NON APPLICABLE"]:
        return ""
    nfkd = unicodedata.normalize('NFKD', color)
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'[^A-Z0-9-]', '', ascii_str.upper().replace(" ", "-").replace("'", ""))

def clean_color_for_folder(color):
    if not color or color.upper() in ["N/A", "STANDARD", "NON APPLICABLE"]:
        return ""
    nfkd = unicodedata.normalize('NFKD', color)
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'[^a-z0-9-]', '', ascii_str.lower().replace(" ", "-").replace("'", ""))

def clean_mem_for_folder(val):
    if not val or val.upper() in ["N/A", "STANDARD", "NON APPLICABLE"]:
        return ""
    s = val.lower().replace(" ", "").replace("gb", "go").replace("tb", "to").replace("mb", "mo")
    return re.sub(r'[^a-z0-9-]', '', s)

def main():
    print("[+] Starting compilation and duplication for all Blackview models (V3.4 - Clean CTA)...")
    
    if not os.path.exists(pd_dir):
        print(f"[-] Error: product-data directory {pd_dir} does not exist.")
        sys.exit(1)
        
    json_files = sorted([f for f in os.listdir(pd_dir) if f.startswith("blackview-") and f.endswith(".json")])
    print(f"[+] Found {len(json_files)} parent JSON files.")
    
    success_count = 0
    fail_count = 0
    variant_total_count = 0
    all_csv_rows = []
    
    for filename in json_files:
        filepath = os.path.join(pd_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[-] Error reading {filename}: {e}")
            continue
            
        slug = filename.replace("blackview-", "").replace(".json", "")
        commercial_name = (
            data.get("woocommerce_csv", {}).get("Name")
            or data.get("product_identity", {}).get("commercial_name")
            or f"{data.get('metadata', {}).get('target_brand', 'Blackview')} {data.get('metadata', {}).get('target_model', slug)}"
        )
        
        # Extract attributes
        woo = data.get("woocommerce_csv", {})
        
        # 1. Colors (Attribute 1)
        attr1_name = woo.get("Attribute 1 name", "").strip().lower()
        colors_str = woo.get("Attribute 1 value(s)", "")
        colors = []
        if attr1_name in ["color", "couleur"] and colors_str:
            colors = [c.strip() for c in colors_str.split("|") if c.strip()]
        if not colors:
            colors = [""]
            
        # 2. ROM / Storage (Attribute 2)
        attr2_name = woo.get("Attribute 2 name", "").strip().lower()
        rom_str = woo.get("Attribute 2 value(s)", "")
        roms = []
        if attr2_name in ["stockage", "rom", "capacité", "capacite", "storage"] and rom_str:
            roms = [r.strip() for r in rom_str.split("|") if r.strip() and r.strip().upper() not in ["STANDARD", "N/A"]]
        if not roms:
            roms = [""]
            
        # 3. RAM (Attribute 3)
        attr3_name = woo.get("Attribute 3 name", "").strip().lower()
        ram_str = woo.get("Attribute 3 value(s)", "")
        rams = []
        if attr3_name in ["ram", "mémoire", "memoire", "memory"] and ram_str:
            rams = [r.strip() for r in ram_str.split("|") if r.strip() and r.strip().upper() not in ["STANDARD", "N/A"]]
        if not rams:
            rams = [""]
            
        # Generate combinations
        combinations = []
        if "paired_variants" in data and data["paired_variants"]:
            for pv in data["paired_variants"]:
                combinations.append((pv.get("ram", ""), pv.get("rom", ""), pv.get("color", "")))
        else:
            for ram in rams:
                for rom in roms:
                    for color in colors:
                        combinations.append((ram, rom, color))
                    
        print(f"\n[+] Model: {commercial_name} ({slug}) -> {len(combinations)} variants.")
        
        for ram, rom, color in combinations:
            # Build variant slug
            ram_clean = clean_mem_for_folder(ram)
            rom_clean = clean_mem_for_folder(rom)
            color_clean = clean_color_for_folder(color)
            
            suffix_parts = []
            if ram_clean:
                suffix_parts.append(ram_clean)
            if rom_clean:
                suffix_parts.append(rom_clean)
            if color_clean:
                suffix_parts.append(color_clean)
                
            if suffix_parts:
                variant_slug = f"{slug}-" + "-".join(suffix_parts)
            else:
                variant_slug = slug
                
            # Sanitize variant slug for file system
            variant_slug = re.sub(r'[^a-zA-Z0-9_-]', '-', variant_slug)
            
            variant_dir = os.path.join(products_dir, variant_slug)
            os.makedirs(variant_dir, exist_ok=True)
            
            # Create variant JSON
            variant_data = json.loads(json.dumps(data))
            v_woo = variant_data["woocommerce_csv"]
            
            # Setup specific attributes
            if ram and attr3_name in ["ram", "mémoire", "memoire", "memory"]:
                v_woo["Attribute 3 value(s)"] = ram
                v_woo["Attribute 3 default"] = ram
            if rom and attr2_name in ["stockage", "rom", "capacité", "capacite", "storage"]:
                v_woo["Attribute 2 value(s)"] = rom
                v_woo["Attribute 2 default"] = rom
            if color and attr1_name in ["color", "couleur"]:
                v_woo["Attribute 1 value(s)"] = color
                v_woo["Attribute 1 default"] = color
                
            # SKU calculation
            official_sku = data.get("woocommerce_csv", {}).get("SKU", f"{slug.upper()}-MASTER")
            clean_official_sku = re.sub(r'-MASTER$', '', official_sku, flags=re.IGNORECASE)
            
            sku_parts = [clean_official_sku]
            rom_sku = clean_mem_for_sku(rom) if attr2_name in ["stockage", "rom", "capacité", "capacite", "storage"] else ""
            ram_sku = clean_mem_for_sku(ram) if attr3_name in ["ram", "mémoire", "memoire", "memory"] else ""
            if rom_sku:
                sku_parts.append(rom_sku)
            if ram_sku:
                sku_parts.append(ram_sku)
            if color:
                color_sku = clean_color_for_sku(color)
                if color_sku:
                    sku_parts.append(color_sku)
            
            variant_sku = "-".join([p for p in sku_parts if p]).upper()
            v_woo["SKU"] = variant_sku
            
            # Name calculation via official nomenclature V3.4 (Enriched Vendor Title)
            final_name = get_formatted_name(data, variant_data)
            v_woo["Name"] = final_name
            
            # Write variant json file
            variant_json_path = os.path.join(variant_dir, f"pack-data-{variant_slug}.json")
            with open(variant_json_path, 'w', encoding='utf-8') as f_out:
                json.dump(variant_data, f_out, ensure_ascii=False, indent=4)
                
            # Run build-product-pack-v3.py
            cmd = [
                sys.executable,
                build_script,
                "--data", variant_json_path,
                "--outdir", variant_dir,
                "--modele", variant_slug,
                "--serie", "blackview-all",
                "--skip-validation"
            ]
            
            res = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
            if res.returncode == 0:
                print(f"  [OK] {variant_slug} (SKU: {variant_sku})")
                success_count += 1
            else:
                print(f"  [FAIL] {variant_slug}")
                print(f"  Error:\n{res.stderr}\n{res.stdout}")
                fail_count += 1
                
            variant_total_count += 1
            
            # Lire et nettoyer les HTML générés pour la ligne CSV
            short_html_path = os.path.join(variant_dir, f"short-{variant_slug}.html")
            long_html_path = os.path.join(variant_dir, f"long-{variant_slug}.html")
            raw_short = open(short_html_path, "r", encoding="utf-8").read() if os.path.exists(short_html_path) else ""
            raw_long = open(long_html_path, "r", encoding="utf-8").read() if os.path.exists(long_html_path) else ""
            clean_short = clean_html(raw_short)
            clean_long = clean_html(raw_long)
            
            row = {h: "" for h in CSV_HEADERS}
            row["ID"] = v_woo.get("ID", "")
            row["Type"] = "simple"
            row["SKU"] = variant_sku
            row["Name"] = final_name
            row["Published"] = v_woo.get("Published", "1")
            row["Visibility in catalog"] = v_woo.get("Visibility in catalog", "visible")
            row["Short description"] = clean_short
            row["Description"] = clean_long
            row["In stock?"] = v_woo.get("In stock?", "1")
            row["Stock"] = v_woo.get("Stock", "10")
            row["Regular price"] = v_woo.get("Regular price", "")
            row["Categories"] = v_woo.get("Categories", "")
            row["Tags"] = v_woo.get("Tags", "")
            
            for i in range(1, 5):
                name_key = f"Attribute {i} name"
                val_key = f"Attribute {i} value(s)"
                def_key = f"Attribute {i} default"
                vis_key = f"Attribute {i} visible"
                glob_key = f"Attribute {i} global"
                
                if name_key in v_woo and v_woo[name_key]:
                    row[name_key] = v_woo.get(name_key, "")
                    row[val_key] = v_woo.get(val_key, "")
                    row[def_key] = v_woo.get(def_key, "")
                    row[vis_key] = v_woo.get(vis_key, "1")
                    row[glob_key] = v_woo.get(glob_key, "1")
                    
            all_csv_rows.append(row)

    # Écriture du CSV consolidé maître
    print(f"\n[+] Writing master consolidated CSV: {master_csv_path} ({len(all_csv_rows)} rows)")
    with open(master_csv_path, 'w', encoding='utf-8', newline='') as f_csv_out:
        writer = csv.DictWriter(f_csv_out, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_csv_rows)

    print(f"\n[DONE] Processed {variant_total_count} variants: {success_count} succeeded, {fail_count} failed.")
    print(f"[DONE] Consolidated CSV: {master_csv_path}")

if __name__ == "__main__":
    main()
