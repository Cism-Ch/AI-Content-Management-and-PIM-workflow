#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outil industriel d'assainissement et de remédiation rédactionnelle pour My-eStore.
Permet d'auditer et d'auto-corriger les tournures publicitaires exagérées (hyperboles)
à l'échelle de n'importe quel catalogue de marque.
"""

import os
import sys
import json
import glob
import re
import argparse

# Configure stdout to support UTF-8 characters on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SEVERE_WORDS = [
    r"monstrueux(se)?(s)?",
    r"majestueux(se)?(s)?", r"majestueusement",
    r"fièrement",
    r"merveille(s)?",
    r"pulvérise(nt)?",
    r"victorieusement",
    r"ingénieux(se)?",
    r"magnifique(s)?", r"magnifiquement",
    r"spectaculaire(s)?",
    r"époustouflant(e)?(s)?",
    r"sensationnel(le)?(s)?",
    r"colossal(e)?(s)?", r"colossaux",
    r"somptueux(se)?(s)?",
    r"luxueux(se)?(s)?",
    r"séduction fatale",
    r"le summum",
    r"chef-d'œuvre(s)?", r"chef-d’œuvre(s)?",
    r"sublime(s)?",
    r"prestigieux(se)?(s)?",
    r"prodigieux(se)?(s)?",
    r"extraordinaire(s)?",
    r"merveilleux(se)?(s)?",
    r"divin(e)?(s)?",
    r"magique(s)?",
    r"invulnérable(s)?",
    r"rutilant(e)?(s)?",
    r"impitoyable(s)?",
    r"terrible(s)?",
    r"fabuleux(se)?(s)?",
    r"phénoménal(e)?(s)?", r"phénoménaux",
    r"inestimable(s)?"
]

SUBSTRING_REPLACEMENTS = {
    # fièrement
    "s'impose fièrement": "s'impose",
    "arbore très fièrement": "arbore",
    "s'appuie fièrement": "s'appuie",
    "affichez fièrement": "affichez",
    "exhibe très fièrement": "exhibe",
    "arbore fièrement": "arbore",
    "démolit fièrement": "dépasse",
    "portez fièrement": "portez",
    "arborer fièrement": "arborer",
    "accompagne fièrement": "accompagne",
    "se distingue fièrement": "se distingue",
    "déploie fièrement": "déploie",

    # magnifique
    "magnifique écran": "écran",
    "magnifiques dalles": "dalles",
    "magnifique machine": "machine",
    "magnifique bijou": "bijou",
    "magnifique personnalisation": "personnalisation",
    "magnifiquement occupée": "occupée",
    "gère magnifiquement": "gère",
    "s'étalent magnifiquement": "s'étalent",
    "magnifiques créations": "créations",
    "magnifique": "raffiné",

    # merveille
    "véritable merveille technologique": "moniteur",
    "merveille numérique": "montre",
    "merveille horlogère": "montre",
    "pure merveille de": "unité de",
    "merveille": "appareil",

    # pulvérise
    "pulvérise victorieusement les": "dépasse les",
    "pulvérise les standards": "surpasse les standards",
    "pulvérise la frêle concurrence": "se distingue",
    "pulvérise facilement les": "gère les",
    "pulvérise": "dépasse",

    # victorieusement
    "repousse victorieusement": "repousse",
    "surmontez victorieusement": "surmontez",
    "perce victorieusement": "perce",
    "déclenche victorieusement": "déclenche",
    "victorieusement": "efficacement",

    # majestueux / majestueusement
    "se déploie majestueusement": "se déploie",
    "exhibe majestueusement": "exhibe",
    "déploie majestueusement": "déploie",
    "bouleverse majestueusement": "bouleverse",
    "majestueux système": "système",
    "majestueuse Blackview": "Blackview",
    "majestueux rectangle": "rectangle",
    "s'effectue majestueusement": "s'effectue avec fluidité",
    "majestueusement": "avec élégance",
    "majestueux": "élégant",

    # ingénieux
    "ingénieux support": "support",
    "très ingénieux dispositif": "dispositif",
    "ingénieux système": "système",
    "ingénieux": "efficace",

    # prestigieux
    "prestigieux système": "système",
    "prestigieux costumes": "costumes",
    "prestigieux": "haut de gamme",

    # divin
    "confort divin": "excellent confort",
    "divine dalle": "dalle",
    "confort oculaire absolument divin": "confort oculaire",
    "absolument divin": "excellent",
    "divin": "excellent"
}

def split_into_sentences(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def get_editorial_text(data):
    copy_parts = []
    sd = data.get("short_description", {})
    if isinstance(sd, dict):
        for k in ['teaser', 'brand_line', 'marketing_conclusion', 'slogan_final']:
            if sd.get(k): copy_parts.append(sd.get(k))
        for f in sd.get("features", []):
            if isinstance(f, dict):
                if f.get("feature"): copy_parts.append(f.get("feature"))
                if f.get("benefice"): copy_parts.append(f.get("benefice"))
                
    ld = data.get("long_description", {})
    if isinstance(ld, dict):
        if ld.get("intro_paragraph"): copy_parts.append(ld.get("intro_paragraph"))
        for s in ld.get("sections", []):
            if isinstance(s, dict):
                if s.get("h2_title"): copy_parts.append(s.get("h2_title"))
                for p in s.get("paragraphs", []):
                    if p: copy_parts.append(p)
    return " ".join(copy_parts)

def rewrite_text(text):
    if not isinstance(text, str):
        return text
    modified_text = text
    for old_sub, new_sub in SUBSTRING_REPLACEMENTS.items():
        modified_text = modified_text.replace(old_sub, new_sub)
        modified_text = modified_text.replace(old_sub.capitalize(), new_sub.capitalize())
    return modified_text

def rewrite_dict(d):
    changes = 0
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, str) and k in [
                'title_format', 'brand_line', 'marketing_conclusion', 'teaser',
                'slogan_final', 'feature', 'benefice', 'intro_paragraph',
                'h2_title', 'box_title'
            ]:
                new_v = rewrite_text(v)
                if new_v != v:
                    d[k] = new_v
                    changes += 1
            elif isinstance(v, list) and k == 'paragraphs':
                for idx, item in enumerate(v):
                    if isinstance(item, str):
                        new_item = rewrite_text(item)
                        if new_item != item:
                            v[idx] = new_item
                            changes += 1
            else:
                changes += rewrite_dict(v)
    elif isinstance(d, list):
        for item in d:
            changes += rewrite_dict(item)
    return changes

def run_detect(args):
    json_pattern = os.path.join(args.products_dir, "**", "pack-data-*.json")
    json_files = sorted(glob.glob(json_pattern, recursive=True))
    
    compiled_patterns = [
        (w, re.compile(rf"\b(?:{w})\b", re.IGNORECASE | re.UNICODE)) for w in SEVERE_WORDS
    ]
    
    failing_packs = []
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
            
        full_text = get_editorial_text(data)
        sentences = split_into_sentences(full_text)
        
        flagged_sentences = []
        found_words = set()
        
        for sent in sentences:
            sent_flagged = False
            sent_words = []
            for word, pattern in compiled_patterns:
                matches = list(pattern.finditer(sent))
                if matches:
                    sent_flagged = True
                    for m in matches:
                        found_words.add(m.group(0).lower())
                        sent_words.append(m.group(0))
            if sent_flagged:
                highlighted = sent
                for w in set(sent_words):
                    highlighted = re.sub(rf"\b({w})\b", r"**\1**", highlighted, flags=re.IGNORECASE)
                flagged_sentences.append(highlighted)
                
        if flagged_sentences:
            failing_packs.append({
                "file": os.path.relpath(filepath, args.products_dir),
                "words": sorted(list(found_words)),
                "sentences": flagged_sentences
            })
            
    # Write output
    md = []
    md.append("# Audit des Tournures Hyperboliques par Pack\n")
    md.append(f"Dossier audité : `{args.products_dir}`\n")
    md.append(f"**Total de packs affectés** : {len(failing_packs)}/{len(json_files)}\n")
    md.append("| # | Dossier Pack | Mots Détectés | Exemples de Phrases Concernées |")
    md.append("|---|--------------|---------------|--------------------------------|")
    
    for idx, pack in enumerate(failing_packs, 1):
        words_str = ", ".join(f"`{w}`" for w in pack["words"])
        sents_str = "<br>".join(f"- {s}" for s in pack["sentences"][:3])
        if len(pack["sentences"]) > 3:
            sents_str += f"<br>*(et {len(pack['sentences']) - 3} autres phrases...)*"
        folder = os.path.dirname(pack["file"])
        md.append(f"| {idx} | `{folder}` | {words_str} | {sents_str} |")
        
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))
        
    print(f"[SUCCESS] Audit terminé. {len(failing_packs)} packs non conformes détectés.")
    print(f"Rapport écrit dans : {args.output}")

def run_rewrite(args):
    json_pattern = os.path.join(args.products_dir, "**", "pack-data-*.json")
    json_files = sorted(glob.glob(json_pattern, recursive=True))
    
    modified = 0
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
            
        changes = rewrite_dict(data)
        if changes > 0:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                modified += 1
            except Exception as e:
                print(f"[ERROR] Impossible de sauvegarder {filepath}: {e}")
                
    print(f"[SUCCESS] Réécriture terminée. {modified}/{len(json_files)} fichiers JSON mis à jour.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Outil d'assainissement de copywriting My-eStore.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # subcommand detect
    parser_detect = subparsers.add_parser("detect", help="Détecte les tournures hyperboliques et écrit un rapport.")
    parser_detect.add_argument("--products-dir", required=True, help="Répertoire contenant les packs de produits.")
    parser_detect.add_argument("--output", required=True, help="Chemin vers le rapport markdown de sortie.")
    
    # subcommand rewrite
    parser_rewrite = subparsers.add_parser("rewrite", help="Réécrit de façon neutre les JSON sources.")
    parser_rewrite.add_argument("--products-dir", required=True, help="Répertoire contenant les packs de produits.")
    
    args = parser.parse_args()
    
    if args.command == "detect":
        run_detect(args)
    elif args.command == "rewrite":
        run_rewrite(args)
