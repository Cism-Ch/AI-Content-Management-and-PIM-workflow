#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'Audit de Conformité des Coloris (V3.3).
Compare les dossiers réels dans products/blackview-all/ avec la liste certifiée des coloris officiels.
Détecte les dossiers aux coloris erronés (ex: argent/gris pour Zeno 10 5G au lieu de Noir/Bleu).
"""

import os
import sys
import json
import re
from pathlib import Path

BLACKVIEW_DIR = Path("products/blackview-all")

# Mapping des alias de couleur FR / EN
COLOR_ALIASES = {
    "black": "noir",
    "shadow black": "noir",
    "dark black": "noir",
    "blue": "bleu",
    "ice blue": "bleu",
    "sky blue": "bleu",
    "green": "vert",
    "forest green": "vert",
    "orange": "orange",
    "sunset orange": "orange",
    "silver": "argent",
    "gray": "gris",
    "grey": "gris",
    "space gray": "gris",
    "gold": "or",
    "pink": "rose",
    "purple": "violet",
    "yellow": "jaune",
    "khaki": "kaki",
    "white": "blanc",
    "beige": "beige"
}

def normalize_color(color_name: str) -> str:
    c = color_name.strip().lower()
    return COLOR_ALIASES.get(c, c)

def audit_colors():
    print(f"\n=======================================================")
    print(f"  AUDIT DE CONFORMITÉ DES COLORIS OFFICIELS (V3.3)")
    print(f"=======================================================\n")

    invalid_folders = []
    missing_variants = []

    # Charger les modèles uniques depuis product-data ou depuis les folders
    for pdir in sorted(BLACKVIEW_DIR.iterdir()):
        if not pdir.is_dir():
            continue

        json_files = list(pdir.glob("pack-data-*.json"))
        if not json_files:
            continue

        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)

        model = data.get("metadata", {}).get("target_model", "").strip()
        woo = data.get("woocommerce_csv", {})
        color_attr = woo.get("Attribute 1 value(s)", "").strip()
        
        # Extraire la couleur depuis le nom du dossier
        folder_color = pdir.name.split("-")[-1].lower()

        # Obtenir la liste certifiée des couleurs
        colors_obj = data.get("colors", {})
        official_colors_raw = colors_obj.get("standard", [])
        
        if not official_colors_raw:
            continue

        official_colors_norm = [normalize_color(c) for c in official_colors_raw]

        norm_folder_color = normalize_color(folder_color)
        norm_attr_color = normalize_color(color_attr)

        # Vérifier si la couleur du dossier est autorisée par la liste officielle
        if norm_folder_color not in official_colors_norm and norm_attr_color not in official_colors_norm:
            invalid_folders.append({
                "folder": pdir.name,
                "model": model,
                "folder_color": folder_color,
                "attribute_color": color_attr,
                "official_allowed": official_colors_raw
            })

    print(f"Total Dossiers avec Coloris Erronés / Non-Officiels : {len(invalid_folders)}\n")
    for item in invalid_folders:
        print(f" ❌ {item['folder']:<40} | Modèle: {item['model']:<25} | Couleur Dossier: {item['folder_color']:<10} | Officiels Autorisés: {item['official_allowed']}")

    return invalid_folders

if __name__ == "__main__":
    audit_colors()
