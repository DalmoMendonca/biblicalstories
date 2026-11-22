#!/usr/bin/env python3
"""Reproducible, provenance-first archival import for 104 illustrated Hübner histories.
No generated or substituted images: every plate is keyed from the Heidelberg 1768 IIIF labels.
"""
import concurrent.futures
import io
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
ART = PUBLIC / "art"
FOLIO_DIR = PUBLIC / "folios"
DATA = PUBLIC / "data"
ORIGINAL = "https://digi.ub.uni-heidelberg.de/diglit/iiif/huebner1768/manifest.json"
ZURICH = "https://www.e-rara.ch/i3f/v20/24283792/manifest"
OCR = "https://www.e-rara.ch/zuz/download/ftpack/plain/24283792"
USER_AGENT = "HuebnerIllustratedEdition/1.0 (public-domain historical research; github.com/DalmoMendonca/biblicalstories)"

def download(url, tries=4):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=50) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt + 1 < tries:
                time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"Failed retrieving {url}: {last}")

def image_url(canvas):
    resource = canvas.get("images", [{}])[0].get("resource", {})
    return resource.get("@id") or resource.get("service", {}).get("@id", "") + "/full/full/0/default.jpg"

def plate_info(canvases):
    found = []
    for canvas_index, canvas in enumerate(canvases):
        label = str(canvas.get("label", "")).strip()
        match = re.fullmatch(r"Tafel\s+(\d+)", label, re.I)
        if match:
            found.append((canvas_index, int(match.group(1)), canvas))
    if len(found) != 104:
        raise ValueError(f"Expected exactly 104 explicitly labelled original plates, found {len(found)}.")
    for i, (_, number, _) in enumerate(found):
        expected = (i % 52) + 1
        if number != expected:
            raise ValueError(f"Plate sequence broken at global {i+1}: source says {number}; expected {expected}.")
    return found

def process_image(item):
    n, original_url = item
    dest = ART / f"{n:03d}.webp"
    thumb = ART / "thumb" / f"{n:03d}.webp"
    if dest.exists() and dest.stat().st_size > 10000 and thumb.exists() and thumb.stat().st_size > 2000:
        return n, dest.stat().st_size, "cached"
    raw = download(original_url)
    if not raw.startswith(b"\xff\xd8"):
        raise ValueError(f"Plate {n} is not JPEG: {original_url}")
    with Image.open(io.BytesIO(raw)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        # Preserve the whole historical sheet; never crop or manufacture picture content.
        if im.width > 1800:
            im.thumbnail((1800, 3200), Image.Resampling.LANCZOS)
        im.save(dest, format="WEBP", quality=85, method=5)
        thumb_im = im.copy()
        thumb_im.thumbnail((600, 940), Image.Resampling.LANCZOS)
        thumb_im.save(thumb, format="WEBP", quality=79, method=5)
    return n, dest.stat().st_size, "downloaded"


def process_folio(item):
    name, original_url = item
    dest = FOLIO_DIR / f"{name}.webp"
    if dest.exists() and dest.stat().st_size > 1500:
        return name, dest.stat().st_size, "cached"
    raw = download(original_url)
    if not raw.startswith(bytes((0xff, 0xd8))):
        raise ValueError(f"German folio {name} is not a JPEG: {original_url}")
    with Image.open(io.BytesIO(raw)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        # Full source page and marginalia, no text redrawing or artificial restoration.
        im.thumbnail((1600, 2500), Image.Resampling.LANCZOS)
        im.save(dest, format="WEBP", quality=82, method=4)
    return name, dest.stat().st_size, "downloaded"

def main():
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "thumb").mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    FOLIO_DIR.mkdir(parents=True, exist_ok=True)
    hb = json.loads(download(ORIGINAL))
    canvases = hb["sequences"][0]["canvases"]
    plates = plate_info(canvases)
    print(f"ARCHIVE: {len(canvases)} leaves; verified {len(plates)} plates: 52 OT + 52 NT.", flush=True)
    stories = []
    images = []
    for ordinal, (canvas_index, local_number, canvas) in enumerate(plates):
        n = ordinal + 1
        artwork = image_url(canvas)
        images.append((n, artwork))
        next_index = plates[ordinal + 1][0] if ordinal + 1 < len(plates) else len(canvases)
        folios = []
        # A plate precedes the corresponding text in this binding.
        for folio in canvases[canvas_index + 1 : next_index]:
            label = str(folio.get("label", ""))
            if re.fullmatch(r"\d+", label):
                folios.append({
                    "label": label,
                    "image": image_url(folio),
                    "source": "https://digi.ub.uni-heidelberg.de/diglit/huebner1768/" + str(canvases.index(folio) + 1).zfill(4)
                })
        stories.append({
            "id": n,
            "book": "old" if n <= 52 else "new",
            "number": local_number,
            "image": f"/art/{n:03d}.webp",
            "thumb": f"/art/thumb/{n:03d}.webp",
            "original_image": artwork,
            "plate_label": canvas["label"],
            "plate_source": "https://digi.ub.uni-heidelberg.de/diglit/huebner1768/" + str(canvas_index + 1).zfill(4),
            "folios": folios,
            "edition": "Giessen, Johann Christoph Schröder, 1768",
            "archive": "Universitätsbibliothek Heidelberg",
            "verified": True,
        })
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for result in concurrent.futures.as_completed([pool.submit(process_image, item) for item in images]):
            n, size, status = result.result()
            results.append((n, size, status))
            if len(results) % 10 == 0 or len(results) == 104:
                print(f"PLATES STORED {len(results)}/104", flush=True)
    stories = sorted(stories, key=lambda item: item["id"])
    for story in stories:
        if not (PUBLIC / story["image"].lstrip("/")).exists():
            raise AssertionError(f"Missing image: {story['image']}")

    folio_jobs = []
    for story in stories:
        for ix, folio in enumerate(story["folios"], 1):
            key = f"{story['id']:03d}-{ix:02d}"
            original = folio["image"]
            folio["original_image"] = original
            folio["image"] = f"/folios/{key}.webp"
            folio_jobs.append((key, original))
    print(f"GERMAN ORIGINAL: {len(folio_jobs)} story text leaves to preserve", flush=True)
    folio_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result in concurrent.futures.as_completed([pool.submit(process_folio, item) for item in folio_jobs]):
            name, size, status = result.result()
            folio_results.append((name, size, status))
            if len(folio_results) % 40 == 0 or len(folio_results) == len(folio_jobs):
                print(f"FOLIOS STORED {len(folio_results)}/{len(folio_jobs)}", flush=True)
    if len(folio_results) < 300:
        raise AssertionError("Too few original German text folios to claim an archival edition.")
    output = {
        "version": 1,
        "issued": datetime.now(timezone.utc).isoformat(),
        "description": "Verified, explicitly numbered plates of Hübner's 1768 Giessen edition",
        "attribution": "Johann Hübner / Georg Peter Monath, Zweymal zwey und funfzig auserlesene Biblische Historien. Giessen: Johann Christoph Schröder, 1768. Universitätsbibliothek Heidelberg. VD18 14362627.",
        "source": ORIGINAL,
        "images": stories,
    }
    (DATA / "archive.json").write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # The German OCR is archival, uncorrected; never label it as a verified transcription.
    try:
        content = download(OCR)
        (DATA / "german-ocr.txt").write_bytes(content)
        print(f"ZURICH OCR {len(content)} bytes, saved uncorrected", flush=True)
    except Exception as exc:
        print("ZURICH OCR unavailable:", exc, flush=True)
    try:
        z = json.loads(download(ZURICH))
        (DATA / "zurich-source.json").write_text(json.dumps({
            "count": len(z.get("sequences", [{}])[0].get("canvases", [])),
            "manifest": ZURICH,
            "citation": "Johann Hübner, Zürich: Bürklische Druckerei, ca. 1775. Zentralbibliothek Zürich, AWZ 727. DOI 10.3931/e-rara-85573. Public Domain Mark.",
            "ocr": OCR
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print("ZURICH METADATA unavailable:", exc, flush=True)
    print(f"SUCCESS: 104 archival plates plus {len(folio_results)} original-language text folios; bytes {sum(r[1] for r in results) + sum(r[1] for r in folio_results)}",flush=True)

if __name__ == "__main__":
    main()
