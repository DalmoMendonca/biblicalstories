#!/usr/bin/env python3
"""Validate the historical source archive and build a self-contained static edition.

BASE_PATH is optional: unset for root Netlify deployment, or set to
/biblicalstories for the GitHub Pages preview. Source data is never modified.
"""
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PUBLIC = ROOT / "public"
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
if BASE_PATH and (
    not BASE_PATH.startswith("/")
    or any(char in BASE_PATH for char in ' "?#<>')
):
    raise SystemExit("BASE_PATH must be a simple absolute URL path without trailing slash.")

if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()
for name in ("index.html", "styles.css"):
    shutil.copy2(ROOT / name, DIST / name)
shutil.copytree(ROOT / "src", DIST / "src", ignore=shutil.ignore_patterns("*.pyc"))

archive_path = PUBLIC / "data" / "archive.json"
if not archive_path.exists():
    raise SystemExit("Archive missing. Run python3 scripts/harvest.py to retrieve historical plates.")

archive = json.loads(archive_path.read_text(encoding="utf-8"))
assert len(archive["images"]) == 104, "Publication blocked: must have 104 original plates."
for i, story in enumerate(archive["images"], 1):
    assert story["id"] == i and story["number"] == (i - 1) % 52 + 1
    assert story["verified"] and story["original_image"]
    assert (PUBLIC / story["image"].lstrip("/")).is_file(), story
    assert (PUBLIC / story["thumb"].lstrip("/")).is_file(), story
    for leaf in story.get("folios", []):
        assert (PUBLIC / leaf["image"].lstrip("/")).is_file(), leaf

for directory in ("data", "art", "folios"):
    shutil.copytree(PUBLIC / directory, DIST / directory)

if BASE_PATH:
    index = (DIST / "index.html").read_text(encoding="utf-8")
    index = index.replace('href="/styles.css"', f'href="{BASE_PATH}/styles.css"')
    index = index.replace('src="/src/app.js"', f'src="{BASE_PATH}/src/app.js"')
    index = index.replace('href="/?view=', f'href="{BASE_PATH}/?view=')
    index = index.replace('href="/"', f'href="{BASE_PATH}/"')
    (DIST / "index.html").write_text(index, encoding="utf-8")

    path = DIST / "src" / "app.js"
    app = path.read_text(encoding="utf-8")
    app = app.replace('"/?view=', f'"{BASE_PATH}/?view=')
    app = app.replace('href="/?view=', f'href="{BASE_PATH}/?view=')
    app = app.replace('let url = "/";', f'let url = "{BASE_PATH}/";')
    app = app.replace('"/data/', f'"{BASE_PATH}/data/')
    app = app.replace('href="/data/', f'href="{BASE_PATH}/data/')
    path.write_text(app, encoding="utf-8")

    for story in archive["images"]:
        for field in ("image", "thumb"):
            story[field] = BASE_PATH + story[field]
        for leaf in story.get("folios", []):
            leaf["image"] = BASE_PATH + leaf["image"]
    (DIST / "data" / "archive.json").write_text(
        json.dumps(archive, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (DIST / ".nojekyll").touch()
    print(f"GitHub Pages preview under {BASE_PATH}/")

print(
    f"Built {DIST} with 104 original engravings and "
    f"{sum(len(s.get('folios', [])) for s in archive['images'])} "
    "original-language folio images."
)
