#!/usr/bin/env python3
"""Repair incomplete historical source-text records only; never overwrite verified existing records.

The source is the Giessen 1768 original facsimile, read by Tesseract Fraktur OCR;
EN/RU are modern machine translations, NOT Hübner's historic translated editions.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
import urllib.request
import urllib.parse
import time
sys.path.insert(0,str(Path(__file__).parent))
import produce_texts as original

# Recover only IDs still missing after the initial ~101/104 completed run.
MISSING=[n for n in range(1,105) if not (original.DEST/f"{n:03d}.json").exists()]
print("MISSING_SOURCE_CHAPTERS",MISSING,flush=True)

def translate_fragments(fragment,lang):
    """First try the historically established endpoint; bisect OCR noise on failure."""
    try:
        return original.translate_chunk(fragment,lang)
    except Exception as error:
        # A rare untranslatable block of OCR can defeat whole-paragraph requests,
        # but shorter complete sentences are accepted reliably.
        if len(fragment)<=220:
            # Google may preserve original noisy proper names; a zero-length
            # translation is not accepted or silently discarded.
            url="https://clients5.google.com/translate_a/t?"+urllib.parse.urlencode({
                "client":"dict-chrome-ex","sl":"de","tl":lang,"q":fragment
            })
            req=urllib.request.Request(url,headers=original.HEADERS)
            with urllib.request.urlopen(req,timeout=25) as r:
                response=json.load(r)
            value=str(response[0] if isinstance(response[0],str) else
                      "".join(part[0] for part in response[0] if part[0])).strip()
            if len(value)<8:
                raise RuntimeError(f"Could not translate short source span ({lang}, {fragment!r}): {error}")
            print("SHORT_BLOCK_TRANSLATED",lang,len(fragment),len(value),flush=True)
            return value
        halfway=len(fragment)//2
        choices=[fragment.rfind(ch,0,halfway+220) for ch in ("\n\n","\n",". ","; ",", "," ")]
        split=max((x for x in choices if x>=halfway-300),default=halfway)
        split=max(40,min(len(fragment)-40,split+1))
        left,right=fragment[:split].strip(),fragment[split:].strip()
        if not left or not right: raise RuntimeError("Cannot partition noisy source OCR")
        print("RETRY_SEGMENT",lang,len(fragment),"as",len(left),len(right),flush=True)
        return translate_fragments(left,lang)+"\n\n"+translate_fragments(right,lang)

def robust_translation(src,lang):
    return "\n\n".join(translate_fragments(piece,lang) for piece in original.chunks(src,cap=1800))

original.translate_story=robust_translation

def main():
    if not MISSING:
        print("Already complete: all 104 original-language chapters",flush=True)
        return
    sources=[]
    seen=set()
    for n in MISSING:
        item=original.ARCHIVE["images"][n-1]
        for key,path in original.pages_for(item):
            if key not in seen:seen.add(key);sources.append((key,path))
        if not item["folios"]:
            for neighbor in original.ARCHIVE["images"][max(0,n-2):min(104,n+1)]:
                for key,path in original.pages_for(neighbor):
                    if key not in seen:seen.add(key);sources.append((key,path))
    print("OCR_REQUIRED_PAGES",len(sources),flush=True)
    pages={}
    with ThreadPoolExecutor(max_workers=4) as executor:
        for f in as_completed([executor.submit(original.ocr_one,src) for src in sources]):
            key,value=f.result();pages[key]=value
            print("SOURCE_PAGE_OK",key,len(value),flush=True)
    for n in MISSING:
        data=original.process_story(original.ARCHIVE["images"][n-1],pages)
        for lang in ("de","en","ru"):
            if len(data[lang]["text"])<200:
                raise ValueError(f"Story {n}, language {lang}, too short")
        target=original.DEST/f"{n:03d}.json"
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf8")
        print("REPAIRED_STORY",n,[len(data[c]["text"]) for c in ("de","en","ru")],flush=True)
    files=sorted(original.DEST.glob("*.json"))
    if len(files)!=104:raise RuntimeError(f"Only {len(files)} of 104 after repair")
    coverage={
        "total":104,"text_complete":104,
        "witness":"Giessen 1768, Universitätsbibliothek Heidelberg",
        "german_kind":"uncorrected Fraktur OCR of printed originals",
        "english_kind":"modern machine translation of uncorrected German OCR; NOT the historical 1765 text",
        "russian_kind":"modern machine translation of uncorrected German OCR; NOT the historical 1815 or 1825 text",
        "proofread":False,
        "source":"https://digi.ub.uni-heidelberg.de/diglit/huebner1768",
        "exceptions":[]
    }
    (original.DATA/"text-coverage.json").write_text(json.dumps(coverage,indent=2),encoding="utf8")
    print("PASS: ALL 104 CHAPTERS, 312 LANGUAGE RECORDS",flush=True)

if __name__=="__main__":main()
