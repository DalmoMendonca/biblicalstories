#!/usr/bin/env python3
"""Validate editorial data and produce a self-contained static Netlify publish directory."""
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
PUBLIC=ROOT/"public"
if DIST.exists():shutil.rmtree(DIST)
DIST.mkdir()
for name in ("index.html","styles.css"):
    shutil.copy2(ROOT/name,DIST/name)
shutil.copytree(ROOT/"src",DIST/"src",ignore=shutil.ignore_patterns("*.pyc"))
if not (PUBLIC/"data"/"archive.json").exists():
    raise SystemExit("Archive not generated. Run python3 scripts/harvest.py to fetch 104 original plates.")
archive=json.loads((PUBLIC/"data"/"archive.json").read_text())
assert len(archive["images"])==104, "Publication blocked: must have 104 original plates."
for i,story in enumerate(archive["images"],1):
    assert story["id"]==i and story["number"]==(i-1)%52+1
    assert story["verified"] and story["original_image"]
    assert (PUBLIC/story["image"].lstrip("/")).is_file(),story
    assert (PUBLIC/story["thumb"].lstrip("/")).is_file(),story
shutil.copytree(PUBLIC/"data",DIST/"data")
shutil.copytree(PUBLIC/"art",DIST/"art")
print(f"Built {DIST}, 104 verified plates, {len(list((DIST/'art').glob('*.webp')))} full-resolution WebP images")
