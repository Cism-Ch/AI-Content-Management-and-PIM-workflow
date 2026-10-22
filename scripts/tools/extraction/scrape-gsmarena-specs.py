#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de scraping amélioré des spécifications techniques depuis GSMArena.

Ce script scrape les spécifications et les transforme en catégories Template.

Usage:
    python scrape-gsmarena-specs.py <url_gsmarena> [--output <chemin>]
    
Exemple:
    python scrape-gsmarena-specs.py https://www.gsmarena.com/huawei_mate_70-13519.php
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[ERROR] Modules requis manquants")
    print("   Installez les dépendances avec: pip install requests beautifulsoup4")
    sys.exit(1)


# ==============================================================================
# Configuration: Mapping GSMArena → Template
# ==============================================================================

# Mapping des catégories
CATEGORY_MAPPING = {
    "Network": "Connectivité",
    "Launch": "Design & Physique",
    "Body": "Écran",
    "Display": "Écran",
    "Platform": "Performances",
    "Memory": "Performances",
    "Main Camera": "Photo & Vidéo",
    "Selfie camera": "Photo & Vidéo",
    "Sound": "Connectivité",
    "Comms": "Connectivité",
    "Features": "Système & Infos",
    "Battery": "Batterie & Charge",
    "Misc": "Système & Infos"
}

# Mapping détaillé des champs: (Template Category, Template Field) → (GS Category, GS Field)
FIELD_MAPPING = {
    # Design & Physique
    ("Design & Physique", "Dimensions"): ("Body", "Dimensions"),
    ("Design & Physique", "Poids"): ("Body", "Weight"),
    ("Design & Physique", "Matériaux"): ("Body", "Build"),
    ("Design & Physique", "Étanchéité"): ("Body", ""),  # Empty key for IP rating
    ("Design & Physique", "Coloris"): ("Misc", "Colors"),
    
    # Écran
    ("Écran", "Taille"): ("Display", "Size"),
    ("Écran", "Technologie"): ("Display", "Type"),
    ("Écran", "Définition"): ("Display", "Resolution"),
    ("Écran", "Protection"): ("Body", "Protection"),  # Sometimes in Body
    ("Écran", "Rafraîchissement"): ("Display", "Type"),  # Parse from Type
    ("Écran", "Luminosité"): ("Display", "Type"),  # Parse from Type
    
    # Performances
    ("Performances", "Processeur (SoC)"): ("Platform", "Chipset"),
    ("Performances", "CPU"): ("Platform", "CPU"),
    ("Performances", "GPU"): ("Platform", "GPU"),
    ("Performances", "Mémoire vive (RAM)"): ("Memory", "Internal"),
    ("Performances", "Stockage (ROM)"): ("Memory", "Internal"),
    ("Performances", "Extension"): ("Memory", "Card slot"),
    
    # Photo & Vidéo
    ("Photo & Vidéo", "Capteur Principal"): ("Main Camera", "Triple"),
    ("Photo & Vidéo", "Capteur Principal (fallback)"): ("Main Camera", "Quad"),
    ("Photo & Vidéo", "Selfie (Avant)"): ("Selfie camera", "Single"),
    ("Photo & Vidéo", "Selfie (Avant) (fallback)"): ("Selfie camera", "Dual"),
    ("Photo & Vidéo", "Vidéo"): ("Main Camera", "Video"),
    
    # Batterie & Charge
    ("Batterie & Charge", "Capacité"): ("Battery", "Type"),
    ("Batterie & Charge", "Charge Filaire"): ("Battery", "Charging"),
    
    # Connectivité
    ("Connectivité", "Réseaux"): ("Network", "Technology"),
    ("Connectivité", "Wi-Fi"): ("Comms", "WLAN"),
    ("Connectivité", "Bluetooth"): ("Comms", "Bluetooth"),
    ("Connectivité", "NFC"): ("Comms", "NFC"),
    ("Connectivité", "USB"): ("Comms", "USB"),
    ("Connectivité", "SIM"): ("Launch", "SIM"),
    ("Connectivité", "Logiciel"): ("Platform", "OS"),
    ("Connectivité", "3.5mm jack"): ("Sound", "3.5mm jack"),
    ("Connectivité", "Radio"): ("Comms", "Radio"),
    
    # Système & Infos
    ("Système & Infos", "Sensors"): ("Features", "Sensors"),
    ("Système & Infos", "Price"): ("Misc", "Price"),
    ("Système & Infos", "Models"): ("Misc", "Models"),
}


# ==============================================================================
# Fonctions utilitaires
# ==============================================================================

def extract_product_info_from_url(url: str) -> Dict[str, str]:
    """Extrait les informations du produit depuis l'URL GSMArena."""
    match = re.search(r'/([^/]+)-(\d+)\.php$', url)
    if not match:
        raise ValueError(f"URL GSMArena invalide: {url}")
    
    slug = match.group(1)
    product_id = match.group(2)
    
    return {
        'slug': slug,
        'product_id': product_id
    }


def parse_product_name(product_name: str) -> Tuple[str, str]:
    """Parse le nom du produit pour extraire marque et modèle."""
    # Ex: "Huawei Mate 70" → ("Huawei", "Mate 70")
    # Ex: "Samsung Galaxy S24 Ultra" → ("Samsung", "Galaxy S24 Ultra")
    # Ex: "Apple iPhone 15 Pro" → ("Apple", "iPhone 15 Pro")
    
    parts = product_name.split(None, 1)  # Split sur le premier espace
    if len(parts) >= 2:
        brand = parts[0]
        model = parts[1]
    else:
        brand = product_name
        model = ""
    
    return brand, model


def extract_series_from_url(url: str, brand: str) -> Optional[str]:
    """Extrait la série depuis l'URL."""
    try:
        info = extract_product_info_from_url(url)
        slug = info['slug'].lower()
        brand_lower = brand.lower()
        
        # Enlever la marque du slug
        if slug.startswith(f"{brand_lower}_"):
            series = slug[len(f"{brand_lower}_"):]
        elif slug.startswith(brand_lower):
            series = slug[len(brand_lower):].lstrip('_')
        else:
            series = slug
        
        # Nettoyer: remplacer underscores par tirets
        series = series.replace('_', '-')
        
        # Conserver la structure: mate-70, nova-13, pura-70, etc.
        # Ne pas enlever les nombres qui font partie du nom
        
        return series if series else None
    except:
        return None


def extract_series_from_breadcrumb(soup) -> Optional[str]:
    """Extrait la série depuis le breadcrumb GSMArena."""
    try:
        breadcrumb = soup.find('div', class_='review-header')
        if not breadcrumb:
            return None
        
        # Chercher les liens dans le breadcrumb
        links = breadcrumb.find_all('a')
        for link in links:
            text = link.get_text(strip=True).lower()
            href = link.get('href', '').lower()
            
            # Chercher "series" dans le texte ou l'URL
            if 'series' in text:
                # "Mate 70 series" → "mate-70"
                series = text.replace(' series', '').replace(' ', '-')
                return series
            
            # Ou chercher dans l'URL
            match = re.search(r'([a-z]+-[\w-]+)-phones', href)
            if match:
                return match.group(1)
        
        return None
    except:
        return None


def extract_series_from_model(model: str, brand: str) -> Optional[str]:
    """Extrait la série depuis le nom du modèle."""
    try:
        model_lower = model.lower()
        brand_lower = brand.lower()
        
        # Enlever la marque
        if model_lower.startswith(brand_lower):
            model_clean = model_lower[len(brand_lower):].strip()
        else:
            model_clean = model_lower
        
        # Extraire la série (première partie significative)
        # Ex: "Mate 70 Pro 5G" → "mate-70"
        match = re.search(r'(mate|nova|pura|matepad|galaxy|iphone|pixel)[\s-]*(\d+|[\w]+)', model_clean)
        if match:
            series_base = match.group(1)
            series_number = match.group(2)
            return f"{series_base}-{series_number}"
        
        # Si pas de numéro, prendre la première partie
        parts = model_clean.split()
        if parts:
            return parts[0].lower()
        
        return None
    except:
        return None


def determine_series(url: str, soup, product_name: str) -> str:
    """Détermine la série de manière dynamique."""
    _, model = parse_product_name(product_name)
    brand, _ = parse_product_name(product_name)
    
    # Méthode 1: Depuis l'URL
    series = extract_series_from_url(url, brand)
    if series and series != "other":
        return series
    
    # Méthode 2: Depuis le breadcrumb
    series = extract_series_from_breadcrumb(soup)
    if series:
        return series
    
    # Méthode 3: Depuis le modèle
    series = extract_series_from_model(model, brand)
    if series:
        return series
    
    return "other"


# ==============================================================================
# Fonctions de parsing
# ==============================================================================

def parse_ip_rating(text: str) -> Optional[str]:
    """Parse le rating IP (étanchéité) depuis le texte SIM."""
    if not text:
        return None
    
    match = re.search(r'IP\d+[X\d]*', text, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    
    # Chercher d'autres mentions d'étanchéité
    if 'water resistant' in text.lower():
        return "Water resistant"
    if 'dust' in text.lower() and 'water' in text.lower():
        return "Dust/Water resistant"
    
    return None


def parse_screen_size(text: str) -> Optional[str]:
    """Parse la taille de l'écran en pouces."""
    if not text:
        return None
    
    match = re.search(r'(\d+\.?\d*)\s*inches?', text)
    if match:
        return f"{match.group(1)} inches"
    
    return None


def parse_refresh_rate(text: str) -> Optional[str]:
    """Parse le taux de rafraîchissement depuis le type d'écran."""
    if not text:
        return None
    
    match = re.search(r'(\d+)\s*Hz', text)
    if match:
        return f"{match.group(1)} Hz"
    
    return None


def parse_brightness(text: str) -> Optional[str]:
    """Parse la luminosité maximale (nits)."""
    if not text:
        return None
    
    match = re.search(r'(\d+)\s*nits?', text)
    if match:
        return f"{match.group(1)} nits"
    
    return None


def parse_ram_storage(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse RAM et Stockage depuis le champ Internal."""
    if not text:
        return None, None
    
    # Ex: "256GB 12GB RAM" → RAM: "12 Go", Storage: "256 Go"
    # Ex: "512GB 16GB RAM, 1TB 16GB RAM" → Prendre le premier
    
    parts = text.split(',')[0]  # Prendre la première config
    
    ram_match = re.search(r'(\d+)\s*GB\s+RAM', parts)
    ram = f"{ram_match.group(1)} Go" if ram_match else None
    
    storage_match = re.search(r'(\d+)\s*GB', parts)
    storage = f"{storage_match.group(1)} Go" if storage_match else None
    
    # Si on trouve TB
    tb_match = re.search(r'(\d+)\s*TB', text)
    if tb_match:
        storage = f"{tb_match.group(1)} To"
    
    return ram, storage


def parse_camera_info(text: str) -> Dict[str, str]:
    """Parse les informations de la caméra."""
    if not text:
        return {}
    
    cameras = {}
    
    # Chercher le capteur principal (premier MP)
    main_match = re.search(r'(\d+)\s*MP', text)
    if main_match:
        cameras['main'] = f"{main_match.group(1)} MP"
    
    # Chercher l'ouverture (f/...)
    aperture_match = re.search(r'f/[\d\.]+', text)
    if aperture_match:
        cameras['aperture'] = aperture_match.group(0)
    
    return cameras


def parse_battery_capacity(text: str) -> Optional[str]:
    """Parse la capacité de la batterie en mAh."""
    if not text:
        return None
    
    match = re.search(r'(\d+)\s*mAh', text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} mAh"
    
    return None


def parse_charging_power(text: str) -> Dict[str, str]:
    """Parse la puissance de charge (filaire et sans fil)."""
    if not text:
        return {}
    
    charging = {}
    
    # Charge filaire
    wired_match = re.search(r'(\d+)\s*W(?:\s+wired)?', text, re.IGNORECASE)
    if wired_match:
        charging['wired'] = f"{wired_match.group(1)}W"
    
    # Charge sans fil
    wireless_match = re.search(r'(\d+)\s*W\s+wireless', text, re.IGNORECASE)
    if wireless_match:
        charging['wireless'] = f"{wireless_match.group(1)}W"
    
    return charging


# ==============================================================================
# Fonction principale de scraping
# ==============================================================================

def scrape_gsmarena_specs(url: str) -> Dict[str, Any]:
    """Scrape les spécifications depuis une page GSMArena."""
    
    print(f"[SCRAPING] Récupération de la page: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Erreur lors de la récupération de la page: {e}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraire le nom du produit
    product_name_elem = soup.find('h1', class_='specs-phone-name-title')
    product_name = product_name_elem.text.strip() if product_name_elem else "Unknown"
    
    # Extraire marque et modèle
    brand, model = parse_product_name(product_name)
    
    # Déterminer la série
    series = determine_series(url, soup, product_name)
    
    print(f"   [PRODUCT] Produit: {product_name}")
    print(f"   [BRAND] Marque: {brand}, Serie: {series}")
    
    # Structure de base
    specs = {
        'metadata': {
            'product_name': product_name,
            'brand': brand,
            'model': model,
            'series': series,
            'source_url': url,
            'scraped_at': datetime.now().isoformat(),
            'source': 'GSMArena'
        },
        'specifications': {
            'Design & Physique': {},
            'Écran': {},
            'Performances': {},
            'Photo & Vidéo': {},
            'Batterie & Charge': {},
            'Connectivité': {},
            'Système & Infos': {}
        }
    }
    
    # Scraper toutes les tables de specs
    # GSMArena structure: th headers and tables are in order
    all_th = soup.find_all('th')
    spec_tables = soup.find_all('table')
    
    raw_specs = {}
    
    # Pair th headers with tables by index
    for i, th in enumerate(all_th):
        category = th.text.strip()
        
        # Get corresponding table
        if i < len(spec_tables):
            table = spec_tables[i]
            
            if category not in raw_specs:
                raw_specs[category] = {}
            
            # Parcourir les lignes
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    spec_name = cells[0].text.strip()
                    spec_value = cells[1].text.strip()
                    
                    # Nettoyer
                    spec_value = re.sub(r'\s+', ' ', spec_value)
                    
                    # Garder les champs même avec clé vide si valeur présente
                    if spec_value:
                        raw_specs[category][spec_name] = spec_value
    

    
    # Transformer les specs vers les catégories Template
    transform_specs(raw_specs, specs['specifications'])
    
    return specs


def transform_specs(raw_specs: Dict, template_specs: Dict):
    """Transforme les specs GSMArena brutes en catégories Template."""
    
    # Parcourir le mapping des champs
    for (template_cat, template_field), (gs_cat, gs_field) in FIELD_MAPPING.items():
        if gs_cat in raw_specs:
            # Gestion des clés vides (ex: pour Étanchéité)
            if gs_field == "":
                # Chercher dans toutes les clés de la catégorie
                for key, value in raw_specs[gs_cat].items():
                    if not key and value:  # Clé vide mais valeur présente
                        processed_value = process_field_value(template_cat, template_field, value)
                        if processed_value:
                            template_specs[template_cat][template_field] = processed_value
                        break
            else:
                value = raw_specs[gs_cat].get(gs_field)
                
                # Gestion des fallbacks
                if not value and '(fallback)' in template_field:
                    # Essayer le fallback
                    fallback_field = template_field.split(' (fallback)')[0]
                    for (tc, tf), (gc, gf) in FIELD_MAPPING.items():
                        if tc == template_cat and tf == fallback_field and gc == gs_cat:
                            value = raw_specs[gc].get(gf)
                            break
                
                if value:
                    # Post-traitement selon le type de champ
                    processed_value = process_field_value(template_cat, template_field, value)
                    if processed_value:
                        # Enlever le suffixe (fallback) si présent
                        clean_field = template_field.replace(' (fallback)', '')
                        template_specs[template_cat][clean_field] = processed_value


def process_field_value(category: str, field: str, value: str) -> Optional[str]:
    """Post-traite les valeurs selon le type de champ."""
    
    if not value or value.lower() in ['no', 'n/a', '', '-']:
        return None
    
    # Design & Physique
    if field == "Étanchéité":
        return parse_ip_rating(value) or value
    
    # Écran
    elif field == "Taille":
        return parse_screen_size(value) or value
    elif field == "Rafraîchissement":
        return parse_refresh_rate(value)
    elif field == "Luminosité":
        return parse_brightness(value)
    
    # Performances
    elif field in ["Mémoire vive (RAM)", "Stockage (ROM)"]:
        ram, storage = parse_ram_storage(value)
        if field == "Mémoire vive (RAM)":
            return ram
        else:
            return storage
    elif field == "Extension":
        if 'no' in value.lower() or value.lower() == 'no':
            return "Non"
        elif 'microsd' in value.lower() or 'yes' in value.lower():
            return "Oui (microSD)"
        return value
    
    # Photo & Vidéo
    elif field == "Capteur Principal":
        cam_info = parse_camera_info(value)
        if cam_info:
            result = cam_info.get('main', '')
            if 'aperture' in cam_info:
                result += f" ({cam_info['aperture']})"
            return result if result else value
        return value
    elif field == "Selfie (Avant)":
        cam_info = parse_camera_info(value)
        if cam_info:
            return cam_info.get('main', value)
        return value
    
    # Batterie
    elif field == "Capacité":
        return parse_battery_capacity(value) or value
    elif field == "Charge Filaire":
        charging = parse_charging_power(value)
        return charging.get('wired')
    
    # Par défaut, retourner la valeur telle quelle
    return value


# ==============================================================================
# Extraction des specs clés
# ==============================================================================

def extract_key_specs(specs_data: Dict[str, Any]) -> Dict[str, str]:
    """Extrait les spécifications clés pour référence rapide."""
    
    template_specs = specs_data.get('specifications', {})
    key_specs = {}
    
    # Batterie
    battery = template_specs.get('Batterie & Charge', {})
    cap = battery.get('Capacité', '')
    match = re.search(r'(\d+)', cap)
    if match:
        key_specs['battery_mah'] = match.group(1)
    
    # RAM
    perf = template_specs.get('Performances', {})
    ram = perf.get('Mémoire vive (RAM)', '')
    match = re.search(r'(\d+)', ram)
    if match:
        key_specs['ram_gb'] = match.group(1)
    
    # Stockage
    storage = perf.get('Stockage (ROM)', '')
    match = re.search(r'(\d+)', storage)
    if match:
        key_specs['storage_gb'] = match.group(1)
    
    # Processeur
    proc = perf.get('Processeur (SoC)', '')
    if proc:
        key_specs['processor'] = proc
    
    # Écran
    screen = template_specs.get('Écran', {})
    size = screen.get('Taille', '')
    match = re.search(r'(\d+\.?\d*)', size)
    if match:
        key_specs['screen_size'] = match.group(1)
    
    res = screen.get('Définition', '')
    if res:
        key_specs['screen_resolution'] = res
    
    # Logiciel
    conn = template_specs.get('Connectivité', {})
    os = conn.get('Logiciel', '')
    if os:
        key_specs['os'] = os
    
    return key_specs


# ==============================================================================
# Sauvegarde
# ==============================================================================

def save_specs_json(specs_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Sauvegarde les spécifications dans un fichier JSON."""
    
    # Ajouter les specs clés
    specs_data['key_specs'] = extract_key_specs(specs_data)
    
    if output_path:
        file_path = Path(output_path)
    else:
        # Générer le chemin automatiquement
        metadata = specs_data.get('metadata', {})
        brand = metadata.get('brand', 'unknown').lower()
        series = metadata.get('series', 'other').lower()
        model = metadata.get('model', 'unknown').lower().replace(' ', '-')
        
        # Créer le répertoire
        base_dir = Path('specs-data')
        brand_dir = base_dir / brand / series
        brand_dir.mkdir(parents=True, exist_ok=True)
        
        # Nom du fichier
        filename = f"{brand}-{model}-specs-data.json"
        file_path = brand_dir / filename
    
    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(specs_data, f, ensure_ascii=False, indent=2)
    
    return str(file_path)


# ==============================================================================
# Point d'entrée
# ==============================================================================

def main():
    """Point d'entrée principal."""
    
    if len(sys.argv) < 2:
        print("Usage: python scrape-gsmarena-specs.py <url_gsmarena> [--output <chemin>]")
        print("")
        print("Exemples:")
        print("  python scrape-gsmarena-specs.py https://www.gsmarena.com/huawei_mate_70-13519.php")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = None
    
    if '--output' in sys.argv:
        output_idx = sys.argv.index('--output')
        if len(sys.argv) > output_idx + 1:
            output_path = sys.argv[output_idx + 1]
    
    print(">> Démarrage du scraping GSMArena")
    print("=" * 80)
    
    try:
        specs_data = scrape_gsmarena_specs(url)
        saved_path = save_specs_json(specs_data, output_path)
        
        print("")
        print("[SUCCESS] Specifications recuperees et sauvegardees")
        print(f"   [FILE] Fichier: {saved_path}")
        print(f"   [PRODUCT] Produit: {specs_data['metadata']['product_name']}")
        print(f"   [SERIES] Serie: {specs_data['metadata']['series']}")
        print("")
        print("[KEY SPECS] Specifications cles extraites:")
        for key, value in specs_data['key_specs'].items():
            print(f"   - {key}: {value}")
        
    except Exception as e:
        print(f"[ERROR] ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
