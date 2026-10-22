#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérification des statistiques de contenu dans les moules JSON.
Vérifie le word count (450-650), le taux de transition (31-72% par paragraphe),
la longueur des phrases (≤25% > 20 mots) et les transitions par phrase (≥30%).

Version 2.1 — Correction Mai 2026 : Le word count ne porte QUE sur les textes
rédactionnels : intro_paragraph + sections[].h2_title + sections[].paragraphs[].
Sont EXCLUS volontairement du décompte :
  - h1 (titre de page, hors contenu éditorial)
  - experience_box (encart visuel, hors flux rédactionnel)
  - summary_specs_table (tableau de données techniques, risque de dépassement artificiel)
Cela reflète exactement ce qu'AIOSEO analyse dans le texte visible du frontend.
"""

import json
import re
import argparse
import sys
import os

# === Mots de transition (début de paragraphe — legacy) ===
TRANSITION_WORDS_PARAGRAPH = [
    "En premier lieu", "En second lieu", "En troisième lieu", "En dernier lieu",
    "D'une part", "D'autre part",
    "En outre", "De plus", "Par ailleurs", "À noter", "À propos", "Qui plus est",
    "Par conséquent", "En effet", "De ce fait", "C'est pourquoi", "Ainsi",
    "Parallèlement", "Ensuite", "Finalement",
    "Notamment", "Par exemple", "En particulier",
    "Certes", "Bien que", "Malgré",
    "Cependant", "Néanmoins", "Toutefois",
    "Autrement dit", "C'est-à-dire", "Bref",
    "D'ailleurs", "Également", "Aussi",
    "Premièrement", "Deuxièmement", "Troisièmement",
    "Après", "Ensuite", "Enfin", "À l'inverse", "Inversement",
    "Quant à", "Concernant", "Relativement à",
    "Donc", "Alors", "Dès lors", "Partant",
    "Sinon", "Autrement",
    "De même", "Pareillement", "Identiquement",
]

# === Mots de transition (par phrase — AIOSEO) ===
# AIOSEO cherche les transitions n'importe où dans la phrase
TRANSITION_WORDS_SENTENCE = [
    # Addition
    "de plus", "en outre", "par ailleurs", "également", "de surcroît", "ainsi que",
    "qui plus est", "de même", "pareillement",
    # Contrast
    "cependant", "toutefois", "néanmoins", "en revanche", "pourtant", "alors que",
    "bien que", "malgré", "à l'inverse", "inversement", "certes",
    # Cause
    "en effet", "car", "étant donné que", "puisque", "parce que", "grâce à",
    "c'est pourquoi", "de ce fait",
    # Consequence
    "par conséquent", "ainsi", "dès lors", "en conséquence", "donc", "alors",
    # Time/Order
    "d'abord", "ensuite", "enfin", "puis", "premièrement", "deuxièmement",
    "troisièmement", "en premier lieu", "en second lieu", "dans un premier temps",
    "dans un second temps", "pour finir", "finalement", "en dernier lieu",
    "après", "parallèlement",
    # Illustration
    "par exemple", "notamment", "en particulier", "spécifiquement", "comme",
    # Other
    "d'une part", "d'autre part", "quant à", "concernant", "relativement à",
    "autrement dit", "c'est-à-dire", "bref", "d'ailleurs", "aussi",
    "en complément", "à noter", "à propos",
]

# === Liste d'hyperboles interdites (V3.2 - Copywriting My-eStore) ===
FORBIDDEN_HYPERBOLES = [
    r"incroyable(s)?",
    r"révolutionnaire(s)?",
    r"le summum",
    r"chef-d'œuvre(s)?",
    r"chef-d’œuvre(s)?",
    r"époustouflant(e)?(s)?",
    r"inégalé(e)?(s)?",
    r"sans précédent",
    r"spectaculaire(s)?",
    r"phénoménal(e)?(s)?",
    r"phénoménaux",
    r"exceptionnel(le)?(s)?",
    r"extraordinaire(s)?",
    r"magique(s)?",
    r"sublime(s)?",
    r"ultime(s)?",
    r"parfait(e)?(s)?",
    r"fabuleux(se)?(s)?",
    r"formidable(s)?",
    r"merveilleux(se)?(s)?",
    r"prodigieux(se)?(s)?",
    r"monstrueux(se)?(s)?",
    r"colossal(e)?(s)?",
    r"colossaux",
    r"vertigineux(se)?(s)?",
    r"inestimable(s)?",
    r"séduction fatale",
    r"magistral(e)?(s)?",
    r"magistraux",
    r"sensationnel(le)?(s)?",
    r"invulnérable(s)?",
    r"rutilant(e)?(s)?",
    r"impitoyable(s)?",
    r"impitoyablement",
    r"insolence",
    r"terrible(s)?",
    r"somptueux(se)?(s)?",
    r"luxueux(se)?(s)?",
    r"coûteux(se)?(s)?",
    r"décupler",
    r"diviser merveilleusement",
    r"panoramique inédit"
]

def count_words(text):
    """Compte les mots après suppression des balises HTML."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    words = [w for w in text.split() if w]
    return len(words)

def split_sentences(text):
    """Découpe un texte en phrases (approximation AIOSEO)."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]
    return sentences

def count_words_in_sentence(sentence):
    """Compte les mots dans une phrase."""
    words = [w for w in sentence.split() if w and not re.match(r'^[.,;:!?()]+$', w)]
    return len(words)

def check_json(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] Le fichier {file_path} n'existe pas.")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Lecture JSON : {e}")
        return False
    
    long_desc = data.get('long_description', {})
    if not long_desc:
        print(f"[ERROR] Pas de section 'long_description' dans {file_path}")
        return False

    # ============================================================
    # COLLECTE RÉDACTIONNELLE STRICTE
    # Seuls sont comptés : intro_paragraph, h2_title de section, paragraphes de section.
    # EXCLUS : h1 (titre page), experience_box (encart visuel), summary_specs_table (tableau données).
    # Raison : AIOSEO analyse le flux textuel visible, pas les encarts structurels ni les tableaux.
    # ============================================================
    
    content_parts = []
    
    # Intro paragraph
    intro = long_desc.get('intro_paragraph', '')
    if intro:
        content_parts.append(intro)
    
    # Paragraphes des sections uniquement (H2 + corps)
    paragraphs = [intro] if intro else []
    for section in long_desc.get('sections', []):
        h2 = section.get('h2_title', '')
        if h2:
            content_parts.append(h2)  # H2 compte dans le word count rédactionnel
        for p in section.get('paragraphs', []):
            if p:
                content_parts.append(p)
                paragraphs.append(p)

    total_text = " ".join(content_parts)
    word_count = count_words(total_text)
    
    # ============================================================
    # 1. WORD COUNT (legacy)
    # ============================================================
    # Cible : 450-650 mots rédactionnels (intro + H2 + paragraphes uniquement)
    wc_ok = 450 <= word_count <= 650
    wc_status = "[OK]" if wc_ok else "[FAIL]"
    
    # ============================================================
    # 2. TRANSITIONS PAR PARAGRAPHE (legacy — conservé)
    # ============================================================
    with_transitions_para = 0
    for p in paragraphs:
        text = p.lstrip()
        for word in TRANSITION_WORDS_PARAGRAPH:
            pattern = rf"^{re.escape(word)}\W"
            if re.search(pattern, text, re.IGNORECASE):
                with_transitions_para += 1
                break
    
    total_paragraphs = len(paragraphs)
    transition_rate_para = (with_transitions_para / total_paragraphs) * 100 if total_paragraphs > 0 else 0
    # Version 2.2 : Les transitions par paragraphe sont indicatives (avertissement) et ne bloquent plus le script
    tr_para_warn = not (31 <= transition_rate_para <= 72)
    tr_para_ok = True
    
    # ============================================================
    # 3. LONGUEUR DES PHRASES (nouveau — AIOSEO)
    # ============================================================
    all_sentences_text = " ".join(paragraphs)
    sentences = split_sentences(all_sentences_text)
    total_sentences = len(sentences)
    
    long_sentences = 0
    for s in sentences:
        if count_words_in_sentence(s) > 20:
            long_sentences += 1
    
    long_pct = (long_sentences / total_sentences * 100) if total_sentences > 0 else 0
    long_ok = long_pct <= 25
    
    # ============================================================
    # 4. TRANSITIONS PAR PHRASE (nouveau — AIOSEO)
    # ============================================================
    with_transitions_sent = 0
    for s in sentences:
        s_lower = s.lower()
        for tw in TRANSITION_WORDS_SENTENCE:
            if tw.lower() in s_lower:
                with_transitions_sent += 1
                break
    
    transition_rate_sent = (with_transitions_sent / total_sentences * 100) if total_sentences > 0 else 0
    tr_sent_ok = transition_rate_sent >= 30
    
    # ============================================================
    # 5. DÉTECTION DES HYPERBOLES (V3.2)
    # ============================================================
    editorial_texts = []
    
    # Short description
    sd = data.get('short_description', {})
    if isinstance(sd, dict):
        for key in ['title_format', 'brand_line', 'marketing_conclusion', 'teaser', 'slogan_final']:
            val = sd.get(key)
            if val and isinstance(val, str):
                editorial_texts.append((f"short_description.{key}", val))
        features = sd.get('features', [])
        if isinstance(features, list):
            for i, feat in enumerate(features):
                if isinstance(feat, dict):
                    for key in ['feature', 'benefice']:
                        val = feat.get(key)
                        if val and isinstance(val, str):
                            editorial_texts.append((f"short_description.features[{i}].{key}", val))
                            
    # Long description
    intro_p = long_desc.get('intro_paragraph')
    if intro_p and isinstance(intro_p, str):
        editorial_texts.append(("long_description.intro_paragraph", intro_p))
    sections = long_desc.get('sections', [])
    if isinstance(sections, list):
        for i, sec in enumerate(sections):
            if isinstance(sec, dict):
                h2 = sec.get('h2_title')
                if h2 and isinstance(h2, str):
                    editorial_texts.append((f"long_description.sections[{i}].h2_title", h2))
                paragraphs_list = sec.get('paragraphs', [])
                if isinstance(paragraphs_list, list):
                    for j, p in enumerate(paragraphs_list):
                        if p and isinstance(p, str):
                            editorial_texts.append((f"long_description.sections[{i}].paragraphs[{j}]", p))
                                
    hyperboles_found = []
    for field, text in editorial_texts:
        clean_text = re.sub(r"<[^>]+>", " ", text)
        clean_text = re.sub(r"<!--.*?-->", "", clean_text, flags=re.DOTALL)
        
        for hp in FORBIDDEN_HYPERBOLES:
            pattern = re.compile(rf"\b(?:{hp})\b", re.IGNORECASE | re.UNICODE)
            for match in pattern.finditer(clean_text):
                start = max(0, match.start() - 40)
                end = min(len(clean_text), match.end() + 40)
                snippet = clean_text[start:end].replace('\n', ' ').strip()
                hyperboles_found.append({
                    "field": field,
                    "term": match.group(0),
                    "snippet": f"... {snippet} ..."
                })
                
    hyp_ok = len(hyperboles_found) == 0
    hyp_status = "[OK]" if hyp_ok else "[FAIL]"
    
    # ============================================================
    # AFFICHAGE
    # ============================================================
    print(f"\n[STATS] {file_path}")
    
    # Word Count
    print(f"{wc_status} Word Count rédactionnel: {word_count} (Cible: 450-650 | intro+H2+paragraphes uniquement)")
    
    # Transitions par paragraphe (legacy)
    tr_para_status = "[WARN]" if tr_para_warn else "[OK]"
    print(f"{tr_para_status} Transitions/paragraphe : {transition_rate_para:.1f}% ({with_transitions_para}/{total_paragraphs}) (Cible optimale: 31-72%)")
    
    # Longueur des phrases (AIOSEO)
    long_status = "[OK]" if long_ok else "[FAIL]"
    print(f"{long_status} Phrases >20 mots : {long_pct:.1f}% ({long_sentences}/{total_sentences}) (Seuil AIOSEO: <=25%)")
    
    # Transitions par phrase (AIOSEO)
    tr_sent_status = "[OK]" if tr_sent_ok else "[FAIL]"
    print(f"{tr_sent_status} Transitions/phrase : {transition_rate_sent:.1f}% ({with_transitions_sent}/{total_sentences}) (Seuil AIOSEO: >=30%)")
    
    # Hyperboles (V3.2)
    print(f"{hyp_status} Hyperboles/Mots interdits : {len(hyperboles_found)} trouvé(s) (Seuil: 0)")
    if hyperboles_found:
        print("   Détail des hyperboles détectées :")
        for h in hyperboles_found:
            print(f"     - [Champ: {h['field']}] Mot trouvé: '{h['term']}'")
            print(f"       Contexte: {h['snippet']}")
            
    return wc_ok and tr_para_ok and long_ok and tr_sent_ok and hyp_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vérifie les stats d'un moule JSON (word count, transitions, longueur phrases).")
    parser.add_argument("files", nargs="+", help="Chemins vers les fichiers JSON à vérifier")
    args = parser.parse_args()
    
    success = True
    for f in args.files:
        if not check_json(f):
            success = False
            
    if not success:
        sys.exit(1)
