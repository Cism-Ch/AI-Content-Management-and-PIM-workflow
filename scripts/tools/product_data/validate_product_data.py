#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_product_data.py — Script de validation pour les fichiers JSON Product Data.

Vérifie la conformité d'un fichier JSON généré par le workflow /generate-product-data :
  - Structure JSON conforme au schéma (tech ou appliance)
  - Champs obligatoires remplis (aucun placeholder)
  - Format des model numbers (regex par constructeur)
  - Fourchettes de prix réalistes (FCFA, marché Côte d'Ivoire)
  - Cohérence des variantes (RAM/Stockage/Couleur non vides)
  - Minimum de sources documentées

Usage:
  python scripts/tools/product_data/validate_product_data.py --input <fichier.json>
  python scripts/tools/product_data/validate_product_data.py --input <dossier/> --batch
  python scripts/tools/product_data/validate_product_data.py --input <fichier.json> --category smartphone
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple



# ── Forcer UTF-8 sur Windows pour éviter les erreurs d'encodage cp1252 ─────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Couleurs terminal ──────────────────────────────────────────────────────────
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ── Constantes ─────────────────────────────────────────────────────────────────
PLACEHOLDER_VALUES = ["", "N/A", "TBD", "TODO", "???", "PLACEHOLDER", "null", "undefined"]
VALID_STATUSES = ["available", "discontinued", "upcoming", "limited"]
VALID_CONFIDENCE_LEVELS = ["high", "medium", "low"]
MIN_SOURCES = 2

# ── Chargement du mapping catégories ───────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
SPECS_MAP_PATH = SCRIPT_DIR / "category_specs_map.json"


def load_specs_map():
    """Charge le fichier category_specs_map.json."""
    if not SPECS_MAP_PATH.exists():
        print(f"{YELLOW}⚠ Fichier category_specs_map.json introuvable : {SPECS_MAP_PATH}{RESET}")
        return {}
    with open(SPECS_MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Fonctions utilitaires ──────────────────────────────────────────────────────

def is_placeholder(value):
    """Vérifie si une valeur est un placeholder interdit."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in [p.lower() for p in PLACEHOLDER_VALUES]:
        return True
    return False


def is_valid_url(url):
    """Vérifie basiquement qu'une URL est valide (format)."""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


# ── Classe principale de validation ────────────────────────────────────────────

class ProductDataValidator:
    """Validateur pour fichiers JSON Product Data."""

    def __init__(self, data, filepath, category_override=None):
        self.data = data
        self.filepath = filepath
        self.category_override = category_override
        self.specs_map = load_specs_map()
        self.errors = []    # FATAL — bloquant
        self.warnings = []  # WARNING — informatif

    def _add_error(self, code, message):
        """Ajoute une erreur fatale."""
        self.errors.append({"code": code, "message": message, "severity": "FATAL"})

    def _add_warning(self, code, message):
        """Ajoute un avertissement."""
        self.warnings.append({"code": code, "message": message, "severity": "WARNING"})

    # ── 1. Validation de structure ─────────────────────────────────────────────

    def validate_structure(self):
        """Vérifie les clés de premier niveau obligatoires."""
        required_keys = [
            "schema_version", "product_type", "generation_metadata",
            "product_identity", "model_numbers", "variants", "colors",
            "key_specifications", "sources"
        ]
        for key in required_keys:
            if key not in self.data:
                self._add_error("STRUCT_MISSING_KEY", f"Clé de premier niveau manquante : '{key}'")

    # ── 2. Validation de l'identité produit ────────────────────────────────────

    def validate_product_identity(self):
        """Vérifie que l'identité produit est complète et valide."""
        identity = self.data.get("product_identity", {})

        # Champs obligatoires
        for field in ["brand", "commercial_name", "category"]:
            if is_placeholder(identity.get(field)):
                self._add_error("IDENTITY_MISSING",
                                f"Champ product_identity.{field} manquant ou placeholder")

        # Statut valide
        status = identity.get("status", "")
        if status and status not in VALID_STATUSES:
            self._add_warning("IDENTITY_STATUS",
                              f"Statut '{status}' non reconnu. Valeurs attendues : {VALID_STATUSES}")

    # ── 3. Validation des model numbers (CRITIQUE) ─────────────────────────────

    def validate_model_numbers(self):
        """Vérifie que les model numbers sont renseignés et crédibles."""
        mn = self.data.get("model_numbers", {})
        primary = mn.get("primary_sku", "")

        # SKU primaire obligatoire
        if is_placeholder(primary):
            self._add_error("MODEL_MISSING_SKU",
                            "Le champ model_numbers.primary_sku est vide ou placeholder. "
                            "Ce champ est CRITIQUE pour l'identification du produit.")
            return

        # Vérifier longueur minimale (un SKU trop court est suspect)
        if len(primary.strip()) < 3:
            self._add_warning("MODEL_SHORT_SKU",
                              f"SKU '{primary}' semble trop court (< 3 caractères)")

        # Vérifier format via patterns constructeur si catégorie connue
        category = self._get_effective_category()
        if category and category in self.specs_map:
            patterns = self.specs_map[category].get("model_number_patterns", [])
            if patterns:
                matched = any(re.match(p, primary) for p in patterns)
                if not matched:
                    self._add_warning("MODEL_PATTERN_MISMATCH",
                                      f"SKU '{primary}' ne correspond à aucun pattern connu "
                                      f"pour la catégorie '{category}': {patterns}")

        # Sources de vérification
        vsources = mn.get("verification_sources", [])
        valid_sources = [s for s in vsources if not is_placeholder(s.get("url", ""))]
        if len(valid_sources) < 1:
            self._add_warning("MODEL_NO_VERIFICATION",
                              "Aucune source de vérification documentée pour le model number")

        # Notes de désambiguïsation (info seulement)
        disambiguation = mn.get("disambiguation_notes", "")
        if disambiguation:
            print(f"  {CYAN}[i] Disambiguation: {disambiguation}{RESET}")

    # ── 4. Validation des variantes ────────────────────────────────────────────

    def validate_variants(self):
        """Vérifie la cohérence et complétude des variantes."""
        variants = self.data.get("variants", [])

        if not variants:
            self._add_error("VARIANTS_EMPTY", "Aucune variante définie (le tableau 'variants' est vide)")
            return

        for i, variant in enumerate(variants):
            prefix = f"variants[{i}]"

            # Nom de la variante
            if is_placeholder(variant.get("variant_name")):
                self._add_error("VARIANT_NO_NAME", f"{prefix}.variant_name est vide")

            # Configuration
            config = variant.get("configurations", {})
            if not config or all(is_placeholder(v) for v in config.values()):
                self._add_warning("VARIANT_NO_CONFIG",
                                  f"{prefix}.configurations est vide ou entièrement placeholder")

            # Pricing
            pricing = variant.get("pricing", {})
            price_range = pricing.get("market_price_range_fcfa", {})
            price_min = price_range.get("min")
            price_max = price_range.get("max")

            if price_min is None and price_max is None:
                official = pricing.get("official_price_fcfa")
                if official is None:
                    self._add_warning("VARIANT_NO_PRICE",
                                      f"{prefix} n'a aucun prix renseigné (ni fourchette, ni officiel)")
            else:
                # Vérifier cohérence min <= max
                if price_min is not None and price_max is not None:
                    if price_min > price_max:
                        self._add_error("VARIANT_PRICE_INVERT",
                                        f"{prefix} prix min ({price_min}) > max ({price_max})")

                # Vérifier fourchette réaliste
                category = self._get_effective_category()
                if category and category in self.specs_map:
                    cat_range = self.specs_map[category].get("price_range_fcfa", {})
                    cat_min = cat_range.get("min", 0)
                    cat_max = cat_range.get("max", float("inf"))
                    effective_min = price_min if price_min is not None else 0
                    effective_max = price_max if price_max is not None else float("inf")

                    if effective_min < cat_min * 0.5:
                        self._add_warning("VARIANT_PRICE_LOW",
                                          f"{prefix} prix min ({effective_min} FCFA) anormalement bas "
                                          f"pour {category} (attendu >= {cat_min})")
                    if effective_max > cat_max * 1.5:
                        self._add_warning("VARIANT_PRICE_HIGH",
                                          f"{prefix} prix max ({effective_max} FCFA) anormalement haut "
                                          f"pour {category} (attendu <= {cat_max})")

            # Source de prix
            if is_placeholder(pricing.get("price_source")):
                self._add_warning("VARIANT_NO_PRICE_SOURCE",
                                  f"{prefix}.pricing.price_source est vide")

    # ── 5. Validation des couleurs ─────────────────────────────────────────────

    def validate_colors(self):
        """Vérifie que les couleurs sont renseignées."""
        colors = self.data.get("colors", {})
        standard = colors.get("standard", [])
        default_color = colors.get("default", "")

        if not standard:
            self._add_warning("COLORS_EMPTY", "Aucune couleur standard définie")

        if is_placeholder(default_color):
            self._add_warning("COLORS_NO_DEFAULT", "Aucune couleur par défaut définie")

        if default_color and standard and default_color not in standard:
            all_colors = standard + colors.get("exclusive", [])
            if default_color not in all_colors:
                self._add_warning("COLORS_DEFAULT_MISMATCH",
                                  f"La couleur par défaut '{default_color}' n'est pas dans la liste des couleurs")

    # ── 5.bis Validation des paired_variants (Standard V3.4) ───────────────────

    def validate_paired_variants(self):
        """Vérifie la présence et la cohérence stricte des déclinaisons exclusives (paired_variants)."""
        paired = self.data.get("paired_variants")
        category = self._get_effective_category()
        specs = self.data.get("key_specifications", {})
        colors_dict = self.data.get("colors", {})

        if paired is not None:
            if not isinstance(paired, list):
                self._add_error("PAIRED_VARIANTS_TYPE", "paired_variants doit être une liste d'objets")
                return

            if len(paired) == 0:
                self._add_warning("PAIRED_VARIANTS_EMPTY", "paired_variants est présent mais vide")
                return

            # Vérifier chaque variante
            seen_skus = set()
            for i, pv in enumerate(paired):
                prefix = f"paired_variants[{i}]"
                if not isinstance(pv, dict):
                    self._add_error("PAIRED_VARIANTS_ITEM_TYPE", f"{prefix} doit être un dictionnaire")
                    continue

                # Couleur
                color_name = pv.get("color_fr") or pv.get("color")
                if is_placeholder(color_name):
                    self._add_error("PAIRED_VARIANTS_NO_COLOR", f"{prefix} n'a pas de couleur renseignée ('color_fr' ou 'color')")

                # Stockage / Mémoire pour les catégories concernées
                if category in ["smartphone", "tablet", "laptop"]:
                    storage = pv.get("storage") or pv.get("rom")
                    if is_placeholder(storage):
                        self._add_error("PAIRED_VARIANTS_NO_STORAGE", f"{prefix} n'a pas de stockage renseigné ('storage' ou 'rom')")

                # Unicité SKU suffix ou code
                sku_suffix = pv.get("sku_suffix")
                if sku_suffix and not is_placeholder(sku_suffix):
                    if sku_suffix in seen_skus:
                        self._add_error("PAIRED_VARIANTS_DUPLICATE_SKU", f"{prefix} sku_suffix '{sku_suffix}' dupliqué")
                    seen_skus.add(sku_suffix)

            # Contrôle de cohérence avec woocommerce_csv si présent
            woo = self.data.get("woocommerce_csv", {})
            if woo:
                pv_colors = set(str(pv.get("color_fr") or pv.get("color", "")).strip().lower() for pv in paired if pv.get("color_fr") or pv.get("color"))
                attr1_raw = woo.get("Attribute 1 value(s)", "")
                if attr1_raw and pv_colors:
                    attr1_colors = set(c.strip().lower() for c in attr1_raw.split(",") if c.strip())
                    orphans = attr1_colors - pv_colors
                    if orphans:
                        self._add_warning("PAIRED_VARIANTS_COLOR_MISMATCH",
                                          f"Couleurs dans Attribute 1 non couvertes par paired_variants: {orphans}")

        else:
            # Si paired_variants est absent mais que le modèle présente des options croisées
            storage_opts = specs.get("storage_options", [])
            colors_list = colors_dict.get("standard", [])
            if isinstance(storage_opts, list) and len(storage_opts) > 1 and isinstance(colors_list, list) and len(colors_list) > 1:
                self._add_warning("PAIRED_VARIANTS_RECOMMENDED",
                                  "Modèle multi-stockage et multi-couleurs sans bloc 'paired_variants'. "
                                  "Recommandé en V3.4 pour interdire le produit cartésien aveugle.")

    # ── 6. Validation des spécifications ───────────────────────────────────────

    def _parse_weight_to_kg(self, weight_str: str) -> Optional[float]:
        """Tente de parser une chaîne de poids et la convertir en kg."""
        w_clean = weight_str.lower().replace("\xa0", " ").strip()
        num_match = re.search(r'(\d+(?:[.,]\d+)?)', w_clean)
        if not num_match:
            return None
        val = float(num_match.group(1).replace(",", "."))
        
        if "kg" in w_clean or "kilo" in w_clean:
            return val
        elif "g" in w_clean or "gram" in w_clean:
            return val / 1000.0
        
        if val >= 50:
            return val / 1000.0
        return val

    def validate_specifications(self):
        """Vérifie les champs requis et les valeurs réalistes (ex: poids) selon la catégorie."""
        specs = self.data.get("key_specifications", {})
        category = self._get_effective_category()

        if not category or category not in self.specs_map:
            self._add_warning("SPECS_NO_CATEGORY",
                              f"Catégorie '{category}' non trouvée dans le mapping. "
                              "Validation des specs requises ignorée.")
            return

        required_fields = self.specs_map[category].get("required", [])
        for field in required_fields:
            value = specs.get(field)
            if is_placeholder(value) or (isinstance(value, list) and len(value) == 0):
                self._add_error("SPECS_REQUIRED_MISSING",
                                f"Spécification requise manquante pour {category}: "
                                f"key_specifications.{field}")

        # Validation du poids réaliste
        weight_val = specs.get("weight") or specs.get("weight_kg")
        if weight_val and not is_placeholder(weight_val):
            kg_val = self._parse_weight_to_kg(str(weight_val))
            if kg_val is not None:
                # Seuils de poids réalistes par catégorie (en kg)
                WEIGHT_RANGES_KG = {
                    "smartphone": {"min": 0.080, "max": 0.350},
                    "tablet": {"min": 0.200, "max": 1.200},
                    "laptop": {"min": 0.800, "max": 4.500},
                    "pc_desktop": {"min": 1.000, "max": 25.000},
                    "audio": {"min": 0.002, "max": 25.000},       # Écouteurs (4g) -> Enceintes lourdes (25kg)
                    "wearable": {"min": 0.015, "max": 0.150},    # Smartwatches (15g-150g)
                    "storage": {"min": 0.005, "max": 1.000},
                    "printer": {"min": 1.500, "max": 30.000}
                }
                
                cat_key = str(category).replace("appliance_", "")
                if cat_key in WEIGHT_RANGES_KG:
                    w_range = WEIGHT_RANGES_KG[cat_key]
                    
                    # Ajustement spécial pour les écouteurs/casques (audio)
                    identity = self.data.get("product_identity") or {}
                    commercial_name = identity.get("commercial_name") or ""
                    notes = (self.data.get("model_numbers") or {}).get("disambiguation_notes") or ""
                    is_headset = any(x in str(commercial_name).lower() or x in str(notes).lower() for x in ["casque", "headphone", "supra-auriculaire", "over-ear", "on-ear"])
                    is_earbuds = any(x in str(commercial_name).lower() for x in ["earbud", "écouteur", "buds", "airbuds"]) and not is_headset
                    
                    # Ajustement spécial pour les smartphones durcis / robustes (ex: batterie 10000+ mAh)
                    sub_category = identity.get("sub_category") or ""
                    is_rugged = any(x in str(commercial_name).lower() or x in str(sub_category).lower() or x in str(self.filepath).lower() for x in ["durci", "robuste", "rugged", "bv", "fort", "xplore"])
                    
                    effective_max = 0.700 if (cat_key == "smartphone" and is_rugged) else w_range["max"]
                    effective_max = 0.100 if (cat_key == "audio" and is_earbuds) else effective_max
                    
                    effective_min = 0.002 if (cat_key == "audio" and is_earbuds) else w_range["min"]
                    
                    if not (effective_min <= kg_val <= effective_max):
                        self._add_error("SPECS_ABNORMAL_WEIGHT",
                                        f"Le poids '{weight_val}' ({kg_val:.3f} kg) est anormal pour la catégorie '{category}' "
                                        f"(attendu entre {effective_min} kg et {effective_max} kg)")

        # Règle anti-hallucination V3.3 : Refus des qualificatifs vagues non chiffrés
        VAGUE_TERMS = ["très bon", "rapide", "grande capacité", "haute définition", "performant", "excellent", "super", "incroyable"]
        for field, value in specs.items():
            if isinstance(value, str):
                v_lower = value.lower()
                if any(vt in v_lower for vt in VAGUE_TERMS) and not re.search(r'\d+', value):
                    self._add_error("SPECS_VAGUE_QUALIFIER",
                                    f"Le champ key_specifications.{field} contient un terme vague ('{value}') "
                                    f"sans valeur chiffrée exacte. Remplacer par une spécification numérique précise.")

    # ── 7. Validation des sources ──────────────────────────────────────────────

    def validate_sources(self):
        """Vérifie qu'il y a suffisamment de sources documentées."""
        sources = self.data.get("sources", [])
        valid_sources = [s for s in sources
                         if not is_placeholder(s.get("name")) and not is_placeholder(s.get("url"))]

        if len(valid_sources) < MIN_SOURCES:
            self._add_error("SOURCES_INSUFFICIENT",
                            f"Seulement {len(valid_sources)} source(s) documentée(s). "
                            f"Au moins {MIN_SOURCES} sources URLs réelles sont OBLIGATOIRES pour éviter les hallucinations.")

        # Vérifier format des URLs
        for i, source in enumerate(valid_sources):
            url = source.get("url", "")
            if url and not is_valid_url(url):
                self._add_warning("SOURCES_BAD_URL",
                                  f"sources[{i}].url semble invalide : '{url}'")

    # ── 8. Validation des métadonnées ──────────────────────────────────────────

    def validate_metadata(self):
        """Vérifie les métadonnées de génération."""
        meta = self.data.get("generation_metadata", {})

        gen_date = meta.get("generated_date", "")
        if is_placeholder(gen_date):
            self._add_warning("META_NO_DATE", "Date de génération manquante")
        else:
            try:
                datetime.strptime(gen_date, "%Y-%m-%d")
            except ValueError:
                self._add_warning("META_BAD_DATE",
                                  f"Format de date invalide : '{gen_date}' (attendu : YYYY-MM-DD)")

        confidence = meta.get("confidence_level", "")
        if confidence and confidence not in VALID_CONFIDENCE_LEVELS:
            self._add_warning("META_BAD_CONFIDENCE",
                              f"Niveau de confiance '{confidence}' non reconnu. "
                              f"Valeurs attendues : {VALID_CONFIDENCE_LEVELS}")

    # ── Utilitaire interne ─────────────────────────────────────────────────────

    def _get_effective_category(self):
        """Retourne la catégorie effective (override ou depuis le JSON)."""
        if self.category_override:
            return self.category_override
        identity = self.data.get("product_identity", {})
        category = identity.get("category", "")
        sub = identity.get("sub_category", "")

        # Essayer le mapping composite (ex: appliance_refrigerator)
        if self.data.get("product_type") == "appliance" and sub:
            composite = f"appliance_{sub}"
            if composite in self.specs_map:
                return composite

        return category

    # ── Exécution complète ─────────────────────────────────────────────────────

    def run_all(self):
        """Exécute toutes les validations et retourne le résultat."""
        self.validate_structure()
        self.validate_metadata()
        self.validate_product_identity()
        self.validate_model_numbers()
        self.validate_variants()
        self.validate_colors()
        self.validate_paired_variants()
        self.validate_specifications()
        self.validate_sources()

        return {
            "file": str(self.filepath),
            "product": (self.data.get("product_identity") or {}).get("commercial_name", "Inconnu"),
            "sku": (self.data.get("model_numbers") or {}).get("primary_sku", "N/A"),
            "errors": self.errors,
            "warnings": self.warnings,
            "is_valid": len(self.errors) == 0
        }


# ── Affichage des résultats ────────────────────────────────────────────────────

def print_result(result):
    """Affiche le résultat de validation d'un fichier."""
    product = result["product"]
    sku = result["sku"]
    filepath = result["file"]

    print(f"\n{'='*70}")
    print(f"  {BOLD}Produit{RESET} : {product}")
    print(f"  {BOLD}SKU{RESET}     : {sku}")
    print(f"  {BOLD}Fichier{RESET} : {filepath}")
    print(f"{'='*70}")

    if result["errors"]:
        print(f"\n  {RED}{BOLD}🔴 ERREURS FATALES ({len(result['errors'])}){RESET}")
        for err in result["errors"]:
            print(f"    {RED}✗ [{err['code']}] {err['message']}{RESET}")

    if result["warnings"]:
        print(f"\n  {YELLOW}{BOLD}🟡 AVERTISSEMENTS ({len(result['warnings'])}){RESET}")
        for warn in result["warnings"]:
            print(f"    {YELLOW}⚠ [{warn['code']}] {warn['message']}{RESET}")

    if result["is_valid"]:
        print(f"\n  {GREEN}{BOLD}✅ VALIDATION RÉUSSIE{RESET} — "
              f"{len(result['warnings'])} avertissement(s)")
    else:
        print(f"\n  {RED}{BOLD}❌ VALIDATION ÉCHOUÉE{RESET} — "
              f"{len(result['errors'])} erreur(s), {len(result['warnings'])} avertissement(s)")

    print()


def print_batch_summary(results):
    """Affiche le résumé d'une validation batch."""
    total = len(results)
    valid = sum(1 for r in results if r["is_valid"])
    failed = total - valid
    total_errors = sum(len(r["errors"]) for r in results)
    total_warnings = sum(len(r["warnings"]) for r in results)

    print(f"\n{'═'*70}")
    print(f"  {BOLD}{CYAN}📊 RÉSUMÉ BATCH{RESET}")
    print(f"{'═'*70}")
    print(f"  Fichiers analysés  : {total}")
    print(f"  {GREEN}✅ Valides          : {valid}{RESET}")
    print(f"  {RED}❌ En erreur        : {failed}{RESET}")
    print(f"  Erreurs totales    : {total_errors}")
    print(f"  Avertissements     : {total_warnings}")
    print(f"{'═'*70}\n")


# ── Point d'entrée ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Valide les fichiers JSON Product Data générés par /generate-product-data."
    )
    parser.add_argument("--input", "-i", required=True,
                        help="Chemin vers un fichier JSON ou un dossier (mode batch)")
    parser.add_argument("--batch", "-b", action="store_true",
                        help="Mode batch : valider tous les fichiers product-data-*.json du dossier")
    parser.add_argument("--category", "-c", default=None,
                        help="Forcer la catégorie de produit (override le JSON)")
    parser.add_argument("--json-report", "-j", default=None,
                        help="Exporter le rapport de validation en JSON")
    parser.add_argument("--strict", "-s", action="store_true",
                        help="Mode strict : les avertissements sont traités comme des erreurs")
    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"{RED}✗ Chemin introuvable : {input_path}{RESET}")
        sys.exit(2)

    # Collecter les fichiers à valider
    files_to_validate = []
    if input_path.is_file():
        files_to_validate.append(input_path)
    elif input_path.is_dir():
        if args.batch:
            # Recherche récursive de tous les product-data-*.json
            files_to_validate = sorted(input_path.rglob("product-data-*.json"))
            if not files_to_validate:
                print(f"{YELLOW}⚠ Aucun fichier product-data-*.json trouvé dans {input_path}{RESET}")
                sys.exit(0)
            print(f"{BLUE}📂 Mode batch : {len(files_to_validate)} fichier(s) trouvé(s){RESET}")
        else:
            print(f"{RED}✗ '{input_path}' est un dossier. Utilisez --batch pour valider tous les fichiers.{RESET}")
            sys.exit(2)
    else:
        print(f"{RED}✗ '{input_path}' n'est ni un fichier ni un dossier.{RESET}")
        sys.exit(2)

    # Valider chaque fichier
    results = []
    for filepath in files_to_validate:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result = {
                "file": str(filepath),
                "product": "ERREUR DE PARSING",
                "sku": "N/A",
                "errors": [{"code": "JSON_PARSE_ERROR",
                            "message": f"Fichier JSON invalide : {e}",
                            "severity": "FATAL"}],
                "warnings": [],
                "is_valid": False
            }
            results.append(result)
            print_result(result)
            continue

        validator = ProductDataValidator(data, filepath, args.category)
        result = validator.run_all()

        # Mode strict : warnings → errors
        if args.strict:
            result["errors"].extend(result["warnings"])
            result["warnings"] = []
            result["is_valid"] = len(result["errors"]) == 0

        results.append(result)
        print_result(result)

    # Résumé batch
    if len(results) > 1:
        print_batch_summary(results)

    # Export JSON
    if args.json_report:
        report_path = Path(args.json_report)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"{GREEN}📄 Rapport JSON exporté : {report_path}{RESET}")

    # Code de sortie
    all_valid = all(r["is_valid"] for r in results)
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
