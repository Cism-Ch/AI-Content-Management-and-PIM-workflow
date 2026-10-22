#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Product Pack V2.1 — Générateur industriel HTML/CSV depuis JSON.

Ce script lit un fichier JSON structuré (moule rempli) et génère :
  - short-[modele].html   (description courte WooCommerce)
  - long-[modele].html    (description longue WooCommerce)
  - specs-[modele].html   (fiche technique — groupe TECH uniquement)
  - import-v2-[modele].csv (ligne CSV pour import WooCommerce)
  - Mise à jour du fichier prix dans Templates/Pricing/

Supporte deux groupes de templates :
  - TECH : smartphones, PC, périphériques, audio, wearables, stockage, imprimantes
  - APPLIANCE : électroménager (specs intégrées au LONG, pas de fichier SPECS séparé)

Usage :
  python build-product-pack-v2.py --data "path/to/pack-data.json" --outdir "path/to/output" --modele "slug-modele"
"""

import json
import os
import sys
import argparse
import csv
import re
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Any


# ==============================================================================
# Constantes de style (extraites des templates HTML maîtres)
# ==============================================================================

# Styles communs partagés par TECH et APPLIANCE
STYLE_CONTAINER = (
    "font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "Roboto, sans-serif; color: #1d1d1f; line-height: 1.6; max-width: 100%; "
    "margin: 0 auto; padding: 40px 20px;"
)
STYLE_H1 = "font-size: clamp(24px, 5vw, 42px); font-weight: 700; line-height: 1.25; margin-bottom: 25px; color: #1d1d1f; text-align: center;"
STYLE_DARK_BOX = (
    "background-color: #1d1d1f; color: #ffffff; border-radius: 16px; "
    "padding: 32px; margin: 35px 0; box-shadow: 0 8px 24px rgba(0,0,0,0.08);"
)
STYLE_BOX_TITLE = "color: #ff4800; text-transform: uppercase; letter-spacing: 2px; font-size: 0.95em; font-weight: 700;"
STYLE_INTRO_P = "font-size: clamp(16px, 2.5vw, 19px); line-height: 1.7; margin-bottom: 40px; color: #1d1d1f;"
STYLE_H2 = (
    "font-size: clamp(20px, 3.5vw, 28px); font-weight: 700; color: #1d1d1f; margin-top: 50px; "
    "margin-bottom: 20px; border-left: 5px solid #ff4800; padding-left: 15px;"
)
STYLE_BODY_P = "font-size: 16px; line-height: 1.75; margin-bottom: 20px;"
STYLE_CTA_CONTAINER = "display: flex; gap: 15px; justify-content: center; margin: 30px 0;"
STYLE_CTA_PRIMARY = (
    "background-color: #ff4800; color: #ffffff !important; padding: 16px 32px; "
    "text-decoration: none; border-radius: 30px; font-weight: 600; "
    "text-align: center; flex-grow: 1; max-width: 300px;"
)
STYLE_CTA_SECONDARY = (
    "background-color: #1d1d1f; color: #ffffff !important; padding: 16px 32px; "
    "text-decoration: none; border-radius: 30px; font-weight: 600; "
    "text-align: center; flex-grow: 1; max-width: 300px;"
)

# Styles spécifiques au tableau TECH (TEMPLATE_SPECS.html)
TECH_TABLE_STYLE = (
    "width: 100%; border-collapse: collapse; margin: 30px 0; background: #ffffff; "
    "border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06);"
)
TECH_TH_STYLE = "background-color: #ff4800; color: #ffffff; padding: 20px; text-align: left; font-weight: 600; font-size: 16px;"
TECH_SECTION_TD_STYLE = (
    "background-color: #f5f5f7; padding: 24px 12px; vertical-align: top; "
    "font-weight: 600; color: #ff4800; font-size: 15px;"
)

# Styles spécifiques au tableau APPLIANCE (TEMPLATE_APPLIANCE_LONG.html)
APPLIANCE_SECTION_TD_STYLE = (
    "background-color: #f5f5f7; padding: 20px 15px; vertical-align: top; "
    "font-weight: 600; color: #ff4800;"
)

# Domaine boutique par défaut
STORE_CART_URL = "https://my-estore.com/panier/"


# ==============================================================================
# Fonctions utilitaires
# ==============================================================================

def sanitize_value(valeur: str) -> str:
    """Remplace les valeurs N/A interdites par une formulation acceptable."""
    if str(valeur).strip().upper() in ["N/A", "NA", "N/D", "NON DISPONIBLE", "INCONNU", "NON DÉFINI", ""]:
        return "Donnée non communiquée"
    return str(valeur)


def convert_weight_to_kg(weight_str: str, group: str = "tech") -> str:
    """
    Normalise une chaîne représentant le poids.
    Si la valeur est en grammes, elle est convertie en kilogrammes (kg).
    Si la valeur est déjà en kg, elle est normalisée en kg.
    Utilise le groupe ('tech' ou 'appliance') pour lever les ambiguïtés en l'absence d'unité.
    """
    if not weight_str:
        return ""
    import re
    w_clean = weight_str.lower().replace("\xa0", " ").strip()
    if any(x in w_clean for x in ["non applicable", "not applicable", "n/a", "none", "sans"]):
        return ""
    num_match = re.search(r'(\d+(?:[.,]\d+)?)', w_clean)
    if not num_match:
        return weight_str
    val_str = num_match.group(1).replace(",", ".")
    try:
        val = float(val_str)
    except ValueError:
        return weight_str
    
    # 1. Unité explicite kg
    if re.search(r'\b(kg|kilo|kilogramme|kilogrammes|kilogram|kilograms)\b', w_clean):
        val_kg_str = f"{val:.3f}".rstrip('0').rstrip('.')
        return f"{val_kg_str} kg"
        
    # 2. Unité explicite g
    if re.search(r'\b(g|gr|gramme|grammes|gram|grams)\b', w_clean) or (w_clean.endswith("g") and not w_clean.endswith("kg")):
        val_kg = val / 1000.0
        val_kg_str = f"{val_kg:.3f}".rstrip('0').rstrip('.')
        return f"{val_kg_str} kg"
        
    # 3. Pas d'unité spécifiée (heuristique intelligente selon le groupe)
    if group == "tech":
        # Pour les produits high-tech, si le poids >= 2.0 (ex: 15, 45, 190), c'est probablement en grammes.
        # Si c'est < 2.0 (ex: 1.2, 0.35, 1.8), c'est probablement déjà en kg.
        if val >= 2.0:
            val_kg = val / 1000.0
        else:
            val_kg = val
    else:
        # Pour l'électroménager, les valeurs sans unité sont presque toujours en kg.
        if val >= 1000.0:
            val_kg = val / 1000.0
        else:
            val_kg = val
            
    val_kg_str = f"{val_kg:.3f}".rstrip('0').rstrip('.')
    return f"{val_kg_str} kg"


def detect_group(data: dict) -> str:
    """Détecte le groupe du produit : 'tech' ou 'appliance'."""
    # Priorité au champ explicite
    group = data.get("template_group", "").upper()
    if group == "APPLIANCE":
        return "appliance"
    return "tech"


def clean_html(html: str) -> str:
    """Nettoie le HTML pour le CSV : retire les commentaires et minifie les espaces."""
    # 1. Supprimer les commentaires HTML <!-- ... -->
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # 2. Remplacer les sauts de ligne et tabulations par des espaces
    html = html.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # 3. Réduire les espaces multiples à un seul
    html = re.sub(r'\s+', ' ', html)
    # 4. Nettoyage final des bords
    return html.strip()


def extract_product_brand_model(data: dict) -> Tuple[str, str, str]:
    """Extrait intelligemment (brand, model, full_model) de n'importe quel JSON (V3.4 ou legacy pack-data)."""
    metadata = data.get("metadata", {})
    prod_id = data.get("product_identity", {})
    
    brand = metadata.get("target_brand") or prod_id.get("brand") or "HiFuture"
    model = metadata.get("target_model") or prod_id.get("commercial_name") or "Produit"
    
    if not model or model in ["Modèle", "Produit"]:
        model = prod_id.get("commercial_name") or metadata.get("target_model") or "Produit"

    if not brand or brand == "Marque":
        brand = prod_id.get("brand") or metadata.get("target_brand") or "HiFuture"
        
    if model.lower().startswith(brand.lower()):
        full_model = model
    else:
        full_model = f"{brand} {model}"
        
    return brand, model, full_model


def format_seo_title_and_description(data: dict) -> Tuple[str, str]:
    """
    Extrait et préserve le SEO Title et la Meta Description directement depuis le JSON Parent (V3.4).
    Source de vérité unique : la section SEO du JSON rédigée par l'agent.
    """
    brand, model, full_model = extract_product_brand_model(data)
    
    seo = (
        data.get("seo") 
        or data.get("long_description", {}).get("seo") 
        or data.get("short_description", {}).get("seo") 
        or {}
    )
    
    title_raw = seo.get("meta_title", "").strip()
    desc_raw = seo.get("meta_description", "").strip()
    
    # 1. SEO Title : Priorité absolue au JSON Parent rédigé
    if title_raw:
        title = title_raw
    else:
        title = f"{full_model} | My-eStore"
        
    # 2. Meta Description : Priorité absolue au JSON Parent rédigé
    if desc_raw:
        desc = desc_raw
    else:
        desc = f"Achetez le {full_model} au meilleur prix chez My-eStore. Produit sous garantie officielle avec livraison rapide en Côte d'Ivoire."
            
    return title, desc


# ==============================================================================
# Générateur : SHORT (identique pour TECH et APPLIANCE)
# ==============================================================================

def build_short_html(data: dict) -> str:
    """Génère le fichier short-*.html conforme aux normes V3.4 et TEMPLATE_SHORT.html."""
    sd = data.get("short_description", {})
    ld = data.get("long_description", {})
    brand, model, full_model = extract_product_brand_model(data)

    # V3.4 vs Legacy extraction
    if isinstance(sd, dict):
        short_text = sd.get("text", "").strip()
        brand_line = sd.get("brand_line", sd.get("title_format", ""))
        hook = sd.get("hook", "").strip()
        synth = sd.get("synthesis_paragraph", sd.get("teaser", "")).strip() or short_text
        features_list = sd.get("top_features_detailed", sd.get("features", []))
    else:
        short_text = str(sd).strip()
        brand_line = ""
        hook = ""
        synth = short_text
        features_list = []

    # En-tête / Accroche
    if not hook:
        if brand_line and "TAGLINE" not in brand_line:
            bl_lower = brand_line.lower().strip()
            model_lower = model.lower().strip()
            full_model_lower = full_model.lower().strip()
            model_short = model_lower.replace(brand.lower(), "").strip()

            if (model_lower in bl_lower or full_model_lower in bl_lower 
                or (model_short and model_short in bl_lower)):
                hook = brand_line
            else:
                hook = f"{full_model} : {brand_line}"
        else:
            hook = f"{full_model} : Spécifications et Performances"

    # Anti-doublon robuste (ex: "Xiaomi Redmi A7 : XIAOMI REDMI A7 : ...")
    m_dup = re.match(r'^([^:]+?)\s*:\s*([^:]+?)\s*:(.*)$', hook, flags=re.IGNORECASE)
    if m_dup:
        part1 = m_dup.group(1).strip().lower()
        part2 = m_dup.group(2).strip().lower()
        if part1 == part2 or part1 in part2 or part2 in part1:
            hook = f"{m_dup.group(2).strip()} :{m_dup.group(3)}"

    html = f"<p><strong>{hook}</strong></p>\n\n"

    if synth:
        html += f"<p>{synth}</p>\n\n"

    # Liste des caractéristiques clés (Fallback V3.4 sur experience_box)
    if not features_list:
        box_items = ld.get("experience_box", {}).get("items", [])
        if box_items:
            features_list = box_items
        else:
            add_feats = data.get("key_specifications", {}).get("additional_features", [])
            features_list = [{"feature": f, "benefice": "Spécification certifiée"} for f in add_feats]

    if features_list:
        html += "<ul>\n"
        for feat in features_list:
            if isinstance(feat, dict):
                f_name = feat.get("feature", "").strip()
                f_ben = feat.get("benefice", "").strip()
                if f_name and f_ben:
                    html += f"  <li><strong>{f_name} :</strong> {f_ben}.</li>\n"
                elif f_name:
                    html += f"  <li><strong>{f_name}.</strong></li>\n"
            elif isinstance(feat, str) and feat.strip():
                html += f"  <li>{feat.strip()}</li>\n"
        html += "</ul>\n\n"
    
    # Fin de description : Slogan Final (Style épuré)
    slogan = sd.get("slogan_final", "")
    if slogan:
        html += f"<p><em>{slogan}</em></p>\n\n"

    # Métadonnées SEO
    seo = data.get("seo", {})
    seo_title, meta_desc = format_seo_title_and_description(data)
    html += f"<!-- AIOSEO METADATA:\n"
    html += f"SEO Title: {seo_title}\n"
    html += f"Meta Description: {meta_desc}\n"
    html += f"-->"

    # Génération et insertion des KEYWORDS UTILES (15 minimum, axés sur les specs)
    focus_kw = seo.get("focus_keyword", "")
    lsi_kws = seo.get("lsi_keywords", [])
        
    final_kws = []
    if focus_kw:
        final_kws.append(focus_kw.strip())
        
    for kw in lsi_kws:
        kw_clean = kw.strip()
        if kw_clean and kw_clean not in final_kws:
            final_kws.append(kw_clean)
            
    # Extraire des informations techniques du pack pour générer des mots-clés utiles
    brand = data.get("metadata", {}).get("target_brand", "Blackview")
    model = data.get("metadata", {}).get("target_model", "Produit")
    if model.lower().startswith(brand.lower()):
        full_model = model
    else:
        full_model = f"{brand} {model}"
        
    # Récupérer les specs utiles
    specs = data.get("full_specs", {})
    ram = ""
    rom = ""
    battery = ""
    camera = ""
    proc = ""
    
    for section in specs.get("sections", []):
        sec_name = section.get("name", "").upper()
        for row in section.get("rows", []):
            label = row.get("label", "").upper()
            val = row.get("valeur", "")
            if "MÉMOIRE VIVE" in label or "RAM" in label:
                ram = val
            elif "STOCKAGE" in label or "ROM" in label:
                rom = val
            elif "BATTERIE" in label or "CAPACITÉ" in label:
                battery = val
            elif "PRINCIPAL" in label or "MÉGAPIXEL" in label or "PHOTO" in label:
                camera = val
            elif "PROCESSEUR" in label or "SOC" in label:
                proc = val

    def clean_spec_val(v_str):
        if not v_str:
            return ""
        v_l = str(v_str).lower().strip()
        if any(x in v_l for x in ["non applicable", "not applicable", "n/a", "non disponible", "none", "sans", "n/d"]):
            return ""
        return str(v_str).strip()

    ram = clean_spec_val(ram)
    rom = clean_spec_val(rom)
    battery = clean_spec_val(battery)
    camera = clean_spec_val(camera)
    proc = clean_spec_val(proc)

    if not ram or not rom:
        for v in data.get("variants", []):
            conf = v.get("configurations", {})
            if "ram" in conf: ram = clean_spec_val(conf["ram"])
            if "storage" in conf: rom = clean_spec_val(conf["storage"])
            
    specs_keywords = []
    if ram and rom:
        specs_keywords.append(f"{full_model} {ram}/{rom}")
        specs_keywords.append(f"{full_model} {ram} RAM")
        specs_keywords.append(f"{full_model} {rom} Stockage")
    if battery:
        specs_keywords.append(f"{full_model} {battery}")
        specs_keywords.append(f"batterie {full_model}")
    if camera:
        cam_num = re.search(r'\d+', camera)
        if cam_num:
            specs_keywords.append(f"{full_model} photo {cam_num.group()}MP")
    if proc:
        specs_keywords.append(f"{full_model} processeur {proc}")
        
    specs_keywords.extend([
        f"fiche technique {full_model}",
        f"{full_model} prix FCFA",
        f"achat {full_model} Abidjan",
        f"{full_model} My-eStore",
        f"caractéristiques {full_model}",
        f"avis {full_model}",
        f"test {full_model}",
        f"spécifications {full_model}",
        f"promo {full_model}"
    ])
    
    for kw in specs_keywords:
        if len(final_kws) >= 15:
            break
        if kw not in final_kws:
            final_kws.append(kw)
            
    while len(final_kws) < 15:
        final_kws.append(f"mot clé {len(final_kws) + 1} {full_model}")
        
    html += f"\n\n<!-- KEYWORDS UTILES:\n"
    html += f"Focus Keyword: {focus_kw}\n"
    html += f"LSI Keywords: {', '.join(final_kws[1:])}\n"
    html += f"-->"

    return html


# ==============================================================================
# Générateur : LONG TECH (basé sur TEMPLATE_LONG.html chargé dynamiquement)
# ==============================================================================

def get_template_content(template_name: str) -> str:
    """Charge le contenu d'un template HTML depuis le dossier Templates."""
    # Recherche du dossier Templates en remontant
    base_dir = "."
    for _ in range(3):
        t_dir = os.path.join(base_dir, "Templates")
        if os.path.isdir(t_dir):
            path = os.path.join(t_dir, template_name)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
        base_dir = os.path.join(base_dir, "..")
    return ""

def render_tech_specs_table_html(full_specs: dict) -> str:
    """Génère dynamiquement la table HTML des spécifications à partir de full_specs (sections listes ou dictionnaires de catégories). Mobile-first responsive."""
    if not full_specs:
        return ""

    sections = full_specs.get("sections", [])
    if not sections and isinstance(full_specs, dict):
        section_titles = {
            "design_physique": "Design & Physique",
            "affichage_ecran": "Affichage & Écran",
            "performances_systeme": "Performances & Système",
            "photographie_video": "Photographie & Vidéo",
            "batterie_alimentation": "Batterie & Alimentation",
            "batterie_charge": "Batterie & Charge",
            "batterie_autonomie": "Batterie & Autonomie",
            "acoustique_audio": "Acoustique & Audio",
            "connectivite_reseau": "Connectivité & Réseau",
            "connectivite_fonctions": "Connectivité & Fonctions",
            "connectivite_capteurs": "Connectivité & Capteurs",
        }
        for sec_key, sec_val in full_specs.items():
            if sec_key in ["header", "footer", "disclaimer", "sources"]:
                continue
            if isinstance(sec_val, dict):
                sec_name = section_titles.get(sec_key, sec_key.replace("_", " ").title())
                rows = []
                for label, val in sec_val.items():
                    rows.append({"label": str(label), "valeur": str(val)})
                if rows:
                    sections.append({"name": sec_name, "rows": rows})

    if not sections:
        return ""

    table_html = []
    table_html.append('    <div class="specs-table-wrapper" style="overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; max-width: 100%; border-radius: 12px; margin: 25px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">')
    table_html.append('    <table class="product-specs-table"')
    table_html.append('        style="width: 100%; min-width: 480px; border-collapse: collapse; background: #ffffff;">')
    table_html.append('        <thead>')
    table_html.append('            <tr>')
    table_html.append('                <th style="background-color: #ff4800; color: #ffffff; padding: 13px 10px; text-align: left; font-weight: 600; font-size: 13px; width: 22%; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">Spécifications</th>')
    table_html.append('                <th style="background-color: #ff4800; color: #ffffff; padding: 13px 10px; text-align: left; font-weight: 600; font-size: 13px; width: 28%; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">Caractéristique</th>')
    table_html.append('                <th style="background-color: #ff4800; color: #ffffff; padding: 13px 10px; text-align: left; font-weight: 600; font-size: 13px; width: 50%; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">Détails</th>')
    table_html.append('            </tr>')
    table_html.append('        </thead>')
    table_html.append('        <tbody>')

    total_sections = len(sections)
    for sec_idx, section in enumerate(sections):
        sec_name = section.get("name", "")
        rows = section.get("rows", [])
        if not rows:
            continue
        rowspan = len(rows)
        border_top = ' border-top: 3px solid #ff4800;' if sec_idx > 0 else ''

        for r_idx, row in enumerate(rows):
            label = row.get("label", "").strip()
            valeur = sanitize_value(row.get("valeur", ""))
            bg_color = "#ffffff" if r_idx % 2 == 0 else "#fbfbfb"
            is_last_row = (sec_idx == total_sections - 1) and (r_idx == rowspan - 1)
            border_bottom = '' if is_last_row else ' border-bottom: 1px solid #f5f5f7;'

            table_html.append(f'            <tr style="background-color: {bg_color};{border_bottom}{border_top if r_idx == 0 else ""}">')
            if r_idx == 0:
                table_html.append(f'                <td rowspan="{rowspan}" style="background-color: #f5f5f7; padding: 14px 10px; vertical-align: top; font-weight: 600; color: #ff4800; font-size: 13px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">{sec_name}</td>')
            table_html.append(f'                <td style="padding: 11px 10px; color: #86868b; font-size: 13px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">{label}</td>')
            table_html.append(f'                <td style="padding: 11px 10px; color: #1d1d1f; font-size: 13px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">{valeur}</td>')
            table_html.append('            </tr>')

    table_html.append('        </tbody>')
    table_html.append('    </table>')
    table_html.append('    </div>')

    return "\n".join(table_html)


def build_long_tech_html(data: dict) -> str:
    """Génère le fichier long-*.html en utilisant TEMPLATE_LONG.html comme base."""
    ld = data.get("long_description", {})
    full_specs = data.get("full_specs") or ld.get("full_specs", {})
    woo = data.get("woocommerce_csv", {})
    seo = ld.get("seo", {})
    
    template = get_template_content("TEMPLATE_LONG.html")
    if not template:
        print("[!] TEMPLATE_LONG.html introuvable, fallback sur génération vide.")
        return "<!-- Error: Template not found -->"

    brand, model, full_model = extract_product_brand_model(data)

    OFFICIAL_DISCLAIMER = "Avis de non-responsabilité (Spécifications) : Les caractéristiques techniques et les images de l'appareil sont fournies à titre purement indicatif et proviennent des données officielles des constructeurs et autres sources. Des variations peuvent survenir selon les lots de fabrication et les régions d'importation. Nous vous invitons à vérifier scrupuleusement la configuration exacte que vous avez sélectionnée dans vos options d'achat avant de valider définitivement votre commande."

    # 1. Variables de base & Fallbacks V3.4
    key_specs = data.get("key_specifications", {})
    replacements = {
        "<!-- VAR_MARQUE -->": brand,
        "<!-- VAR_MODELE -->": model,
        "<!-- VAR_RESUME_PHRASE -->": full_specs.get("header", {}).get("subtitle", "Spécifications complètes."),
        "<!-- SPEC_DISCLAIMER -->": full_specs.get("footer", {}).get("disclaimer", OFFICIAL_DISCLAIMER),
        "<!-- TITRE_H1 -->": ld.get("h1", "Titre Produit"),
        "<!-- INTRO_PARAGRAPHE -->": ld.get("intro_paragraph", ""),
        "<!-- SPEC_PERFORMANCES_PROCESSEUR_SOC -->": key_specs.get("processor", "Non spécifié"),
        "<!-- SPEC_PERFORMANCES_MEMOIRE_VIRTUELLE_EXTENSION -->": key_specs.get("ram_extension", "Non disponible"),
        "<!-- SPEC_AUDIO_CONFIGURATION_AUDIO -->": key_specs.get("audio_config", "Haut-parleurs intégrés"),
        "<!-- SPEC_AUDIO_TECHNOLOGIES_AUDIO -->": key_specs.get("audio_tech", "Stéréo HD"),
        "<!-- SPEC_BATTERIE_CHARGE_CAPACITE -->": key_specs.get("battery_capacity", "Standard"),
        "<!-- SPEC_BATTERIE_CHARGE_VITESSE_DE_CHARGE -->": key_specs.get("charging_wired", "Charge Rapide"),
        "<!-- SPEC_CONNECTIVITE_SYSTEMES_DE_NAVIGATION_GPS -->": key_specs.get("navigation_gps", "GPS, GLONASS, Beidou, Galileo"),
        "<!-- SPEC_CONNECTIVITE_CARD_SLOT_ET_CONFIGURATION -->": key_specs.get("card_slot", "Dual SIM / MicroSD"),
        "<!-- SPEC_CONNECTIVITE_MISES_A_JOUR -->": "Selon politique constructeur",
        "<!-- SPEC_CONNECTIVITE_FONCTIONS_IA -->": "Non spécifié",
        "<!-- ENERGY_RATING -->": data.get("energy_rating", "Non spécifiée (voir sur emballage constructeur)"),
    }

    # 2. Experience Box
    box = ld.get("experience_box", {})
    replacements["<!-- BOX_TITLE -->"] = box.get("box_title", "")
    box_html = ""
    for item in box.get("items", []):
        box_html += f'<li style="list-style: none !important; margin-bottom: 10px;"><strong>{item.get("feature", "")}</strong> — {item.get("benefice", "")}.</li>\n'
    replacements["<!-- BOX_ITEMS -->"] = box_html

    # 3. Sections (H2 + Paragraphes)
    sections = ld.get("sections", [])
    for i, sec in enumerate(sections):
        replacements[f"<!-- SECTION_{i+1}_TITLE -->"] = sec.get("h2_title", "")
        p_html = ""
        for p in sec.get("paragraphs", []):
            p_html += f'<p style="{STYLE_BODY_P}">{p}</p>\n'
        replacements[f"<!-- SECTION_{i+1}_CONTENT -->"] = p_html

    # 4. Spécifications Détaillées (Remplacement dynamique de la table V3.4)
    dynamic_table = render_tech_specs_table_html(full_specs)

    # 5. Sources
    footer = full_specs.get("footer", {})
    sources = list(footer.get("sources", []))
    
    # Filtrer et nettoyer les sources de footer pour ne garder que les URLs valides (commençant par http)
    valid_sources = []
    for src in sources:
        url_val = src.get("url", "").strip()
        if url_val and url_val.lower().startswith("http") and url_val != "#":
            valid_sources.append({"name": src.get("name", "Source"), "url": url_val})
            
    # Si pas assez de sources valides, essayer d'ajouter celles de sourcing.specs_sources
    if len(valid_sources) < 3:
        sourcing_sources = data.get("sourcing", {}).get("specs_sources", [])
        for src in sourcing_sources:
            url_val = src.get("url", "").strip()
            if url_val and url_val.lower().startswith("http") and url_val != "#":
                # Éviter les doublons de domaine/URL
                if not any(url_val == vs.get("url") for vs in valid_sources):
                    valid_sources.append({"name": src.get("name", "Source"), "url": url_val})
                    
    # S'assurer d'avoir toujours le site officiel constructeur pour la véracité
    official_url = ""
    has_official = any(official_url in src.get("url", "") for src in valid_sources)
    if not has_official:
        valid_sources.insert(0, {"name": "", "url": official_url})
        
    # Compléter jusqu'à 3 sources avec "Recherche spécialisée IA" et lien mort (#) constructeur
    extended_sources = list(valid_sources)
    while len(extended_sources) < 3:
        extended_sources.append({
            "name": "Recherche spécialisée IA",
            "url": ""
        })
        
    for i, src in enumerate(extended_sources[:3]):
        replacements[f"<!-- SOURCE_URL_{i+1} -->"] = src.get("url", "")
        replacements[f"<!-- SOURCE_NAME_{i+1} -->"] = src.get("name", "Source")

    # 6. CTA
    cta = ld.get("cta", {})
    replacements["<!-- CTA_OFFICIAL_URL -->"] = cta.get("official_link", "#")

    # 7. SEO (Remplacement des phrases types du template)
    seo_title, meta_desc = format_seo_title_and_description(data)
    replacements["Titre SEO 50-60 caractères avec mot-clé focus"] = seo_title
    replacements["Description SEO 155-160 caractères avec bénéfices et CTA"] = meta_desc
    replacements["Mot-clé principal du produit"] = seo.get("focus_keyword", "")
    replacements["5-8 mots-clés sémantiquement liés, séparés par des virgules"] = ", ".join(seo.get("lsi_keywords", []))

    # Application des remplacements
    html = template

    # Remplacement dynamique de la table des spécifications
    if dynamic_table:
        import re
        if '<div class="specs-table-wrapper"' in html:
            html = re.sub(r'<div class="specs-table-wrapper"[^>]*>.*?<table class="product-specs-table".*?</table>\s*</div>', dynamic_table, html, flags=re.DOTALL)
        else:
            html = re.sub(r'<table class="product-specs-table".*?</table>', dynamic_table, html, flags=re.DOTALL)

    # A. Brand Doubling & Placeholder Cleanup
    html = html.replace("<!-- VAR_MARQUE --> <!-- VAR_MODELE -->", full_model)
    html = html.replace("Marque Modèle", full_model)
    html = html.replace("[MARQUE] [MODELE]", full_model)
    html = html.replace("[MARQUE]", brand)
    html = html.replace("[MODELE]", model)
    
    # B. Duplicated spec intro sentences
    subtitle_val = full_specs.get("header", {}).get("subtitle", "")
    if subtitle_val.lower().startswith("caractéristiques officielles et détaillées"):
        # Replace the entire template sentence to avoid duplication
        target_block = f"Consultez les caractéristiques officielles et détaillées du <strong>{full_model}</strong>.\n            <!-- VAR_RESUME_PHRASE -->."
        html = html.replace(target_block, f"Consultez les caractéristiques officielles et détaillées du <strong>{full_model}</strong>.")
        target_block_alt = f"Consultez les caractéristiques officielles et détaillées du <strong>{full_model}</strong>. <!-- VAR_RESUME_PHRASE -->."
        html = html.replace(target_block_alt, f"Consultez les caractéristiques officielles et détaillées du <strong>{full_model}</strong>.")
        
    # C. Duplicated disclaimer & Official Disclaimer Notice V3.4
    disclaimer_val = full_specs.get("footer", {}).get("disclaimer", OFFICIAL_DISCLAIMER)
    if not disclaimer_val or "Avis de non-responsabilité" not in disclaimer_val:
        disclaimer_val = OFFICIAL_DISCLAIMER

    target_disclaimer_block = "Données extraites des fiches techniques\n            officielles. <!-- SPEC_DISCLAIMER -->"
    html = html.replace(target_disclaimer_block, disclaimer_val)
    target_disclaimer_block_alt = "Données extraites des fiches techniques officielles. <!-- SPEC_DISCLAIMER -->"
    html = html.replace(target_disclaimer_block_alt, disclaimer_val)

    for key, val in replacements.items():
        html = html.replace(key, str(val))

    # --- SÉCURITÉ QUALITÉ V2.1 : Détection des placeholders non remplis ---
    import re
    # Regex qui capture tout le contenu des placeholders non remplacés
    orphans = re.findall(r"<!-- ((?:SPEC_|VAR_|SECTION_|BOX_|TITRE_|INTRO_)[A-Z0-9_/-]+) -->", html)
    if orphans:
        print(f"\n[CRITICAL ERROR] Placeholders non remplis détectés dans le HTML :")
        for orphan in orphans:
            print(f"   - {orphan}")
        print("[!] Le build échouera après l'écriture du fichier pour debugging.")
        # On ne sys.exit pas ici, on laisse le script principal écrire et échouer plus tard
    # -----------------------------------------------------------------------

    return html


# ==============================================================================
# Générateur : LONG APPLIANCE (basé sur TEMPLATE_APPLIANCE_LONG.html)
# ==============================================================================

def build_long_appliance_html(data: dict) -> str:
    """Génère le fichier long-*.html conforme à TEMPLATE_APPLIANCE_LONG.html."""
    ld = data.get("long_description", {})
    seo = ld.get("seo", {})
    h1 = ld.get("h1", "Titre")
    box = ld.get("experience_box", {})
    intro = ld.get("intro_paragraph", "")
    sections = ld.get("sections", [])
    specs_table = ld.get("full_specs_table", {})
    sources = ld.get("sources_footer", {})
    cta = ld.get("cta", {})

    html = f'<div id="product-long-description"\n  style="{STYLE_CONTAINER}">\n\n'
    html += f'  <h1 style="{STYLE_H1}">\n    {h1}\n  </h1>\n\n'

    # Experience Box
    if box:
        html += f'  <div\n    style="{STYLE_DARK_BOX}">\n'
        html += f'    <p style="margin: 0 0 20px 0;"><strong\n        style="{STYLE_BOX_TITLE}">{box.get("box_title", "")}</strong>\n    </p>\n'
        html += '    <ul style="list-style: none !important; padding-left: 0; margin: 0; color: #ffffff;">\n'
        for item in box.get("items", []):
            html += f'      <li style="list-style: none !important; margin-bottom: 10px;">\n'
            html += f'        <strong>{item.get("feature", "")}</strong> —\n'
            html += f'        {item.get("benefice", "")}.\n'
            html += f'      </li>\n'
        html += '    </ul>\n'
        html += '  </div>\n\n'

    # Intro paragraph
    html += f'  <p style="{STYLE_INTRO_P}">\n    {intro}\n  </p>\n\n'

    # 3 sections H2 + P + P (titres imposés pour Appliance)
    for sec in sections:
        html += f'  <h2\n    style="{STYLE_H2}">\n    {sec.get("h2_title", "")}</h2>\n'
        for p in sec.get("paragraphs", []):
            html += f'  <p style="{STYLE_BODY_P}">\n    {p}\n  </p>\n'
        html += '\n'

    # Fiche technique complète (intégrée au LONG pour Appliance)
    html += f'  <h2\n    style="{STYLE_H2}">\n    {specs_table.get("title", "Fiche Technique Complète")}</h2>\n\n'

    col_widths = specs_table.get("column_widths", ["30%", "30%", "40%"])
    col_headers = specs_table.get("column_headers", ["Catégorie", "Caractéristique", "Détails"])

    html += '  <div class="specs-table-wrapper" style="overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; max-width: 100%; border-radius: 12px; margin: 25px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">\n'
    html += '  <table class="product-specs-table"\n'
    html += '    style="width: 100%; min-width: 480px; border-collapse: collapse; background: #ffffff;">\n'
    html += '    <thead>\n'
    html += '      <tr style="background-color: #ff4800; color: #ffffff;">\n'
    for i, header in enumerate(col_headers):
        html += f'        <th style="padding: 13px 10px; text-align: left; font-weight: 600; font-size: 13px; width: {col_widths[i]}; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">{header}</th>\n'
    html += '      </tr>\n'
    html += '    </thead>\n'
    html += '    <tbody>\n'

    sections_list = specs_table.get("sections", [])
    total_sections = len(sections_list)
    for sec_idx, section in enumerate(sections_list):
        rows = section.get("rows", [])
        if not rows:
            continue
        rowspan = len(rows)
        border_top = ' border-top: 3px solid #ff4800;' if sec_idx > 0 else ''
        for idx, row in enumerate(rows):
            is_last_row = (sec_idx == total_sections - 1) and (idx == rowspan - 1)
            border_bottom = '' if is_last_row else ' border-bottom: 1px solid #f5f5f7;'
            html += f'      <tr style="{border_bottom}{border_top if idx == 0 else ""}">\n'
            if idx == 0:
                html += f'        <td rowspan="{rowspan}"\n          style="{APPLIANCE_SECTION_TD_STYLE}">\n          {section.get("name", "")}</td>\n'
            html += f'        <td style="padding: 11px 10px; color: #86868b; font-size: 13px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">{row.get("label", "")}</td>\n'
            html += f'        <td style="padding: 11px 10px; color: #1d1d1f; font-size: 13px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">{sanitize_value(row.get("valeur", ""))}</td>\n'
            html += '      </tr>\n'

    html += '    </tbody>\n'
    html += '  </table>\n'
    html += '  </div>\n\n'

    # Sources footer (spécifique Appliance)
    src = sources.get("source_link", {})
    cert = sources.get("certification", "")
    html += '  <div style="font-size: 0.8em; color: #86868b; margin-top: 10px; text-align: center; margin-bottom: 30px;">\n'
    html += '    <strong>Sources & Crédibilité :</strong>\n'
    html += f'    <a href="{src.get("url", "#")}" style="color: #ff4800; text-decoration: none;">{src.get("name", "Fiche constructeur officielle")}</a> •\n'
    html += f'    <span style="font-style: italic;">{cert}</span>\n'
    html += '  </div>\n\n'

    # CTA buttons
    html += '  <div style="display: flex; gap: 15px; justify-content: center; margin: 30px 0;">\n'
    html += '    <a style="background-color: #ff4800; color: #ffffff !important; padding: 16px 32px; text-decoration: none; border-radius: 30px; font-weight: 600; text-align: center; flex-grow: 1; max-width: 300px;" href="#">Remonter pour commander</a>\n'
    html += '    <a style="background-color: #1d1d1f; color: #ffffff !important; padding: 16px 32px; text-decoration: none; border-radius: 30px; font-weight: 600; text-align: center; flex-grow: 1; max-width: 300px;" href="https://my-estore.com/boutiques-officielles/">Nos Boutiques Officielles</a>\n'
    html += '  </div>\n'
    html += '</div>\n\n'

    # Commentaires SEO pour facilitation des opérateurs humains (AIOSEO back-office)
    seo_title, meta_desc = format_seo_title_and_description(data)
    html += f"<!-- AIOSEO METADATA:\n"
    html += f"SEO Title: {seo_title}\n"
    html += f"Meta Description: {meta_desc}\n"
    html += f"-->\n\n"
    html += f"<!-- KEYWORDS UTILES:\n"
    html += f"Focus Keyword: {seo.get('focus_keyword', '')}\n"
    html += f"LSI Keywords: {', '.join(seo.get('lsi_keywords', []))}\n"
    html += f"-->\n"

    return html


# ==============================================================================
# Gestion des fichiers Prix
# ==============================================================================

def create_or_update_price_file(base_dir: str, marque: str, serie: str, nom_complet: str, prix_cfa) -> str:
    """Crée ou met à jour le fichier prix dans Templates/Pricing/."""
    price_dir = os.path.join(base_dir, "Pricing")
    if not os.path.exists(price_dir):
        price_dir = os.path.join(base_dir, "Templates", "Pricing")
    os.makedirs(price_dir, exist_ok=True)

    file_name = f"prix-{marque}-{serie}-v2.csv".lower().replace(" ", "-")
    file_path = os.path.join(price_dir, file_name)

    file_exists = os.path.isfile(file_path)
    with open(file_path, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Modèle", "Variante", "Prix Estimé FCFA", "Prix USD", "Notes"])
        writer.writerow([
            nom_complet, "Standard", prix_cfa, "",
            f"Généré V2.1 le {datetime.now().strftime('%Y-%m-%d')}"
        ])
    return file_path


def process_tags(original_tags: str, ram: str, rom: str, network: str, group: str) -> str:
    """Nettoie, enrichit et limite les tags à 12 maximum."""
    tags_list = []
    if original_tags:
        tags_list = [t.strip() for t in original_tags.split(",") if t.strip()]
        
    cleaned_list = []
    for tag in tags_list:
        tag_lower = tag.lower()
        if "côte" in tag_lower and "ivoire" in tag_lower:
            continue
        if "lsi keywords" in tag_lower or "lsi keyword" in tag_lower:
            continue
        if "nonapplicable" in tag_lower:
            continue
        if not any(x.lower() == tag_lower for x in cleaned_list):
            cleaned_list.append(tag)
            
    if group == "tech":
        if ram:
            clean_ram = ram.upper().replace("GB", "Go").replace("TB", "To")
            if not any(x.lower() == clean_ram.lower() for x in cleaned_list):
                cleaned_list.append(clean_ram)
            ram_suffix = f"{clean_ram} RAM"
            if not any(x.lower() == ram_suffix.lower() for x in cleaned_list):
                cleaned_list.append(ram_suffix)
        if rom:
            clean_rom = rom.upper().replace("GB", "Go").replace("TB", "To")
            if not any(x.lower() == clean_rom.lower() for x in cleaned_list):
                cleaned_list.append(clean_rom)
        if network:
            net_tag = network.upper()
            if not any(x.lower() == net_tag.lower() for x in cleaned_list):
                cleaned_list.append(net_tag)
                
    final_tags = cleaned_list[:12]
    return ", ".join(final_tags)


# ==============================================================================
# Génération CSV WooCommerce
# ==============================================================================

def generate_csv(data: dict, outdir: str, modele: str, serie: str = None):
    """Génère le fichier CSV d'import WooCommerce avec les colonnes exactes du template CSV en mode append par série."""
    woo = data.get("woocommerce_csv", {})

    # Les colonnes exactes du CSV WooCommerce (Template de production)
    headers = [
        "ID", "Type", "SKU", "Name", "Published",
        "Visibility in catalog", "Short description", "Description",
        "In stock?", "Stock", "Regular price", "Categories", "Tags",
        "Attribute 1 name", "Attribute 1 value(s)", "Attribute 1 default", "Attribute 1 visible", "Attribute 1 global",
        "Attribute 2 name", "Attribute 2 value(s)", "Attribute 2 default", "Attribute 2 visible", "Attribute 2 global",
        "Attribute 3 name", "Attribute 3 value(s)", "Attribute 3 default", "Attribute 3 visible", "Attribute 3 global",
        "Attribute 4 name", "Attribute 4 value(s)", "Attribute 4 default", "Attribute 4 visible", "Attribute 4 global"
    ]

    row = dict(woo)
    
    # Extraction du Poids (Attribute 4)
    poids = ""
    for section in data.get("full_specs", {}).get("sections", []):
        if "design" in section.get("name", "").lower() or "physique" in section.get("name", "").lower():
            for r in section.get("rows", []):
                if r.get("label", "").strip().lower() == "poids":
                    poids = r.get("valeur", "").strip()
                    break
    if poids:
        group = detect_group(data)
        poids_kg = convert_weight_to_kg(poids, group=group)
        if poids_kg:
            row["Attribute 4 name"] = "Poids"
            row["Attribute 4 value(s)"] = poids_kg
            row["Attribute 4 default"] = poids_kg
            row["Attribute 4 visible"] = "1"
            row["Attribute 4 global"] = "1"
    
    networks = ""
    rom = ""
    ram = ""
    
    group = detect_group(data)
    if group == "tech":
        # Force/Normalise le SKU WooCommerce selon le format unifié : [official_sku]-[Réseaux]-[ROM]-[RAM]
        official_sku = data.get("sourcing", {}).get("official_sku", "").strip()
        if not official_sku:
            official_sku = row.get("SKU", "").strip().split("-")[0]
            
        if official_sku:
            networks = ""
            rom = ""
            ram = ""
            color = ""
            
            # Tenter d'extraire la RAM, le Stockage et la Couleur depuis les attributs WooCommerce uniques (prioritaire pour les variantes)
            for i in range(1, 5):
                attr_name = row.get(f"Attribute {i} name", "").strip().upper()
                attr_val = row.get(f"Attribute {i} value(s)", "").strip()
                if attr_name in ["STOCKAGE", "MÉMOIRE"] and "," not in attr_val and "|" not in attr_val:
                    rom = attr_val.upper().replace("GO", "GB").replace("TO", "TB").replace(" ", "")
                elif attr_name == "RAM" and "," not in attr_val and "|" not in attr_val:
                    ram = attr_val.upper().replace("GO", "GB").replace(" ", "")
                elif attr_name in ["COULEUR", "COLOR"] and "," not in attr_val and "|" not in attr_val:
                    color = attr_val.strip()
            
            # Les variables seront nettoyées après la boucle des spécifications ci-dessous
            
            for section in data.get("full_specs", {}).get("sections", []):
                sec_name = section.get("name", "").strip().upper()
                if sec_name == "CONNECTIVITÉ":
                    for r in section.get("rows", []):
                        if r.get("label", "").strip().upper() == "RÉSEAUX":
                            val = r.get("valeur", "").upper()
                            if "5G" in val:
                                networks = "5G"
                            elif "4G" in val or "LTE" in val:
                                networks = "4G"
                elif sec_name == "PERFORMANCES":
                    for r in section.get("rows", []):
                        label = r.get("label", "").strip().upper()
                        if ("STOCKAGE" in label or "ROM" in label) and not rom:
                            val = r.get("valeur", "")
                            match = re.search(r'(\d+)\s*(GB|TB|MB|KB|GO|TO|MO|KO)', val, re.IGNORECASE)
                            if match:
                                rom = f"{match.group(1)}{match.group(2).upper().replace('GO', 'GB').replace('TO', 'TB').replace('MO', 'MB').replace('KO', 'KB')}"
                        elif ("MÉMOIRE" in label or "RAM" in label) and not ram:
                            val = r.get("valeur", "")
                            match = re.search(r'(\d+)\s*(GB|TB|MB|KB|GO|TO|MO|KO)', val, re.IGNORECASE)
                            if match:
                                ram = f"{match.group(1)}{match.group(2).upper().replace('GO', 'GB').replace('TO', 'TB').replace('MO', 'MB').replace('KO', 'KB')}"
            
            if rom and "NONAPPLICABLE" in rom.upper():
                rom = ""
            if ram and "NONAPPLICABLE" in ram.upper():
                ram = ""

            clean_official_sku = official_sku
            while True:
                new_base = re.sub(r'-\d+(?:GB|TB|GO|TO)$', '', clean_official_sku, flags=re.IGNORECASE)
                if new_base == clean_official_sku:
                    break
                clean_official_sku = new_base

            sku_parts = [clean_official_sku]
            if networks and not clean_official_sku.upper().endswith(f"-{networks.upper()}"):
                sku_parts.append(networks)
            if rom:
                sku_parts.append(rom)
            if ram:
                sku_parts.append(ram)
            if color:
                import unicodedata
                nfkd = unicodedata.normalize('NFKD', color)
                color_sku = nfkd.encode('ASCII', 'ignore').decode('ASCII').upper().replace(" ", "-").replace("'", "")
                sku_parts.append(color_sku)
            row["SKU"] = "-".join(sku_parts).upper()
            
    if not row.get("SKU"):
        row["SKU"] = data.get("sourcing", {}).get("official_sku", "")
    
    # Injecter le contenu HTML généré dans Short/Description (avec nettoyage complet)
    row["Short description"] = clean_html(build_short_html(data))
    
    group = detect_group(data)
    if group == "tech":
        long_html = build_long_tech_html(data)
    row["Description"] = clean_html(long_html)
    
    # Traitement intelligent des tags (nettoyage, injection des variantes et limite à 12 max)
    row["Tags"] = process_tags(row.get("Tags", ""), ram, rom, networks, group)
        
    # Validation et adaptation des attributs multiples
    for i in range(1, 4):
        val_key = f"Attribute {i} value(s)"
        if row.get(val_key) and "|" in row[val_key]:
            row[val_key] = row[val_key].replace(" | ", ", ").replace("|", ",")
            
    # Tentative d'injection automatique et résiliente des prix depuis Templates/Pricing/
    if serie:
        pricing_dir = os.path.join(os.path.dirname(os.path.dirname(outdir)), "Pricing")
        if not os.path.exists(pricing_dir):
            pricing_dir = os.path.join("Pricing")
        if not os.path.exists(pricing_dir):
            pricing_dir = os.path.join("Templates", "Pricing")
        
        if os.path.exists(pricing_dir):
            price_file_patterns = [
                f"prix-{serie}-v2.csv",
                f"prix-{serie}-fcfa.csv",
                f"prix-{serie}.csv",
                f"prix-{serie.replace('-all', '')}-v2.csv",
                f"prix-{serie.replace('-all', '')}-fcfa.csv",
                f"prix-{serie.replace('-all', '')}-series-v2.csv",
                f"prix-{serie.replace('-all', '')}-series-fcfa.csv",
            ]
            price_file_path = None
            for pattern in price_file_patterns:
                temp_path = os.path.join(pricing_dir, pattern)
                if os.path.exists(temp_path):
                    price_file_path = temp_path
                    break
            
            if price_file_path:
                try:
                    with open(price_file_path, mode="r", encoding="utf-8-sig") as pf:
                        pf_reader = csv.reader(pf)
                        pf_rows = list(pf_reader)
                    
                    if pf_rows:
                        model_idx = 0
                        price_idx = 2
                        prod_name = row.get("Name", "").strip().lower()
                        price_found = None
                        
                        for p_row in pf_rows[1:]:
                            if len(p_row) > max(model_idx, price_idx):
                                m_val = p_row[model_idx].strip().lower().replace('"', '').replace("'", "").replace('\\', '')
                                clean_prod_name = prod_name.replace('"', '').replace("'", "").replace('\\', '')
                                if m_val == clean_prod_name or clean_prod_name.startswith(m_val) or m_val.startswith(clean_prod_name):
                                    price_found = p_row[price_idx].strip()
                                    break
                        
                        if price_found:
                            price_cleaned = "".join(filter(str.isdigit, price_found))
                            if price_cleaned:
                                row["Regular price"] = price_cleaned
                                print(f"[INFO] Prix injecte automatiquement depuis {os.path.basename(price_file_path)} : {price_cleaned} FCFA")
                except Exception as e:
                    print(f"[WARN] Erreur de lecture de prix sur {price_file_path} : {e}")
        
    if serie:
        serie_dir = os.path.dirname(outdir)
        csv_out = os.path.join(serie_dir, f"import-v2-{serie}.csv")
    else:
        csv_out = os.path.join(outdir, f"import-v2-{modele}.csv")

    # Supprimer 'Modèle Constructeur' si pas de RAM/ROM
    has_ram = False
    has_rom = False
    for i in range(1, 5):
        attr_name = row.get(f"Attribute {i} name", "").strip().upper()
        if attr_name == "RAM":
            has_ram = True
        elif attr_name in ["STOCKAGE", "MÉMOIRE"]:
            has_rom = True
            
    if not (has_ram or has_rom):
        for i in range(1, 5):
            attr_name = row.get(f"Attribute {i} name", "").strip().upper()
            if attr_name == "MODÈLE CONSTRUCTEUR":
                row[f"Attribute {i} name"] = ""
                row[f"Attribute {i} value(s)"] = ""
                row[f"Attribute {i} default"] = ""
                row[f"Attribute {i} visible"] = ""
                row[f"Attribute {i} global"] = ""

    new_row = []
    for h in headers:
        val = row.get(h, "")
        if h == "Type":
            val = "simple"
        elif h == "Stock":
            val = "50"
        elif h == "In stock?":
            val = "1"
        new_row.append(val)
    
    sku_index = headers.index("SKU")
    new_sku = new_row[sku_index]

    if os.path.isfile(csv_out):
        with open(csv_out, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            existing_rows = list(reader)

        if existing_rows and existing_rows[0] != headers:
            print(f"[INFO] En-tete different detecte dans {os.path.basename(csv_out)}. Reinitialisation dynamique des colonnes.")
            existing_rows = [headers]

        updated = False
        if existing_rows:
            header = existing_rows[0]
            for i in range(1, len(existing_rows)):
                if len(existing_rows[i]) > sku_index and existing_rows[i][sku_index] == new_sku:
                    existing_rows[i] = new_row
                    updated = True
                    break

        if not updated:
            existing_rows.append(new_row)

        with open(csv_out, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(existing_rows)

        mode_label = "Mis à jour" if updated else "Append Mode"
    else:
        with open(csv_out, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerow(new_row)
        mode_label = "Créé"

    print(f"[OK] import-v2-{serie or modele}.csv généré/mis à jour ({mode_label})")
    return csv_out


# ==============================================================================
# Validation interne
# ==============================================================================

def validate_json(data: dict, group: str) -> list[str]:
    """Vérifie que le JSON respecte les contraintes structurelles minimales."""
    errors = []
    ld = data.get("long_description", {})

    # Experience Box : exactement 4 items
    box_items = ld.get("experience_box", {}).get("items", [])
    if len(box_items) != 4:
        errors.append(f"Experience Box doit contenir exactement 4 items (trouvé: {len(box_items)})")

    # Sections LONG : exactement 3
    sections = ld.get("sections", [])
    if len(sections) != 3:
        errors.append(f"long_description.sections doit contenir exactement 3 sections H2 (trouvé: {len(sections)})")

    # Chaque section doit avoir 2 paragraphes
    for i, sec in enumerate(sections):
        p_count = len(sec.get("paragraphs", []))
        if p_count != 2:
            errors.append(f"Section {i+1} '{sec.get('h2_title', '')}' doit avoir 2 paragraphes (trouvé: {p_count})")

    # --- SÉCURITÉ QUALITÉ : Vérification de la densité des specs ---
    if group == "tech":
        full_specs = data.get("full_specs") or ld.get("full_specs", {})
        for section in full_specs.get("sections", []):
            for row in section.get("rows", []):
                val = str(row.get("valeur", "")).strip()
                label = row.get("label", "").strip().lower()
                if not val or len(val) < 2:
                    errors.append(f"Donnée manquante : {section.get('name')} > {row.get('label')} est vide.")
                elif label in ["poids", "weight", "poids net"]:
                    # Vérifier que le poids contient au moins un chiffre et pas de marketing verbeux
                    has_digit = any(c.isdigit() for c in val)
                    has_marketing = any(w in val.lower() for w in ["ergonomie", "prise", "confort", "léger", "légère", "robuste", "équilibré", "conception"])
                    if not has_digit or has_marketing or len(val) > 20:
                        errors.append(f"Le poids '{val}' dans {section.get('name')} n'est pas conforme (doit être une valeur purement chiffrée, ex: '194 g').")
    # ---------------------------------------------------------------

    if group == "tech":
        # Full specs : 6 sections minimum pour le nouveau tableau
        full_sections = (data.get("full_specs") or ld.get("full_specs", {})).get("sections", [])
        if len(full_sections) < 6:
            errors.append(f"full_specs.sections doit contenir au moins 6 sections (trouvé: {len(full_sections)})")

    elif group == "appliance":
        app_sections = ld.get("full_specs_table", {}).get("sections", [])
        if len(app_sections) < 4 or len(app_sections) > 5:
            errors.append(f"full_specs_table.sections doit contenir 4-5 sections (trouvé: {len(app_sections)})")

    return errors


# ==============================================================================
# Point d'entrée principal
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Builder de Pack Produit V2.1 — Génération industrielle depuis JSON"
    )
    parser.add_argument("--data", required=True, help="Chemin vers le fichier pack-data JSON")
    parser.add_argument("--outdir", required=True, help="Dossier de sortie des fichiers HTML")
    parser.add_argument("--modele", required=True, help="Slug du modèle (ex: redmi-a3)")
    parser.add_argument("--serie", required=False, help="Slug de la série pour consolider le CSV (ex: redmi-a-all)")
    parser.add_argument("--skip-validation", action="store_true", help="Ignorer la validation interne")
    parser.add_argument("--no-csv", action="store_true", help="Ne pas générer de fichier CSV individuel dans le dossier de sortie")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    group = detect_group(data)
    print(f"[INFO] Groupe détecté : {group.upper()}")

    if not args.skip_validation:
        errors = validate_json(data, group)
        if errors:
            print(f"\n[INFO] {len(errors)} erreur(s) de structure détectée(s) :")
            for err in errors:
                print(f"   [!]  {err}")
            sys.exit(1)

    os.makedirs(args.outdir, exist_ok=True)

    # 1. SHORT
    short_path = os.path.join(args.outdir, f"short-{args.modele}.html")
    with open(short_path, "w", encoding="utf-8") as f:
        f.write(build_short_html(data))
    print(f"[OK] short-{args.modele}.html généré")

    # 2. LONG (inclut désormais les specs pour TECH)
    long_path = os.path.join(args.outdir, f"long-{args.modele}.html")
    if group == "tech":
        with open(long_path, "w", encoding="utf-8") as f:
            f.write(build_long_tech_html(data))
    else:
        with open(long_path, "w", encoding="utf-8") as f:
            f.write(build_long_appliance_html(data))
    print(f"[OK] long-{args.modele}.html généré ({group})")

    # 3. CSV WooCommerce
    if not args.no_csv:
        csv_path = generate_csv(data, args.outdir, args.modele, args.serie)

    # 4. Fichier Prix
    woo = data.get("woocommerce_csv", {})
    cat_parts = woo.get("Categories", "").split(">")
    marque = cat_parts[1].strip() if len(cat_parts) > 1 else "Generic"
    serie = cat_parts[2].strip() if len(cat_parts) > 2 else "Produit"

    base_dir = "."
    price_path = create_or_update_price_file(
        base_dir, marque, serie,
        woo.get("Name", args.modele),
        woo.get("Regular price", 0)
    )
    print(f"[OK] Prix ajouté dans {os.path.basename(price_path)}")

    print(f"\n[DONE] Build V2.1 terminé pour '{args.modele}' (groupe {group.upper()})")


if __name__ == "__main__":
    main()
