#!/usr/bin/env python3
"""Fail publication if a story is missing one of its three *complete* text witnesses."""
from pathlib import Path
import json
import statistics

root=Path(__file__).resolve().parents[1]
files=sorted((root/"public"/"texts").glob("*.json"))
if len(files)!=104:raise SystemExit(f"Incomplete multilingual edition: {len(files)}/104")
total={"de":0,"en":0,"ru":0}
suspect=[]
for n,p in enumerate(files,1):
    rec=json.loads(p.read_text("utf8"))
    if rec.get("id")!=n:raise AssertionError(f"Wrong story id: {p}")
    if rec.get("editorial",{}).get("proofread") is True:
        raise AssertionError("Uncorrected machine OCR was improperly marked proofread")
    for lang in total:
        t=rec.get(lang,{}).get("text","")
        if len(t)<200:raise AssertionError(f"{n}: {lang} text too short ({len(t)} characters)")
        if len(set(t.split()))<12:raise AssertionError(f"{n}: {lang} suspiciously repetitive")
        total[lang]+=len(t)
    if rec["de"]["text"]==rec["en"]["text"] or rec["en"]["text"]==rec["ru"]["text"]:
        raise AssertionError(f"Translation replaced by repeated source in story {n}")
    if rec["de"].get("kind")!="uncorrected-fraktur-ocr":
        raise AssertionError("German text must retain explicit original OCR source designation")
    for lang in ("en","ru"):
        if not rec[lang]["kind"].startswith("modern-machine-translation"):
            raise AssertionError(f"{n}: untraceable {lang} translation provenance")
    if len(rec["en"]["text"])/len(rec["de"]["text"])<.15:
        suspect.append((n,"English too short"))
    if len(rec["ru"]["text"])/len(rec["de"]["text"])<.15:
        suspect.append((n,"Russian too short"))
if suspect:raise AssertionError("Potential truncation: "+str(suspect))
print("PASS: 104 histories, 312 nonempty source-linked texts, characters",total)
