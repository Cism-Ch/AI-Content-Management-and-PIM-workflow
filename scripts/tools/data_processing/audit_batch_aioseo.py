"""
Script d'audit batch AIOSEO & 3 Personas (V3.4) pour My-eStore
Permet d'auditer dynamiquement un dossier complet ou une liste de fichiers JSON parents.

Usage:
  python scripts/tools/data_processing/audit_batch_aioseo.py --dir product-data/hifuture
  python scripts/tools/data_processing/audit_batch_aioseo.py --files product-data/hifuture/hifuture-aurora.json product-data/hifuture/hifuture-active.json
"""

import os
import sys
import argparse
import subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_batch_audit(file_list):
    print("======================================================================")
    print("  AUDIT QA BATCH AIOSEO & 3 PERSONAS (V3.4)")
    print("======================================================================\n")

    passed_count = 0
    failed_count = 0
    summary_results = []

    for idx, filepath in enumerate(file_list, 1):
        if not os.path.exists(filepath):
            print(f"[{idx:02d}/{len(file_list)}] ❌ FICHIER INTROUVABLE : {filepath}")
            failed_count += 1
            continue

        cmd = f'python scripts/tools/data_processing/audit_aioseo_sentences.py "{filepath}"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        
        output = res.stdout
        is_pass = "[OK]" in output and "[FAIL]" not in output and res.returncode == 0
        
        filename = os.path.basename(filepath)
        if is_pass:
            passed_count += 1
            status = "[PASS]"
        else:
            failed_count += 1
            status = "[FAIL]"

        summary_results.append((filename, status, output))
        print(f"--- [{idx:02d}/{len(file_list)}] {filename:<30} | {status} ---")
        print(output.strip())
        print("-" * 70 + "\n")

    print("======================================================================")
    print("  RESUME FINAL DE L'AUDIT BATCH")
    print(f"  Total fichiers audites : {len(file_list)}")
    print(f"  [PASS] Succes        : {passed_count}")
    print(f"  [FAIL] Echecs        : {failed_count}")
    if failed_count > 0:
        print("\n  ❌ DÉTAIL DES FICHIERS EN ÉCHEC ET MOTIFS :")
        for fn, st, out in summary_results:
            if st == "[FAIL]":
                diag_lines = [line.strip() for line in out.splitlines() if "👉" in line or "[FAIL]" in line]
                print(f"    - {fn} :")
                if diag_lines:
                    for dl in diag_lines:
                        print(f"        {dl}")
                else:
                    print("        Vérifier les critères AIOSEO détaillés ci-dessus.")
    print("======================================================================\n")

    return failed_count == 0

def main():
    parser = argparse.ArgumentParser(description="Audit Batch AIOSEO & 3 Personas V3.4")
    parser.add_argument("--dir", help="Dossier contenant les fichiers JSON parents (ex: product-data/hifuture)")
    parser.add_argument("--files", nargs="+", help="Liste de fichiers JSON spécifiques à auditer")
    parser.add_argument("--file", help="Fichier JSON unique à auditer")
    
    args = parser.parse_args()

    file_list = []
    if args.file:
        file_list = [args.file]
    elif args.files:
        file_list = args.files
    elif args.dir:
        if os.path.exists(args.dir):
            file_list = []
            for root, dirs, files in os.walk(args.dir):
                for f in files:
                    if f.endswith(".json"):
                        file_list.append(os.path.join(root, f))
            file_list.sort()
        else:
            print(f"❌ Dossier introuvable : {args.dir}")
            sys.exit(1)
    else:
        # Default fallback to hifuture folder
        default_dir = os.path.join("product-data", "hifuture")
        if os.path.exists(default_dir):
            file_list = [os.path.join(default_dir, f) for f in os.listdir(default_dir) if f.endswith(".json")]
            file_list.sort()

    if not file_list:
        print("❌ Aucun fichier JSON à auditer.")
        sys.exit(1)

    success = run_batch_audit(file_list)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
