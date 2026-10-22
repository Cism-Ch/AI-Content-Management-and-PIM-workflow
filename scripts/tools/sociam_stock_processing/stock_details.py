import openpyxl
import re
import argparse
import os

def get_stock_details(excel_path, skus):
    """
    Récupère les détails (prix, couleur, désignation) pour une liste de SKUs.
    """
    if not os.path.exists(excel_path):
        print(f"Erreur : Le fichier {excel_path} n'existe pas.")
        return

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active
    
    # Normalisation des SKUs cibles pour la correspondance
    norm_targets = {re.sub(r'[^A-Z0-9]', '', s.upper()): s for s in skus}
    results = {}

    color_keywords = [
        "TITANIUM", "SILVER", "DARK BLUE", "INOX", "WHITE", "BLANC", 
        "GRIS", "BLACK", "NOIR", "ROSE", "GOLD", "STAINLESS", "ACIER", "STEEL",
        "METALLIC", "BRUSHED", "TITANE"
    ]

    for row in sheet.iter_rows(values_only=True):
        sku_val = str(row[1]) if len(row) > 1 and row[1] else ""
        norm_sku = re.sub(r'[^A-Z0-9]', '', sku_val.upper())
        designation = str(row[2]) if len(row) > 2 and row[2] else ""
        
        match_found = False
        target_orig = None
        
        if norm_sku in norm_targets:
            match_found = True
            target_orig = norm_targets[norm_sku]
        else:
            # Recherche du SKU dans la désignation
            for norm_t, orig_t in norm_targets.items():
                if orig_t.upper() in designation.upper():
                    match_found = True
                    target_orig = orig_t
                    break
        
        if match_found:
            price = str(row[3]) if len(row) > 3 and row[3] else "N/A"
            clean_price = "".join(filter(str.isdigit, price)) if price != "N/A" else "N/A"
            
            # Extraction de la couleur
            color = "Inconnu"
            search_text = (designation + " " + sku_val).upper()
            for kw in color_keywords:
                if kw in search_text:
                    color = kw.capitalize()
                    break
            
            # Normalisation couleur
            norm_c = {"Blanc": "White", "Noir": "Black", "Titane": "Titanium", "Acier": "Steel"}
            color = norm_c.get(color, color)
            
            results[target_orig] = {"price": clean_price, "color": color, "designation": designation}

    # Affichage en format table markdown
    print(f"\n| Modèle | Prix (CFA) | Couleur | Désignation |")
    print(f"| :--- | :--- | :--- | :--- |")
    for s in skus:
        data = results.get(s, {"price": "Non trouvé", "color": "N/A", "designation": "N/A"})
        print(f"| {s} | {data['price']} | {data['color']} | {data['designation']} |")
    print("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Récupération détaillée des prix et couleurs Sociam.")
    parser.add_argument("skus", nargs="+", help="Liste des SKUs à analyser")
    parser.add_argument("--excel", default=r"c:\Users\hanok\wordpress\Copie de STOCK DISPO SOCIAM RIVIERA.xlsx", help="Chemin vers le fichier Excel")
    
    args = parser.parse_args()
    get_stock_details(args.excel, args.skus)
