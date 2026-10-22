import os
import json
import csv

pd_dir = r"c:\Users\My-eStore-PC2\My-eStore-workspace\wordpress\product-data\blackview"
csv_color = r"c:\Users\My-eStore-PC2\My-eStore-workspace\wordpress\product-data\blackview_models_color_verification.csv"

files = sorted([f.replace("blackview-", "").replace(".json", "") for f in os.listdir(pd_dir) if f.startswith("blackview-") and f.endswith(".json")])

print(f"Total models in product-data/blackview: {len(files)}")

# 1. Check bv- vs non-bv duplicates
print("\n--- 1. Doublons de nom (avec et sans préfixe 'bv-') ---")
for f in files:
    if f.startswith("bv-"):
        base = f[3:]
        if base in files:
            print(f"  Doublon détecté : '{f}' ET '{base}'")

# 2. Check models in product-data that were NOT in blackview_models_color_verification.csv
print("\n--- 2. Modèles dans product-data non présents dans la liste de référence (blackview_models_color_verification.csv) ---")
color_slugs = set()
with open(csv_color, "r", encoding="utf-8-sig") as fp:
    reader = csv.DictReader(fp)
    for r in reader:
        # Extract base slug without memory suffix
        s = r["model_slug"]
        color_slugs.add(s)

print(f"Total modèles dans CSV de référence : {len(color_slugs)}")

# Compare
print("\n--- 3. Décomposition détaillée des 85 modèles actuels ---")
for f in files:
    full_path = os.path.join(pd_dir, f"blackview-{f}.json")
    with open(full_path, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    c_name = d.get("product_identity", {}).get("commercial_name", "")
    p_type = d.get("product_type", d.get("product_identity", {}).get("category", ""))
    woo = d.get("woocommerce_csv", {})
    colors = woo.get("Attribute 1 value(s)", "").split("|")
    roms = woo.get("Attribute 2 value(s)", "").split("|")
    rams = woo.get("Attribute 3 value(s)", "").split("|")
    n_vars = max(1, len([c for c in colors if c.strip()])) * max(1, len([r for r in roms if r.strip() and r.strip() != "Standard"])) * max(1, len([m for m in rams if m.strip() and m.strip() != "Standard"]))
    print(f"  {f:25} | {c_name:30} | {p_type:12} | {n_vars} variantes")
