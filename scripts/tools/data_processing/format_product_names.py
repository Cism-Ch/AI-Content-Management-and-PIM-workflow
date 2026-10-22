#!/usr/bin/env encoding=utf-8
# -*- coding: utf-8 -*-
"""
Format Product Names — Script utilitaire pour formater automatiquement
les noms de produits dans les fichiers pack-data JSON selon la nouvelle nomenclature
validée pour toutes les catégories TECH et APPLIANCE.
"""

import os
import json
import re
import argparse


def clean_spaces(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text)).strip()


def extract_regex(pattern, text, default=""):
    if not text:
        return default
    match = re.search(pattern, str(text), re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return default


def clean_cpu(cpu_str):
    if not cpu_str or cpu_str.upper() == "N/A":
        return ""
    # Enlever les termes marketing non-specs
    cpu = cpu_str.split("(")[0].strip()
    generic_terms = [
        "High-Performance", "high-performance", "high performance", 
        "Haute Performance", "haute performance", 
        "Multicoeur haute efficacité", "multicoeur", "haute efficacité",
        "Octa-Core", "Quad-Core", "Dual-Core"
    ]
    for term in generic_terms:
        cpu = re.sub(rf'(?i)\b{re.escape(term)}\b', '', cpu).strip()
    return clean_spaces(cpu)


def clean_os(os_str):
    if not os_str or os_str.upper() == "N/A":
        return "Win11"
    # Enlever les suffixes marketing comme Familiale, Pro, Familiale/Pro, Licence, Native, Préinstallé
    os_clean = re.sub(r'(?i)\b(familiale|professionnel|professionnelle|home|pro|authentique|licence|native|préinstallé|preinstalle|officiel|officielle)\b', '', os_str).strip()
    os_clean = re.sub(r'(?i)\bwindows\s*11\b', 'Win11', os_clean)
    os_clean = re.sub(r'(?i)\bwindows\s*10\b', 'Win10', os_clean)
    os_clean = re.sub(r'(?i)\bwindows\b', 'Win', os_clean)
    return clean_spaces(os_clean) or "Win11"


def clean_gpu(gpu_str):
    if not gpu_str or gpu_str.upper() == "N/A":
        return "Intel Graphics"
    gpu = gpu_str.split("(")[0].strip()
    gpu = re.sub(r'(?i)\b(intégré|intégrée|integrated)\b', '', gpu).strip()
    return clean_spaces(gpu)


def clean_energy_class(ec_str):
    if not ec_str or ec_str.strip().lower() in ["", "n/a", "tbd", "todo", "???", "placeholder", "null", "undefined", "non applicable", "not applicable"]:
        return "A+"
    val = re.sub(r'(?i)classe\s+', '', ec_str).strip()
    return val


class ResilientSpecs(dict):
    def __init__(self, key_specs, full_data):
        super().__init__(key_specs)
        self.full_data = full_data

    def get(self, key, default=""):
        val = super().get(key)
        if val is not None and val != "":
            return val
        
        label_mappings = {
            "sim_type": ["sim", "carte sim", "card slot", "card_slot", "nano-sim", "nano sim", "dualsim"],
            "screen_size": ["écran", "taille de l'écran", "screen"],
            "screen_technology": ["technologie", "technology", "dalle", "type d'écran", "type decran"],
            "energy_class": ["classe énergétique", "classe d'efficacité", "classe energetique", "energy class", "classe d'énergie", "classe d'energie", "efficacité énergétique", "efficacite energetique"],
            "keyboard_type": ["type de touches", "switches", "touches", "keyboard type", "switch type"],
            "keyboard_layout": ["disposition", "layout", "configuration des touches", "keyboard layout"],
            "camera_main": ["appareil photo", "caméra", "camera"],
            "battery_capacity": ["batterie", "battery", "capacité"],
            "networks": ["réseaux", "network", "connect"],
            "connectivity": ["connectivity", "connex", "sans-fil", "sans fil", "connectivité"],
            "ram_options": ["ram", "mémoire vive"],
            "storage_options": ["rom", "stockage", "mémoire"],
            "processor": ["processeur", "cpu", "soc"],
            "cpu_frequency": ["fréquence", "clock"],
            "graphics": ["gpu", "carte graphique", "graphique"],
            "os": ["os", "système d'exploitation", "operating system"],
            "water_resistance": ["étanchéité", "water", "ip"]
        }
        
        labels_to_search = label_mappings.get(key, [key])
        
        if key in ["ram_options", "storage_options"]:
            str_val = ""
            for section in self.full_data.get("full_specs", {}).get("sections", []):
                for row in section.get("rows", []):
                    row_label = row.get("label", "").strip().lower()
                    for label in labels_to_search:
                        if label in row_label:
                            str_val = row.get("valeur", "").strip()
                            break
            if str_val:
                return [str_val]
            return default if isinstance(default, list) else [""]
            
        for section in self.full_data.get("full_specs", {}).get("sections", []):
            sec_name = section.get("name", "").strip().lower()
            for row in section.get("rows", []):
                row_label = row.get("label", "").strip().lower()
                for label in labels_to_search:
                    if label in row_label:
                        if key == "screen_size" and label == "taille" and "écran" not in sec_name and "screen" not in sec_name:
                            continue
                        if key == "connectivity" and "charge" in row_label:
                            continue
                        return row.get("valeur", "").strip()
        
        return default


def get_formatted_name(data, pack_data=None):
    identity = data.get("product_identity", {})
    metadata = data.get("metadata", {})
    woo = pack_data.get("woocommerce_csv", {}) if (pack_data and "woocommerce_csv" in pack_data) else data.get("woocommerce_csv", {})
    
    brand = clean_spaces(identity.get("brand", metadata.get("target_brand", "")))
    model = clean_spaces(identity.get("commercial_name", metadata.get("target_model", "")))
    
    category = clean_spaces(identity.get("category", "")).lower()
    if category in ["peripherique", "peripheral", ""] or not category:
        cats = woo.get("Categories", "").lower()
        if any(x in model.lower() for x in ["scm", "dcm"]) or "extender" in model.lower() or "moniteur" in cats:
            category = "extender"
            
    if not category:
        cats = woo.get("Categories", "").lower()
        if "smartphone" in cats or "téléphone" in cats or "telephone" in cats:
            category = "smartphone"
        elif "tablet" in cats or "tablette" in cats or "active series" in cats:
            category = "tablet"
        elif "mini pc" in cats or "pc de bureau" in cats:
            category = "desktop"
        elif "portable" in cats or "laptop" in cats:
            category = "laptop"
        elif "audio" in cats or "écouteur" in cats or "casque" in cats or "enceinte" in cats:
            category = "audio"
        elif "montre" in cats or "wearable" in cats or "watch" in cats:
            category = "wearable"
        elif "clavier" in cats or "keyboard" in cats or "périphérique" in cats or "peripheral" in cats or "souris" in cats or "mouse" in cats:
            category = "peripheral"

    sub_category = clean_spaces(identity.get("sub_category", "")).lower()

    if model.lower().startswith(brand.lower()):
        full_model = model
    else:
        full_model = f"{brand} {model}"

    # Nettoyage des suffixes mémoires redondants dans le modèle
    full_model = re.sub(r'\s+\d+(?:Go|GB|To|TB)(?:/\d+(?:Go|GB|To|TB))?$', '', full_model, flags=re.IGNORECASE).strip()

    actual_ram = ""
    actual_rom = ""
    actual_color = ""
    
    for i in range(1, 5):
        name_key = f"Attribute {i} name"
        val_key = f"Attribute {i} value(s)"
        attr_name = woo.get(name_key, "").strip().upper()
        if attr_name == "RAM":
            val = woo.get(val_key, "").strip()
            if "|" not in val and "," not in val:
                actual_ram = val
        elif attr_name in ["STOCKAGE", "MÉMOIRE"]:
            val = woo.get(val_key, "").strip()
            if "|" not in val and "," not in val:
                actual_rom = val
        elif attr_name in ["COULEUR", "COLOR"]:
            val = woo.get(val_key, "").strip()
            color_vals = [c.strip() for c in re.split(r'[,|]', val) if c.strip()]
            if len(color_vals) == 1:
                actual_color = color_vals[0]

    specs = ResilientSpecs(data.get("key_specifications", {}), data)
    
    colors = data.get("colors", {})
    default_color = clean_spaces(colors.get("default", "Noir"))
    color_list = colors.get("standard", [])
    if isinstance(color_list, str):
        color_list = [c.strip() for c in re.split(r'[,|]', color_list) if c.strip()]
    has_multiple_colors = len(color_list) > 1 or (woo.get("Attribute 1 value(s)") and len(re.split(r'[,|]', woo.get("Attribute 1 value(s)"))) > 1)
    
    if actual_color:
        color_suffix = f" - {actual_color}"
    else:
        color_suffix = ""

    # --------------------------------------------------------------------------
    # 1. SMARTPHONE & TABLET
    # --------------------------------------------------------------------------
    if category in ["smartphone", "tablet", "tablette"] or "tablet" in sub_category or "tablette" in sub_category:
        parts = [full_model]

        # SIM (Détection 100% robuste SIM / eSIM / Dual SIM (Nano) V3.4)
        sim_val = str(specs.get("sim_type", specs.get("card_slot", ""))).lower()
        full_sim_text = (model + " " + sim_val + " " + json.dumps(data, ensure_ascii=False)).lower()
        
        if "esim" in sim_val and "nano" in sim_val:
            parts.append("Dual SIM (eSIM/Nano)")
        elif "esim" in sim_val:
            parts.append("eSIM")
        elif "wifi" in model.lower() or "wi-fi" in model.lower() or ("microsd" in sim_val and "sim" not in sim_val):
            pass # Les tablettes Wi-Fi sans carte SIM n'ont pas de tag SIM
        elif any(x in full_sim_text for x in ["nano", "dual", "triple slot", "2 nano", "2x nano", "lte", "4g", "5g", "sim"]):
            parts.append("Dual SIM (Nano)")
        elif "single" in sim_val:
            parts.append("Single SIM")
        else:
            parts.append("Dual SIM (Nano)")

        # Écran
        screen = extract_regex(r'(\d+(?:\.\d+)?)\s*(?:inches|pouces|")', specs.get("screen_size", ""))
        if screen:
            parts.append(f'{screen}\"')

        # Réseaux (Détection 100% robuste 5G / 4G / Wi-Fi V3.4)
        proc_text = str(specs.get("processor", "")).lower()
        model_text = model.lower()
        full_json_str = json.dumps(data, ensure_ascii=False).lower()
        pack_json_str = json.dumps(pack_data, ensure_ascii=False).lower() if pack_data else ""
        combined_text = f"{model_text} {proc_text} {full_json_str} {pack_json_str}"
        
        is_5g = (
            ("5g" in model_text)
            or ("5g" in proc_text)
            or ("5g nr" in combined_text)
            or ("5g lte" in combined_text)
            or ("5g dual" in combined_text)
            or ("t820" in proc_text)
            or (woo.get("Attribute 5 value(s)", "").strip().upper() == "5G")
            or ("5g" in str(specs.get("card_slot", "")).lower())
            or ("5g" in str(specs.get("networks", "")).lower())
        )
        
        if is_5g:
            parts.append("5G")
        elif "wifi" in model_text or "wi-fi" in model_text or ("wifi" in combined_text and "4g" not in combined_text and "lte" not in combined_text and "sim" not in combined_text):
            parts.append("Wi-Fi")
        else:
            parts.append("4G")

        # RAM / ROM
        ram_options = specs.get("ram_options", [""])
        rom_options = specs.get("storage_options", [""])
        ram = actual_ram.replace(" ", "") if actual_ram else (ram_options[0].replace(" ", "") if ram_options else "")
        rom = actual_rom.replace(" ", "") if actual_rom else (rom_options[0].replace(" ", "") if rom_options else "")
        
        # Clean non-digits
        if not re.search(r'\d+', ram):
            ram = ""
        if not re.search(r'\d+', rom):
            rom = ""
            
        if ram and rom:
            parts.append(f"{ram}/{rom}")
        elif ram or rom:
            parts.append(ram or rom)

        # Appareil photo
        cam_val = specs.get("camera_main", "")
        match = re.search(r'(\d+)\s*MP', cam_val, re.IGNORECASE)
        if match:
            parts.append(f"{match.group(1)}MP")

        # Batterie
        bat_val = specs.get("battery_capacity", "")
        battery = extract_regex(r'(\d+)\s*mAh', bat_val)
        if not battery:
            battery = extract_regex(r'(\d+)', bat_val)
        if battery:
            parts.append(f"{battery}mAh")

        return " - ".join(parts) + color_suffix

    # --------------------------------------------------------------------------
    # 2. WEARABLE / WATCH
    # --------------------------------------------------------------------------
    elif category == "wearable" or "watch" in model.lower() or sub_category == "watch":
        parts = [f"{full_model} Smartwatch"]

        # Écran - technologie/dalle
        screen_tech = specs.get("screen_technology", specs.get("screen_type", ""))
        if not screen_tech:
            for section in specs.full_data.get("full_specs", {}).get("sections", []):
                if "écran" in section.get("name", "").lower() or "screen" in section.get("name", "").lower():
                    for r in section.get("rows", []):
                        if "technologie" in r.get("label", "").lower() or "type" in r.get("label", "").lower():
                            screen_tech = r.get("valeur", "")
                            break
        
        tech_match = re.search(r'(AMOLED|TFT|IPS|LCD|OLED|LED)', screen_tech, re.IGNORECASE)
        tech_str = tech_match.group(1).upper() if tech_match else "TFT"
        parts.append(f"Écran {tech_str}")

        sim = specs.get("sim_type", "")
        is_invalid_sim = any(x in sim.lower() for x in ["non applicable", "not applicable", "n/a", "no ", " non", "none", "sans", "not avail", "n/d"]) or sim.lower() in ["no", "non", ""]
        if sim and not is_invalid_sim:
            if "esim" in sim.lower():
                parts.append("eSIM")
            else:
                parts.append(sim)
        
        screen = extract_regex(r'(\d+(?:\.\d+)?)\s*(?:inches|pouces|")', specs.get("screen_size", ""))
        if screen:
            parts.append(f'{screen}\"')

        net_val = str(specs.get("networks", specs.get("connectivity", specs.get("sans-fil", "")))).lower()
        if "lte" in net_val or "4g" in net_val or "5g" in net_val:
            parts.append("LTE")

        ram_options = specs.get("ram_options", [""])
        rom_options = specs.get("storage_options", [""])
        ram = ram_options[0].replace(" ", "") if ram_options else ""
        rom = rom_options[0].replace(" ", "") if rom_options else ""
        
        if not re.search(r'\d+', ram) or "MO" in ram.upper() or "MB" in ram.upper():
            ram = ""
        if not re.search(r'\d+', rom) or "MO" in rom.upper() or "MB" in rom.upper():
            rom = ""
            
        if ram and rom:
            parts.append(f"{ram}/{rom}")
        elif ram or rom:
            parts.append(ram or rom)

        bat_val = specs.get("battery_capacity", "")
        battery = extract_regex(r'(\d+)\s*mAh', bat_val)
        if battery:
            parts.append(f"{battery}mAh")

        return " - ".join(parts) + color_suffix

    # --------------------------------------------------------------------------
    # 3. AUDIO (Casques, Écouteurs, Enceintes)
    # --------------------------------------------------------------------------
    elif category == "audio" or sub_category in ["audio", "headphone", "earbuds", "speaker", "enceinte"] or any(x in model.lower() for x in ["airbuds", "fitbuds", "aura bass", "headset"]):
        parts = [full_model]

        # Enceintes Bluetooth
        if "speaker" in model.lower() or "speaker" in sub_category or "enceinte" in model.lower() or "enceinte" in sub_category or "aura bass" in model.lower():
            parts.append("Enceinte Bluetooth")

            power = specs.get("power_watts", specs.get("audio_power", specs.get("audio_config", "")))
            p_match = re.search(r'(\d+)\s*W', str(power), re.IGNORECASE)
            if p_match:
                parts.append(f"{p_match.group(1)}W Stéréo")

            tech = specs.get("audio_tech", "")
            if "bass" in str(tech).lower():
                parts.append("Bass Boost")

            autonomy = specs.get("battery_life", specs.get("autonomie", ""))
            if autonomy:
                a_match = re.search(r'(\d+)\s*h', str(autonomy), re.IGNORECASE)
                if a_match:
                    parts.append(f"Autonomie {a_match.group(1)}h")

            bat_val = specs.get("battery_capacity", "")
            b_match = re.search(r'(\d+)\s*mAh', str(bat_val), re.IGNORECASE)
            if b_match:
                parts.append(f"Batterie {b_match.group(1)}mAh")

            ip = extract_regex(r'(IP[X\d]\d)', specs.get("water_resistance", specs.get("protection", "")))
            if ip:
                parts.append(ip)

            return " - ".join(parts) + color_suffix
        
        # Casques & Écouteurs
        else:
            is_headphone = "headphone" in sub_category or "casque" in model.lower() or "casque" in sub_category or "fitbuds" in model.lower()
            device_type = "Casque Audio Sans Fil" if is_headphone else "Écouteurs Sans Fil TWS"
            parts.append(device_type)

            # Bluetooth
            bt_full = str(specs.get("processor", "")) + " " + str(specs.get("bluetooth_version", "")) + " " + str(specs.get("bluetooth", ""))
            bt_match = re.search(r'Bluetooth\s*(\d+\.\d+)', bt_full, re.IGNORECASE)
            if bt_match:
                parts.append(f"Bluetooth {bt_match.group(1)}")
            else:
                parts.append("Bluetooth 5.3")

            # ANC / ENC
            tech_text = (str(specs.get("audio_tech", "")) + " " + str(specs.get("os_skin", "")) + " " + str(specs.get("anc", ""))).lower()
            if "anc & enc" in tech_text or ("anc" in tech_text and "enc" in tech_text):
                parts.append("ANC & ENC")
            elif "anc" in tech_text:
                db_match = re.search(r'-(\d+)\s*db', tech_text)
                if db_match:
                    parts.append(f"ANC -{db_match.group(1)}dB")
                else:
                    parts.append("ANC")

            # Drivers mm
            driver_text = str(specs.get("audio_config", "")) + " " + str(specs.get("audio_driver", ""))
            d_match = re.search(r'(\d+)\s*mm', driver_text, re.IGNORECASE)
            if d_match:
                parts.append(f"Drivers {d_match.group(1)}mm")

            # Autonomie / Batterie mAh
            autonomy = specs.get("battery_life", specs.get("autonomie", ""))
            a_match = re.search(r'(\d+)\s*h', str(autonomy), re.IGNORECASE)
            if a_match:
                parts.append(f"Autonomie {a_match.group(1)}h")
            else:
                bat_val = specs.get("battery_capacity", "")
                b_match = re.search(r'(\d+)\s*mAh', str(bat_val), re.IGNORECASE)
                if b_match:
                    parts.append(f"Boîtier {b_match.group(1)}mAh")

            ip = extract_regex(r'(IP[X\d]\d)', specs.get("water_resistance", specs.get("protection", "")))
            if ip:
                parts.append(ip)

            return " - ".join(parts) + color_suffix

    # --------------------------------------------------------------------------
    # 3.8 SCREEN EXTENDER / PORTABLE MONITOR (SCM & DCM)
    # --------------------------------------------------------------------------
    elif category == "extender":
        parts = [full_model, "Écran portable"]
        
        screen = ""
        for i in range(1, 5):
            if woo.get(f"Attribute {i} name", "").strip().upper() in ["TAILLE", "SCREEN"]:
                val = woo.get(f"Attribute {i} value(s)", "").strip()
                if "pouce" in val or "inch" in val or '"' in val:
                    screen = val.replace("pouces", "\"").replace("inches", "\"").replace(" ", "").strip()
                    break
        if not screen:
            tags = woo.get("Tags", "")
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:pouces|inches|")', tags, re.IGNORECASE)
            if match:
                screen = f"{match.group(1)}\""
        if not screen:
            screen = "14\""
            
        parts.append(screen)
        
        panel = "IPS"
        res = "FHD (1080p)"
        tags_lower = woo.get("Tags", "").lower()
        if "ips" in tags_lower:
            panel = "IPS"
        if "fhd" in tags_lower or "1080p" in tags_lower:
            res = "FHD (1080p)"
        elif "2k" in tags_lower:
            res = "2K"
        elif "4k" in tags_lower:
            res = "4K UHD"
            
        parts.append(res)
        parts.append(panel)
        
        return " - ".join(parts) + color_suffix

    # --------------------------------------------------------------------------
    # 4. PC PORTABLES
    # --------------------------------------------------------------------------
    elif category in ["laptop", "pc_portable"] or sub_category in ["laptop", "pc_portable"] or "acebook" in model.lower():
        screen = extract_regex(r'(\d+(?:\.\d+)?)\s*(?:inches|pouces|")', specs.get("screen_size", ""))
        screen = f"{screen}\"" if screen else "15.6\""

        cpu = clean_cpu(specs.get("processor", specs.get("cpu", "Intel Core i7")))
        
        ram_options = specs.get("ram_options", [""])
        rom_options = specs.get("storage_options", [""])
        ram = actual_ram.replace(" ", "") if actual_ram else (ram_options[0].replace(" ", "") if ram_options else "16Go")
        rom = actual_rom.replace(" ", "") if actual_rom else (rom_options[0].replace(" ", "") if rom_options else "512Go SSD")
        ram_rom = f"{ram}/{rom}"

        gpu = clean_gpu(specs.get("graphics_card", specs.get("gpu", "Intel Graphics")))
        os_sys = clean_os(specs.get("os", specs.get("operating_system", "Windows 11")))

        return f"{full_model} - {screen} - {cpu} - {ram_rom} - {gpu} - {os_sys}{color_suffix}"

    # --------------------------------------------------------------------------
    # 5. PC DE BUREAU / ALL-IN-ONE / MINI PC
    # --------------------------------------------------------------------------
    elif category in ["desktop", "pc_bureau"] or sub_category in ["desktop", "pc_bureau"] or any(x in model.lower() for x in ["mini pc", "mini-pc", "mp100", "mp200", "mp80", "mp20", "dcm"]):
        is_mini_pc = any(x in model.lower() for x in ["mini pc", "mini-pc", "mp100", "mp200", "mp80", "mp20", "dcm"])
        
        cpu = clean_cpu(specs.get("processor", specs.get("cpu", "")))
        gpu = clean_gpu(specs.get("graphics_card", specs.get("gpu", specs.get("graphics", ""))))
        os_sys = clean_os(specs.get("os", specs.get("operating_system", "Win11")))
            
        ram_options = specs.get("ram_options", [""])
        rom_options = specs.get("storage_options", [""])
        ram = actual_ram.replace(" ", "") if actual_ram else (ram_options[0].replace(" ", "") if ram_options else "8Go")
        rom = actual_rom.replace(" ", "") if actual_rom else (rom_options[0].replace(" ", "") if rom_options else "256Go SSD")
        
        if "ssd" not in rom.lower():
            rom = f"{rom} SSD"
        ram_rom = f"{ram}/{rom}"

        if is_mini_pc:
            return f"{full_model} - Mini PC - {cpu} - {ram_rom} - {gpu} - {os_sys}{color_suffix}"
            
        screen_size = extract_regex(r'(\d+(?:\.\d+)?)\s*(?:inches|pouces|")', specs.get("screen_size", ""))
        fmt = f"All-in-One ({screen_size}\")" if screen_size or "all-in-one" in model.lower() or "aio" in model.lower() else "Tour"

        return f"{full_model} - {fmt} - {cpu} - {ram_rom} - {gpu} - {os_sys}{color_suffix}"

    # --------------------------------------------------------------------------
    # 6. IMPRIMANTES
    # --------------------------------------------------------------------------
    elif category in ["printer", "imprimante"] or sub_category in ["printer", "imprimante"]:
        tech = specs.get("printing_technology", "Laser")
        color_output = specs.get("color_output", "Couleur")
        multifunc = "Multifonction 3-en-1" if "multi" in str(specs.get("multifunction", "")).lower() else "Impression seule"
        
        wifi_val = str(specs.get("connectivity", "")).lower()
        wifi = "Wi-Fi" if "wifi" in wifi_val or "wi-fi" in wifi_val else "USB"

        speed = specs.get("print_speed", "20 ppm")

        return f"{full_model} - Imprimante {tech} {color_output} - {multifunc} - {wifi} - {speed}{color_suffix}"

    # --------------------------------------------------------------------------
    # 7. STOCKAGE
    # --------------------------------------------------------------------------
    elif category in ["storage", "stockage"] or sub_category in ["storage", "stockage"]:
        # Type
        st_type = specs.get("storage_type", "SSD Externe")
        if "ssd" in model.lower() and "m.2" in model.lower():
            st_type = "SSD M.2"
        elif "usb" in model.lower():
            st_type = "Clé USB"

        capacity = actual_rom if actual_rom else specs.get("capacity", specs.get("storage_options", ["1To"])[0])
        speed = specs.get("transfer_speed", specs.get("read_speed", "1050 Mo/s"))
        interface = specs.get("interface", "USB-C")

        return f"{full_model} - {st_type} - {capacity} - {speed} - {interface}{color_suffix}"

    # --------------------------------------------------------------------------
    # 8. PÉRIOHÉRIQUES
    # --------------------------------------------------------------------------
    elif category in ["peripheral", "peripherique"] or sub_category in ["peripheral", "peripherique"]:
        # Écrans PC
        if "monitor" in model.lower() or "ecran" in model.lower() or sub_category in ["monitor", "ecran"]:
            screen = extract_regex(r'(\d+(?:\.\d+)?)\s*(?:inches|pouces|")', specs.get("screen_size", ""))
            screen = f"{screen}\"" if screen else "27\""
            res = specs.get("screen_resolution", "FHD (1080p)")
            tech = specs.get("screen_technology", "IPS")
            hz = specs.get("screen_refresh_rate", "144Hz")
            return f"{full_model} - Écran PC {screen} - {res} - {tech} - {hz}{color_suffix}"
        
        # Clavier / Souris
        else:
            dev_type = "Souris" if "souris" in model.lower() or "mouse" in model.lower() or "mouse" in sub_category else "Clavier"
            conn = "sans fil" if any(x in str(specs.get("connectivity", "")).lower() for x in ["wireless", "sans fil", "bluetooth"]) else "filaire"
            
            if dev_type == "Clavier":
                kb_type = specs.get("keyboard_type", "")
                if not kb_type:
                    kb_type = "Membrane"
                kb_type = kb_type.replace("Clavier", "").strip()
                
                layout = specs.get("keyboard_layout", "")
                if not layout:
                    layout = "AZERTY"
                layout = layout.replace("Disposition", "").strip()
                
                return f"{full_model} - Clavier {conn} - {kb_type} - {layout}{color_suffix}"
            else:
                feat = specs.get("dpi", specs.get("switches", "Ergonomique"))
                if feat and "dpi" in str(feat).lower() and "DPI" not in str(feat):
                    feat = f"{feat} DPI"
                return f"{full_model} - Souris {conn} - {feat}{color_suffix}"

    # --------------------------------------------------------------------------
    # 9. ELECTROMENAGER (APPLIANCE)
    # --------------------------------------------------------------------------
    elif category in ["appliance", "household", "home_appliance"] or data.get("product_type", "") == "appliance":
        
        # A. Climatiseurs (Splits)
        if "split" in model.lower() or "climatiseur" in model.lower() or sub_category in ["split", "ac", "air_conditioner"]:
            power = specs.get("capacity", specs.get("power_btu", "12000 BTU (1.5 CV)"))
            inverter = "Inverter" if "inverter" in str(specs.get("cooling_system", specs.get("installation_type", ""))).lower() else "On-Off"
            gas = specs.get("gas_type", specs.get("refrigerant", "R32"))
            energy_class = clean_energy_class(specs.get("energy_class", ""))
            return f"{full_model} - Climatiseur Split - {power} - {inverter} - Gaz {gas} - Classe {energy_class}{color_suffix}"

        # B. Réfrigérateurs & Congélateurs
        elif "frigo" in model.lower() or "refrigérateur" in model.lower() or "refrigerateur" in model.lower() or "congelateur" in model.lower() or "congélateur" in model.lower() or sub_category in ["refrigerator", "fridge", "freezer"]:
            ref_type = "Combiné"
            if "americain" in model.lower() or "américain" in model.lower():
                ref_type = "Américain"
            elif "double" in model.lower():
                ref_type = "Double-portes"
            elif "congelateur" in model.lower() or "congélateur" in model.lower():
                ref_type = "Congélateur Coffre" if "coffre" in model.lower() else "Congélateur"

            vol = specs.get("capacity", "300L")
            if vol and "L" not in str(vol):
                vol = f"{vol}L"

            cooling = specs.get("cooling_system", "No Frost")
            energy_class = clean_energy_class(specs.get("energy_class", ""))
            return f"{full_model} - Réfrigérateur {ref_type} - {vol} - {cooling} - Classe {energy_class}{color_suffix}"

        # C. Lave-linges & Sèche-linges
        elif "lave-linge" in model.lower() or "machine à laver" in model.lower() or "seche-linge" in model.lower() or "washer" in sub_category or "dryer" in sub_category:
            machine_type = "Hublot" if "hublot" in model.lower() or "front" in str(specs.get("installation_type", "")).lower() else "Top"
            cap = specs.get("capacity", "9kg")
            if cap and "kg" not in str(cap):
                cap = f"{cap}kg"
            
            speed = specs.get("noise_level_db", "1400 tr/min") # standard fallback
            if specs.get("additional_features"):
                for feat in specs.get("additional_features", []):
                    if "tr/min" in feat or "rpm" in feat:
                        speed = feat
            if not speed or "tr/min" not in str(speed):
                speed = "1400 tr/min"

            motor = "Moteur Inverter" if "inverter" in str(specs.get("cooling_system", specs.get("additional_features", ""))).lower() else "Standard"
            energy_class = clean_energy_class(specs.get("energy_class", ""))
            return f"{full_model} - Lave-linge {machine_type} - {cap} - {speed} - {motor} - Classe {energy_class}{color_suffix}"

        # D. Cuisinières (Gazinières)
        elif "cuisiniere" in model.lower() or "cuisinière" in model.lower() or "gaziniere" in model.lower() or "gazinière" in model.lower() or "cooker" in sub_category:
            c_type = "Gaz"
            if "mixte" in model.lower():
                c_type = "Mixte"
            elif "electrique" in model.lower() or "électrique" in model.lower():
                c_type = "Électrique"

            dims = specs.get("dimensions_hxwxd", "60x60 cm")
            # Extract width x depth, e.g. 60x60
            dims_match = re.search(r'(\d+x\d+)', dims)
            dims_str = f"{dims_match.group(1)} cm" if dims_match else "60x60 cm"

            feux = "4 Feux"
            if specs.get("additional_features"):
                for feat in specs.get("additional_features", []):
                    if "feu" in feat.lower() or "brûleur" in feat.lower():
                        feux = feat
            
            oven = specs.get("cooling_system", "Four à gaz Grill")
            if not oven or oven == "No Frost": # default fallback
                oven = "Four à gaz Grill"

            energy_class = clean_energy_class(specs.get("energy_class", ""))
            return f"{full_model} - Cuisinière {c_type} - {dims_str} - {feux} - {oven} - Classe {energy_class}{color_suffix}"

        # E. Autres Electroménagers (Fallback)
        else:
            cap = specs.get("capacity", "")
            cap_str = f" - {cap}" if cap else ""
            energy_class = clean_energy_class(specs.get("energy_class", ""))
            return f"{full_model} - Électroménager{cap_str} - Classe {energy_class}{color_suffix}"

    # --------------------------------------------------------------------------
    # 10. FALLBACK GÉNÉRAL (Si non identifié)
    # --------------------------------------------------------------------------
    else:
        return f"{full_model}{color_suffix}"


def main():
    parser = argparse.ArgumentParser(description="Formate les noms de produits dans les pack-data JSON.")
    parser.add_argument("--products-dir", required=True, help="Chemin vers le répertoire de la série de produits (ex: products/google-pixel-all)")
    parser.add_argument("--product-data-dir", required=True, help="Chemin vers le répertoire product-data contenant les specs (ex: product-data/google/google-pixel-all)")
    args = parser.parse_args()

    # 1. Charger toutes les spécifications par SKU de référence
    sku_to_data = {}
    if os.path.exists(args.product_data_dir):
        for root, dirs, files in os.walk(args.product_data_dir):
            for filename in files:
                if filename.endswith(".json"):
                    filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sku = data.get("model_numbers", {}).get("primary_sku", "")
                    if sku:
                        sku = sku.strip().upper()
                        sku_to_data[sku] = data
                except Exception as e:
                    print(f"[!] Erreur de lecture de {filename} : {e}")

    # 2. Parcourir et mettre à jour les packs de rédaction
    count = 0
    for root, dirs, files in os.walk(args.products_dir):
        for filename in files:
            if filename.startswith("pack-data-") and filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        pack_data = json.load(f)

                    sku = pack_data.get("sourcing", {}).get("official_sku", "")
                    if not sku:
                        sku = pack_data.get("woocommerce_csv", {}).get("SKU", "")
                    sku = sku.strip().upper()

                    if sku in sku_to_data:
                        matched_sku = sku
                    else:
                        # Fallback fuzzy matching (e.g. BV-COLOR-8-128GB vs COLOR-8-128GB)
                        matched_sku = None
                        for db_sku in sku_to_data.keys():
                            if sku.endswith(db_sku) or db_sku.endswith(sku) or sku.replace("BV-", "") == db_sku.replace("BV-", ""):
                                matched_sku = db_sku
                                break

                    spec_data = None
                    if matched_sku:
                        spec_data = sku_to_data[matched_sku]
                    else:
                        if "full_specs" in pack_data or "key_specifications" in pack_data:
                            spec_data = pack_data

                    if spec_data:
                        new_name = get_formatted_name(spec_data, pack_data)
                        
                        # Mettre à jour dans woocommerce_csv
                        pack_data["woocommerce_csv"]["Name"] = new_name
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(pack_data, f, indent=4, ensure_ascii=False)
                        print(f"[OK] Nom mis à jour pour {sku} -> '{new_name}'")
                        count += 1
                    else:
                        print(f"[WARN] SKU {sku} non trouvé dans product-data et pas de specs locales")
                except Exception as e:
                    print(f"[!] Erreur lors du traitement de {filename} : {e}")

    print(f"\n[DONE] Terminé. {count} fichier(s) JSON mis à jour.")


if __name__ == "__main__":
    main()
