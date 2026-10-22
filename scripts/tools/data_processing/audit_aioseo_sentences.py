#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse AIOSEO détaillée : longueur de phrases + transitions par PHRASE (pas par paragraphe).
Simule le comportement exact de AIOSEO/Yoast pour identifier les problèmes.
"""

import json
import re
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === Mots de transition AIOSEO (français) ===
# AIOSEO cherche les transitions dans CHAQUE PHRASE, pas juste en début de paragraphe.
TRANSITION_WORDS_FR = [
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

def split_sentences(text):
    """Découpe un texte en phrases (approximation AIOSEO)."""
    # Supprimer les balises HTML
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = text.strip()
    
    # Découper sur . ! ? suivis d'un espace ou fin de texte
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filtrer les phrases vides
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]
    return sentences

def count_words_in_sentence(sentence):
    """Compte les mots dans une phrase."""
    words = [w for w in sentence.split() if w and not re.match(r'^[.,;:!?()]+$', w)]
    return len(words)

def has_transition(sentence):
    """Vérifie si une phrase contient un mot de transition (comme AIOSEO)."""
    sentence_lower = sentence.lower()
    for tw in TRANSITION_WORDS_FR:
        # AIOSEO cherche le mot de transition N'IMPORTE OÙ dans la phrase
        if tw.lower() in sentence_lower:
            return True, tw
    return False, None

def analyze_json(file_path):
    """Analyse complète d'un JSON de pack-data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    long_desc = data.get('long_description', {})
    if not long_desc:
        print(f"[ERROR] Pas de long_description dans {file_path}")
        return
    
    # Collecter tout le texte visible
    all_text_parts = []
    
    intro = long_desc.get('intro_paragraph', '')
    if intro:
        all_text_parts.append(intro)
    
    for section in long_desc.get('sections', []):
        for p in section.get('paragraphs', []):
            all_text_parts.append(p)
    
    full_text = " ".join(all_text_parts)
    sentences = split_sentences(full_text)
    
    total_sentences = len(sentences)
    long_sentences = []
    short_sentences = []
    transitions_found = []
    no_transitions = []
    
    for i, s in enumerate(sentences):
        wc = count_words_in_sentence(s)
        has_t, tw = has_transition(s)
        
        if wc > 20:
            long_sentences.append((i+1, wc, s[:80] + "..."))
        else:
            short_sentences.append((i+1, wc))
        
        if has_t:
            transitions_found.append((i+1, tw, s[:60] + "..."))
        else:
            no_transitions.append((i+1, s[:80] + "..."))
    
    # Calcul des taux
    long_pct = (len(long_sentences) / total_sentences * 100) if total_sentences > 0 else 0
    transition_pct = (len(transitions_found) / total_sentences * 100) if total_sentences > 0 else 0
    
    # 5. DÉTECTION DES HYPERBOLES (V3.2)
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

    model = data.get('metadata', {}).get('target_model', os.path.basename(file_path))
    
    print(f"\n{'='*70}")
    print(f"  AUDIT AIOSEO - {model}")
    print(f"{'='*70}")
    
    # 1. Sentence Length
    status_len = "[OK]" if long_pct <= 25 else "[FAIL]"
    print(f"\n{status_len} LONGUEUR DES PHRASES")
    print(f"   Total phrases : {total_sentences}")
    print(f"   Phrases > 20 mots : {len(long_sentences)} ({long_pct:.1f}%)")
    print(f"   Seuil AIOSEO : <= 25%")
    
    if long_sentences:
        print(f"\n   Phrases trop longues :")
        for idx, wc, preview in long_sentences:
            print(f"     [{idx}] {wc} mots -> {preview}")
    
    # 2. Transitions
    status_tr = "[OK]" if (30 < transition_pct < 50) else "[FAIL]"
    print(f"\n{status_tr} MOTS DE TRANSITION")
    print(f"   Phrases avec transition : {len(transitions_found)} ({transition_pct:.1f}%)")
    print(f"   Seuil AIOSEO : > 30% et < 50% (cible : 31%-49%)")
    
    if no_transitions:
        print(f"\n   Phrases SANS transition ({len(no_transitions)}) :")
        for idx, preview in no_transitions[:10]:
            print(f"     [{idx}] {preview}")
            
    # 3. Hyperboles
    status_hyp = "[OK]" if len(hyperboles_found) == 0 else "[FAIL]"
    print(f"\n{status_hyp} HYPERBOLES ET MOTS INTERDITS (V3.2)")
    print(f"   Hyperboles détectées : {len(hyperboles_found)} (Seuil: 0)")
    if hyperboles_found:
        for h in hyperboles_found:
            print(f"     - [Champ: {h['field']}] Mot trouvé: '{h['term']}'")
            print(f"       Contexte: {h['snippet']}")
            
    # 4. Phrases Consécutives (Yoast/AIOSEO)
    consecutive_issues = []
    first_words = []
    for s in sentences:
        clean = re.sub(r'^[«"\'\s\-\,\.\:]+', '', s).strip()
        words = [w for w in clean.split() if w]
        if words:
            w = re.sub(r'[.,;:!?()\"\'»«]+$', '', words[0]).lower()
            first_words.append(w)
        else:
            first_words.append('')
            
    for i in range(len(first_words) - 2):
        w1 = first_words[i]
        w2 = first_words[i+1]
        w3 = first_words[i+2]
        if w1 and w1 == w2 and w2 == w3:
            consecutive_issues.append((i+1, w1, sentences[i:i+3]))
            
    status_cons = "[OK]" if len(consecutive_issues) == 0 else "[WARN]"
    print(f"\n{status_cons} PHRASES CONSECUTIVES (AIOSEO)")
    print(f"   Groupes de 3+ phrases débutant par le même mot : {len(consecutive_issues)}")
    if consecutive_issues:
        for idx, w, group in consecutive_issues:
            print(f"     - Ligne {idx} | Mot: '{w}'")
            for gs in group:
                print(f"       * {gs[:80]}...")
    
    # 5. CONFORMITÉ TITRE H1 (V3.4 Standard B - Top Specs)
    h1_val = (long_desc.get('h1') or long_desc.get('main_title') or '').strip()
    forbidden_h1_patterns = [r"fiche\s+technique", r"spécification(s)?", r"specification(s)?"]
    h1_issues = []
    if not h1_val:
        h1_issues.append("Titre H1 manquant dans long_description")
    else:
        for pat in forbidden_h1_patterns:
            if re.search(pat, h1_val, re.IGNORECASE):
                h1_issues.append(f"Formule générique interdite détectée : '{pat}' dans '{h1_val}'")
    
    status_h1 = "[OK]" if len(h1_issues) == 0 else "[FAIL]"
    print(f"\n{status_h1} TITRE H1 (Standard B Top Specs V3.4)")
    print(f"   Titre H1 : {h1_val}")
    if h1_issues:
        for iss in h1_issues:
            print(f"   [!] Non-conformité : {iss}")
        print("   -> Règle V3.4 Standard B : [MARQUE] [MODÈLE] : [Top Spec 1], [Top Spec 2] et [Top Spec 3]")

    pass_h1 = len(h1_issues) == 0
    pass_transitions = 30.0 < transition_pct < 50.0
    pass_length = long_pct <= 25.0
    pass_hyperboles = len(hyperboles_found) == 0

    failures = []
    if not pass_length:
        failures.append(f"LONGUEUR DES PHRASES : {long_pct:.1f}% > 25% max ({len(long_sentences)} phrases trop longues). Réduire chaque phrase sous 20 mots.")
    if transition_pct <= 30.0:
        needed = max(1, int((0.31 * total_sentences) - len(transitions_found)) + 1)
        failures.append(f"TRANSITIONS TROP FAIBLES : {transition_pct:.1f}% <= 30% min ({len(transitions_found)}/{total_sentences} phrases). Ajouter au moins {needed} mot(s) de transition.")
    elif transition_pct >= 50.0:
        to_remove = max(1, len(transitions_found) - int(0.49 * total_sentences))
        info_len = f"Total de phrases faible ({total_sentences} au lieu des ~41 phrases de la formule fixe 15/41)." if total_sentences < 35 else f"Supprimer ou reformuler au moins {to_remove} phrase(s) avec connecteur."
        failures.append(f"TRANSITIONS TROP ÉLEVÉES : {transition_pct:.1f}% >= 50% max ({len(transitions_found)}/{total_sentences} phrases). {info_len}")
    if not pass_hyperboles:
        terms = sorted(list(set(h['term'] for h in hyperboles_found)))
        failures.append(f"HYPERBOLES DÉTECTÉES ({len(hyperboles_found)}) : Mots interdits : {', '.join(terms)}. Remplacer par des termes factuels.")
    if not pass_h1:
        failures.append(f"TITRE H1 INVALIDE : '{h1_val}'. Respecter le format Standard B : [MARQUE] [MODÈLE] : [Top Spec 1], [Top Spec 2] et [Top Spec 3].")

    if failures:
        print(f"\n{'!'*70}")
        print(f"  ❌ DIAGNOSTIC PRÉCIS DE L'ÉCHEC (POURQUOI L'AUDIT ÉCHOUE) :")
        for f in failures:
            print(f"    👉 {f}")
        print(f"{'!'*70}\n")
    else:
        print(f"\n  ✅ TOUS LES CRITÈRES SONT VALIDES (PASS V3.4)\n")
    
    print(f"{'='*70}")
    print(f"  VERDICT : Long={long_pct:.1f}% (max 25%) | Trans={transition_pct:.1f}% (min 30%) | Hyperboles={len(hyperboles_found)} | H1={status_h1} | ConsConsec={len(consecutive_issues)}")
    print(f"{'='*70}\n")
    
    return {
        "model": model,
        "total_sentences": total_sentences,
        "long_pct": long_pct,
        "transition_pct": transition_pct,
        "pass_length": pass_length,
        "pass_transitions": pass_transitions,
        "pass_hyperboles": pass_hyperboles,
        "pass_h1": pass_h1,
        "hyperboles_found": hyperboles_found,
        "consecutive_issues": len(consecutive_issues),
        "failures": failures
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audit_aioseo_sentences.py <fichier.json ou dossier>")
        sys.exit(1)
    
    target = sys.argv[1]
    results = []
    
    if os.path.isfile(target):
        results.append(analyze_json(target))
    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for f in files:
                if f.startswith("pack-data-") and f.endswith(".json"):
                    r = analyze_json(os.path.join(root, f))
                    if r:
                        results.append(r)
    
    if results:
        print(f"\n{'='*70}")
        print(f"  RESUME BATCH ({len(results)} fichiers)")
        print(f"{'='*70}")
        success = True
        for r in results:
            s1 = "[OK]" if r["pass_length"] else "[FAIL]"
            s2 = "[OK]" if r["pass_transitions"] else "[FAIL]"
            s3 = "[OK]" if r.get("pass_hyperboles", True) else "[FAIL]"
            s4 = "[OK]" if r.get("pass_h1", True) else "[FAIL]"
            print(f"  {s1} {s2} {s3} {s4} {r['model']:30s} | Long: {r['long_pct']:5.1f}% | Trans: {r['transition_pct']:5.1f}% | Hyp: {len(r.get('hyperboles_found', []))}")
            if not r["pass_length"] or not r["pass_transitions"] or not r.get("pass_hyperboles", True) or not r.get("pass_h1", True):
                success = False
        if not success:
            sys.exit(1)

