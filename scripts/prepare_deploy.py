#!/usr/bin/env python3
"""
Prepare repository for Hugging Face Spaces deployment.
Cleans up unnecessary files and shows deployment size.
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

print("=" * 70)
print("PREPARE FOR HUGGING FACE SPACES DEPLOYMENT")
print("=" * 70)

# Check what will be deployed
print("\n[SIZE] Current Repository Size (excluding .venv):")
print("-" * 70)

total_size = 0
for item in ROOT.iterdir():
    if item.name in ['.venv', '.git', '__pycache__', '.pytest_cache']:
        continue
    
    if item.is_file():
        size = item.stat().st_size
        total_size += size
        print(f"  {item.name:<30s} {size/1024:>8.1f} KB")
    elif item.is_dir():
        dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
        total_size += dir_size
        print(f"  {item.name}/{'':<28s} {dir_size/1024:>8.1f} KB")

print(f"\n  {'TOTAL':<30s} {total_size/(1024*1024):>8.2f} MB")

print("\n" + "=" * 70)
print("[CHECK] DEPLOYMENT CHECKLIST")
print("=" * 70)

checks = [
    ("Dockerfile exists", (ROOT / "Dockerfile").exists()),
    (".dockerignore exists", (ROOT / ".dockerignore").exists()),
    ("setup.py exists", (ROOT / "setup.py").exists()),
    ("FAISS index exists", (ROOT / "data" / "indexes" / "faiss_index.bin").exists()),
    ("chunks-latest.json exists", (ROOT / "data" / "processed" / "chunks-latest.json").exists()),
    (".env NOT in git", not (ROOT / ".env").exists() or ".env" in open(ROOT / ".gitignore").read()),
    (".venv in .gitignore", ".venv" in open(ROOT / ".gitignore").read()),
]

all_good = True
for check_name, passed in checks:
    status = "[OK]" if passed else "[FAIL]"
    print(f"  {status} {check_name}")
    if not passed:
        all_good = False

print("\n" + "=" * 70)
if all_good:
    print("[OK] READY FOR DEPLOYMENT!")
    print("\nNext steps:")
    print("  1. Commit all files to GitHub")
    print("  2. Create Hugging Face Space (Docker SDK)")
    print("  3. Link GitHub repo to HF Space")
    print("  4. Add GROQ_API_KEY as secret in HF Space")
    print("  5. Wait for build (~5 minutes)")
    print("\nSee DEPLOYMENT_GUIDE.md for full instructions")
else:
    print("[FAIL] FIX ISSUES ABOVE BEFORE DEPLOYING")

print("=" * 70)
