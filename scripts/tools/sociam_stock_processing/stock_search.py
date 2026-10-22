import openpyxl
import argparse
import os

def stock_search(excel_path, keywords):
    """
    Recherche des produits dans le fichier Excel en fonction de mots-clés.
    """
    if not os.path.exists(excel_path):
        print(f"Erreur : Le fichier {excel_path} n'existe pas.")
        return

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active
    
    matches = []
    keywords_upper = [k.upper() for k in keywords]

    for row in sheet.iter_rows(values_only=True):
        row_str = " ".join([str(cell) for cell in row if cell is not None]).upper()
        
        # Vérifie si TOUS les mots-clés sont présents dans la ligne
        if all(k in row_str for k in keywords_upper):
            sku = str(row[1]) if len(row) > 1 and row[1] else "N/A"
            designation = str(row[2]) if len(row) > 2 and row[2] else "N/A"
            matches.append({"sku": sku, "designation": designation})

    # Déduplication par SKU
    unique_matches = {m['sku']: m for m in matches}.values()
    
    print(f"\n--- Résultats de recherche pour : {', '.join(keywords)} ---")
    for m in unique_matches:
        print(f"SKU: {m['sku']} | {m['designation']}")
    print(f"--- Total : {len(unique_matches)} produits trouvés ---\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recherche universelle dans le stock Sociam.")
    parser.add_argument("keywords", nargs="+", help="Mots-clés de recherche (ex: MIDEA CONGELATEUR)")
    parser.add_argument("--excel", default=r"c:\Users\hanok\wordpress\Copie de STOCK DISPO SOCIAM RIVIERA.xlsx", help="Chemin vers le fichier Excel")
    
    args = parser.parse_args()
    stock_search(args.excel, args.keywords)
