import os
import re
from pathlib import Path

root_dir = Path(r'c:\Users\hanok\wordpress\products-appliance\midea\preparation-culinaire')
results = []

for subdir in root_dir.iterdir():
    if not subdir.is_dir():
        continue
    
    long_file = next(subdir.glob("*LONG.html"), None)
    if long_file:
        try:
            content = long_file.read_text(encoding='utf-8')
            # Extract content within the main div to avoid counting tags in comments or metadata
            main_match = re.search(r'<div id="product-long-description".*?>(.*?)</div>\s*(?:<!--|$)', content, re.DOTALL | re.IGNORECASE)
            if main_match:
                main_content = main_match.group(1)
                h2_count = len(re.findall(r'<h2[^>]*>', main_content, re.IGNORECASE))
                
                # Check for the dark feature card as a section
                has_dark_card = 1 if 'background-color: #1d1d1f' in main_content else 0
                
                # Total editorial sections (excluding the tech spec table h2 if it's the only one)
                # But let's just stick to H2 count for now as a baseline and see.
                
                results.append({
                    'folder': subdir.name,
                    'h2_count': h2_count,
                    'has_dark_card': has_dark_card,
                    'path': str(long_file)
                })
        except Exception as e:
            print(f"Error reading {long_file}: {e}")

# Filter those with less than 3 H2 tags
low_sections = [r for r in results if r['h2_count'] < 3]

print(f"{'Folder':<25} | {'H2 Count':<10} | {'Dark Card'}")
print("-" * 50)
for r in results:
    status = " [LOW]" if r['h2_count'] < 3 else ""
    print(f"{r['folder']:<25} | {r['h2_count']:<10} | {r['has_dark_card']}{status}")

print("\nFiles to analyze deeper:")
for r in low_sections:
    print(f"- {r['path']}")
