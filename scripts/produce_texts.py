#!/usr/bin/env python3
"""Build three *readable* language texts from the 1768 Hübner source folios.

German = uncorrected Fraktur OCR of the archived Giessen 1768 printed pages.
English / Russian = explicitly modern machine translations of that OCR text.
Neither translation is passed off as the historical 1765 / 1815 witness.
All 104 stories keep bibliographic source pages and OCR provenance.

CAUTION: An uncorrected OCR transcription cannot be certified word-for-word.
Source page facsimiles must remain available beside the copy.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"public"
FOLIOS=PUBLIC/"folios"
DEST=PUBLIC/"texts"
DATA=PUBLIC/"data"
ARCHIVE=json.loads((DATA/"archive.json").read_text("utf-8"))
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; historical-public-domain-edition/1.0)"}
GTRANS="https://translate.googleapis.com/translate_a/single"
LANGS=("en","ru")

def roman(n):
    result=""
    for v,s in ((50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")):
        while n>=v:result+=s;n-=v
    return result

def normalize_fraktur(s):
    # Unicode normalization for translation only, historical orthography in raw OCR retained.
    replacements={"ſ":"s","ﬅ":"st","ꝛ":"r","‚":",","„":'"'}
    for a,b in replacements.items():s=s.replace(a,b)
    s=re.sub(r"(?<=\w)[-\u00ad]\s*\n\s*(?=\w)","",s)
    s=re.sub(r"\n{3,}","\n\n",s)
    s=re.sub(r" {2,}"," ",s)
    return s.strip()

def ocr_one(item):
    key,path=item
    if not path.exists():
        raise FileNotFoundError(str(path))
    p=subprocess.run(
        ["tesseract",str(path),"stdout","-l","frk","--psm","3"],
        capture_output=True,text=True,timeout=65)
    if p.returncode:
        raise RuntimeError(f"{key} OCR failed: {p.stderr[-500:]}")
    result=p.stdout.strip()
    if len(result)<180:
        raise RuntimeError(f"{key} OCR too short ({len(result)} chars)")
    return key,result

def pages_for(story):
    return [(f"{story['id']:03d}-{i:02d}",FOLIOS/f"{story['id']:03d}-{i:02d}.webp")
            for i,_ in enumerate(story["folios"],1)]

def possible_heading_start(s,chapter):
    # OCR of a Fraktur printed book often confuses s/ſ/f and Roman I with 1.
    label=str(chapter)
    patterns=[
        rf"\bDie\s+{label}[.,]?\s+Hi[ſsft]torie",
        rf"\bDie\s+{roman(chapter)}[.,]?\s+Hi[ſsft]torie",
        rf"\bDie\s+{label}[.,]?\s+Historie",
    ]
    starts=[]
    normalized=normalize_fraktur(s)
    for pat in patterns:
        starts += [m.start() for m in re.finditer(pat,normalized,re.I)]
    return min(starts) if starts else None

def scrub_watermarks(s):
    # Only obvious digitizer furniture; do not rewrite historical German prose.
    s=re.sub(r"(?im)^\s*UNIVERSITÄTS\s*$","",s)
    s=re.sub(r"(?im)^\s*BIBLIOTHEK\s*$","",s)
    s=re.sub(r"(?im)^.*digi\.ub\.uni-heidelberg\.de.*$","",s)
    s=re.sub(r"(?im)^\s*DFG\s*$","",s)
    return re.sub(r"\n{3,}","\n\n",s).strip()

def translate_chunk(content,lang):
    query=urllib.parse.urlencode(
        [("client","gtx"),("sl","de"),("tl",lang),("dt","t"),("q",content)])
    target=GTRANS+"?"+query
    # service supports HTTP GET; honor request-size limits through small chunks.
    if len(target)>9100:
        raise ValueError("Translation chunk URL exceeded 9KB")
    error=None
    for attempt in range(7):
        try:
            req=urllib.request.Request(target,headers=HEADERS)
            with urllib.request.urlopen(req,timeout=35) as r:
                data=json.load(r)
            parts=data[0]
            result="".join(str(part[0]) for part in parts if part and part[0])
            if len(result)<max(40,len(content)*.16):
                raise RuntimeError("Translation unexpectedly short")
            return result.strip()
        except (urllib.error.URLError,TimeoutError,ValueError,IndexError,KeyError,RuntimeError) as e:
            error=e
            pause=min(32,(attempt+1)**1.55)
            time.sleep(pause)
    raise RuntimeError(f"{lang} translation unavailable after retries: {error}")

def chunks(s,cap=1800):
    """Split at human-readable paragraph/sentence boundaries; never truncate."""
    text=normalize_fraktur(s)
    result=[]
    while text:
        if len(text)<=cap:
            result.append(text);break
        window=text[:cap]
        breaks=[window.rfind(c) for c in ("\n\n","\n",". ","? ","! ","; ",", "," ")]
        cut=max([b for b in breaks if b>=int(cap*.60)] or [cap-1])
        cut+=1
        result.append(text[:cut].strip())
        text=text[cut:].lstrip()
    assert "".join(z.replace(" ","") for z in result), "Empty chunk list"
    return result

def translate_story(s,lang):
    pieces=chunks(s)
    outputs=[translate_chunk(p,lang) for p in pieces]
    result="\n\n".join(outputs)
    if len(result)<150:
        raise RuntimeError(f"Translated story is too short: {lang}")
    return result

def process_story(item,allocr):
    n=item["id"]
    own=pages_for(item)
    sources=list(item["folios"])
    if not own:
        # Heidelberg's plate 17 NT sits adjacent to an earlier/later text-page
        # boundary; do not invent an independent page that does not exist.
        adjacent=ARCHIVE["images"][n-2:n+1]
        own=[p for entry in adjacent for p in pages_for(entry)]
        sources=[f for entry in adjacent for f in entry["folios"]]
        boundary_note="Source-page boundary requires manual collation; adjacent folios included."
    else:
        boundary_note=""
    raw="\n\n".join(allocr[k] for k,_ in own)
    if boundary_note:
        # If found, isolate NT XVII from OCR of neighboring book leaves.
        start=possible_heading_start(raw,item["number"])
        finish=possible_heading_start(raw,item["number"]+1)
        if start is not None:
            raw=normalize_fraktur(raw)[start:finish if finish is not None and finish>start else None]
    else:
        # Remove preceding history's tail only when the new chapter's heading
        # is actually found on the first source page.
        first=allocr[own[0][0]]
        start=possible_heading_start(first,item["number"])
        if start is not None and 0<start<len(first)*.80:
            raw=first[start:]+"\n\n"+"\n\n".join(allocr[k] for k,_ in own[1:])
    raw=scrub_watermarks(raw)
    if len(raw)<300:
        raise RuntimeError(f"Story {n}: German source transcription under 300 chars")
    data={
        "id":n,
        "de":{"text":raw,"kind":"uncorrected-fraktur-ocr","source":"Giessen 1768",
              "source_pages":list(dict.fromkeys(f["source"] for f in sources))},
        "en":{"text":"","kind":"modern-machine-translation-of-1768-ocr",
              "source":"German OCR; Giessen 1768"},
        "ru":{"text":"","kind":"modern-machine-translation-of-1768-ocr",
              "source":"German OCR; Giessen 1768"},
        "editorial":{"boundary_note":boundary_note,"proofread":False}
    }
    for language in LANGS:
        data[language]["text"]=translate_story(raw,language)
    return data

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    allpages={key:path for entry in ARCHIVE["images"] for key,path in pages_for(entry)}
    print(f"OCR of {len(allpages)} authentic 1768 Fraktur pages",flush=True)
    allocr={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(ocr_one,(key,path)) for key,path in allpages.items()]
        for i,f in enumerate(as_completed(futures),1):
            key,transcription=f.result()
            allocr[key]=transcription
            if i%40==0:print(f"OCR {i}/{len(allpages)}",flush=True)
    print(f"OCR finished; {sum(len(z) for z in allocr.values())} source characters",flush=True)

    results={}
    failure=[]
    # Avoid burst traffic; at most two chapters translating at once.
    # Resumability: keep already-complete validated per-story text on rerun.
    pending=[]
    for item in ARCHIVE["images"]:
        n=item["id"]
        path=DEST/f"{n:03d}.json"
        if path.exists():
            try:
                previous=json.loads(path.read_text("utf-8"))
                if all(len(previous[k]["text"])>150 for k in ("de","en","ru")):
                    results[n]=previous;continue
            except (ValueError,KeyError,TypeError):pass
        pending.append(item)
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut={pool.submit(process_story,item,allocr):item["id"] for item in pending}
        for f in as_completed(fut):
            n=fut[f]
            try:
                data=f.result()
                path=DEST/f"{n:03d}.json"
                path.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),"utf-8")
                results[n]=data
                print("TEXT COMPLETED",n,"chars",
                      *[len(data[k]["text"]) for k in ("de","en","ru")],flush=True)
            except Exception as exc:
                failure.append((n,str(exc)))
                print("TEXT FAILED",n,str(exc),flush=True)
    coverage={
        "witness":"Giessen 1768, Universitätsbibliothek Heidelberg",
        "german_kind":"uncorrected Fraktur OCR of original printed pages",
        "english_kind":"modern machine translation from German OCR; not the 1765 translation",
        "russian_kind":"modern machine translation from German OCR; not the 1815/1825 translations",
        "text_complete":sum(1 for x in results.values() if all(len(x[k]["text"])>150 for k in ("de","en","ru"))),
        "total":104,
        "provenance":"/data/archive.json",
        "exceptions":failure
    }
    (DATA/"text-coverage.json").write_text(json.dumps(coverage,ensure_ascii=False,indent=2),"utf-8")
    print("TEXT COVERAGE",coverage["text_complete"],"/ 104",flush=True)
    if failure:print("FAILURES",failure,flush=True)
    if len(results)!=104:
        # Do not claim a fully translated edition until every file is present.
        raise RuntimeError(f"Only {len(results)}/104 full trilingual chapters generated.")
    for n in range(1,105):
        data=results[n]
        assert all(len(data[lang]["text"])>150 for lang in ("de","en","ru"))
    print("PASS: 104 complete chapters each in 3 languages; 312 provenance-marked texts",flush=True)

if __name__=="__main__":
    main()
