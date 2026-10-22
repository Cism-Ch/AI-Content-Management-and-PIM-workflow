#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nettoie les anciens dossiers de variantes contenant '-n-a-' et re-duplique proprement les modèles parents certifiés concernés.
"""

import os
import shutil
import subprocess
import sys

base_dir = r"c:\Users\My-eStore-PC2\My-eStore-workspace\wordpress"
products_dir = os.path.join(base_dir, "products", "blackview-all")
duplicate_script = os.path.join(base_dir, "scripts", "tools", "product_data", "duplicate_single_parent.py")

# Modèles d'accessoires sans RAM/ROM déjà certifiés
models_to_reprocess = [
    "airbuds-12", "airbuds-13", "airbuds-20", "airbuds-200", "airbuds-30",
    "airbuds-300", "airbuds-60", "airbuds-7", "airbuds-8", "aura-bass-3",
    "bv-100", "bv-dcm5", "bv-dcm6-pro", "bv-dcm8", "bv-scm5", "bv-scm8",
    "dcm6", "fitbuds-h1"
]

print("=== NETTOYAGE DES DOSSIERS DE VARIANTES '-n-a-' ===")

# 1. Supprimer les anciens dossiers contenant '-n-a-'
for item in os.listdir(products_dir):
    item_path = os.path.join(products_dir, item)
    if os.path.isdir(item_path) and "-n-a-" in item:
        print(f"[-] Suppression de l'ancien dossier obsolète : {item}")
        shutil.rmtree(item_path, ignore_errors=True)

print("\n=== RE-DUPLICATION PROPRE DES MODÈLES SANS RAM/ROM ===")

# 2. Re-dupliquer proprement
for slug in models_to_reprocess:
    cmd = [sys.executable, duplicate_script, slug]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[OK] Re-duplication propre de {slug}")
    else:
        print(f"[!] Échec pour {slug}: {res.stderr[:200]}")

print("\n[OK] Nettoyage et re-duplication terminés avec succès !")
