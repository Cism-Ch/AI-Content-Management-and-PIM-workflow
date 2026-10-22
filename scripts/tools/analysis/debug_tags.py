import csv

csv_path = r"c:\Users\hanok\wordpress\products-appliance\midea\refrigerateur\midea-refrigerators-import.csv"

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        tags = row.get('Tags', '')
        if "LSI" in tags.upper() or "KEYWORDS" in tags.upper():
            print(f"Row {i+1} SKU {row.get('SKU')}: Tags = [{tags}]")
        if i > 100: break
