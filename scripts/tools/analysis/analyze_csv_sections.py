import csv
import re

csv_path = r'c:\Users\hanok\wordpress\products-appliance\midea\preparation-culinaire\import-midea-preparation-culinaire.csv'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print(f"{'SKU':<25} | {'H2 Count':<10} | {'Char Count'}")
    print("-" * 50)
    for row in reader:
        desc = row.get('Description', '')
        # Count H2 tags in the cleaned description
        h2_count = len(re.findall(r'<h2', desc, re.IGNORECASE))
        char_count = len(desc)
        
        status = " [LOW]" if h2_count < 3 else ""
        print(f"{row['SKU']:<25} | {h2_count:<10} | {char_count}{status}")
