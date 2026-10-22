import os
import re
import argparse
from pathlib import Path

# Forbidden words list from verify_nasco_freezers.py
FORBIDDEN_WORDS = [
    "majestueusement", "héroïquement", "divinement", "victorieusement", 
    "héroïque", "divin", "majestueux"
]

def analyze_html_file(file_path):
    """
    Analyses a LONG.html file to check:
    1. Number of editorial H2 sections (excluding Tech Specs).
    2. Presence of at least 2 paragraphs per editorial section.
    3. Absence of forbidden hyperbolic words.
    4. Presence of 'Sources & Crédibilité' section.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check for forbidden words
        forbidden_found = []
        for word in FORBIDDEN_WORDS:
            if word.lower() in content.lower():
                forbidden_found.append(word)
        
        # Check for Sources & Crédibilité
        has_sources = "Sources & Crédibilité" in content
        
        # Clean the content to handle potential nested structures or comments that might break regex
        # We focus on the product-long-description div
        main_match = re.search(r'<div[^>]*id="product-long-description"[^>]*>(.*)</div>\s*(?:<!--|$)', content, re.DOTALL | re.IGNORECASE)
        
        if not main_match:
            # Fallback if the standard closing is missing
            main_match = re.search(r'<div[^>]*id="product-long-description"[^>]*>(.*)', content, re.DOTALL | re.IGNORECASE)
            
        if not main_match:
            return {
                'sections': None,
                'forbidden_found': forbidden_found,
                'has_sources': has_sources
            }
            
        main_content = main_match.group(1)
        
        # Split by H2 tags to isolate sections
        parts = re.split(r'(<h2[^>]*>.*?</h2>)', main_content, flags=re.IGNORECASE | re.DOTALL)
        
        sections = []
        # Index 0 is intro, we start at first H2
        for i in range(1, len(parts), 2):
            h2_tag = parts[i]
            # The body is everything between this H2 and the next one (or end of content)
            section_body = parts[i+1] if i+1 < len(parts) else ""
            
            # Clean H2 text
            h2_text = re.sub(r'<[^>]+>', '', h2_tag).strip()
            h2_text = re.sub(r'\s+', ' ', h2_text)
            
            is_tech = any(kw in h2_text.lower() for kw in ["fiche technique", "spécifications", "technique"])
            
            # Count distinct <p> tags
            # We filter out empty paragraphs or those that might be purely decorative
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', section_body, re.IGNORECASE | re.DOTALL)
            p_count = 0
            for p in paragraphs:
                clean_p = re.sub(r'<[^>]+>', '', p).strip()
                if len(clean_p) > 5: # Ignore very short placeholder-like paragraphs
                    p_count += 1
            
            sections.append({
                'title': h2_text,
                'is_tech': is_tech,
                'p_count': p_count
            })
            
        return {
            'sections': sections,
            'forbidden_found': forbidden_found,
            'has_sources': has_sources
        }
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Analyse des sections éditoriales, forbidden words et sources.")
    parser.add_argument("--input", "-i", help="Répertoire racine à scanner", 
                        default=r"c:\Users\hanok\wordpress\products-appliance\nasco-all\congelateur")
    args = parser.parse_args()
    
    root_dir = Path(args.input)
    if not root_dir.exists():
        print(f"Erreur: Le répertoire {root_dir} n'existe pas.")
        return

    print(f"\n[SCAN] Analyse de l'integrite editoriale : {root_dir}")
    print(f"{'Dossier':<25} | {'H2':<4} | {'Src':<3} | {'Mots interdits':<15} | {'Paragraphes'}")
    print("-" * 110)
    
    total_folders = 0
    errors_found = 0
    
    for subdir in sorted(root_dir.iterdir()):
        if not subdir.is_dir():
            continue
        
        long_file = next(subdir.glob("*LONG.html"), None)
        if long_file:
            total_folders += 1
            analysis = analyze_html_file(long_file)
            
            if not analysis or analysis['sections'] is None:
                print(f"{subdir.name[:25]:<25} | ERR  | ERR | ERR             | [ERREUR DE PARSING]")
                errors_found += 1
                continue
                
            sections = analysis['sections']
            forbidden = analysis['forbidden_found']
            has_sources = analysis['has_sources']
            
            editorial_sections = [s for s in sections if not s['is_tech']]
            editorial_count = len(editorial_sections)
            
            # Check for paragraph count errors (must be >= 2)
            p_errors = []
            for s in editorial_sections:
                if s['p_count'] < 2:
                    short_title = (s['title'][:15] + '..') if len(s['title']) > 15 else s['title']
                    p_errors.append(f"'{short_title}'({s['p_count']}p)")
            
            # Formatting outputs
            src_status = "OK" if has_sources else "!!"
            forbidden_status = f"!! {', '.join(forbidden)}" if forbidden else "OK None"
            h2_status = f"{editorial_count}"
            if editorial_count < 3: h2_status += "!!"

            p_status = "!! " + " | ".join(p_errors) if p_errors else "OK"
            
            if editorial_count < 3 or p_errors or forbidden or not has_sources:
                errors_found += 1
                print(f"{subdir.name[:25]:<25} | {h2_status:<4} | {src_status:<3} | {forbidden_status[:15]:<15} | {p_status}")
            else:
                print(f"{subdir.name[:25]:<25} | {h2_status:<4} | {src_status:<3} | {forbidden_status:<15} | {p_status}")

    print("-" * 110)
    print(f"Résumé : {total_folders} packs vérifiés, {errors_found} anomalies détectées.")
    if errors_found > 0:
        print("\nCritères de conformité :")
        print("   1. Au moins 3 sections H2 éditoriales.")
        print("   2. Au moins 2 paragraphes par section.")
        print("   3. Aucun mot hyperbolique interdit.")
        print("   4. Présence du bloc 'Sources & Crédibilité'.")

if __name__ == "__main__":
    main()
