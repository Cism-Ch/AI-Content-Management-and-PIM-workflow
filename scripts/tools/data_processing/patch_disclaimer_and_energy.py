#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_disclaimer_and_energy.py
Met à jour la classe énergétique (energy_rating) à "Non spécifiée (voir sur emballage constructeur)"
et le bloc d'avis de non-responsabilité (disclaimer) avec le texte officiel exact V3.4
sur l'ensemble des JSONs parents, JSONs déclinaisons et Templates.
"""

import os
import json
import sys

# Configurer UTF-8 sur Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OFFICIAL_DISCLAIMER = (
    "Avis de non-responsabilité (Spécifications) : Les caractéristiques techniques et les images de l'appareil "
    "sont fournies à titre purement indicatif et proviennent des données officielles des constructeurs et autres sources. "
    "Des variations peuvent survenir selon les lots de fabrication et les régions d'importation. "
    "Nous vous invitons à vérifier scrupuleusement la configuration exacte que vous avez sélectionnée "
    "dans vos options d'achat avant de valider définitivement votre commande."
)

NON_SPECIFIED_ENERGY = "Non spécifiée (voir sur emballage constructeur)"

def patch_json_file(file_path, is_appliance_override=False):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Erreur de lecture pour {file_path} : {e}")
        return False

    prod_type = data.get("product_type", "")
    is_appliance = prod_type == "appliance" or "appliance" in file_path.lower()
    
    # Mettre à jour energy_rating si non-électroménager
    if not is_appliance and not is_appliance_override:
        data["energy_rating"] = NON_SPECIFIED_ENERGY

    # Mettre à jour le disclaimer dans long_description.full_specs.footer
    ld = data.setdefault("long_description", {})
    fs = ld.setdefault("full_specs", {})
    ft = fs.setdefault("footer", {})
    ft["disclaimer"] = OFFICIAL_DISCLAIMER

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    return True

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    print("=======================================================")
    print("  MISE À JOUR DE LA CLASSE ÉNERGÉTIQUE & DISCLAIMER V3.4")
    print("=======================================================")

    # 1. Parents JSON
    p_dir = os.path.join(root_dir, "product-data", "blackview")
    parent_count = 0
    if os.path.exists(p_dir):
        for fname in os.listdir(p_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(p_dir, fname)
                if patch_json_file(fpath):
                    parent_count += 1
    print(f"[*] {parent_count} JSONs parents mis à jour.")

    # 2. Déclinaisons JSON
    b_dir = os.path.join(root_dir, "products", "blackview-all")
    variant_count = 0
    if os.path.exists(b_dir):
        for folder in os.listdir(b_dir):
            fpath = os.path.join(b_dir, folder)
            if os.path.isdir(fpath):
                for fname in os.listdir(fpath):
                    if fname.startswith("pack-data-") and fname.endswith(".json"):
                        vpath = os.path.join(fpath, fname)
                        if patch_json_file(vpath):
                            variant_count += 1
    print(f"[*] {variant_count} JSONs de déclinaisons mis à jour.")

    # 3. Templates JSON
    t_dir = os.path.join(root_dir, "Templates")
    template_count = 0
    if os.path.exists(t_dir):
        for fname in os.listdir(t_dir):
            if fname.endswith(".json"):
                tpath = os.path.join(t_dir, fname)
                if patch_json_file(tpath):
                    template_count += 1
    print(f"[*] {template_count} modèles de Templates JSON mis à jour.")

    print("=======================================================")
    print(f"  PAREMENT TERMINÉ V3.4")
    print("=======================================================")

if __name__ == "__main__":
    main()
