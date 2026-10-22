#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Propagation & Compilation Global (V3.4).
1. Propage les fiches certifiées V3.4 sur les répertoires de déclinaisons dans products/[serie]-all/.
2. Recompile le fichier CSV WooCommerce global import-v2-[serie]-all.csv.

Options:
  --serie SERIE        Slug de la série (ex: blackview-all, hifuture-all). Défaut: blackview-all
  --skip-rebuild       Ne pas relancer build-product-pack-v2.py, collecter les CSV existants directement.
  --delete-local       Supprimer les CSV individuels après consolidation dans le CSV global.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

PYTHON_EXE = sys.executable

def main():
    parser = argparse.ArgumentParser(description="Propagation & Compilation CSV Global V3.4")
    parser.add_argument("--serie", default="blackview-all", help="Slug de la série (ex: blackview-all, hifuture-all)")
    parser.add_argument("--skip-rebuild", action="store_true", help="Ne pas relancer le build, collecter les CSV existants directement")
    parser.add_argument("--delete-local", action="store_true", help="Supprimer les CSV individuels après consolidation")
    args = parser.parse_args()

    serie_dir = Path(f"products/{args.serie}")
    global_csv_path = serie_dir / f"import-v2-{args.serie}.csv"

    print(f"\n=======================================================")
    print(f"  COMPILATION CSV GLOBAL (V3.4) — {args.serie.upper()}")
    print(f"  Mode rebuild : {'NON (--skip-rebuild)' if args.skip_rebuild else 'OUI'}")
    print(f"  Suppression CSV locaux : {'OUI (--delete-local)' if args.delete_local else 'NON'}")
    print(f"=======================================================\n")

    all_folders = [p for p in sorted(serie_dir.iterdir()) if p.is_dir()]
    total = len(all_folders)
    success = 0
    failed = 0

    header_written = False
    csv_rows = []

    for idx, pdir in enumerate(all_folders, 1):
        json_files = list(pdir.glob("pack-data-*.json"))
        if not json_files:
            continue

        json_path = json_files[0]

        # 1. Build HTML & CSV local (sauf si --skip-rebuild)
        if not args.skip_rebuild:
            cmd_build = [
                PYTHON_EXE, "scripts/build-product-pack-v2.py",
                "--data", str(json_path),
                "--outdir", str(pdir),
                "--modele", pdir.name,
                "--skip-validation"
            ]
            res_b = subprocess.run(cmd_build, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res_b.returncode == 0:
                success += 1
            else:
                print(f"  ❌ Échec build pour {pdir.name}")
                print(f"     {res_b.stderr[:200]}")
                failed += 1
        else:
            success += 1

        # 2. Collecter la ligne CSV individuelle
        local_csvs = list(pdir.glob("import-v2-*.csv"))
        if local_csvs:
            with open(local_csvs[0], "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
                if lines:
                    if not header_written:
                        header_line = lines[0].replace('\ufeff', '').strip() + "\n"
                        csv_rows.append(header_line)
                        header_written = True
                    if len(lines) > 1:
                        csv_rows.append(lines[1])

            # 3. Supprimer le CSV local si --delete-local
            if args.delete_local:
                for lcsv in local_csvs:
                    lcsv.unlink()

    # Écrire le CSV Global avec BOM propre utf-8-sig
    with open(global_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(csv_rows)

    print(f"\n=======================================================")
    print(f"  BILAN V3.4 — {args.serie.upper()}")
    print(f"  Packs traités : {success} / {total}")
    print(f"  CSV Global : {global_csv_path} ({len(csv_rows)-1} produits)")
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
