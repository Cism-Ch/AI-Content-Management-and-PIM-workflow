"""
Vérifie les attributs Color d'un CSV WooCommerce.
Usage: python check_csv_colors.py --csv path/to/file.csv
"""
import csv
import argparse

parser = argparse.ArgumentParser(description="Affiche les SKU et couleurs d'un CSV WooCommerce.")
parser.add_argument('--csv', '-c', required=True, help="Chemin vers le fichier CSV WooCommerce")
args = parser.parse_args()

with open(args.csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print(f"\n{'SKU':<30} | {'Color':<30}")
    print("-" * 65)
    missing_count = 0
    total = 0
    for row in reader:
        sku = row.get('SKU', '?')
        # Recherche dynamique de l'attribut Color parmi les colonnes Attribute N
        color = "N/A"
        for i in range(1, 10):
            attr_name = row.get(f'Attribute {i} name', '')
            if attr_name.strip().lower() == 'color':
                color = row.get(f'Attribute {i} value(s)', 'EMPTY')
                break
        flag = " ⚠️" if color in ("N/A", "EMPTY", "") else ""
        print(f"{sku:<30} | {color:<30}{flag}")
        total += 1
        if color in ("N/A", "EMPTY", ""):
            missing_count += 1
    print("-" * 65)
    print(f"Total: {total} produits | {missing_count} sans couleur")
