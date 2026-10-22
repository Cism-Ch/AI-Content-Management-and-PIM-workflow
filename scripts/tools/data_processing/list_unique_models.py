#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'identification des modèles uniques du catalogue Blackview.
Parcourt products/blackview-all/ et extrait tous les modèles uniques.
"""

import os
import json
import re
from pathlib import Path

BLACKVIEW_DIR = Path("products/blackview-all")

BLACKVIEW_MODELS_FALLBACK = [
    ("Blackview A53 Pro 64Go", "a53-pro-4go-64go-bleu"),
    ("Blackview AceBook 10 16Go/512Go", "acebook-10-16go-512go-gris"),
    ("Blackview AceBook 8 16Go/512Go", "acebook-8-16go-512go-gris"),
    ("Blackview Active 5 128Go", "active-5-8go-128go-noir"),
    ("Blackview Active 7 128Go", "active-7-8go-128go-noir"),
    ("Blackview AirBuds 12", "airbuds-12-blanc"),
    ("Blackview AirBuds 13", "airbuds-13-blanc"),
    ("Blackview AirBuds 20", "airbuds-20-blanc"),
    ("Blackview AirBuds 200", "airbuds-200-blanc"),
    ("Blackview AirBuds 30", "airbuds-30-blanc"),
    ("Blackview AirBuds 300", "airbuds-300-blanc"),
    ("Blackview AirBuds 60", "airbuds-60-blanc"),
    ("Blackview AirBuds 7", "airbuds-7-blanc"),
    ("Blackview AirBuds 8", "airbuds-8-blanc"),
    ("Blackview Aura Bass 3", "aura-bass-3-bleu"),
    ("Blackview BL7000 5G", "bl7000-5g-8go-256go-noir"),
    ("Blackview BV100 Smart Glasses", "bv-100-noir"),
    ("Blackview BV4800 Pro 128Go", "bv-4800-pro-4go-128go-noir"),
    ("Blackview BV7300 256Go", "bv-7300-6go-256go-noir"),
    ("Blackview Color 8", "bv-color-8-8go-128go-bleu"),
    ("Blackview DCM5", "bv-dcm5-gris"),
    ("Blackview DCM6 Pro", "bv-dcm6-pro-gris"),
    ("Blackview DCM8", "bv-dcm8-gris"),
    ("Blackview Fort 100", "bv-fort-100-8go-128go-noir"),
    ("Blackview Fort 200", "bv-fort-200-12go-128go-noir"),
    ("Blackview Link 1 Kids", "bv-link-1-kids-4go-64go-bleu"),
    ("Blackview Rock 2 5G", "bv-rock-2-8go-256go-jaune"),
    ("Blackview Rock 3", "bv-rock-3-8go-256go-noir"),
    ("Blackview SCM5", "bv-scm5-gris"),
    ("Blackview SCM8", "bv-scm8-gris"),
    ("Blackview Wave 10", "bv-wave-10-8go-128go-bleu"),
    ("Blackview Wave 10C", "bv-wave-10c-4go-128go-bleu"),
    ("Blackview Wave 2C", "bv-wave-2c-3go-32go-noir"),
    ("Blackview Wave 7C", "bv-wave-7c-4go-128go-bleu"),
    ("Blackview Xplorer X1 5G", "bv-xplorer-x1-12go-256go-noir"),
    ("Blackview Zeno 10 5G", "bv-zeno-10-6go-128go-bleu"),
    ("Blackview Zeno 5", "bv-zeno-5-8go-128go-bleu"),
    ("Blackview Color 6 128Go", "color-6-8go-128go-bleu"),
    ("Blackview Color 6 256Go", "color-6-8go-256go-bleu"),
    ("Blackview DCM6", "dcm6-noir"),
    ("Blackview FitBuds H1", "fitbuds-h1-blanc"),
    ("Blackview Fort 1", "fort-1-6go-128go-noir"),
    ("Blackview Fort 1 256Go", "fort-1-6go-256go-noir"),
    ("Blackview Hero 10", "hero-10-12go-256go-noir"),
    ("Blackview K1", "k1-blanc"),
    ("Blackview Link 8", "link-8-12go-256go-bleu"),
    ("Blackview Mega 1", "mega-1-12go-256go-bleu"),
    ("Blackview Mega 2", "mega-2-set-12go-256go-argent"),
    ("Blackview Mega 3", "mega-3-12go-256go-bleu"),
    ("Blackview MP100 Pro", "mp100-pro-16go-512go-noir"),
    ("Blackview MP20", "mp20-16go-512go-noir"),
    ("Blackview MP200 (Core i5)", "mp200-i5-16go-1to-noir"),
    ("Blackview MP200 (Core i9)", "mp200-i9-16go-1to-noir"),
    ("Blackview MP80", "mp80-16go-512go-noir"),
    ("Blackview R30 Pro", "r30-pro-gris"),
    ("Blackview SCM6", "scm6-gris"),
    ("Blackview Shark 6", "shark-6-4go-128go-bleu"),
    ("Blackview Shark 8", "shark-8-8go-128go-bleu"),
    ("Blackview Shark 9", "shark-9-8go-256go-bleu"),
    ("Blackview Tab 10 WiFi", "tab-10-wifi-8go-256go-bleu"),
    ("Blackview Tab 12 Pro", "tab-12-pro-8go-128go-argent"),
    ("Blackview Tab 20 Kids", "tab-20-kids-4go-64go-bleu"),
    ("Blackview Tab 30 WiFi", "tab-30-wifi-2go-64go-bleu"),
    ("Blackview Tab 60 Pro Kids", "tab-60-pro-kids-4go-128go-bleu"),
    ("Blackview Tab 60 Pro Set", "tab-60-pro-set-4go-128go-argent"),
    ("Blackview Tab 90 WiFi", "tab-90-wifi-4go-128go-bleu"),
    ("Blackview Tab Kids 3", "tab-kids-3-2go-32go-bleu"),
    ("Blackview W50", "w50-gris"),
    ("Blackview W50 Pro", "w50-pro-kaki"),
    ("Blackview W70 Pro", "w70-pro-argent"),
    ("Blackview W80 Pro", "w80-pro-kaki"),
    ("Blackview W90 Pro", "w90-pro-argent"),
    ("Blackview Wave 8", "wave-8-4go-128go-bleu"),
    ("Blackview Wave 9C", "wave-9c-4go-128go-bleu"),
    ("Blackview X20", "x20-argent"),
    ("Blackview Xplore 1 5G", "xplore-1-5g-8go-256go-noir"),
    ("Blackview Xplore 2 5G", "xplore-2-5g-12go-1to-beige"),
    ("Blackview Zeno 1", "zeno-1-6go-64go-noir")
]

def get_unique_models():
    unique_models = {}
    
    if BLACKVIEW_DIR.exists():
        for pdir in sorted(BLACKVIEW_DIR.iterdir()):
            if not pdir.is_dir():
                continue
            
            json_files = list(pdir.glob("pack-data-*.json"))
            if not json_files:
                continue
                
            json_path = json_files[0]
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                model_name = data.get("metadata", {}).get("target_model", "").strip()
                cat = data.get("woocommerce_csv", {}).get("Categories", "").strip()
                
                if not model_name:
                    folder = pdir.name
                    clean_folder = re.sub(r'-(noir|bleu|vert|orange|argent|gris|rose|jaune|kaki|violet|or|blanc|beige)$', '', folder, flags=re.I)
                    clean_folder = re.sub(r'-[0-9]+go-[0-9]+(go|to)$', '', clean_folder, flags=re.I)
                    model_name = clean_folder.replace('-', ' ').title()
                    
                if model_name not in unique_models:
                    unique_models[model_name] = {
                        "sample_folder": pdir.name,
                        "json_path": str(json_path),
                        "category": cat,
                        "variants_count": 1
                    }
                else:
                    unique_models[model_name]["variants_count"] += 1

            except Exception as e:
                pass
                
    if not unique_models:
        for m_name, sample_folder in BLACKVIEW_MODELS_FALLBACK:
            unique_models[m_name] = {
                "sample_folder": sample_folder,
                "json_path": "",
                "category": "High-Tech",
                "variants_count": 1
            }
            
    return unique_models

if __name__ == "__main__":
    models = get_unique_models()
    print(f"\n=======================================================")
    print(f"  IDENTIFICATION DES MODÈLES UNIQUES BLACKVIEW")
    print(f"  Total Modèles Uniques Trouvés : {len(models)}")
    print(f"=======================================================\n")
    
    for idx, (m_name, info) in enumerate(models.items(), 1):
        print(f" {idx:02d}. {m_name:<35} | Dossier: {info['sample_folder']:<30} | Variantes: {info['variants_count']}")
