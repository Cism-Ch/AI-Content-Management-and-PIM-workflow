#!/usr/bin/env python3
# =============================================================================
# generate_appliance_csv.py
# =============================================================================
# Auteur    : AI Agent (Antigravity)
# Date      : 2026-02-24
# Version   : 1.0.0
# Description:
#   GÃ©nÃ¨re un CSV d'import WooCommerce pour un rÃ©pertoire parent contenant
#   des packs produits Ã©lectromÃ©nagers (LONG.html + SHORT.html).
#   Chaque sous-rÃ©pertoire reprÃ©sente un modÃ¨le produit.
#
# Structure attendue :
#   <ParentDir>/
#     <Brand>/
#       <ModelName>/
#         <Brand>-<ModelName>-LONG.html
#         <Brand>-<ModelName>-SHORT.html
#         .gitkeep
#
# Usage :
#   python generate_appliance_csv.py --input products-appliance/Midea
#   python generate_appliance_csv.py --input products-appliance --brand Midea --output exports/
#   python generate_appliance_csv.py --input products-appliance/Midea --validate
#
# =============================================================================

import argparse
import csv
import io
import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime


# =============================================================================
# CONFIGURATION
# =============================================================================

# Colonnes du template CSV WooCommerce (Template-products-list-for-import.csv)
CSV_HEADERS = [
    "ID", "Type", "SKU", "Name", "Published",
    "Visibility in catalog", "Short description", "Description",
    "In stock?", "Stock", "Regular price", "Categories", "Tags", "Images",
    "Attribute 1 name", "Attribute 1 value(s)", "Attribute 1 default", "Attribute 1 visible", "Attribute 1 global",
    "Attribute 2 name", "Attribute 2 value(s)", "Attribute 2 default", "Attribute 2 visible", "Attribute 2 global",
    "Attribute 3 name", "Attribute 3 value(s)", "Attribute 3 default", "Attribute 3 visible", "Attribute 3 global",
    "Attribute 4 name", "Attribute 4 value(s)", "Attribute 4 default", "Attribute 4 visible", "Attribute 4 global"
]

# Mapping des marques vers leurs catÃ©gories WooCommerce
CATEGORY_MAP = {
    "midea"     : "ElectromÃ©nagers",
    "samsung"   : "ElectromÃ©nagers",
    "lg"        : "ElectromÃ©nagers",
    "philips"   : "ElectromÃ©nagers",
    "bosch"     : "ElectromÃ©nagers",
    "whirlpool" : "ElectromÃ©nagers",
    "nasco"     : "ElectromÃ©nagers",
    "beko"      : "ElectromÃ©nagers",
    "hisense"   : "ElectromÃ©nagers",
    "tcl"       : "ElectromÃ©nagers",
    "carrier"   : "ElectromÃ©nagers",
    "toshiba"   : "Electroménagers",
    "unionaire" : "Electroménagers",
    "galaxy"    : "Electroménagers",
    "oraimo"    : "Electroménagers",
}

# RÃ©pertoire de sortie par dÃ©faut (relatif au workspace)
DEFAULT_OUTPUT_DIR = "Exports/CSV_Imports/Appliance"


# =============================================================================
# FONCTIONS UTILITAIRES HTML
# =============================================================================

def strip_html_comments(html: str) -> str:
    """Supprime tous les commentaires HTML <!-- ... --> du contenu."""
    if not html:
        return ""
    cleaned = re.sub(r'<!--[\s\S]*?-->', '', html)
    # Supprimer les lignes vides excessives
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def sanitize_for_csv(html: str) -> str:
    """
    Nettoie une chaÃ®ne HTML pour l'insertion dans un CSV WooCommerce.
    Supprime les sauts de ligne cosmÃ©tiques (\n, \r, \t) qui brisent
    l'affichage dans les cellules CSV et dans l'Ã©diteur WooCommerce.
    Remplace par un espace simple pour conserver la lisibilitÃ© du HTML.
    """
    if not html:
        return ""
    # Remplacer les tabulations par des espaces
    cleaned = html.replace('\t', ' ')
    # Fusionner les sauts de ligne entourÃ©s de tags HTML (ex: >\n<)
    cleaned = re.sub(r'>\s*\n\s*<', '><', cleaned)
    # Remplacer tous les retours chariot / sauts de ligne restants par un espace
    cleaned = re.sub(r'[\r\n]+', ' ', cleaned)
    # Normaliser les espaces multiples consÃ©cutifs
    cleaned = re.sub(r'  +', ' ', cleaned)
    return cleaned.strip()


def extract_long_description(content: str) -> str:
    """
    Extrait le bloc <div id="product-long-description"> du fichier LONG.html.
    Supprime les commentaires internes mais conserve tout le HTML de contenu.
    """
    # Chercher le div principal avec id="product-long-description"
    match = re.search(
        r'(<div[^>]*id=["\']product-long-description["\'][^>]*>[\s\S]*?</div>)\s*<!--',
        content,
        re.IGNORECASE
    )
    if match:
        return strip_html_comments(match.group(1))

    # Fallback: div avec style font-family (ancien format)
    match = re.search(
        r'(<div[^>]*style=["\'][^"\']*font-family[^"\']*["\'][^>]*>[\s\S]*?</div>)\s*<!--',
        content,
        re.IGNORECASE
    )
    if match:
        return strip_html_comments(match.group(1))

    # Dernier recours: tout le contenu avant le premier commentaire AIOSEO
    match = re.search(r'^([\s\S]*?)\s*<!--\s*(AIOSEO|KEYWORDS)', content, re.IGNORECASE)
    if match:
        return strip_html_comments(match.group(1))

    return strip_html_comments(content)


def extract_short_description(content: str) -> str:
    """
    Extrait la description courte du fichier SHORT.html.
    Supprime les commentaires AIOSEO/KEYWORDS de fin de fichier.
    """
    # Supprimer les commentaires du dÃ©but (guide de rÃ©daction, etc.)
    content = re.sub(r'^\s*<!--[\s\S]*?-->\s*', '', content)

    # Extraire tout avant le premier commentaire AIOSEO/KEYWORDS
    match = re.search(r'([\s\S]*?)\s*<!--\s*(AIOSEO|KEYWORDS)', content, re.IGNORECASE)
    if match:
        return strip_html_comments(match.group(1)).strip()

    # Fallback: tout avant le premier commentaire
    match = re.search(r'([\s\S]*?)\s*<!--', content)
    if match:
        return strip_html_comments(match.group(1)).strip()

    return strip_html_comments(content).strip()


def extract_product_name(content: str) -> str:
    """
    Extrait le nom du produit depuis le H1 du fichier LONG.html.
    Retourne le texte brut du H1 (sans balises HTML internes).
    """
    match = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', content, re.IGNORECASE)
    if match:
        # Nettoyer le HTML interne (balises, retours ligne, espaces multiples)
        raw = match.group(1)
        raw = re.sub(r'<[^>]+>', '', raw)        # Supprimer les balises
        raw = re.sub(r'\s+', ' ', raw)            # Normaliser les espaces
        return raw.strip()
    return ""


def extract_keywords(long_content: str, short_content: str) -> str:
    """
    Extrait les mots-clÃ©s depuis le commentaire <!-- KEYWORDS UTILES: -->
    des fichiers LONG ou SHORT.
    Retourne uniquement le Focus Keyword comme tag.
    """
    keywords = []

    # Chercher dans SHORT d'abord, puis LONG
    for content in [short_content, long_content]:
        if not content:
            continue

        # Format : <!-- KEYWORDS UTILES: ... -->
        match = re.search(
            r'<!--[\s\S]*?KEYWORDS UTILES[\s\S]*?:([\s\S]*?)-->',
            content,
            re.IGNORECASE
        )
        if match:
            block = match.group(1)

            # Extraire le Focus Keyword - on s'arrÃªte avant "LSI Keywords" ou la fin de ligne
            focus_match = re.search(r'Focus Keyword:\s*(.*?)(?=\s*LSI Keywords:|$)', block, re.IGNORECASE)
            if focus_match:
                kw = focus_match.group(1).strip()
                if kw and kw not in keywords:
                    keywords.append(kw)

            # Extraire les LSI Keywords - on s'arrÃªte avant le "-->"
            lsi_match = re.search(r'LSI Keywords:\s*(.*?)(?=\s*-->|$)', block, re.IGNORECASE)
            if lsi_match:
                lsi_raw = lsi_match.group(1).strip()
                # On divise par virgule et on nettoie chaque mot-clÃ©
                lsi_list = [k.strip() for k in lsi_raw.split(',') if k.strip()]
                for lsi in lsi_list:
                    if lsi and lsi not in keywords:
                        keywords.append(lsi)

            if keywords:
                break

    return ', '.join(keywords)


def extract_coloris(long_content: str, product_name: str = "", keywords: str = "") -> str:
    """
    Extrait la valeur du coloris depuis la table des specs ou via fallback.
    Supporte de nombreux libellÃ©s (Coloris, Couleur, Finition, Surface, MatÃ©riau).
    """
    if not long_content:
        return ""

    # 1. Extraction via la table HTML (plus prÃ©cis)
    # On cherche un TD contenant un libellÃ© clÃ©, suivi d'un TD contenant la valeur
    labels = [
        "Coloris", "Couleur", "Finition", "Design", "Surface", 
        "MatÃ©riau Surface", "Couleur / Finition", "Finition / Couleur",
        "Type de surface", "MatÃ©riau", "Surface de cuisson", "Finition Verre",
        "Coloris principal", "Coloris de la porte", "Couleur carrosserie"
    ]
    
    for label in labels:
        # Regex flexible: <td...>Label</td> <td...>Valeur</td>
        # GÃ¨re les espaces, les tags internes (ex: <strong>) et les styles
        pattern = rf'<td[^>]*>\s*(?:<[^>]+>)*\s*{re.escape(label)}\s*(?:<[^>]+>)*\s*</td>\s*<td[^>]*>\s*([\s\S]*?)\s*</td>'
        match = re.search(pattern, long_content, re.IGNORECASE)
        if match:
            raw = match.group(1)
            raw = re.sub(r'<[^>]+>', '', raw)   # Supprimer les balises HTML
            raw = re.sub(r'\s+', ' ', raw)       # Normaliser
            val = raw.strip()
            if val and len(val) < 100: # SÃ©curitÃ© contre capture trop large
                return val

    # 2. Fallback via le nom du produit (Name)
    # Souvent "Noir", "Inox", "Silver", "Blanc" sont dans le titre
    search_text = f"{product_name} {keywords}".lower()
    
    color_map = {
        "inox noir"     : "Inox Noir / Black Stainless",
        "inox silver"   : "Inox Silver",
        "inox"          : "Acier Inoxydable (Inox)",
        "noir mat"      : "Noir Matte",
        "noir"          : "Noir",
        "blanc"         : "Blanc",
        "silver"        : "Silver",
        "argent"        : "Argent",
        "verre noir"    : "Verre TrempÃ© Noir",
        "verre blanc"   : "Verre TrempÃ© Blanc",
    }
    
    for key, display in color_map.items():
        if key in search_text:
            return display

    # 3. Fallback spÃ©cifique par catÃ©gorie/marque
    # Pour les TVs et Audio Hisense, si rien n'est trouvÃ©, on assume "Noir / Black"
    if "hisense" in search_text and any(k in search_text for k in ["tv", "led", "audio", "rocker", "display"]):
        return "Noir / Black"

    return ""


def convert_weight_to_kg(weight_str: str, group: str = "appliance") -> str:
    """
    Normalise une chaîne représentant le poids.
    Si la valeur est en grammes, elle est convertie en kilogrammes (kg).
    Si la valeur est déjà en kg, elle est normalisée en kg.
    Utilise le groupe ('tech' ou 'appliance') pour lever les ambiguïtés en l'absence d'unité.
    """
    if not weight_str:
        return ""
    w_clean = weight_str.lower().replace("\xa0", " ").strip()
    if any(x in w_clean for x in ["non applicable", "not applicable", "n/a", "none", "sans"]):
        return ""
    num_match = re.search(r'(\d+(?:[.,]\d+)?)', w_clean)
    if not num_match:
        return weight_str
    val_str = num_match.group(1).replace(",", ".")
    try:
        val = float(val_str)
    except ValueError:
        return weight_str
    
    # 1. Unité explicite kg
    if re.search(r'\b(kg|kilo|kilogramme|kilogrammes|kilogram|kilograms)\b', w_clean):
        val_kg_str = f"{val:.3f}".rstrip('0').rstrip('.')
        return f"{val_kg_str} kg"
        
    # 2. Unité explicite g
    if re.search(r'\b(g|gr|gramme|grammes|gram|grams)\b', w_clean) or (w_clean.endswith("g") and not w_clean.endswith("kg")):
        val_kg = val / 1000.0
        val_kg_str = f"{val_kg:.3f}".rstrip('0').rstrip('.')
        return f"{val_kg_str} kg"
        
    # 3. Pas d'unité spécifiée (heuristique intelligente selon le groupe)
    if group == "tech":
        if val >= 2.0:
            val_kg = val / 1000.0
        else:
            val_kg = val
    else:
        if val >= 1000.0:
            val_kg = val / 1000.0
        else:
            val_kg = val
            
    val_kg_str = f"{val_kg:.3f}".rstrip('0').rstrip('.')
    return f"{val_kg_str} kg"


def extract_poids(long_content: str) -> str:
    """
    Extrait la valeur du poids depuis la table des specs HTML,
    puis la normalise en kg.
    """
    if not long_content:
        return ""
    pattern = r'<td[^>]*>\s*(?:<[^>]+>)*\s*Poids\s*(?:<[^>]+>)*\s*</td>\s*<td[^>]*>\s*([\s\S]*?)\s*</td>'
    match = re.search(pattern, long_content, re.IGNORECASE)
    if match:
        raw = match.group(1)
        raw = re.sub(r'<[^>]+>', '', raw)
        raw = re.sub(r'\s+', ' ', raw)
        val = raw.strip()
        if val and len(val) < 100:
            return convert_weight_to_kg(val)
    return ""


def extract_seo_title(content: str) -> str:
    """
    Extrait le SEO Title depuis le commentaire <!-- AIOSEO METADATA: --> du fichier.
    """
    match = re.search(
        r'<!--[\s\S]*?AIOSEO METADATA[\s\S]*?SEO Title:\s*([^\r\n]+)',
        content,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return ""


def find_images(product_dir: Path) -> str:
    """
    Scanne le rÃ©pertoire produit pour trouver des images (jpg, png, webp).
    Filtre les icÃ´nes ou fichiers non pertinents.
    Retourne une liste de noms de fichiers sÃ©parÃ©s par des virgules.
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    found_images = []
    
    for f in sorted(product_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in image_extensions:
            # On ignore les fichiers trop petits qui pourraient Ãªtre des icÃ´nes
            if f.stat().st_size > 5000: # > 5 KB
                found_images.append(f.name)
    
    return ', '.join(found_images)


# =============================================================================
# FONCTIONS DE DÃ‰TECTION DE FICHIERS
# =============================================================================

def find_long_short_files(product_dir: Path) -> tuple[Path | None, Path | None]:
    """
    Trouve les fichiers LONG.html et SHORT.html dans un rÃ©pertoire produit.
    Supporte les patterns :
      - [Brand]-[Model]-LONG.html / SHORT.html
      - [Model]-LONG.html / SHORT.html (cas hÃ©ritage)
    """
    long_file = None
    short_file = None

    for f in product_dir.iterdir():
        if not f.is_file() or f.suffix.lower() != '.html':
            continue
        name_upper = f.name.upper()
        if 'LONG' in name_upper and long_file is None:
            long_file = f
        elif 'SHORT' in name_upper and short_file is None:
            short_file = f

    return long_file, short_file


def guess_brand_from_dir(product_dir: Path, root_dir: Path) -> str:
    """
    Devine la marque du produit depuis la structure du rÃ©pertoire.
    Exemple: products-appliance/Midea/Model -> 'Midea'
    """
    # Si une marque connue est dans le chemin, on l'utilise
    path_str = str(product_dir).lower()
    if 'midea' in path_str:
        return "Midea"
    if 'nasco' in path_str:
        return "Nasco"
    if 'samsung' in path_str:
        return "Samsung"
    if 'lg' in path_str:
        return "LG"
    if 'beko' in path_str:
        return "Beko"
    if 'hisense' in path_str:
        return "Hisense"
    if 'tcl' in path_str:
        return "TCL"
    if 'toshiba' in path_str:
        return "Toshiba"
    if 'unionaire' in path_str:
        return "Unionaire"
    if 'galaxy' in path_str:
        return "Galaxy"
    if 'carrier' in path_str:
        return "Carrier"
    
    # Sinon fallback sur la logique prÃ©cÃ©dente
    try:
        relative = product_dir.relative_to(root_dir)
        parts = relative.parts
        if len(parts) >= 1:
            return parts[0]
    except ValueError:
        pass
    return "Inconnu"


def get_category(brand: str, product_dir: Path, keywords: str = "") -> str:
    """Retourne la catÃ©gorie WooCommerce selon la marque et le rÃ©pertoire produit."""
    brand_lower = brand.lower()
    path_str = str(product_dir).lower()
    
    # 1. Fallback sur le contenu si le chemin est ambigu (ex: TP200K dans barre de son)
    content_norm = keywords.lower() + " " + product_dir.name.lower()
    if "speaker" in content_norm or "enceinte" in content_norm:
        if "fete" in content_norm or "party" in content_norm or "bluetooth" in content_norm:
            return "Audio & Hi-fi > Enceintes Bluetooth"

    # 2. Mapping spÃ©cifique basÃ© sur le rÃ©pertoire (prioritÃ© sur la marque)
    path_norm = path_str.replace("-", " ").replace("_", " ")
    
    if "refroidisseur" in path_norm or "refrigerateur" in path_norm or "chiller" in path_norm:
        return "ElectromÃ©nagers > RÃ©frigÃ©rateurs & RÃ©froidisseurs"
    if "congelateur" in path_norm or "freezer" in path_norm:
        return "ElectromÃ©nagers > CongÃ©lateurs"
    if "cuisiniere" in path_norm or "four" in path_norm or "cooking" in path_norm or "gaziniere" in path_norm:
        return "ElectromÃ©nagers > Ã‰lectromÃ©nager culinaire > CuisiniÃ¨re â€“ Fours & Micro-ondes"
    if "lave vaisselle" in path_norm or "dishwasher" in path_norm:
        return "ElectromÃ©nagers > Ã‰lectromÃ©nager Entretien > Lave vaisselle"
    if "machine a laver" in path_norm or "washer" in path_norm or "seche linge" in path_norm or "dryer" in path_norm:
        return "ElectromÃ©nagers > Ã‰lectromÃ©nager Entretien > Machine a Laver & SÃ©cher"
    if "barre de son" in path_norm or "soundbar" in path_norm:
        return "Audio & Hi-fi > Barres de Son"
    if "enceinte" in path_norm or "speaker" in path_norm:
        return "Audio & Hi-fi > Enceintes Bluetooth"
    if "tv" in path_norm or "television" in path_norm:
        return "TV & Equipement > TV QLED â€“ DLED â€“ ULED â€“ OLED"
    if "climatiseur" in path_norm or "ac " in path_norm or "air conditioner" in path_norm or "split" in path_norm:
        return "Traitement d'Air > Climatisation"
    if "mixeur" in path_norm or "mixer" in path_norm or "blender" in path_norm:
        return "Electroménagers > Petit Electroménager > Mixeur"
    if "disributeur" in path_norm or "dispenser" in path_norm or "distributeur" in path_norm:
        return "ElectromÃ©nagers > Distributeur d'eau"

    # 3. Oraimo Specific Mapping
    if brand_lower == "oraimo":
        if any(k in content_norm for k in ["watch", "montre"]):
            return "Wearables > Smartwatches"
        if any(k in content_norm for k in ["buds", "pods", "ecouteur", "earphone", "headset", "boom", "sound", "speaker"]):
            if "speaker" in content_norm or "enceinte" in content_norm:
                return "Audio & Hi-fi > Enceintes Bluetooth"
            return "Audio & Hi-fi > Ecouteurs & Casques"
        if any(k in content_norm for k in ["power", "bank", "chargeur", "cable", "charger", "toaster", "toast"]):
            if "toast" in content_norm or "toaster" in content_norm:
                return "Accessoires > Chargeurs & Powerbanks" # Oraimo uses Toast for some chargers
            return "Accessoires > Chargeurs & Powerbanks"
        if any(k in content_norm for k in ["trimmer", "curler", "clipper", "tondeuse", "boucleur"]):
            return "Petit Electroménager > Beauté & Bien-être"
        if any(k in content_norm for k in ["scale", "pese"]):
            return "Wearables > Santé Connectée"
        if any(k in content_norm for k in ["vacuum", "cleaner", "aspirateur"]):
            return "Electroménagers > Aspirateurs"
        if any(k in content_norm for k in ["fryer", "friteuse"]):
            return "Electroménagers > Friteuses"
        if any(k in content_norm for k in ["fan", "ventilateur"]):
            return "Electroménagers > Ventilateurs"
        if any(k in content_norm for k in ["bottle", "thermo", "gourde"]):
            return "Petit Electroménager > Maison"

    return CATEGORY_MAP.get(brand_lower, f"ElectromÃ©nagers > {brand}")


def get_sku(model_dir_name: str, brand: str) -> str:
    """
    GÃ©nÃ¨re un SKU normalisÃ© depuis le nom du rÃ©pertoire.
    Si le nom du rÃ©pertoire commence par la marque (ex: GAZ_...), on l'utilise tel quel.
    Sinon, on prÃ©fixe par la marque.
    """
    model_upper = model_dir_name.upper()
    brand_upper = brand.upper()
    
    # Si le modÃ¨le commence dÃ©jÃ  par la marque ou un prÃ©fixe connu (ex: GAZ)
    # on ne rajoute pas la marque devant pour Ã©viter les doublons.
    if model_upper.startswith(brand_upper) or model_upper.startswith("GAZ_") or model_upper.startswith("GAZINIERE"):
        return model_upper
    
    return f"{brand_upper}-{model_upper}"


# =============================================================================
# PROCESSING PRINCIPAL
# =============================================================================

def process_product(product_dir: Path, root_dir: Path, verbose: bool = True, price_data: dict = None) -> dict | None:
    """
    Traite un rÃ©pertoire produit et retourne un dictionnaire de donnÃ©es CSV.
    Retourne None si le produit ne peut pas Ãªtre traitÃ© (fichiers manquants).
    """
    model_name = product_dir.name
    long_file, short_file = find_long_short_files(product_dir)

    if not long_file and not short_file:
        if verbose:
            print(f"  [IGNORÃ‰] (aucun HTML trouvÃ©) : {model_name}")
        return None

    if verbose:
        status_long  = "OK" if long_file  else "KO"
        status_short = "OK" if short_file else "KO"
        print(f"  [SCAN] [{status_long} LONG / {status_short} SHORT] {model_name}")

    # Lire les contenus
    long_content  = long_file.read_text(encoding='utf-8')  if long_file  else ""
    short_content = short_file.read_text(encoding='utf-8') if short_file else ""

    # Extraire les donnÃ©es
    brand        = guess_brand_from_dir(product_dir, root_dir)
    product_name = extract_product_name(long_content)
    description  = sanitize_for_csv(extract_long_description(long_content))
    short_desc   = sanitize_for_csv(extract_short_description(short_content))
    keywords     = extract_keywords(long_content, short_content)
    # Fallback sur le SEO Title si H1 vide
    if not product_name:
        product_name = extract_seo_title(long_content) or extract_seo_title(short_content)

    # Fallback final sur le nom du rÃ©pertoire
    if not product_name:
        product_name = f"{brand} {model_name}"

    # Extraction du coloris (aprÃ¨s avoir finalisÃ© le product_name pour le fallback)
    coloris  = extract_coloris(long_content, product_name, keywords)
    poids    = extract_poids(long_content)
    sku      = get_sku(model_name, brand)
    category = get_category(brand, product_dir, keywords)

    images   = find_images(product_dir)

    return {
        "ID"                    : "",
        "Type"                  : "simple",
        "SKU"                   : sku,
        "Name"                  : product_name,
        "Published"             : "1",
        "Visibility in catalog" : "visible",
        "Short description"     : short_desc,
        "Description"           : description,
        "In stock?"             : "1",
        "Stock"                 : "10",
        "Regular price"         : str(price_data.get(model_name, price_data.get(sku, ""))),
        "Categories"            : category,
        "Tags"                  : keywords,
        "Images"                : images,
        "Attribute 1 name"      : "Color" if coloris else "",
        "Attribute 1 value(s)"  : coloris,
        "Attribute 1 default"   : coloris,
        "Attribute 1 visible"   : "1" if coloris else "",
        "Attribute 1 global"    : "1" if coloris else "",
        "Attribute 4 name"      : "Poids" if poids else "",
        "Attribute 4 value(s)"  : poids,
        "Attribute 4 default"   : poids,
        "Attribute 4 visible"   : "1" if poids else "",
        "Attribute 4 global"    : "1" if poids else "",
    }


def scan_products(input_dir: Path, recursive: bool = True, verbose: bool = True, price_data: dict = None) -> list[dict]:
    """
    Scanne le rÃ©pertoire d'entrÃ©e et retourne une liste de donnÃ©es produits.
    Si recursive=True, descend dans les sous-dossiers marque/modÃ¨le.
    """
    products = []

    if not input_dir.exists():
        print(f"âŒ RÃ©pertoire introuvable : {input_dir}")
        sys.exit(1)

    if verbose:
        print(f"\n[DIR] Scan de : {input_dir.resolve()}")

    # Collecter tous les rÃ©pertoires contenant des fichiers HTML
    candidate_dirs = []

    def collect(directory: Path, depth: int = 0):
        if depth > 3:  # SÃ©curitÃ© contre les structures trop profondes
            return
        
        # Un rÃ©pertoire est un candidat s'il contient Ã  la fois LONG et SHORT
        long_f, short_f = find_long_short_files(directory)
        if long_f and short_f:
            candidate_dirs.append(directory)
            
        # Continuer la recherche dans les sous-rÃ©pertoires si demandÃ©
        if recursive:
            for sub in sorted(directory.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.'):
                    collect(sub, depth + 1)

    collect(input_dir)

    if not candidate_dirs:
        print("[WARN] Aucun rÃ©pertoire produit trouvÃ© (pas de fichiers .html).")
        return []

    if verbose:
        print(f"OK {len(candidate_dirs)} produit(s) dÃ©tectÃ©s\n")

    for product_dir in sorted(candidate_dirs):
        data = process_product(product_dir, input_dir, verbose=verbose, price_data=price_data)
        if data:
            products.append(data)

    return products


# =============================================================================
# GÃ‰NÃ‰RATION CSV
# =============================================================================

def generate_csv(products: list[dict], output_path: Path) -> None:
    """
    GÃ©nÃ¨re le fichier CSV WooCommerce depuis la liste de produits.
    Utilise UTF-8-BOM pour compatibilitÃ© Excel.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=CSV_HEADERS,
            quoting=csv.QUOTE_MINIMAL,
            extrasaction='ignore',
        )
        writer.writeheader()
        for product in products:
            writer.writerow(product)

    print(f"\n[OK] CSV gÃ©nÃ©rÃ© avec succÃ¨s !")
    print(f"   - Fichier  : {output_path.resolve()}")
    print(f"   - Produits : {len(products)}")


# =============================================================================
# VALIDATION
# =============================================================================

def validate_products(products: list[dict]) -> dict:
    """
    Valide la qualitÃ© des donnÃ©es extraites et affiche un rapport.
    Retourne un dict de statistiques.
    """
    stats = {
        "total"           : len(products),
        "no_name"         : 0,
        "no_description"  : 0,
        "no_short"        : 0,
        "no_coloris"      : 0,
        "no_keywords"     : 0,
        "warnings"        : [],
    }

    print("\n" + "="*60)
    print("              RAPPORT DE VALIDATION")
    print("="*60 + "\n")

    for p in products:
        name = p.get("Name", "")
        sku  = p.get("SKU", "?")

        if not name or name == p.get("SKU", ""):
            stats["no_name"] += 1
            stats["warnings"].append(f"  [WARN] [{sku}] Nom produit manquant ou gÃ©nÃ©rique")

        if len(p.get("Description", "")) < 100:
            stats["no_description"] += 1
            stats["warnings"].append(f"  [WARN] [{sku}] Description trop courte (<100 chars)")

        if len(p.get("Short description", "")) < 50:
            stats["no_short"] += 1
            stats["warnings"].append(f"  [WARN] [{sku}] Description courte trop courte (<50 chars)")

        if not p.get("Attribute 1 value(s)"):
            stats["no_coloris"] += 1
            # Info seulement â€” pas tous les appareils ont un coloris
            stats["warnings"].append(f"  [INFO] [{sku}] Attribut Coloris non dÃ©tectÃ©")

        if not p.get("Tags"):
            stats["no_keywords"] += 1
            stats["warnings"].append(f"  [WARN] [{sku}] Aucun mot-clÃ© (Tags) extrait")

    # Afficher les avertissements
    for w in stats["warnings"]:
        print(w)

    print(f"\nSTATISTIQUES :")
    print(f"  - Produits totaux    : {stats['total']}")
    print(f"  - Noms manquants     : {stats['no_name']}")
    print(f"  - Descriptions KO    : {stats['no_description']}")
    print(f"  - Short desc KO      : {stats['no_short']}")
    print(f"  - Sans Coloris       : {stats['no_coloris']}")
    print(f"  - Sans mots-clÃ©s     : {stats['no_keywords']}")

    status = "[OK] VALIDATION RÃ‰USSIE" if stats["no_name"] == 0 and stats["no_description"] == 0 else "[WARN] VALIDATION AVEC AVERTISSEMENTS"
    print(f"\n{status}\n")

    return stats


# =============================================================================
# POINT D'ENTRÃ‰E
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="GÃ©nÃ¨re un CSV WooCommerce depuis un rÃ©pertoire de packs produits Ã©lectromÃ©nagers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  # GÃ©nÃ©rer un CSV pour tous les produits Midea
  python generate_appliance_csv.py --input products-appliance/Midea

  # SpÃ©cifier un rÃ©pertoire parent et filtrer par marque
  python generate_appliance_csv.py --input products-appliance --output Exports/

  # Mode validation + gÃ©nÃ©ration
  python generate_appliance_csv.py --input products-appliance/Midea --validate

  # Mode silencieux (pas de logs de progression)
  python generate_appliance_csv.py --input products-appliance/Midea --quiet
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="RÃ©pertoire d'entrÃ©e contenant les packs produits (ex: products-appliance/Midea)"
    )
    parser.add_argument(
        "--output", "-o",
        default="",
        help=f"RÃ©pertoire de sortie pour le CSV (dÃ©faut: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--filename", "-f",
        default="",
        help="Nom du fichier CSV de sortie (dÃ©faut: auto-gÃ©nÃ©rÃ© depuis le rÃ©pertoire d'entrÃ©e)"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Active le rapport de validation des donnÃ©es extraites"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Mode silencieux : supprime les logs de progression"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Ne pas scanner en profondeur (seulement le rÃ©pertoire d'entrÃ©e direct)"
    )

    args = parser.parse_args()

    verbose = not args.quiet

    # RÃ©soudre les chemins (relatifs au rÃ©pertoire de travail ou absolu)
    input_dir = Path(args.input).resolve()

    # DÃ©terminer le nom du fichier de sortie
    if args.filename:
        out_filename = args.filename
        if not out_filename.endswith('.csv'):
            out_filename += '.csv'
    else:
        # Auto-gÃ©nÃ©rer depuis le chemin d'entrÃ©e
        group_name = input_dir.name.lower().replace(' ', '-')
        timestamp  = datetime.now().strftime("%Y%m%d")
        out_filename = f"products-import-appliance-{group_name}-{timestamp}.csv"

    # RÃ©soudre le rÃ©pertoire de sortie
    if args.output:
        out_dir = Path(args.output).resolve()
    else:
        # Remonter jusqu'Ã  trouver un rÃ©pertoire "Exports" ou utiliser Ã  cÃ´tÃ© de scripts/
        script_dir = Path(__file__).parent.resolve()
        out_dir    = script_dir.parent / DEFAULT_OUTPUT_DIR

    output_path = out_dir / out_filename

    if verbose:
        print("\n" + "="*60)
        print("    GENERATION CSV ELECTROMENAGER - WooCommerce")
        print("="*60)

    # Charger les prix depuis les maps JSON si disponibles
    price_data = {}
    script_dir = Path(__file__).parent.resolve()
    pricing_dirs = [
        script_dir.parent / "Pricing",
        script_dir / "Pricing",
        script_dir / "pricing",
        script_dir
    ]
    for pdir in pricing_dirs:
        if pdir.exists():
            for price_map_file in pdir.glob("price_map_*.json"):
                try:
                    with open(price_map_file, 'r', encoding='utf-8') as f:
                        price_data.update(json.load(f))
                    if verbose:
                        print(f"[INFO] Map de prix chargée : {price_map_file.name}")
                except Exception as e:
                    print(f"[WARN] Erreur lors du chargement de {price_map_file.name}: {e}")

    # Scanner les produits
    products = scan_products(
        input_dir,
        recursive=not args.no_recursive,
        verbose=verbose,
        price_data=price_data
    )

    if not products:
        print("[ERROR] Aucun produit Ã  exporter. VÃ©rifiez le rÃ©pertoire d'entrÃ©e.")
        sys.exit(1)

    # Validation optionnelle
    if args.validate:
        validate_products(products)

    # GÃ©nÃ©rer le CSV
    generate_csv(products, output_path)

    if verbose:
        print(f"\n[INFO] Pour importer dans WooCommerce:")
        print(f"   Produits -> Importer -> Choisir le fichier CSV")
        print(f"   Mapper les colonnes selon le modÃ¨le WooCommerce standard\n")


if __name__ == "__main__":
    main()
