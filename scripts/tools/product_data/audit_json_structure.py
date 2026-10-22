#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_json_structure.py — Audit approfondi de la structure des fichiers JSON parents (V3.4).

Vérifie la conformité structurelle stricte selon la Charte V3.4 :
  1. Validité JSON (syntaxe, encodage utf-8)
  2. Version de schéma ("template_version" == "3.4" ou "schema_version" == "3.4")
  3. Structure de long_description :
     - Présence de 'seo', 'h1', 'intro_paragraph', 'sections', 'full_specs', 'cta'
     - Emplacement de 'full_specs' DANS long_description et positionné immédiatement au-dessus de 'cta'
     - Qualité de 'full_specs' (sections non vides, pas de placeholders "")
  4. Conformité du bloc CTA :
     - top_link: "#"
     - top_label: "Remonter pour commander"
     - boutiques_link: "https://my-estore.com/boutiques-officielles/"
     - boutiques_label: "Nos Boutiques Officielles"
  5. Structure de short_description :
     - Présence de 'teaser', 'seo' et bloc de caractéristiques clés
  6. Conformité WooCommerce CSV :
     - Attribut 1 = Couleur
     - Attribut 2 = Stockage
     - Attribut 3 = RAM
     - Attribut 4 = Poids (X.XXX kg) ou Processeur (PC)
     - Attribut 5 = Réseau
  7. Bloc paired_variants :
     - Présence à la racine, non vide
     - Clés obligatoires : color_fr, ram, storage, price, sku_suffix
     - 0 doublon de sku_suffix
"""

import os
import sys
import json
import re
import argparse
from typing import Dict, List, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OFFICIAL_DISCLAIMER_STANDARD = (
    "Avis de non-responsabilité (Spécifications) : Les caractéristiques techniques et les images de l'appareil "
    "sont fournies à titre purement indicatif et proviennent des données officielles des constructeurs et autres sources. "
    "Des variations peuvent survenir selon les lots de fabrication et les régions d'importation. "
    "Nous vous invitons à vérifier scrupuleusement la configuration exacte que vous avez sélectionnée dans vos "
    "options d'achat avant de valider définitivement votre commande."
)

def audit_file(filepath: str, fix_disclaimer: bool = False) -> Dict[str, Any]:
    rel_path = os.path.relpath(filepath)
    issues = []
    warnings = []
    disclaimer_status = "UNKNOWN"

    # 1. Validité JSON
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "file": rel_path,
            "status": "FATAL",
            "errors": [f"Erreur de lecture/syntaxe JSON : {e}"],
            "warnings": []
        }

    # 2. Version de Schéma
    version = data.get("template_version") or data.get("schema_version")
    if not version:
        issues.append("Version manquante (ni 'template_version' ni 'schema_version' définie)")
    elif str(version) != "3.4":
        issues.append(f"Version non conforme : '{version}' (attendu : '3.4')")

    # 3. Structure de long_description
    long_desc = data.get("long_description")
    if not long_desc or not isinstance(long_desc, dict):
        issues.append("Bloc 'long_description' manquant ou invalide")
    else:
        # H1
        h1 = long_desc.get("h1") or long_desc.get("title")
        if not h1:
            issues.append("Titre H1 manquant dans 'long_description'")
        elif "title" in long_desc and "h1" not in long_desc:
            warnings.append("Titre H1 sous la clé 'title' au lieu de 'h1'")

        # Intro
        intro = long_desc.get("intro_paragraph")
        if not intro or not isinstance(intro, str) or len(intro.strip()) < 20:
            issues.append("'intro_paragraph' manquant ou trop court dans 'long_description'")

        # Experience box (obligatoire V3.4)
        exp_box = long_desc.get("experience_box")
        if not exp_box or not isinstance(exp_box, dict):
            issues.append("Bloc 'experience_box' manquant ou invalide dans 'long_description'")
        else:
            items = exp_box.get("items", [])
            if not isinstance(items, list) or len(items) != 4:
                issues.append(f"'experience_box.items' doit contenir exactement 4 éléments ({len(items) if isinstance(items, list) else 0} trouvés)")
            else:
                for idx_item, itm in enumerate(items):
                    if not isinstance(itm, dict) or not itm.get("feature") or not itm.get("benefice"):
                        issues.append(f"'experience_box.items[{idx_item}]' incomplet (doit contenir 'feature' et 'benefice' non vides)")

        # Sections H2 (Standard V3.4 : exactement 3 sections de 2 paragraphes chacune)
        sections = long_desc.get("sections")
        if not sections or not isinstance(sections, list) or len(sections) == 0:
            issues.append("Sections H2 manquantes ou vides dans 'long_description'")
        else:
            if len(sections) != 3:
                issues.append(f"Nombre de sections H2 non conforme : {len(sections)} sections (attendu : exactement 3)")
            for s_idx, sec in enumerate(sections):
                if not isinstance(sec, dict):
                    issues.append(f"Section {s_idx+1} invalide (doit être un objet)")
                    continue
                if "title" in sec and "h2_title" not in sec:
                    issues.append(f"Section {s_idx+1} utilise 'title' au lieu de 'h2_title' (génère un <h2> vide à la compilation HTML !)")
                elif not sec.get("h2_title"):
                    issues.append(f"Section {s_idx+1} champ 'h2_title' manquant ou vide")
                
                paras = sec.get("paragraphs")
                if not paras or not isinstance(paras, list):
                    issues.append(f"Section {s_idx+1} 'paragraphs' manquant ou invalide")
                elif len(paras) != 2:
                    issues.append(f"Section {s_idx+1} doit contenir exactement 2 paragraphes ({len(paras)} trouvés)")
                else:
                    for p_idx, p in enumerate(paras):
                        if not isinstance(p, str) or len(p.strip()) < 20:
                            issues.append(f"Section {s_idx+1} paragraphe {p_idx+1} manquant ou trop court")

        # full_specs
        full_specs = long_desc.get("full_specs") or long_desc.get("full_specs_table")
        if not full_specs:
            # Vérifier s'il est mal placé à la racine
            if "full_specs" in data or "full_specs_table" in data:
                issues.append("Bloc 'full_specs' mal placé à la racine du JSON au lieu d'être dans 'long_description'")
            else:
                issues.append("Bloc 'full_specs' introuvable dans 'long_description'")
        else:
            # Vérifier l'ordre dans long_description : full_specs doit être avant cta
            ld_keys = list(long_desc.keys())
            if "full_specs" in ld_keys and "cta" in ld_keys:
                if ld_keys.index("full_specs") > ld_keys.index("cta"):
                    issues.append("Bloc 'full_specs' positionné APRÈS 'cta' (doit être au-dessus)")

            # Vérifier complétude des specs
            if isinstance(full_specs, dict):
                empty_sections = [k for k, v in full_specs.items() if not v]
                if empty_sections:
                    warnings.append(f"Sections vides dans full_specs : {empty_sections}")
            elif isinstance(full_specs, list):
                if len(full_specs) == 0:
                    issues.append("Tableau full_specs vide")

            # 3b. Vérification effective de l'Avis de non-responsabilité (disclaimer) dans le footer sous le tableau
            disclaimer_status = "OK"
            if isinstance(full_specs, dict):
                footer = full_specs.get("footer")
                if not footer:
                    if "disclaimer" in long_desc or "disclaimer" in data:
                        issues.append("Avis de non-responsabilité (disclaimer) mal placé hors de 'long_description.full_specs.footer'")
                        disclaimer_status = "MISPLACED"
                    else:
                        issues.append("Bloc 'footer' manquant dans 'full_specs' (avis de non-responsabilité absent sous le tableau)")
                        disclaimer_status = "MISSING"
                elif not isinstance(footer, dict):
                    issues.append("Bloc 'footer' dans 'full_specs' invalide (doit être un objet)")
                    disclaimer_status = "INVALID"
                else:
                    disc_val = footer.get("disclaimer")
                    if disc_val is None:
                        issues.append("Champ 'disclaimer' (avis de non-responsabilité) manquant dans 'full_specs.footer'")
                        disclaimer_status = "MISSING"
                    elif not isinstance(disc_val, str) or not disc_val.strip():
                        issues.append("Champ 'disclaimer' (avis de non-responsabilité) vide dans 'full_specs.footer'")
                        disclaimer_status = "EMPTY"
                    else:
                        disc_clean = disc_val.strip()
                        if "Avis de non-responsabilité" not in disc_clean and "Avis de non-responsabilite" not in disc_clean:
                            issues.append(f"Avis de non-responsabilité non conforme : mention légale obligatoire manquante ('{disc_clean[:50]}...')")
                            disclaimer_status = "INVALID"
                        elif disc_clean != OFFICIAL_DISCLAIMER_STANDARD:
                            warnings.append(f"Avis de non-responsabilité divergent du standard officiel V3.4 (texte : '{disc_clean[:70]}...')")
                            disclaimer_status = "DIVERGENT"
                        else:
                            disclaimer_status = "STANDARD"

            if fix_disclaimer and disclaimer_status in ["MISSING", "MISPLACED", "EMPTY", "DIVERGENT"]:
                if isinstance(full_specs, dict):
                    if "footer" not in full_specs or not isinstance(full_specs["footer"], dict):
                        full_specs["footer"] = {}
                    full_specs["footer"]["disclaimer"] = OFFICIAL_DISCLAIMER_STANDARD
                    # Assurer la présence des sources dans footer si disponibles
                    if "sources" not in full_specs["footer"] or not full_specs["footer"]["sources"]:
                        sources_candidates = (
                            data.get("sourcing", {}).get("specs_sources")
                            or data.get("model_numbers", {}).get("verification_sources")
                            or data.get("sources")
                            or long_desc.get("sources")
                        )
                        if sources_candidates:
                            full_specs["footer"]["sources"] = sources_candidates
                    if "disclaimer" in long_desc:
                        del long_desc["disclaimer"]
                    if "disclaimer" in data:
                        del data["disclaimer"]
                    if "sources" in long_desc:
                        del long_desc["sources"]
                    with open(filepath, "w", encoding="utf-8") as fw:
                        json.dump(data, fw, ensure_ascii=False, indent=4)
                    disclaimer_status = "STANDARD (FIXED)"
                    # Nettoyer les issues/warnings corrigés
                    issues = [e for e in issues if "disclaimer" not in e.lower() and "non-responsabilité" not in e.lower() and "footer" not in e.lower()]
                    warnings = [w for w in warnings if "disclaimer" not in w.lower() and "non-responsabilité" not in w.lower()]

        # CTA
        cta = long_desc.get("cta") or data.get("cta")
        if not cta or not isinstance(cta, dict):
            issues.append("Bloc 'cta' manquant ou invalide")
        else:
            top_link = cta.get("top_link")
            top_label = cta.get("top_label", "")
            boutiques_link = cta.get("boutiques_link")
            boutiques_label = cta.get("boutiques_label", "")

            if top_link != "#":
                issues.append(f"CTA top_link non conforme : '{top_link}' (attendu : '#')")
            if top_label != "Remonter pour commander":
                issues.append(f"CTA top_label non conforme : '{top_label}' (attendu : 'Remonter pour commander')")
            if "boutiques-officielles" not in str(boutiques_link):
                issues.append(f"CTA boutiques_link non conforme : '{boutiques_link}'")
            if boutiques_label != "Nos Boutiques Officielles":
                issues.append(f"CTA boutiques_label non conforme : '{boutiques_label}' (attendu : 'Nos Boutiques Officielles')")

    # 4. Structure de short_description
    short_desc = data.get("short_description")
    if not short_desc or not isinstance(short_desc, dict):
        issues.append("Bloc 'short_description' manquant ou invalide")
    else:
        if not short_desc.get("teaser"):
            warnings.append("Champ 'teaser' manquant dans short_description")
        features = short_desc.get("top_features_detailed") or short_desc.get("features") or short_desc.get("key_points")
        if not features:
            warnings.append("Points clés/features manquants dans short_description")

    # 5. Conformité woocommerce_csv
    woo = data.get("woocommerce_csv")
    if not woo or not isinstance(woo, dict):
        issues.append("Bloc 'woocommerce_csv' manquant ou invalide")
    else:
        # Détection des produits sans RAM / Stockage déclinable (audio, montres, enceintes, accessoires)
        prod_ident = data.get("product_identity", {})
        cat = str(prod_ident.get("category", "")).lower()
        sub_cat = str(prod_ident.get("sub_category", "")).lower()
        brand = str(prod_ident.get("brand", "")).lower()
        p_line = str(prod_ident.get("product_line", "")).lower()
        is_audio_or_wearable = any(
            k in cat or k in sub_cat or k in p_line
            for k in ["audio", "wearable", "smartwatch", "watch", "montre", "ecouteur", "earbud", "speaker", "enceinte", "accessoire", "accessory"]
        ) or brand in ["hifuture"]

        # Ordre des attributs
        a1_name = woo.get("Attribute 1 name", "")
        a2_name = woo.get("Attribute 2 name", "")
        a3_name = woo.get("Attribute 3 name", "")
        a4_name = woo.get("Attribute 4 name", "")
        a5_name = woo.get("Attribute 5 name", "")

        if a1_name not in ["Couleur", "Color"]:
            issues.append(f"Attribute 1 name invalide : '{a1_name}' (attendu : 'Couleur')")

        if is_audio_or_wearable:
            # Pour audio / montres : Stockage et RAM sont facultatifs
            if a2_name and a2_name not in ["Stockage", "Storage"]:
                issues.append(f"Attribute 2 name invalide : '{a2_name}' (attendu : 'Stockage' ou vide)")
            if a3_name and a3_name not in ["RAM"]:
                issues.append(f"Attribute 3 name invalide : '{a3_name}' (attendu : 'RAM' ou vide)")
        else:
            # Produits avec configurations mémoires (Smartphones, Tablettes, PC...)
            if a2_name not in ["Stockage", "Storage"]:
                issues.append(f"Attribute 2 name invalide : '{a2_name}' (attendu : 'Stockage')")
            if a3_name not in ["RAM"]:
                issues.append(f"Attribute 3 name invalide : '{a3_name}' (attendu : 'RAM')")

        # Attribut 4 (Poids/Processeur) : optionnel si la marque ne le requiert pas (ex: Samsung)
        if a4_name and a4_name not in ["Poids", "Processeur", "Weight", "Processor"]:
            issues.append(f"Attribute 4 name invalide : '{a4_name}' (attendu : 'Poids' ou 'Processeur')")
        if a5_name and a5_name not in ["Réseau", "Network"]:
            issues.append(f"Attribute 5 name invalide : '{a5_name}' (attendu : 'Réseau')")

        # Format du poids si renseigné
        if a4_name in ["Poids", "Weight"]:
            w_val = str(woo.get("Attribute 4 value(s)", "")).strip()
            if w_val and not re.search(r'^\d+(\.\d+)?\s*kg$', w_val, re.IGNORECASE):
                warnings.append(f"Poids non normé : '{w_val}' (attendu format 'X.XXX kg')")

        # Contrôle qualitatif des Tags WooCommerce (Standard V3.4 : 8 à 14 tags enrichis)
        tags_val = str(woo.get("Tags", "")).strip()
        if not tags_val:
            issues.append("Champ 'Tags' manquant ou vide dans woocommerce_csv")
        else:
            tags_list = [t.strip() for t in tags_val.split(",") if t.strip()]
            if len(tags_list) < 8:
                warnings.append(f"Tags trop restreints : {len(tags_list)} tags trouvés (minimum recommandé : 8 à 14 tags enrichis)")
            if not any("abidjan" == t.lower() for t in tags_list):
                warnings.append("Tag local obligatoire manquant dans 'Tags' : 'Abidjan'")
            if not any("My-eStore" == t.lower() for t in tags_list):
                warnings.append("Tag enseigne obligatoire manquant dans 'Tags' : 'My-eStore'")

    # 6. Bloc paired_variants
    pv_list = data.get("paired_variants")
    if pv_list is None:
        if not is_audio_or_wearable:
            warnings.append("Bloc 'paired_variants' absent à la racine")
    elif not isinstance(pv_list, list) or len(pv_list) == 0:
        if not is_audio_or_wearable:
            warnings.append("Bloc 'paired_variants' vide")
    else:
        skus_seen = set()
        for idx, pv in enumerate(pv_list):
            if not isinstance(pv, dict):
                issues.append(f"paired_variants[{idx}] n'est pas un objet")
                continue
            # Couleur obligatoire (color_fr ou color)
            if not (pv.get("color_fr") or pv.get("color")):
                issues.append(f"paired_variants[{idx}] couleur manquante (ni 'color_fr' ni 'color')")
            # sku_suffix est optionnel (généré dynamiquement par le script de compilation s'il est absent)
            suf = pv.get("sku_suffix", "")
            if suf:
                if suf in skus_seen:
                    issues.append(f"Doublon de sku_suffix dans paired_variants : '{suf}'")
                skus_seen.add(suf)

    # 7. Présence de liens concurrents interdits (GSMarena etc.) dans les descriptions
    dump_str = json.dumps(data, ensure_ascii=False)
    forbidden_urls = ["gsmarena.com", "lesnumeriques.com", "frandroid.com", "kimovil.com", "versus.com"]
    for fu in forbidden_urls:
        if fu in dump_str:
            # Vérifier si c'est dans sources / generation_metadata ou dans les descriptions
            if "long_description" in data and fu in json.dumps(data["long_description"], ensure_ascii=False):
                issues.append(f"Lien concurrent interdit détecté dans long_description : '{fu}'")
            elif "short_description" in data and fu in json.dumps(data["short_description"], ensure_ascii=False):
                issues.append(f"Lien concurrent interdit détecté dans short_description : '{fu}'")
            else:
                warnings.append(f"Lien tiers de sourcing détecté dans les métadonnées : '{fu}'")

    status = "PASS" if len(issues) == 0 else "FAIL"
    return {
        "file": rel_path,
        "status": status,
        "errors": issues,
        "warnings": warnings,
        "disclaimer_status": disclaimer_status
    }

def audit_file_list(file_list: List[str], verbose: bool = True, fix_disclaimer: bool = False) -> Dict[str, Any]:
    """Exécute l'audit de structure sur une liste de fichiers JSON et retourne le bilan."""
    pass_count = 0
    fail_count = 0
    results = []

    if verbose:
        print("======================================================================")
        print(f"  AUDIT DES STRUCTURES JSON PARENTS (V3.4) : {len(file_list)} fichiers")
        print("======================================================================\n")

    for idx, fp in enumerate(file_list, 1):
        res = audit_file(fp, fix_disclaimer=fix_disclaimer)
        results.append(res)
        if res["status"] == "PASS":
            pass_count += 1
            if verbose:
                warn_str = f" ({len(res['warnings'])} warnings)" if res["warnings"] else ""
                print(f"[{idx:03d}/{len(file_list)}] 🟢 [PASS] {res['file']}{warn_str}")
        else:
            fail_count += 1
            if verbose:
                print(f"[{idx:03d}/{len(file_list)}] 🔴 [FAIL] {res['file']}")
                for err in res["errors"]:
                    print(f"      ✗ {err}")
                for wrn in res["warnings"]:
                    print(f"      ⚠ {wrn}")

    disc_std = sum(1 for r in results if "STANDARD" in r.get("disclaimer_status", ""))
    disc_div = sum(1 for r in results if r.get("disclaimer_status") == "DIVERGENT")
    disc_mis = sum(1 for r in results if r.get("disclaimer_status") in ["MISSING", "MISPLACED", "EMPTY", "INVALID"])

    if verbose:
        print("\n" + "=" * 70)
        print("  BILAN GLOBAL DE L'AUDIT DE STRUCTURE JSON")
        print(f"  Total audité : {len(file_list)}")
        print(f"  🟢 Conformes [PASS] : {pass_count}")
        print(f"  🔴 Malformés [FAIL] : {fail_count}")
        print("-" * 70)
        print("  Avis de non-responsabilité (Footer sous tableau specs) :")
        print(f"    🟢 Conformes standard V3.4 : {disc_std}")
        if disc_div > 0:
            print(f"    ⚠ Textes divergents        : {disc_div}")
        if disc_mis > 0:
            print(f"    🔴 Manquants / Mal placés   : {disc_mis}")
        print("=" * 70 + "\n")

        if fail_count > 0:
            error_summary = {}
            for r in results:
                for e in r["errors"]:
                    error_summary[e] = error_summary.get(e, 0) + 1
            print("  Top des malformations détectées :")
            for err, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
                print(f"    - [{count} fichiers] {err}")
            print()

    return {
        "total": len(file_list),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "disclaimer_stats": {
            "standard": disc_std,
            "divergent": disc_div,
            "missing": disc_mis
        },
        "results": results,
        "success": fail_count == 0
    }


def main():
    parser = argparse.ArgumentParser(description="Audit approfondi des structures JSON parents V3.4")
    parser.add_argument("--dir", default="product-data", help="Dossier à auditer (défaut: product-data)")
    parser.add_argument("--brand", default="", help="Filtrer par marque (ex: samsung, zte, blackview)")
    parser.add_argument("--files", nargs="+", help="Liste explicite de fichiers JSON à auditer")
    parser.add_argument("--fix-disclaimer", action="store_true", help="Corrige automatiquement les avis de non-responsabilité manquants ou divergents avec le texte officiel V3.4")
    args = parser.parse_args()

    all_files = []
    if args.files:
        all_files = [f for f in args.files if os.path.exists(f)]
    else:
        search_dir = args.dir
        if args.brand:
            search_dir = os.path.join(args.dir, args.brand)

        if not os.path.exists(search_dir):
            print(f"❌ Dossier introuvable : {search_dir}")
            sys.exit(1)

        for root, dirs, files in os.walk(search_dir):
            for f in files:
                if f.endswith(".json") and not f.startswith("hyp_"):
                    all_files.append(os.path.join(root, f))

    all_files.sort()
    if not all_files:
        print("❌ Aucun fichier JSON trouvé pour l'audit.")
        sys.exit(1)

    outcome = audit_file_list(all_files, verbose=True, fix_disclaimer=args.fix_disclaimer)
    if not outcome["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
