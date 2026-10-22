import os
import re
from pathlib import Path

root_dir = Path(r'c:\Users\hanok\wordpress\products-appliance\midea\preparation-culinaire')
results = {}

labels = ["Coloris", "Couleur", "Finition", "Matériau", "Bocal", "Bol"]

for subdir in root_dir.iterdir():
    if not subdir.is_dir():
        continue
    
    long_file = next(subdir.glob("*LONG.html"), None)
    if long_file:
        content = long_file.read_text(encoding='utf-8')
        color = "Not found"
        
        # Try spec table first
        for label in labels:
            pattern = rf'<td[^>]*>.*?{label}.*?</td>\s*<td[^>]*>(.*?)</td>'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                raw_val = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                color = raw_val
                break
        
        results[subdir.name] = color

print(f"{'Folder':<25} | {'Detected Color'}")
print("-" * 50)
for folder, color in results.items():
    print(f"{folder:<25} | {color}")
