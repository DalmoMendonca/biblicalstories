#!/usr/bin/env python3
"""The trilingual release gate excludes the rejected legacy machine OCR/translation corpus."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.call([sys.executable,str(root/"scripts/audit_corpus.py"),"--release"],cwd=root))
