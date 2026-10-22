import openpyxl
import json
import re
import os

class UniversalStockExtractor:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        # Comprehensive list of color keywords
        self.color_keywords = [
            "TITANIUM", "SILVER", "DARK BLUE", "INOX", "WHITE", "BLANC", 
            "GRIS", "BLACK", "NOIR", "ROSE", "GOLD", "STAINLESS", "ACIER", "STEEL",
            "METALLIC", "BRUSHED", "TITANE", "GREY", "NAVY", "RED"
        ]
        self.color_map = {}
        self.price_map = {}

    def extract(self, brand_keyword=None):
        """
        Extracts prices and colors. 
        If brand_keyword is provided, only extracts for that brand.
        """
        if not os.path.exists(self.excel_path):
            print(f"Excel file not found: {self.excel_path}")
            return
            
        print(f"Opening Excel: {self.excel_path}...")
        wb = openpyxl.load_workbook(self.excel_path, data_only=True)
        sheet = wb.active
        
        count = 0
        for row in sheet.iter_rows(values_only=True):
            # Convert row to a single searchable string
            row_content = [str(cell) for cell in row if cell is not None]
            row_str = " ".join(row_content).upper()
            
            # Filter by brand if requested
            if brand_keyword and brand_keyword.upper() not in row_str:
                continue
            
            # Attempt to find SKU (usually in column 1 or 2)
            # We look for the longest alphanumeric string that looks like a SKU
            sku = None
            if len(row) > 1 and row[1]: sku = str(row[1])
            elif len(row) > 2 and row[2]: sku = str(row[2]) # Fallback
            
            if not sku or len(sku) < 3: continue
            
            designation = str(row[2]) if len(row) > 2 and row[2] else ""
            price = str(row[3]) if len(row) > 3 and row[3] else ""
            
            # Extract Color from designation or SKU
            found_color = None
            search_text = (designation + " " + sku).upper()
            for kw in self.color_keywords:
                if kw in search_text:
                    found_color = kw.capitalize()
                    break
            
            if found_color:
                # Normalization
                norm_colors = {
                    "Blanc": "White", "Noir": "Black", "Titane": "Titanium",
                    "Acier": "Steel", "Gris": "Grey", "Argent": "Silver"
                }
                found_color = norm_colors.get(found_color, found_color)
                self.color_map[sku] = found_color
            
            # Extract Price
            if price:
                clean_price = "".join(filter(str.isdigit, price))
                if clean_price:
                    self.price_map[sku] = int(clean_price)
                    count += 1

        print(f"Extraction complete: {count} products identified.")

    def save_maps(self, price_json, color_json):
        with open(price_json, 'w', encoding='utf-8') as f:
            json.dump(self.price_map, f, indent=4, ensure_ascii=False)
        with open(color_json, 'w', encoding='utf-8') as f:
            json.dump(self.color_map, f, indent=4, ensure_ascii=False)
        print(f"Maps saved: {price_json}, {color_json}")

if __name__ == "__main__":
    EXCEL = r"c:\Users\hanok\wordpress\Copie de STOCK DISPO SOCIAM RIVIERA.xlsx"
    DATA_DIR = r"c:\Users\hanok\wordpress\scripts\tools\sociam_stock_processing\data"
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    extractor = UniversalStockExtractor(EXCEL)
    # Extract everything
    extractor.extract() 
    extractor.save_maps(os.path.join(DATA_DIR, "prices_map.json"), 
                        os.path.join(DATA_DIR, "colors_map.json"))
