"""
Vérifie les prix (Regular price) d'un CSV WooCommerce.
Usage: python check_csv_prices.py --csv path/to/file.csv
"""
import csv
import argparse

parser = argparse.ArgumentParser(description="Affiche les SKU et prix d'un CSV WooCommerce.")
parser.add_argument('--csv', '-c', required=True, help="Chemin vers le fichier CSV WooCommerce")
args = parser.parse_args()

with open(args.csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print(f"\n{'SKU':<30} | {'Regular price':<12} | {'Sale price':<12}")
    print("-" * 60)
    empty_count = 0
    total = 0
    for row in reader:
        sku = row.get('SKU', '?')
        regular = row.get('Regular price', '')
        sale = row.get('Sale price', '')
        flag = " ⚠️" if not regular else ""
        print(f"{sku:<30} | {regular or '(vide)':<12} | {sale or '—':<12}{flag}")
        total += 1
        if not regular:
            empty_count += 1
    print("-" * 60)
    print(f"Total: {total} produits | {empty_count} sans prix")
