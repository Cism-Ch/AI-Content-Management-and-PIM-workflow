#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_product_existence.py — Script de vérification de l'existence d'un modèle et de ses spécifications en ligne.

Recherche le produit sur le web (DuckDuckGo HTML, GSMArena, etc.) et s'assure :
  1. Que le modèle commercial de base existe.
  2. Que la configuration demandée (RAM, Stockage, Connectivité, Coloris) est documentée en ligne.
  3. De signaler les incohérences ou les variantes correctes s'il y a confusion.

Usage:
  python scripts/tools/product_data/check_product_existence.py --product "Blackview Tab 12 WiFi 128GB" --color "Gris Lunaire" --category tablet
"""

import argparse
import sys
import re
import urllib.parse
import time
from typing import List, Dict, Tuple, Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[ERROR] Modules requis manquants. Installez-les avec: pip install requests beautifulsoup4")
    sys.exit(1)

# Forcer UTF-8 sur Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Couleurs terminal
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Dictionnaire étendu de traduction et synonymes des couleurs principales pour la recherche web
COLOR_MAP = {
    "gris": ["gray", "grey", "space gray", "space grey", "lunaire", "graphite", "titanium", "lunar", "greyish"],
    "argent": ["silver", "stellaire", "platinum", "platine", "chrome"],
    "noir": ["black", "dark", "midnight", "charcoal", "obsidian", "noirâtre"],
    "blanc": ["white", "pearl", "perle", "ceramic", "snow"],
    "bleu": ["blue", "ocean", "sky", "indigo", "navy", "cyan", "teal"],
    "or": ["gold", "rose gold", "champagne", "bronze"],
    "vert": ["green", "mint", "olive", "emerald", "forest", "sage"],
    "rouge": ["red", "ruby", "scarlet", "crimson"],
    "rose": ["rose", "pink", "coral", "gold rose", "rose gold"],
    "kaki": ["kaki", "khaki", "military", "army"],
    "jaune": ["jaune", "yellow", "gold jaune", "gold yellow"],
    "violet": ["violet", "purple", "lavender", "lavande"],
    "beige": ["beige", "sand", "sable", "desert", "désert"]
}


def normalize_string(s: str) -> str:
    """Normalise une chaîne pour faciliter la comparaison (minuscules, sans accents, sans espaces doubles)."""
    import unicodedata
    s = s.lower().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9\s-]', '', s)


def get_color_terms(color: str) -> List[str]:
    """Retourne la liste des termes anglais et français acceptables pour une couleur donnée."""
    normalized = normalize_string(color)
    terms = [normalized]
    
    # Chercher des correspondances dans la color map
    for primary, synonyms in COLOR_MAP.items():
        if primary in normalized or any(syn in normalized for syn in synonyms):
            terms.append(primary)
            terms.extend(synonyms)
            
    # Décomposer les mots composés
    for part in normalized.split():
        if len(part) > 2:
            terms.append(part)
            
    return list(set(terms))


def fetch_url_content(url: str) -> str:
    """Télécharge le contenu HTML d'une page, le nettoie et extrait le texte brut."""
    skip_domains = ["youtube.com", "youtu.be", "facebook.com", "instagram.com", "twitter.com", "x.com", "pinterest.com", "linkedin.com", "tiktok.com"]
    if any(domain in url.lower() for domain in skip_domains):
        return ""
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr,en-US;q=0.9,en;q=0.8"
    }
    
    try:
        # Extraire l'URL réelle de redirection de DuckDuckGo si présente
        if "duckduckgo.com/y.js" in url or "duckduckgo.com/l/" in url:
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if "uddg" in query_params:
                url = query_params["uddg"][0]
                
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for s in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                s.decompose()
            text = soup.get_text(separator=" ")
            return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        pass
    return ""


def extract_specifications_from_text(text: str) -> Dict[str, List[str]]:
    """Analyse un texte brut pour en extraire le poids, les coloris, la RAM et le stockage."""
    text_lower = text.lower()
    
    # 1. Extraction des coloris
    found_colors = set()
    for primary, synonyms in COLOR_MAP.items():
        if re.search(r'\b' + re.escape(primary) + r'\b', text_lower):
            found_colors.add(primary.capitalize())
        else:
            for syn in synonyms:
                if re.search(r'\b' + re.escape(syn) + r'\b', text_lower):
                    found_colors.add(primary.capitalize())
                    break
                    
    # 2. Extraction du poids (en g ou kg)
    weights = []
    weight_keywords = [r'weight', r'poids', r'weighs', r'pèse', r'mass', r'masse', r'heavy']
    pattern_keyword = r'(?:' + '|'.join(weight_keywords) + r')'
    
    # Scan de motifs globaux
    matches_global = re.finditer(r'\b(\d+(?:\.\d+)?)\s*(g|gr|grams|grammes|kg|kilograms|kilogrammes)\b', text_lower)
    for m in matches_global:
        val = float(m.group(1))
        unit = m.group(2)
        if unit.startswith("k"):
            if 0.01 < val < 50.0:
                weights.append(f"{val} kg")
        else:
            if 5 < val < 5000:
                weights.append(f"{int(val)} g")
                
    # Scan ciblé autour des mots-clés de poids
    for match in re.finditer(pattern_keyword, text_lower):
        start = max(0, match.start() - 30)
        end = min(len(text_lower), match.end() + 50)
        window = text_lower[start:end]
        m_w = re.search(r'\b(\d+(?:\.\d+)?)\s*(g|gr|kg)\b', window)
        if m_w:
            val = float(m_w.group(1))
            unit = m_w.group(2)
            if unit.startswith("k"):
                if 0.01 < val < 50.0:
                    weights.append(f"{val} kg")
            else:
                if 5 < val < 5000:
                    weights.append(f"{int(val)} g")
                    
    # 3. Extraction RAM et Stockage
    found_ram = set()
    found_storage = set()
    
    ram_matches = re.findall(r'\b(2|3|4|6|8|12|16|24|32)\s*(?:gb|go)\s*(?:ram|de\s*ram|mémoire\s*vive)?\b', text_lower)
    storage_matches = re.findall(r'\b(16|32|64|128|256|512)\s*(?:gb|go)\s*(?:rom|ssd|flash|stockage|de\s*stockage)?\b', text_lower)
    storage_tb_matches = re.findall(r'\b(1|2)\s*(?:tb|to)\b', text_lower)
    
    for r in ram_matches:
        found_ram.add(f"{r}GB")
    for s in storage_matches:
        found_storage.add(f"{s}GB")
    for s in storage_tb_matches:
        found_storage.add(f"{s}TB")
        
    return {
        "weights": sorted(list(set(weights))),
        "colors": sorted(list(found_colors)),
        "ram": sorted(list(found_ram), key=lambda x: int(re.search(r'\d+', x).group())),
        "storage": sorted(list(found_storage), key=lambda x: int(re.search(r'\d+', x).group()) * (1024 if "TB" in x else 1))
    }


def parse_specs_from_text(product_name: str) -> Dict[str, List[str]]:
    """Parse les mots-clés techniques recherchés à partir du nom complet saisi par l'utilisateur."""
    specs = {
        "model": [],
        "storage": [],
        "ram": [],
        "connectivity": []
    }
    
    normalized_name = product_name.upper()
    
    # Extraction stockage (ROM) et RAM
    # Exemples: "128GB", "128 Go", "4GB RAM", "128Go/4Go"
    storage_matches = re.findall(r'(\d+)\s*(?:GB|GO|TB|TO)', normalized_name)
    for m in storage_matches:
        val = int(m)
        if val in [16, 32, 64, 128, 256, 512]:
            specs["storage"].append(f"{val}GB")
            specs["storage"].append(f"{val}GO")
            specs["storage"].append(f"{val} GO")
        elif val in [1, 2] and ("TB" in normalized_name or "TO" in normalized_name):
            specs["storage"].append(f"{val}TB")
            specs["storage"].append(f"{val}TO")
            
    # Détecter RAM si mentionnée séparément ou combinée
    ram_matches = re.findall(r'(\d+)\s*(?:GB\s*RAM|GO\s*RAM|RAM)', normalized_name)
    for m in ram_matches:
        specs["ram"].append(f"{m}GB")
        specs["ram"].append(f"{m}GO")
        
    # Connectivité
    if "WIFI" in normalized_name or "WI-FI" in normalized_name:
        specs["connectivity"].append("wifi")
        specs["connectivity"].append("wi-fi")
    if "5G" in normalized_name:
        specs["connectivity"].append("5g")
    elif "4G" in normalized_name or "LTE" in normalized_name:
        specs["connectivity"].append("4g")
        specs["connectivity"].append("lte")
        
    # Modèle (enlever specs pour avoir le tronc commun)
    model_part = product_name
    # Supprimer les mentions de RAM/Stockage/Connectivité
    model_part = re.sub(r'\b\d+\s*(?:GB|GO|TB|TO|RAM)\b', '', model_part, flags=re.IGNORECASE)
    model_part = re.sub(r'\b(?:WIFI|WI-FI|5G|4G|LTE)\b', '', model_part, flags=re.IGNORECASE)
    model_part = re.sub(r'\s+', ' ', model_part).strip()
    
    specs["model"] = [model_part]
    
    return specs


def search_duckduckgo(query: str) -> List[Dict[str, str]]:
    """Effectue une recherche sur DuckDuckGo HTML et extrait les titres et snippets."""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    results = []
    
    try:
        response = requests.get(url, params={"q": query}, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        result_divs = soup.find_all("div", class_="result")
        
        for div in result_divs:
            title_elem = div.find("a", class_="result__url")
            snippet_elem = div.find("a", class_="result__snippet")
            
            if title_elem:
                title = title_elem.text.strip()
                snippet = snippet_elem.text.strip() if snippet_elem else ""
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": title_elem.get("href", "")
                })
    except Exception as e:
        print(f"  {YELLOW}⚠ Erreur lors de la recherche DuckDuckGo : {e}{RESET}")
        
    return results


def check_existence_online(product_name: str, color: Optional[str], category: str) -> Tuple[bool, List[str]]:
    """Vérifie si le produit existe en ligne en analysant les résultats de recherche et le contenu des pages."""
    parsed = parse_specs_from_text(product_name)
    model_query = parsed["model"][0]
    
    print(f"🔍 Analyse du produit : {BOLD}{model_query}{RESET}")
    print(f"   Stockage cible    : {parsed['storage'][:2] if parsed['storage'] else 'Non spécifié'}")
    print(f"   RAM cible         : {parsed['ram'][:2] if parsed['ram'] else 'Non spécifiée'}")
    print(f"   Connectivité cible: {parsed['connectivity'][:2] if parsed['connectivity'] else 'Non spécifiée'}")
    if color:
        print(f"   Coloris cible     : {color} (mots-clés: {get_color_terms(color)})")
        
    # Lancer la recherche web
    search_query = f'"{model_query}"'
    if parsed["connectivity"]:
        search_query += f' {parsed["connectivity"][0]}'
    if parsed["storage"]:
        search_query += f' "{parsed["storage"][0]}"'
        
    print(f"📡 Lancement de la requête web : {CYAN}{search_query}{RESET}")
    search_results = search_duckduckgo(search_query)
    
    # Si aucun résultat avec stockage, essayer plus large
    if not search_results:
        search_query_broad = f'"{model_query}"'
        if parsed["connectivity"]:
            search_query_broad += f' {parsed["connectivity"][0]}'
        print(f"📡 Aucun résultat avec stockage. Essai élargi : {CYAN}{search_query_broad}{RESET}")
        search_results = search_duckduckgo(search_query_broad)
        
    if not search_results:
        return False, ["Aucun résultat trouvé sur Internet pour ce produit."]
        
    # Analyse de la véracité
    model_exists = False
    has_target_storage = False
    has_target_connectivity = True if not parsed["connectivity"] else False
    has_target_color = True if not color else False
    
    # Structure pour accumuler les specs découvertes
    discovered_specs = {
        "weights": [],
        "colors": [],
        "ram": [],
        "storage": []
    }
    
    # Normalisation du modèle pour regex flexible
    model_norm = normalize_string(model_query)
    model_regex_pattern = r'\b' + r'\s*'.join(re.escape(word) for word in model_norm.split()) + r'\b'
    model_regex = re.compile(model_regex_pattern, re.IGNORECASE)
    
    print("\n   --- Détails de l'analyse des résultats ---")
    
    # 1. Analyser les snippets des 8 premiers résultats
    found_variants = []
    for idx, res in enumerate(search_results[:8]):
        text_to_scan = normalize_string(res["title"] + " " + res["snippet"])
        
        # Vérification de l'existence du modèle
        if model_regex.search(text_to_scan):
            is_different_variant = False
            for variant_suffix in ["pro", "kids", "active", "plus", "ultra", "max"]:
                if variant_suffix in text_to_scan and variant_suffix not in model_norm:
                    is_different_variant = True
                    if variant_suffix == "pro":
                        found_variants.append(f"{model_query} Pro")
                    elif variant_suffix == "kids":
                        found_variants.append(f"{model_query} Kids")
            
            if is_different_variant:
                continue
                
            model_exists = True
            
            # Extraire les specs du snippet
            specs = extract_specifications_from_text(res["title"] + " " + res["snippet"])
            discovered_specs["weights"].extend(specs["weights"])
            discovered_specs["colors"].extend(specs["colors"])
            discovered_specs["ram"].extend(specs["ram"])
            discovered_specs["storage"].extend(specs["storage"])

    # 2. Téléchargement et analyse approfondie des pages des 3 premiers résultats
    pages_analyzed = 0
    for idx, res in enumerate(search_results[:3]):
        url = res["url"]
        if not url:
            continue
        print(f"   📥 Téléchargement et scan approfondi de : {BLUE}{url[:70]}...{RESET}")
        page_text = fetch_url_content(url)
        if page_text:
            specs = extract_specifications_from_text(page_text)
            discovered_specs["weights"].extend(specs["weights"])
            discovered_specs["colors"].extend(specs["colors"])
            discovered_specs["ram"].extend(specs["ram"])
            discovered_specs["storage"].extend(specs["storage"])
            pages_analyzed += 1

    # Dédoublonner
    for k in discovered_specs:
        discovered_specs[k] = sorted(list(set(discovered_specs[k])))
        
    print(f"\n📊 Spécifications découvertes en ligne ({pages_analyzed} page(s) web analysée(s)) :")
    print(f"   Poids détectés : {discovered_specs['weights'] if discovered_specs['weights'] else 'Aucun'}")
    print(f"   Coloris        : {discovered_specs['colors'] if discovered_specs['colors'] else 'Aucun'}")
    print(f"   RAM            : {discovered_specs['ram'] if discovered_specs['ram'] else 'Aucune'}")
    print(f"   Stockage       : {discovered_specs['storage'] if discovered_specs['storage'] else 'Aucun'}")
    print()

    if not model_exists:
        if found_variants:
            unique_variants = sorted(list(set(found_variants)))
            return False, [
                f"Le modèle de base '{model_query}' semble introuvable en ligne.",
                f"Cependant, des variantes existent : {', '.join(unique_variants)}."
            ]
        return False, [f"Le modèle de base '{model_query}' semble introuvable ou mal orthographié."]
        
    # Vérification de la connectivité exacte
    if parsed["connectivity"]:
        for res in search_results[:8]:
            text_to_scan = normalize_string(res["title"] + " " + res["snippet"])
            if any(conn in text_to_scan for conn in parsed["connectivity"]):
                has_target_connectivity = True
                break

    # Vérification du stockage
    if parsed["storage"]:
        for st in parsed["storage"]:
            st_norm = st.upper().replace(" ", "")
            if any(st_norm == ds.upper() for ds in discovered_specs["storage"]):
                has_target_storage = True
                break
                
    # Vérification de la couleur
    if color:
        color_terms = get_color_terms(color)
        for term in color_terms:
            if any(term.lower() == dc.lower() for dc in discovered_specs["colors"]):
                has_target_color = True
                break

    warnings = []
    
    # Vérification de la configuration de stockage exacte
    if parsed["storage"] and not has_target_storage:
        warn = f"La configuration de stockage demandée ({parsed['storage'][0]}) n'est pas confirmée en ligne."
        if discovered_specs["storage"]:
            warn += f" Les stockages officiels trouvés pour le modèle '{model_query}' standard sont : {', '.join(discovered_specs['storage'])}."
        warnings.append(warn)
        
    # Vérification de la connectivité exacte
    if parsed["connectivity"] and not has_target_connectivity:
        warnings.append(f"La connectivité spécifiée ({parsed['connectivity'][0]}) n'est pas confirmée pour ce modèle.")
        
    # Vérification des coloris
    if color and not has_target_color:
        warnings.append(f"Le coloris demandé '{color}' n'a pas pu être validé en ligne pour ce modèle.")
        
    if warnings:
        return False, warnings
        
    return True, []


def main():
    parser = argparse.ArgumentParser(
        description="Vérifie l'existence en ligne d'un produit et de sa configuration."
    )
    parser.add_argument("--product", "-p", required=True, help="Nom complet du produit (ex: Blackview Tab 12 WiFi 128GB)")
    parser.add_argument("--color", "-c", default=None, help="Coloris du produit (ex: Gris Lunaire)")
    parser.add_argument("--category", "-cat", default="smartphone", help="Catégorie (smartphone, tablet, etc.)")
    args = parser.parse_args()
    
    success, errors = check_existence_online(args.product, args.color, args.category)
    
    print("\n" + "="*70)
    if success:
        print(f"  {GREEN}{BOLD}✅ VÉRACITÉ CONFIRMÉE{RESET} : Le produit et sa configuration existent en ligne.")
        print("="*70 + "\n")
        sys.exit(0)
    else:
        print(f"  {RED}{BOLD}❌ ERREUR DE VÉRACITÉ / INCOHÉRENCE DÉTECTÉE{RESET}")
        for err in errors:
            print(f"    - {RED}{err}{RESET}")
        print("="*70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
