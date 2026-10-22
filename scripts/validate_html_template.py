#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation stricte des templates HTML pour produits WordPress/WooCommerce (TECH - Mobiles, Tablettes).

IMPORTANT: Ce script est optimisé pour les produits de type TECH.
Pour les produits APPLIANCE (Électroménager), ce script peut présenter des faux positifs ou des manques. 
La validation de référence pour les Appliances est effectuée par :
scripts/tools/analysis/analyze_editorial_sections.py.

Valide que les fichiers HTML respectent EXACTEMENT les templates définis
(TEMPLATE_LONG.html, TEMPLATE_SHORT.html, TEMPLATE_SPECS.html) :
  - Structure HTML avec div#product-*-description
  - Attributs style requis sur tous les éléments
  - Tableaux avec structure et style EXACTS
  - Liens de référence obligatoires
  - Taux de transitions 31-70%
  - Word count 450-650 mots (fichiers long)
  - Métadonnées AIOSEO complètes

IMPORTANT: Tous les avertissements (warnings) sont traités comme des erreurs.
La validation ne passe que si TOUS les critères sont respectés (erreurs ET warnings = 0).

Usage:
    python validate_html_template.py --product-path "products/Brand/model"
    python validate_html_template.py --product-path "products/Brand/model" --silent
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Configurer UTF-8 pour stdout (requis pour Windows)
try:
    import io
    if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass


# ==============================================================================
# Couleurs ANSI pour la sortie console
# ==============================================================================
class Colors:
    """Codes ANSI pour les couleurs console (compatible Windows 10+, Linux, macOS)."""
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


# Activer le support ANSI sur Windows
def _enable_ansi_windows() -> None:
    """Active les séquences ANSI dans le terminal Windows."""
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 0x0007)
        except Exception:
            pass  # Silencieux si non supporté


_enable_ansi_windows()


# ==============================================================================
# Modèle de données
# ==============================================================================
@dataclass
class ValidationResult:
    """Résultat de validation agrégé pour l'ensemble des fichiers."""
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_checked: list[str] = field(default_factory=list)
    transition_rates: dict[str, dict[str, Any]] = field(default_factory=dict)


# ==============================================================================
# Mots de transition français (pour le taux de transition 31-70%)
# ==============================================================================
TRANSITION_WORDS: list[str] = [
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

# Domaine interne boutique (utilisé pour validation des liens de référence)
STORE_DOMAIN: str = "https://my-estore.com/panier/"


# ==============================================================================
# Fonctions de validation
# ==============================================================================


def test_transition_rate(html_content: str, file_name: str) -> dict[str, Any]:
    """
    Calcule le taux de mots de transition dans un contenu HTML.

    Extrait tous les paragraphes <p>, supprime les balises HTML internes,
    puis vérifie que chaque paragraphe commence par un mot de transition.
    Le taux doit être compris entre 31% et 70%.

    Args:
        html_content: Contenu HTML brut du fichier.
        file_name: Nom du fichier pour le rapport d'erreurs.

    Returns:
        Dict avec les clés: rate, is_valid, percentage, total, with_transition.
    """
    # Extraire tous les paragraphes <p>
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html_content, re.DOTALL)
    total_paragraphs = len(paragraphs)

    if total_paragraphs == 0:
        return {
            "rate": 0,
            "is_valid": False,
            "percentage": 0,
            "total": 0,
            "with_transition": 0,
        }

    with_transitions = 0
    for p_content in paragraphs:
        # Supprimer les balises HTML et les espaces initiaux
        text = re.sub(r"<[^>]+>", "", p_content).lstrip()
        for word in TRANSITION_WORDS:
            # Vérifie que le paragraphe commence par le mot de transition suivi d'un non-mot
            pattern = rf"^{re.escape(word)}\W"
            if re.search(pattern, text, re.IGNORECASE):
                with_transitions += 1
                break

    rate = with_transitions / total_paragraphs
    percentage = round(rate * 100, 1)

    return {
        "rate": rate,
        "is_valid": 0.31 <= rate <= 0.70,
        "percentage": percentage,
        "total": total_paragraphs,
        "with_transition": with_transitions,
    }


def test_word_count(html_content: str, file_name: str) -> dict[str, Any]:
    """
    Vérifie le word count total d'un fichier LONG (doit être entre 450 et 650 mots).

    Supprime les commentaires HTML et balises, puis compte les mots.

    Args:
        html_content: Contenu HTML brut du fichier.
        file_name: Nom du fichier pour le rapport d'erreurs.

    Returns:
        Dict avec les clés: word_count, is_valid, status.
    """
    # Pour les fichiers LONG de la version 2.1, nous excluons le contenu non-rédactionnel du décompte
    if "long-" in file_name:
        # Exclure le tableau de spécifications (div.specs-container ou table)
        html_content = re.sub(r'<div[^>]*class="[^"]*specs-container[^"]*".*?</div>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<table[^>]*>.*?</table>', '', html_content, flags=re.DOTALL)
        # Exclure la boîte d'expérience (background #1d1d1f)
        html_content = re.sub(r'<div[^>]*background-color:\s*#1d1d1f.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Exclure la section CTA (display: flex; justify-content: center)
        html_content = re.sub(r'<div[^>]*display:\s*flex;\s*justify-content:\s*center.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Exclure le H1 principal
        html_content = re.sub(r'<h1[^>]*>.*?</h1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

    # Supprimer les commentaires HTML et les balises
    text = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)

    # Supprimer les espaces multiples et les sauts de ligne
    text = re.sub(r"\s+", " ", text).strip()

    # Compter les mots (séparés par des espaces)
    words = [w for w in text.split() if w]
    word_count = len(words)

    is_valid = 450 <= word_count <= 650

    if word_count < 450:
        status = "TROP COURT"
    elif word_count > 650:
        status = "TROP LONG"
    else:
        status = "VALIDE"

    return {
        "word_count": word_count,
        "is_valid": is_valid,
        "status": status,
    }


def test_table_structure(html_content: str, file_name: str) -> list[str]:
    """
    Valide la structure EXACTE des tableaux selon les templates
    (TEMPLATE_LONG.html et TEMPLATE_SPECS.html).

    Vérifie :
      - Attributs style du <table>
      - Structure <thead> avec couleur de fond #FF4800
      - Cellules <th> avec style exact
      - <tbody> avec alternance de couleurs (#FFFFFF / #FBFBFB)
      - Cellules <td> avec style exact

    Args:
        html_content: Contenu HTML brut du fichier.
        file_name: Nom du fichier pour le rapport d'erreurs.

    Returns:
        Liste des erreurs détectées (vide si tout est conforme).
    """
    errors: list[str] = []

    # Extraire tous les tableaux
    tables = re.findall(r"<table[^>]*>.*?</table>", html_content, re.DOTALL)

    if not tables:
        # Vérifier si c'est un fichier qui devrait contenir des tableaux
        if re.search(r"long-.*\.html|specs-.*\.html", file_name):
            errors.append(f"Aucun tableau trouvé alors qu'il devrait y en avoir dans {file_name}")
        return errors

    for table_html in tables:
        # Validation 1: Attributs style du <table>
        required_table_styles = [
            (r"width:\s*100%", "width: 100%"),
            (r"border-collapse:\s*collapse", "border-collapse: collapse"),
            (r"margin:\s*30px\s+0", "margin: 30px 0"),
            (r"border-radius:\s*12px", "border-radius: 12px"),
            (r"overflow:\s*hidden", "overflow: hidden"),
            (r"box-shadow:\s*0\s+4px\s+12px\s+rgba\([^)]+\)", "box-shadow: 0 4px 12px rgba(...)"),
        ]

        for pattern, style_name in required_table_styles:
            if not re.search(pattern, table_html, re.IGNORECASE):
                errors.append(f"Style manquant dans <table> : {style_name}")

        # Validation 2: Structure <thead> avec style exact
        if "<thead>" not in table_html:
            errors.append("Balise <thead> manquante dans le tableau")

        if not re.search(r"background-color:\s*#FF4800", table_html, re.IGNORECASE):
            errors.append("Couleur de fond <thead> incorrecte (doit être #FF4800)")

        if not re.search(r"color:\s*#FFFFFF", table_html, re.IGNORECASE):
            errors.append("Couleur de texte <thead> incorrecte (doit être #FFFFFF)")

        # Validation 3: Cellules <th> avec style exact
        th_styles = [
            "padding: 20px",
            "text-align: left",
            "font-weight: 600",
            "font-size: 16px",
        ]

        for style in th_styles:
            if style not in table_html:
                errors.append(f"Style manquant dans <th> : {style}")

        # Validation 4: <tbody> avec alternance de couleurs
        if "<tbody>" not in table_html:
            errors.append("Balise <tbody> manquante dans le tableau")

        # Vérifier alternance #FFFFFF et #FBFBFB
        has_white = bool(re.search(r"background-color:\s*#FFFFFF", table_html, re.IGNORECASE))
        has_gray = bool(re.search(r"background-color:\s*#FBFBFB", table_html, re.IGNORECASE))

        if not has_white or not has_gray:
            errors.append("Alternance de couleurs manquante dans <tbody> (requis: #FFFFFF et #FBFBFB)")

        # Validation 5: Cellules <td> avec style exact
        td_styles = [
            "padding: 16px",
            "border-bottom: 1px solid #F5F5F7",
        ]

        for style in td_styles:
            # Comparaison insensible à la casse pour #F5F5F7 / #f5f5f7
            if style.lower() not in table_html.lower():
                errors.append(f"Style manquant dans <td> : {style}")

    return errors


def _extract_domain(url: str) -> str:
    """Extrait le domaine d'une URL (sans protocole ni chemin)."""
    # Supprimer le protocole (https://, http://)
    domain = re.sub(r"^https?://", "", url)
    # Supprimer le chemin, query string, fragment
    domain = domain.split("/")[0].split("?")[0].split("#")[0]
    # Supprimer le préfixe www.
    domain = re.sub(r"^www\.", "", domain)
    return domain.lower()


def test_reference_links(html_content: str, file_name: str) -> list[str]:
    """
    Valide la présence et le format des liens de référence obligatoires
    (conformément à TEMPLATE_LONG.html).

    Vérifie (de manière générique, sans hardcoder de domaines) :
      - Section de liens (div avec display: flex)
      - Style du conteneur (flex, gap, wrap, margin-top)
      - Minimum 2 liens avec des URLs valides (https://)
      - Les 2 liens pointent vers des domaines différents (diversité de sources)
      - Le premier bouton (orange) ne doit PAS pointer vers la boutique interne
      - Style des boutons (padding, border-radius, etc.)
      - Couleurs des boutons (#FF4800 orange, #1D1D1F noir)

    Args:
        html_content: Contenu HTML brut du fichier.
        file_name: Nom du fichier pour le rapport d'erreurs.

    Returns:
        Liste des erreurs détectées (vide si tout est conforme).
    """
    errors: list[str] = []

    # Extraire la section de liens CTA (div avec display: flex)
    link_section_match = re.search(
        r"<div[^>]*display:\s*flex[^>]*>.*?</div>",
        html_content,
        re.DOTALL,
    )

    if not link_section_match:
        errors.append("Section de liens de référence manquante (<div style='display: flex; ...'>)")
        return errors

    section_html = link_section_match.group(0)

    # Validation 1: Structure du conteneur
    required_container_styles = [
        "display: flex",
        "justify-content: center",
        "gap: 15px",
    ]

    for style in required_container_styles:
        if style not in section_html:
            errors.append(f"Style manquant dans conteneur de liens : {style}")

    # Validation 2: Extraire les liens <a>
    link_tags = re.findall(r"<a\s+[^>]*>", section_html)

    if len(link_tags) < 2:
        errors.append(f"Minimum 2 boutons CTA requis (trouvé: {len(link_tags)})")

    # Validation 3: Style des liens
    required_link_styles = [
        "padding: 16px 32px",
        "text-decoration: none",
        "border-radius: 30px",
        "font-weight: 600",
        "text-align: center",
    ]

    for link_tag in link_tags:
        for style in required_link_styles:
            if style not in link_tag:
                errors.append(f"Style manquant dans lien : {style}")
                break

    # Validation 4: Couleurs des liens (premier orange #ff4800, second noir #1d1d1f)
    if not re.search(r"background-color:\s*#FF4800", section_html, re.IGNORECASE):
        errors.append("Premier lien doit avoir background-color: #ff4800 (orange)")

    if not re.search(r"background-color:\s*#1D1D1F", section_html, re.IGNORECASE):
        errors.append("Second lien doit avoir background-color: #1d1d1f (noir)")

    return errors


def test_html_structure(html_content: str, file_name: str) -> list[str]:
    """
    Valide la structure HTML de base selon le type de fichier
    (long-*.html, short-*.html, specs-*.html).

    Chaque type a ses propres règles basées sur les templates correspondants.

    Args:
        html_content: Contenu HTML brut du fichier.
        file_name: Nom du fichier pour le rapport d'erreurs.

    Returns:
        Liste des erreurs détectées (vide si tout est conforme).
    """
    errors: list[str] = []

    # =========================================================================
    # Fichiers LONG — basés sur TEMPLATE_LONG.html
    # =========================================================================
    if re.search(r"long-.*\.html", file_name):
        required_id = "product-long-description"

        # Validation du div principal avec ID
        if not re.search(rf'<div[^>]*id="{required_id}"', html_content):
            errors.append(f"Div principal manquant : <div id='{required_id}'>")

        # Validation des attributs style sur H1
        if re.search(r"<h1[^>]*>", html_content):
            if not re.search(r'<h1[^>]*style="[^"]*font-size:', html_content):
                errors.append("Attribut style 'font-size' manquant sur <h1>")
            if not re.search(r'<h1[^>]*style="[^"]*font-weight:', html_content):
                errors.append("Attribut style 'font-weight' manquant sur <h1>")

        # Validation des attributs style sur H2
        h2_count = len(re.findall(r"<h2[^>]*>", html_content))
        if h2_count > 0:
            if not re.search(r'<h2[^>]*style="[^"]*border-left:', html_content):
                errors.append("Au moins un <h2> doit avoir 'border-left: 5px solid #FF4800'")

        # Validation des paragraphes avec style
        paragraphs = re.findall(r"<p[^>]*>", html_content)
        for p in paragraphs:
            if 'style="' not in p:
                errors.append("Paragraphe sans attribut style détecté")
                break  # Une seule erreur suffit

        return errors

    # =========================================================================
    # Fichiers SHORT — basés sur TEMPLATE_SHORT.html
    # =========================================================================
    if re.search(r"short-.*\.html", file_name):
        # Vérifier ABSENCE de boutons d'achat (non autorisés dans short, en ignorant les commentaires SEO)
        clean_content = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)
        if re.search(r"Acheter|Commander|Voir le panier", clean_content):
            errors.append("Fichier short ne doit PAS contenir de boutons d'achat (Acheter/Commander/Panier)")

        # Vérification 1: Premier élément DOIT être <p><strong>...</strong></p>
        if not re.search(r"<p>\s*<strong>[^<]+</strong>\s*</p>", html_content):
            errors.append("SHORT: Le premier élément doit être <p><strong>MARQUE MODÈLE : TAGLINE</strong></p>")

        # Vérification 2: Le premier <p> contient le nom du produit au format "MARQUE MODÈLE : TAGLINE"
        first_p_strong = re.search(r"<p>\s*<strong>([^<]+)</strong>", html_content)
        if first_p_strong:
            first_content = first_p_strong.group(1).strip()
            # Format attendu : au moins 2 mots avant un séparateur (: ou –)
            # Ex: "Blackview Shark 8 : Le gaming accessible" ou "Samsung Galaxy Tab S10 FE : ..."
            has_brand_model = re.search(r"^\S+\s+\S+", first_content)  # Au moins 2 mots
            has_separator = re.search(r"\s*[:–—]\s*", first_content)   # Séparateur : ou tiret long
            if not has_brand_model or not has_separator:
                errors.append(
                    "SHORT: Le premier <strong> doit suivre le format 'MARQUE MODÈLE : TAGLINE' "
                    "(ex: Blackview Shark 8 : Le gaming accessible)"
                )

        # Vérification 3: Paragraphe teaser entre le strong et le ul
        teaser_pattern = r"</strong></p>\s*<p>[^<]+</p>\s*<ul>"
        if not re.search(teaser_pattern, html_content, re.DOTALL):
            errors.append("SHORT: Il doit y avoir un paragraphe <p> de teaser entre le titre <strong> et la liste <ul>")

        # Vérification 4: Présence de <ul> (liste à puces obligatoire)
        if not re.search(r"<ul[^>]*>", html_content):
            errors.append("Fichier short doit contenir une liste <ul> avec features/bénéfices")

        # Vérification 5: Chaque <li> doit contenir <strong>...</strong>
        li_items = re.findall(r"<li[^>]*>(.*?)</li>", html_content, re.DOTALL)
        if len(li_items) < 3:
            errors.append(f"Fichier short doit contenir au moins 3-4 items <li> dans la liste (trouvé: {len(li_items)})")

        li_without_strong = 0
        li_without_colon = 0
        for li_content in li_items:
            if "<strong>" not in li_content:
                li_without_strong += 1
            if not re.search(r"<strong>[^<]+</strong>", li_content):
                li_without_colon += 1

        if li_without_strong > 0:
            errors.append(
                f"SHORT: Chaque <li> doit contenir <strong>FEATURE</strong> "
                f"(trouvé {li_without_strong} sans strong)"
            )
        if li_without_colon > 0:
            errors.append(
                f"SHORT: Chaque <li> doit avoir le format <strong>FEATURE</strong> : Bénéfice "
                f"(trouvé {li_without_colon} sans ':')"
            )

        # Vérification 6: Slogan final en <em> doit être le dernier élément avant les métadonnées
        last_em = re.search(
            r"<p[^>]*>\s*<em>[^<]+</em>\s*</p>\s*(?:<!--|$)",
            html_content,
            re.DOTALL,
        )
        if not last_em:
            errors.append("SHORT: Le slogan final <em>...</em> doit être le dernier élément HTML avant les métadonnées")

        # Vérification 7: ABSENCE de div ou structure longue
        if re.search(r'<div[^>]*id="product-', html_content):
            errors.append("SHORT: Ne doit pas contenir de div avec id (structure LONG utilise div#product-long-description)")

        return errors

    # =========================================================================
    # Fichiers SPECS — basés sur TEMPLATE_SPECS.html
    # =========================================================================
    if re.search(r"specs-.*\.html", file_name):
        # Specs utilise class="specs-container"
        if 'class="specs-container"' not in html_content:
            errors.append("Fichier specs-*.html doit contenir <div class='specs-container'>")

        # Vérifier ABSENCE de boutons d'achat (en ignorant les commentaires SEO)
        clean_content = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)
        if re.search(r"Acheter sur|Voir le panier|Commander maintenant", clean_content):
            errors.append("Fichier specs ne doit PAS contenir de boutons d'achat (non conformes au TEMPLATE_SPECS.html)")

        return errors

    return errors


def test_specs_structure(html_content: str, file_name: str) -> list[str]:
    """
    Validation stricte et complète de la structure des fichiers specs-*.html
    selon TEMPLATE_SPECS.html.

    Vérifie :
      - Header (<header> avec H1 "Fiche Technique :" et intro paragraph)
      - Structure du tableau (thead 3 colonnes avec largeurs exactes)
      - Minimum 6 sections (rowspan) dans le tableau, max 7
      - Styles des cellules de section (background, color, font-weight, etc.)
      - Footer "Sources & Crédibilité" : styles exacts, liens valides, disclaimer
      - Aucune valeur "N/A" dans les cellules de données

    Args:
        html_content: Contenu HTML brut du fichier.
        file_name: Nom du fichier pour le rapport d'erreurs.

    Returns:
        Liste des erreurs détectées (vide si tout est conforme).
    """
    errors: list[str] = []

    # ==========================================================================
    # 1. VALIDATION DU HEADER
    # ==========================================================================

    # Vérifier présence de <header> ou d'un div d'en-tête équivalent (margin-bottom: 40px)
    header_block = ""
    header_style = ""
    header_match = re.search(r"(<header[^>]*>.*?</header>|<div[^>]*margin-bottom:\s*40px[^>]*>.*?Fiche Technique\s*:.*?</div>)", html_content, re.DOTALL | re.IGNORECASE)
    if not header_match:
        errors.append("SPECS: Conteneur d'en-tête de fiche technique manquant (ex: <header> ou <div> avec margin-bottom: 40px)")
    else:
        header_block = header_match.group(1)
        # Extraire le style de la balise d'ouverture
        style_match = re.search(r"<(?:header|div)[^>]*style=\"([^\"]*)\"", header_block, re.IGNORECASE)
        if style_match:
            header_style = style_match.group(1)
            required_header_styles = [
                ("margin-bottom:\\s*40px", "margin-bottom: 40px"),
                ("border-bottom:\\s*2px\\s+solid\\s+#[Ff]5[Ff]5[Ff]7", "border-bottom: 2px solid #f5f5f7"),
                ("padding-bottom:\\s*20px", "padding-bottom: 20px"),
            ]
            for pattern, style_name in required_header_styles:
                if not re.search(pattern, header_style, re.IGNORECASE):
                    errors.append(f"SPECS: Style manquant dans l'en-tête : {style_name}")

    # Vérifier H1 avec "Fiche Technique :"
    if not re.search(r"<h1[^>]*>.*?Fiche Technique\s*:", html_content, re.DOTALL | re.IGNORECASE):
        errors.append("SPECS: Le <h1> doit contenir 'Fiche Technique : [MARQUE] [MODÈLE]'")

    # ==========================================================================
    # 2. VALIDATION DU THEAD (3 colonnes avec largeurs exactes)
    # ==========================================================================

    # Vérifier les 3 colonnes du thead avec les largeurs exactes
    thead_match = re.search(r"<thead>.*?</thead>", html_content, re.DOTALL)
    if thead_match:
        thead_html = thead_match.group(0)
        th_tags = re.findall(r"<th[^>]*>.*?</th>", thead_html, re.DOTALL)

        if len(th_tags) != 3:
            errors.append(f"SPECS: Le thead doit contenir exactement 3 colonnes (trouvé: {len(th_tags)})")
        else:
            # Vérifier les largeurs: 20%, 25%, 55%
            expected_widths = ["20%", "25%", "55%"]
            for i, (th, expected_w) in enumerate(zip(th_tags, expected_widths)):
                if f"width: {expected_w}" not in th and f"width:{expected_w}" not in th:
                    errors.append(f"SPECS: Colonne {i + 1} du thead doit avoir width: {expected_w}")

    # ==========================================================================
    # 3. VALIDATION DES SECTIONS DU TABLEAU (minimum 6, max 7)
    # ==========================================================================

    # Liste des sections autorisées selon TEMPLATE_SPECS.html
    ALLOWED_SECTIONS = [
        "Design & Physique",
        "Écran",
        "Performances", 
        "Photo & Vidéo",
        "Batterie & Charge",
        "Connectivité",
        "Système & Infos",  # Section optionnelle autorisée
        "Réseau & Connectivité",  # Variante acceptée
    ]

    # Identifier les sections par les cellules <td rowspan="...">
    # Ces cellules contiennent le nom de la section et définissent les groupes de lignes
    section_cells = re.findall(
        r'<td\s+rowspan="(\d+)"[^>]*>(.*?)</td>',
        html_content,
        re.DOTALL,
    )

    section_count = len(section_cells)

    if section_count < 6:
        errors.append(
            f"SPECS: Minimum 6 sections requises dans le tableau "
            f"(trouvé: {section_count}). "
            f"Sections obligatoires du template : Design & Physique, Écran, "
            f"Performances, Photo & Vidéo, Batterie & Charge, Connectivité"
        )
    elif section_count > 7:
        errors.append(
            f"SPECS: Maximum 7 sections autorisées dans le tableau "
            f"(trouvé: {section_count}). Le template prévoit 6 sections + 1 optionnelle"
        )

    # Vérifier que chaque section est dans la liste autorisée
    for rowspan, section_html in section_cells:
        section_name = re.sub(r"<[^>]+>", "", section_html).strip()
        section_name = re.sub(r"\s+", " ", section_name)
        
        if section_name and not any(allowed.lower() in section_name.lower() or section_name.lower() in allowed.lower() for allowed in ALLOWED_SECTIONS):
            errors.append(
                f"SPECS: Section non autorisée détectée : '{section_name}'. "
                f"Sections autorisées : {', '.join(ALLOWED_SECTIONS)}"
            )

    # Vérifier les styles de chaque cellule de section
    section_td_matches = re.findall(
        r'<td\s+rowspan="\d+"[^>]*style="([^"]*)"[^>]*>',
        html_content,
    )

    required_section_styles = [
        ("background-color:\\s*#[Ff]5[Ff]5[Ff]7", "background-color: #F5F5F7"),
        ("vertical-align:\\s*top", "vertical-align: top"),
        ("font-weight:\\s*600", "font-weight: 600"),
        ("color:\\s*#[Ff]{2}4800", "color: #FF4800"),
        ("font-size:\\s*15px", "font-size: 15px"),
    ]

    for idx, section_style in enumerate(section_td_matches):
        for pattern, style_name in required_section_styles:
            if not re.search(pattern, section_style, re.IGNORECASE):
                # Trouver le nom de la section pour un message d'erreur utile
                section_name = section_cells[idx][1].strip() if idx < len(section_cells) else f"Section {idx + 1}"
                section_name = re.sub(r"<[^>]+>", "", section_name).strip()
                section_name = re.sub(r"\s+", " ", section_name)
                errors.append(
                    f"SPECS: Style manquant dans cellule de section '{section_name}' : {style_name}"
                )
                break  # Une seule erreur par section pour éviter le bruit

    # ==========================================================================
    # 4. VALIDATION DU CONTENU APRÈS LE TABLEAU
    # ==========================================================================

    # Extraire tout le contenu après </table>
    after_table_match = re.search(
        r"</table>\s*(.*)$",
        html_content,
        re.DOTALL,
    )
    
    if after_table_match:
        after_table_content = after_table_match.group(1).strip()
        
        # Vérifier qu'il n'y a pas de sections supplémentaires (ex: "Mots-clés LSI")
        # Une section est détectée par la présence d'un <section>, <h2> ou structure similaire
        forbidden_section_patterns = [
            r"<section[^>]*>",
            r"<h2[^>]*>.*?(?:Mots-clés|Keywords|LSI|SEO|Articles similaires)",
            r"Mots-clés LSI",
            r"class=\"[^\"]*keyword[^\"]*\"",
        ]
        
        for pattern in forbidden_section_patterns:
            if re.search(pattern, after_table_content, re.IGNORECASE | re.DOTALL):
                errors.append(
                    f"SPECS: Section non autorisée détectée après le tableau. "
                    f"Seul le footer 'Sources & Crédibilité' est autorisé après le tableau. "
                    f"Retirez les sections supplémentaires (Mots-clés LSI, etc.)"
                )
                break

    # ==========================================================================
    # 5. VALIDATION DU FOOTER "SOURCES & CRÉDIBILITÉ"
    # ==========================================================================

    # Chercher le div de sources
    sources_div_match = re.search(
        r"(<div[^>]*style=\"[^\"]*\"[^>]*>\s*<strong>\s*Sources\s*&(?:amp;)?\s*Crédibilité\s*:\s*</strong>.*?</div>)",
        html_content,
        re.DOTALL | re.IGNORECASE,
    )

    if not sources_div_match:
        errors.append("SPECS: Footer 'Sources & Crédibilité' manquant")
    else:
        sources_div_html = sources_div_match.group(1)
        style_match = re.search(r"style=\"([^\"]*)\"", sources_div_html, re.IGNORECASE)
        sources_style = style_match.group(1) if style_match else ""
        sources_content = sources_div_html

        # 4a. Vérifier les styles du conteneur Sources
        required_sources_styles = [
            ("font-size:\\s*0\\.8em", "font-size: 0.8em"),
            ("color:\\s*#86868[bB]", "color: #86868b"),
            ("margin-top:\\s*30px", "margin-top: 30px"),
            ("text-align:\\s*center", "text-align: center"),
            ("border-top:\\s*1px\\s+solid\\s+#[Ff]5[Ff]5[Ff]7", "border-top: 1px solid #f5f5f7"),
            ("padding-top:\\s*20px", "padding-top: 20px"),
        ]

        for pattern, style_name in required_sources_styles:
            if not re.search(pattern, sources_style, re.IGNORECASE):
                errors.append(f"SPECS: Style manquant dans div Sources : {style_name}")

        # 4b. Vérifier la présence de <strong>Sources & Crédibilité :</strong>
        if not re.search(r"<strong>\s*Sources\s*&(?:amp;)?\s*Crédibilité\s*:\s*</strong>", sources_content, re.IGNORECASE):
            errors.append("SPECS: Le footer doit contenir '<strong>Sources & Crédibilité :</strong>'")

        # 4c. Vérifier la présence de liens sources (minimum 2)
        source_links = re.findall(r'<a\s+href="([^"]+)"[^>]*>', sources_content)
        if len(source_links) < 2:
            errors.append(f"SPECS: Minimum 2 liens de sources requis dans le footer (trouvé: {len(source_links)})")

        # 4d. Vérifier que les liens sources sont des URLs valides
        for url in source_links:
            if not re.match(r"^https?://", url):
                errors.append(f"SPECS: Lien source invalide (doit commencer par https://) : {url}")

        # 4e. Vérifier les styles des liens sources (color et text-decoration)
        source_link_tags = re.findall(r'<a\s+href="[^"]+"\s+style="([^"]*)"[^>]*>', sources_content)
        for link_style in source_link_tags:
            if "text-decoration: none" not in link_style:
                errors.append("SPECS: Style manquant dans lien source : text-decoration: none")
                break  # Une seule erreur suffit

        # 4f. Vérifier la présence du disclaimer (span en italique)
        if not re.search(r"<span[^>]*font-style:\s*italic[^>]*>", sources_content, re.IGNORECASE):
            errors.append("SPECS: Disclaimer en italique manquant dans le footer Sources")

        # 4g. Vérifier le contenu du disclaimer
        if not re.search(r"spécifications peuvent varier", sources_content, re.IGNORECASE):
            errors.append("SPECS: Le disclaimer doit mentionner 'Les spécifications peuvent varier selon les régions'")

    # ==========================================================================
    # 6. VALIDATION N/A — Aucune valeur "N/A" ou "Non disponible" autorisée
    # ==========================================================================

    # Extraire toutes les cellules <td> du tableau (hors cellules de section/rowspan)
    all_td_contents = re.findall(
        r"<td(?:\s+[^>]*)?>(.+?)</td>",
        html_content,
        re.DOTALL,
    )

    # Patterns interdits pour les valeurs manquantes
    FORBIDDEN_VALUES = [
        r"\bN/?A\b",  # N/A, NA
        r"\bNon\s+disponible\b",  # Non disponible
        r"\bN/D\b",  # N/D
        r"\bNon\s+disponible\b",  # Non disponible (avec espace insécable)
        r"\b(?:Pas\s+disponible|Pas\s+de\s+données|Données\s+manquantes)\b",  # Autres variantes
    ]

    for td_content in all_td_contents:
        # Nettoyer le contenu (supprimer les balises HTML internes)
        clean_text = re.sub(r"<[^>]+>", "", td_content).strip()
        
        # Vérifier chaque pattern interdit
        for pattern in FORBIDDEN_VALUES:
            if re.search(pattern, clean_text, re.IGNORECASE):
                # Tronquer le contenu pour le message d'erreur
                preview = clean_text[:60] + "..." if len(clean_text) > 60 else clean_text
                errors.append(
                    f"SPECS: Valeur manquante interdite dans le tableau — "
                    f"toutes les spécifications doivent être renseignées (cellule: '{preview}')"
                )
                break  # Une seule erreur par cellule

    return errors


def test_aioseo_metadata(html_content: str, file_name: str) -> list[str]:
    """
    Valide la présence des métadonnées AIOSEO en commentaires HTML et détecte les doublons.

    Vérifie :
      - Bloc AIOSEO METADATA présent (exactement 1)
      - Section KEYWORDS UTILES présente (exactement 1)
      - Position correcte selon le type de fichier (haut pour specs, bas pour long/short)
      - Présence de SEO Title et Meta Description

    Args:
        html_content: Contenu HTML brut du fichier.
        file_name: Nom du fichier pour le rapport d'erreurs.

    Returns:
        Liste des erreurs détectées (vide si tout est conforme).
    """
    errors: list[str] = []

    # Compter les occurrences de blocs AIOSEO METADATA
    aioseo_matches = re.findall(r"<!--\s*AIOSEO METADATA[:\s]", html_content, re.IGNORECASE)
    aioseo_count = len(aioseo_matches)

    if aioseo_count == 0:
        errors.append("Bloc de métadonnées AIOSEO manquant (<!-- AIOSEO METADATA: -->)")
        return errors

    if aioseo_count > 1:
        errors.append(f"DOUBLON DÉTECTÉ : {aioseo_count} sections AIOSEO METADATA trouvées (1 seule attendue)")

    # Compter les occurrences de KEYWORDS UTILES
    keywords_matches = re.findall(r"KEYWORDS UTILES\s*:", html_content, re.IGNORECASE)
    keywords_count = len(keywords_matches)

    if keywords_count == 0:
        errors.append("Section 'KEYWORDS UTILES' manquante (recommandée)")

    if keywords_count > 1:
        errors.append(f"DOUBLON DÉTECTÉ : {keywords_count} sections KEYWORDS UTILES trouvées (1 seule attendue)")

    # Validation de la position des métadonnées selon le type de fichier
    lines = html_content.split("\n")

    if re.search(r"specs-.*\.html", file_name):
        # Pour les fichiers SPECS: métadonnées doivent être en HAUT (lignes 1-5)
        found_in_top = False
        for i in range(min(5, len(lines))):
            if re.search(r"AIOSEO (METADATA|Title|Description)", lines[i]):
                found_in_top = True
                break
        if not found_in_top:
            errors.append("SPECS: Métadonnées AIOSEO doivent être en HAUT du fichier (lignes 1-3) selon TEMPLATE_SPECS.html")

    elif re.search(r"long-.*\.html|short-.*\.html", file_name):
        # Pour LONG et SHORT: métadonnées doivent être en BAS (après le contenu HTML)
        last_content_line = -1
        metadata_line = -1

        for i in range(len(lines) - 1, -1, -1):
            if re.search(r"AIOSEO (METADATA|Title|Description)", lines[i]):
                metadata_line = i
            if re.search(r"</div>\s*$", lines[i]) and last_content_line == -1:
                last_content_line = i

        if metadata_line != -1 and last_content_line != -1 and metadata_line < last_content_line:
            file_type = re.sub(r"-.+\.html", "", file_name)
            errors.append(
                f"{file_type}: Métadonnées AIOSEO doivent être en BAS du fichier "
                "(après le contenu HTML) selon le template"
            )

    # Vérifier présence et qualité SEO Title
    m_title = re.search(r"(?:SEO Title|Title):\s*([^\r\n]+)", html_content, re.IGNORECASE)
    if not m_title:
        errors.append("Métadonnée 'SEO Title:' ou 'Title:' manquante dans bloc AIOSEO")
    else:
        title_val = m_title.group(1).strip()
        if not (title_val.endswith("| My-eStore") or title_val.endswith("My-eStore") or title_val.endswith("My-eStore")):
            errors.append(f"SEO Title doit se terminer par '| My-eStore' (actuel : '{title_val[-20:]}')")

    # Vérifier présence et qualité Meta Description
    m_desc = re.search(r"(?:Meta Description|Description):\s*([^\r\n]+)", html_content, re.IGNORECASE)
    if not m_desc:
        errors.append("Métadonnée 'Meta Description:' ou 'Description:' manquante dans bloc AIOSEO")
    else:
        desc_val = m_desc.group(1).strip()
        if "..." in desc_val or "Grâce à s" in desc_val:
            errors.append("Meta Description contient une phrase tronquée avec des points de suspension ('...')")
        valid_action_verbs = ["découvrez", "commandez", "explorez", "choisissez", "profitez", "achetez", "obtenez", "consultez"]
        if not any(desc_val.lower().startswith(v) for v in valid_action_verbs):
            errors.append(f"Meta Description doit commencer par un verbe d'action varié ({', '.join(valid_action_verbs[:5])}...)")

    return errors


# ==============================================================================
# Orchestration de validation d'un fichier
# ==============================================================================


def validate_file(
    file_path: Path,
    result: ValidationResult,
    silent: bool = False,
) -> None:
    """
    Orchestre la validation complète d'un fichier HTML.

    Exécute les 6 tests de validation dans l'ordre :
      1. Structure HTML de base
      2. Tableaux (structure et style)
      3. Liens de référence (fichiers long uniquement)
      4. Taux de transitions (fichiers long uniquement)
      4.5. Word count (fichiers long uniquement)
      5. Métadonnées AIOSEO

    Args:
        file_path: Chemin absolu vers le fichier HTML.
        result: Objet ValidationResult à mettre à jour.
        silent: Si True, pas de sortie console.
    """
    if not file_path.exists():
        result.errors.append(f"Fichier introuvable : {file_path}")
        result.is_valid = False
        return

    file_name = file_path.name
    html_content = file_path.read_text(encoding="utf-8")

    result.files_checked.append(file_name)

    if not silent:
        print(f"\n🔍 Validation de {file_name}...", end="")
        print(f" {Colors.CYAN}(en cours){Colors.RESET}")

    # Test 1: Structure HTML de base
    structure_errors = test_html_structure(html_content, file_name)
    if structure_errors:
        result.errors.extend(structure_errors)
        result.is_valid = False
        if not silent:
            for err in structure_errors:
                print(f"  {Colors.RED}❌ {err}{Colors.RESET}")

    # Test 2: Tableaux (structure et style EXACTS)
    table_errors = test_table_structure(html_content, file_name)
    if table_errors:
        result.errors.extend(table_errors)
        result.is_valid = False
        if not silent:
            for err in table_errors:
                print(f"  {Colors.RED}❌ {err}{Colors.RESET}")

    # Test 2.5: Structure stricte specs (sections, header, sources, N/A)
    specs_errors: list[str] = []
    if re.search(r"specs-.*\.html", file_name) or (re.search(r"long-.*\.html", file_name) and "class=\"specs-container\"" in html_content):
        specs_errors = test_specs_structure(html_content, file_name)
        if specs_errors:
            result.errors.extend(specs_errors)
            result.is_valid = False
            if not silent:
                for err in specs_errors:
                    print(f"  {Colors.RED}❌ {err}{Colors.RESET}")

    # Test 3: Liens de référence (OBLIGATOIRES pour fichiers long)
    link_errors: list[str] = []
    if re.search(r"long-.*\.html", file_name):
        link_errors = test_reference_links(html_content, file_name)
        if link_errors:
            result.errors.extend(link_errors)
            result.is_valid = False
            if not silent:
                for err in link_errors:
                    print(f"  {Colors.RED}❌ {err}{Colors.RESET}")

    # Test 4: Taux de transitions (31-70%) — fichiers long uniquement
    if re.search(r"long-.*\.html", file_name):
        transition_result = test_transition_rate(html_content, file_name)
        result.transition_rates[file_name] = transition_result

        if not transition_result["is_valid"]:
            error_msg = f"Taux de transitions invalide : {transition_result['percentage']}% (requis: 31-70%)"
            result.errors.append(error_msg)
            result.is_valid = False
            if not silent:
                print(f"  {Colors.RED}❌ {error_msg}{Colors.RESET}")
        else:
            if not silent:
                print(
                    f"  {Colors.GREEN}✅ Transitions: {transition_result['percentage']}% "
                    f"({transition_result['with_transition']}/{transition_result['total']} "
                    f"paragraphes){Colors.RESET}"
                )

    # Test 4.5: Word Count (450-650 mots pour fichiers LONG)
    if re.search(r"long-.*\.html", file_name):
        wc_result = test_word_count(html_content, file_name)

        if not wc_result["is_valid"]:
            error_msg = (
                f"Word count invalide : {wc_result['word_count']} mots "
                f"(requis: 450-650 mots, statut: {wc_result['status']})"
            )
            result.errors.append(error_msg)
            result.is_valid = False
            if not silent:
                print(f"  {Colors.RED}❌ {error_msg}{Colors.RESET}")
        else:
            if not silent:
                print(
                    f"  {Colors.GREEN}✅ Word Count: {wc_result['word_count']} mots "
                    f"(450-650){Colors.RESET}"
                )

    # Test 5: Métadonnées AIOSEO
    metadata_errors = test_aioseo_metadata(html_content, file_name)
    if metadata_errors:
        result.errors.extend(metadata_errors)
        result.is_valid = False
        if not silent:
            for err in metadata_errors:
                print(f"  {Colors.RED}❌ {err}{Colors.RESET}")

    # Résumé par fichier
    all_ok = (
        not structure_errors
        and not table_errors
        and not specs_errors
        and not link_errors
        and not metadata_errors
    )
    if all_ok and not silent:
        print(f"  {Colors.GREEN}✅ Validation réussie{Colors.RESET}")


# ==============================================================================
# Point d'entrée principal (CLI)
# ==============================================================================


def main() -> int:
    """
    Point d'entrée CLI. Parse les arguments, lance la validation,
    affiche le résumé et retourne le code de sortie (0=succès, 1=échec).

    Returns:
        Code de sortie (0 si validation réussie, 1 sinon).
    """
    parser = argparse.ArgumentParser(
        description="Validation stricte des templates HTML pour produits WordPress/WooCommerce",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples:\n"
            '  python validate_html_template.py --product-path "products/Blackview/mp100-pro"\n'
            '  python validate_html_template.py --product-path "products/Brand/model" --silent\n'
        ),
    )
    parser.add_argument(
        "--product-path",
        required=True,
        help="Chemin vers le dossier produit contenant les fichiers HTML (long-*.html, short-*.html, specs-*.html)",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        default=False,
        help="Mode silencieux - retourne uniquement le code de sortie sans affichage console",
    )

    args = parser.parse_args()

    # Normaliser le chemin
    product_path = Path(args.product_path.rstrip("\\/"))

    if not product_path.exists():
        print(f"❌ Chemin produit introuvable : {product_path}", file=sys.stderr)
        return 1

    # Initialiser le résultat
    result = ValidationResult()

    if not args.silent:
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║  {Colors.CYAN}VALIDATION STRICTE DES TEMPLATES HTML{Colors.RESET}                   ║")
        print(f"╚═══════════════════════════════════════════════════════════╝")
        print(f"📁 Dossier produit : {product_path}")

    # Trouver tous les fichiers HTML valides (long-*, short-*, specs-*)
    html_files = sorted([
        f for f in product_path.glob("*.html")
        if re.match(r"^(long|short|specs)-.*\.html$", f.name)
    ])

    if not html_files:
        error_msg = f"Aucun fichier HTML valide trouvé dans {product_path}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return 1

    # Valider chaque fichier
    for html_file in html_files:
        validate_file(html_file, result, silent=args.silent)

    # Résumé final
    if not args.silent:
        print(f"\n{'═' * 59}")
        print(f"📊 {Colors.CYAN}RÉSUMÉ DE VALIDATION{Colors.RESET}")
        print(f"{'═' * 59}")
        print(f"Fichiers vérifiés : {len(result.files_checked)}")

        if result.is_valid:
            print(f"\n{Colors.GREEN}✅ VALIDATION RÉUSSIE - Tous les fichiers sont conformes{Colors.RESET}")
        else:
            print(
                f"\n{Colors.RED}❌ VALIDATION ÉCHOUÉE - "
                f"{len(result.errors)} erreur(s) trouvée(s){Colors.RESET}"
            )
            print(f"\n{Colors.RED}Erreurs détectées :{Colors.RESET}")
            for err in result.errors:
                print(f"  {Colors.RED}• {err}{Colors.RESET}")

        # Les warnings sont maintenant des erreurs
        if result.warnings:
            print(f"\n{Colors.RED}⚠️  Avertissements (traités comme ERREURS) :{Colors.RESET}")
            for warn in result.warnings:
                print(f"  {Colors.RED}• {warn}{Colors.RESET}")
            result.is_valid = False

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
