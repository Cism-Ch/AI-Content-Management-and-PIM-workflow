#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outil d'auto-remédiation SEO pour My-eStore.
Scinde automatiquement les phrases de plus de 18 mots dans les descriptions longues.
"""

import os
import sys
import json
import re
import argparse

def split_sentence(sentence):
    """Scinde une phrase longue en deux à un point logique (virgule ou conjonction)."""
    words = sentence.strip().split()
    if len(words) <= 18:
        return [sentence]
    
    # Recherche d'un point de césure dans la zone médiane (index 6 à 13)
    split_indices = []
    for idx, word in enumerate(words):
        if 6 <= idx <= 13:
            clean_word = word.lower().strip(",.;!?")
            if word.endswith(",") or clean_word in ["et", "mais", "car", "donc", "ainsi", "alors", "puis"]:
                split_indices.append(idx)
                
    if split_indices:
        # Prendre l'indice le plus proche du milieu
        middle = len(words) // 2
        best_idx = min(split_indices, key=lambda x: abs(x - middle))
        
        part1 = words[:best_idx+1]
        part2 = words[best_idx+1:]
        
        # Nettoyer la fin de la première partie
        s1 = " ".join(part1).strip()
        if s1.endswith(","):
            s1 = s1[:-1]
        if not s1.endswith((".", "!", "?")):
            s1 += "."
            
        # Nettoyer et capitaliser la deuxième partie
        s2 = " ".join(part2).strip()
        if s2:
            # Enlever la conjonction en début de deuxième phrase pour le style
            first_word = part2[0].lower().strip(",.;!?")
            if first_word in ["et", "mais", "car", "donc", "ainsi", "alors", "puis"]:
                part2 = part2[1:]
                s2 = " ".join(part2).strip()
            if s2:
                s2 = s2[0].upper() + s2[1:]
                if not s2.endswith((".", "!", "?")):
                    s2 += "."
                return [s1, s2]
                
    # Fallback si aucun séparateur trouvé : couper bêtement au milieu
    middle = len(words) // 2
    s1 = " ".join(words[:middle]).strip()
    if not s1.endswith((".", "!", "?")):
        s1 += "."
    s2 = " ".join(words[middle:]).strip()
    if s2:
        s2 = s2[0].upper() + s2[1:]
        if not s2.endswith((".", "!", "?")):
            s2 += "."
        return [s1, s2]
    return [s1]

def process_paragraph(paragraph):
    """Découpe un paragraphe en phrases, applique le découpage si nécessaire et recompose."""
    if not paragraph:
        return ""
    
    # Séparer les phrases (détection simple de la ponctuation forte)
    raw_sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
    
    final_sentences = []
    for s in raw_sentences:
        if not s.strip():
            continue
        # Récursivement scinder les phrases tant qu'elles dépassent 18 mots
        to_process = [s]
        processed = []
        while to_process:
            current = to_process.pop(0)
            parts = split_sentence(current)
            if len(parts) == 1:
                processed.append(parts[0])
            else:
                # Si scindée, on remet les parties pour vérification de longueur
                to_process = parts + to_process
        final_sentences.extend(processed)
        
    return " ".join(final_sentences)

def fix_json_file(file_path):
    """Parcourt et corrige le JSON en place."""
    if not os.path.exists(file_path):
        print(f"[-] Fichier introuvable : {file_path}")
        return False
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    modified = False
    
    # 1. Paragraphe d'introduction
    long_desc = data.get("long_description", {})
    intro = long_desc.get("intro_paragraph", "")
    if intro:
        fixed_intro = process_paragraph(intro)
        if fixed_intro != intro:
            long_desc["intro_paragraph"] = fixed_intro
            modified = True
            
    # 2. Sections de description longue
    for section in long_desc.get("sections", []):
        paragraphs = section.get("paragraphs", [])
        for idx, p in enumerate(paragraphs):
            fixed_p = process_paragraph(p)
            if fixed_p != p:
                paragraphs[idx] = fixed_p
                modified = True
                
    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[+] {file_path} corrige avec succes.")
    else:
        print(f"[INFO] {file_path} respecte deja les limites de phrase.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Auto-correcteur de phrases longues dans le JSON.")
    parser.add_argument("--input", required=True, help="Chemin vers le fichier pack-data-[modele].json")
    args = parser.parse_args()
    fix_json_file(args.input)

if __name__ == "__main__":
    main()
