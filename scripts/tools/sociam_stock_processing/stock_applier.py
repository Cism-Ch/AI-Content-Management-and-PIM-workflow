import csv
import json
import os
import re

class UniversalStockApplier:
    def __init__(self, price_map_path, color_map_path):
        self.price_map = self._load_json(price_map_path)
        self.color_map = self._load_json(color_map_path)
        # Pre-normalize maps for high performance matching
        self.norm_price_map = {self._normalize_sku(k): v for k, v in self.price_map.items()}
        self.norm_color_map = {self._normalize_sku(k): v for k, v in self.color_map.items()}

    def _load_json(self, path):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _normalize_sku(self, sku):
        if not sku: return ""
        # Generic normalization: remove common brand and category prefixes
        s = sku.upper()
        prefixes = [
            "MIDEA-", "MIDEA_", "GAZ_", "NASCO-", "LG-", "SAMSUNG-", "M_",
            "MIXER_", "EXTRACTEUR_", "BATTEUR_", "TABLE_", "ROBOT_", "JUICE_"
        ]
        for p in prefixes:
            if s.startswith(p):
                s = s[len(p):]
        # Remove any leading/trailing underscores or dashes that might remain
        s = s.strip("_-")
        # Return alphanumeric only for final comparison
        return re.sub(r'[^A-Z0-9]', '', s)

    def apply_to_file(self, csv_path):
        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}")
            return

        temp_path = csv_path + ".tmp"
        updated_prices = 0
        updated_colors = 0
        total = 0

        with open(csv_path, 'r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames
            
            with open(temp_path, 'w', encoding='utf-8', newline='') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in reader:
                    total += 1
                    sku = row.get('SKU', '')
                    norm_sku = self._normalize_sku(sku)
                    
                    # Apply Price
                    if norm_sku in self.norm_price_map:
                        row['Regular price'] = self.norm_price_map[norm_sku]
                        updated_prices += 1
                    
                    # Apply Color
                    if norm_sku in self.norm_color_map:
                        found_color = self.norm_color_map[norm_sku]
                        applied_color = False
                        
                        # 1. Look for existing "Color" attribute slot
                        idx = 1
                        while f"Attribute {idx} name" in row:
                            if row[f"Attribute {idx} name"] == "Color":
                                row[f"Attribute {idx} value(s)"] = found_color
                                row[f"Attribute {idx} default"] = found_color
                                applied_color = True
                                break
                            idx += 1
                        
                        # 2. Look for first available empty slot
                        if not applied_color:
                            idx = 1
                            while f"Attribute {idx} name" in row:
                                if not row[f"Attribute {idx} name"] or row[f"Attribute {idx} name"].strip() == "":
                                    row[f"Attribute {idx} name"] = "Color"
                                    row[f"Attribute {idx} value(s)"] = found_color
                                    row[f"Attribute {idx} default"] = found_color
                                    row[f"Attribute {idx} visible"] = "1"
                                    applied_color = True
                                    break
                                idx += 1
                        
                        if applied_color:
                            updated_colors += 1
                    
                    writer.writerow(row)
        
        os.replace(temp_path, csv_path)
        print(f"[{os.path.basename(csv_path)}] Processed: {total} rows. Prices: +{updated_prices}, Colors: +{updated_colors}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Applique les prix et couleurs du stock Sociam à un CSV WooCommerce.")
    parser.add_argument("--csv", required=True, help="Chemin vers le fichier CSV à mettre à jour")
    args = parser.parse_args()
    
    BASE_DIR = r"c:\Users\hanok\wordpress\scripts\tools\sociam_stock_processing\data"
    applier = UniversalStockApplier(os.path.join(BASE_DIR, "prices_map.json"),
                                     os.path.join(BASE_DIR, "colors_map.json"))
    
    applier.apply_to_file(args.csv)
