#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalize Product Colors — Outil de simplification et de normalisation
des noms de couleurs dans les fichiers pack-data JSON de WooCommerce.
"""

import os
import json
import re
import argparse

COLOR_MAPPING = {
    # --- Collisions Composées & Exceptions ---
    "titanium black": "Noir",
    "black titanium": "Noir",
    "titanium noir": "Noir",
    "noir titane": "Noir",
    "titanium blue": "Bleu",
    "blue titanium": "Bleu",
    "bleu titane": "Bleu",
    "titanium gold": "Or",
    "gold titanium": "Or",
    "or titane": "Or",
    "titanium yellow": "Jaune",
    "yellow titanium": "Jaune",
    "jaune titane": "Jaune",
    "titanium violet": "Violet",
    "violet titanium": "Violet",
    "violet titane": "Violet",
    "titanium white": "Blanc",
    "white titanium": "Blanc",
    "blanc titane": "Blanc",
    "titanium gray": "Gris",
    "titanium grey": "Gris",
    "gray titanium": "Gris",
    "grey titanium": "Gris",
    "gris titane": "Gris",
    "desert titanium": "Or",
    "natural titanium": "Gris",
    "silver shadow": "Argent",
    "argent titane": "Argent",
    "titane argent": "Argent",
    "bora purple": "Violet",
    "rose gold": "Rose",
    "pink gold": "Rose",
    "or rose": "Rose",
    "olive twilight": "Vert",
    
    # Noir
    "obsidian": "Noir",
    "charcoal": "Noir",
    "matte black": "Noir",
    "volcanic black": "Noir",
    "black": "Noir",
    "noir": "Noir",
    "dark": "Noir",
    "shadow": "Noir",
    "space gray": "Gris",
    "space grey": "Gris",
    "space black": "Noir",
    "midnight": "Noir",
    "onyx": "Noir",
    "jet black": "Noir",
    "carbon": "Noir",
    
    # Blanc
    "porcelain": "Blanc",
    "snow": "Blanc",
    "white": "Blanc",
    "blanc": "Blanc",
    "ceramic": "Blanc",
    "cream": "Blanc",
    "crème": "Blanc",
    "starlight": "Blanc",
    
    # Argenté / Gris
    "polished silver": "Argent",
    "silver": "Argent",
    "argent": "Argent",
    "argenté": "Argent",
    "frost": "Argent",
    "moonstone": "Gris",
    "hazel": "Gris",
    "grey": "Gris",
    "gray": "Gris",
    "gris": "Gris",
    "titanium": "Gris",
    "titane": "Gris",
    "graphite": "Gris",
    "lunar dust": "Gris",
    
    # Or / Jaune
    "champagne gold": "Or",
    "gold": "Or",
    "or": "Or",
    "doré": "Or",
    "dore": "Or",
    "yellow": "Jaune",
    "jaune": "Jaune",
    "lemon": "Jaune",
    
    # Bleu
    "bay": "Bleu",
    "indigo": "Bleu",
    "blue": "Bleu",
    "bleu": "Bleu",
    "sky": "Bleu",
    "aqua bliss": "Bleu",
    "navy": "Bleu",
    "teal": "Bleu",
    "ultramarine": "Bleu",
    
    # Vert
    "mint": "Vert",
    "aloe": "Vert",
    "lemongrass": "Vert",
    "jade": "Vert",
    "green": "Vert",
    "vert": "Vert",
    "seafoam": "Vert",
    "lime": "Vert",
    "olive": "Vert",
    
    # Kaki / Khaki
    "kaki militaire": "Kaki",
    "khaki": "Kaki",
    "kaki": "Kaki",
    
    # Rose / Violet
    "rose": "Rose",
    "peony": "Rose",
    "pink": "Rose",
    "peach": "Rose",
    "iris": "Violet",
    "violet": "Violet",
    "purple": "Violet",
    "deep purple": "Violet",
    "lavender purple": "Violet",
    "lavender": "Violet",
    "lilac": "Violet",
    
    # Rouge / Orange / Marron
    "red": "Rouge",
    "rouge": "Rouge",
    "burgundy": "Rouge",
    "orange": "Orange",
    "coral": "Orange",
    "corail": "Orange",
    "tangerine": "Orange",
    "cuivre": "Marron",
    "marron": "Marron",
    "beige": "Beige",
    "sand": "Beige",
    "sable": "Beige",
    "desert": "Beige",
    "désert": "Beige"
}


def map_color(color_name):
    if not color_name:
        return ""
    color_clean = color_name.strip().lower()
    
    # Kaki / Khaki est désormais une catégorie de couleur unique (intermédiaire entre Vert et Beige)
    if "kaki" in color_clean or "khaki" in color_clean:
        return "Kaki"
    
    # 1. Priorité aux mots-clés de couleurs primaires spécifiques pour éviter les faux positifs (comme "dark red" -> Noir)
    primaries = {
        "red": "Rouge", "rouge": "Rouge", "burgundy": "Rouge",
        "green": "Vert", "vert": "Vert", "mint": "Vert", "olive": "Vert", "jade": "Vert",
        "blue": "Bleu", "bleu": "Bleu", "indigo": "Bleu", "navy": "Bleu", "teal": "Bleu",
        "gold": "Or", "or": "Or", "doré": "Or", "dore": "Or",
        "silver": "Argent", "argent": "Argent", "argenté": "Argent",
        "kaki": "Kaki", "khaki": "Kaki", "beige": "Beige",
        "pink": "Rose", "rose": "Rose", "peach": "Rose",
        "purple": "Violet", "violet": "Violet", "lavender": "Violet", "lavande": "Violet", "lilac": "Violet", "lilas": "Violet",
        "yellow": "Jaune", "jaune": "Jaune", "lemon": "Jaune", "citron": "Jaune",
        "orange": "Orange", "coral": "Orange", "corail": "Orange",
        "marron": "Marron", "cuivre": "Marron", "brown": "Marron",
        "anthracite": "Gris", "graphite": "Gris", "gray": "Gris", "grey": "Gris", "gris": "Gris",
        "black": "Noir", "noir": "Noir", "charcoal": "Noir",
        "white": "Blanc", "blanc": "Blanc", "snow": "Blanc", "neige": "Blanc"
    }
    
    words = re.findall(r'\b\w+\b', color_clean)
    for word in words:
        if word in primaries:
            return primaries[word]
            
    # 2. Correspondance standard du dictionnaire ordonné
    sorted_keys = sorted(COLOR_MAPPING.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if re.search(r'\b' + re.escape(key) + r'\b', color_clean):
            return COLOR_MAPPING[key]
            
    return color_name.strip().capitalize()


def normalize_color_attribute_string(attr_str):
    if not attr_str:
        return ""
    
    # Séparer les couleurs
    parts = [p.strip() for p in re.split(r'\s*\|\s*|\s*,\s*|\s*;\s*', attr_str) if p.strip()]
    mapped_list = [map_color(p) for p in parts]
    
    # Détection et gestion des collisions de couleurs
    from collections import Counter
    counts = Counter(mapped_list)
    final_colors = []
    
    for orig, mapped in zip(parts, mapped_list):
        if counts[mapped] > 1:
            orig_lower = orig.lower()
            if any(k in orig_lower for k in ["ciel", "light", "sky", "mint", "pale", "clair", "frost", "glow"]):
                disambiguated = f"{mapped} clair"
            elif any(k in orig_lower for k in ["sombre", "dark", "deep", "midnight", "navy", "nuit", "shadow"]):
                disambiguated = f"{mapped} sombre"
            elif any(k in orig_lower for k in ["gold", "doré", "dore", "or"]):
                disambiguated = f"{mapped} doré"
            elif any(k in orig_lower for k in ["titanium", "titane"]):
                disambiguated = f"{mapped} titane"
            else:
                disambiguated = orig.strip().capitalize()
            final_colors.append(disambiguated)
        else:
            final_colors.append(mapped)
            
    # Dédoublonner tout en préservant l'ordre
    seen = set()
    deduped = []
    for c in final_colors:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
            
    return " | ".join(deduped)


def process_pack_data(json_path, dry_run=False, verbose=False):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    woo = data.get("woocommerce_csv", {})
    changed = False
    
    # 1. Rechercher l'attribut de couleur (Attribute X name = Couleur ou Color)
    color_attr_num = None
    for n in range(1, 6):
        name_key = f"Attribute {n} name"
        if name_key in woo and woo[name_key].strip().lower() in ["couleur", "color"]:
            color_attr_num = n
            break

    if color_attr_num:
        val_key = f"Attribute {color_attr_num} value(s)"
        def_key = f"Attribute {color_attr_num} default"
        
        old_val = woo.get(val_key, "")
        old_def = woo.get(def_key, "")
        
        new_val = normalize_color_attribute_string(old_val)
        new_def = map_color(old_def)
        
        if old_val != new_val:
            woo[val_key] = new_val
            changed = True
            if verbose:
                print(f"  [COLOR ATTR] {old_val} -> {new_val}")
                
        if old_def != new_def:
            woo[def_key] = new_def
            changed = True
            if verbose:
                print(f"  [COLOR DEFAULT] {old_def} -> {new_def}")
                
        # S'assurer que le nom de l'attribut est "Couleur" en français
        if woo[f"Attribute {color_attr_num} name"] != "Couleur":
            woo[f"Attribute {color_attr_num} name"] = "Couleur"
            changed = True

    # 2. Mettre à jour la couleur dans le nom du produit (Name)
    if "Name" in woo:
        old_name = woo["Name"]
        parts = old_name.split(" - ")
        if len(parts) >= 2:
            # Le dernier élément est la couleur par défaut
            old_name_color = parts[-1].strip()
            new_name_color = map_color(old_name_color)
            if old_name_color != new_name_color:
                parts[-1] = new_name_color
                new_name = " - ".join(parts)
                woo["Name"] = new_name
                changed = True
                if verbose:
                    print(f"  [NAME] '{old_name}' -> '{new_name}'")

    # 3. Mettre à jour les clés standard colors du JSON
    colors_section = data.get("colors", {})
    if "standard" in colors_section:
        old_std = colors_section.get("standard", [])
        new_std = []
        for c in old_std:
            mapped = map_color(c)
            if mapped and mapped not in new_std:
                new_std.append(mapped)
        if old_std != new_std:
            colors_section["standard"] = new_std
            changed = True
            
    if "default" in colors_section:
        old_default = colors_section.get("default", "")
        new_default = map_color(old_default)
        if old_default != new_default:
            colors_section["default"] = new_default
            changed = True

    if changed and not dry_run:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    return changed


def main():
    parser = argparse.ArgumentParser(description="Normalise les couleurs des produits dans les pack-data JSON.")
    parser.add_argument("--products-dir", required=True, help="Chemin vers le répertoire de la série de produits (ex: products/google-pixel-all)")
    parser.add_argument("--dry-run", action="store_true", help="Simuler les changements sans modifier les fichiers")
    parser.add_argument("--verbose", action="store_true", help="Afficher les détails de chaque modification")
    args = parser.parse_args()

    if not os.path.isdir(args.products_dir):
        print(f"[ERROR] Répertoire introuvable : {args.products_dir}")
        return

    print("=" * 70)
    print("  NORMALIZE PRODUCT COLORS — Outil de Simplification")
    print("=" * 70)
    print(f"  Dossier  : {args.products_dir}")
    print(f"  Mode     : {'DRY-RUN' if args.dry_run else 'ECRITURE'}")
    print("=" * 70)

    count = 0
    modified = 0
    for root, dirs, files in os.walk(args.products_dir):
        for filename in files:
            if filename.startswith("pack-data-") and filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                count += 1
                try:
                    is_modified = process_pack_data(filepath, args.dry_run, args.verbose)
                    if is_modified:
                        modified += 1
                        print(f"[OK] Normalisé : {os.path.basename(filepath)}")
                except Exception as e:
                    print(f"[!] Erreur de traitement sur {filename} : {e}")

    print(f"\n[DONE] {modified}/{count} fichier(s) JSON mis à jour.")


if __name__ == "__main__":
    main()
