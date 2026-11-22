#!/usr/bin/env python3
"""Independent offline backup of a 104-story trilingual Hübner edition.

Local Argos Translate models, no external translation service at runtime.
The output is kept on a separate branch pending comparisons and may be
promoted to production only if the primary source transcription fails.

German: uncorrected OCR of original Giessen 1768 pages.
English: modern machine translation de→en.
Russian: modern machine translation de→en→ru through an English pivot.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from functools import lru_cache
import json
import os
from pathlib import Path
import subprocess
import sys

import argostranslate.package
import argostranslate.translate

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import produce_texts as core

def setup_models():
    argostranslate.package.update_package_index()
    available=argostranslate.package.get_available_packages()
    for from_code,to_code in (("de","en"),("en","ru")):
        candidates=[p for p in available if p.from_code==from_code and p.to_code==to_code]
        if not candidates:raise RuntimeError(f"No offline Argos model for {from_code}→{to_code}")
        pkg=candidates[0]
        print("DOWNLOADING MODEL",from_code,to_code,flush=True)
        file=pkg.download()
        print("INSTALLING MODEL",file,flush=True)
        argostranslate.package.install_from_path(file)
    probe=argostranslate.translate.translate("Gott erschuf Himmel und Erde.","de","en")
    if len(probe)<10:raise RuntimeError("Offline language model failed")
    print("TRANSLATION MODELS READY",probe,flush=True)

@lru_cache(maxsize=3)
def translate_english(src):
    parts=core.chunks(src,cap=2400)
    return "\n\n".join(argostranslate.translate.translate(p,"de","en") for p in parts)

def translate_story(src,lang):
    english=translate_english(src)
    if lang=="en":return english
    parts=core.chunks(english,cap=2400)
    return "\n\n".join(argostranslate.translate.translate(p,"en","ru") for p in parts)

core.translate_story=translate_story

def main():
    setup_models()
    allpages={key:path for entry in core.ARCHIVE["images"] for key,path in core.pages_for(entry)}
    print("OCR ORIGINAL GERMAN PAGES",len(allpages),flush=True)
    pages={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks=[pool.submit(core.ocr_one,(key,path)) for key,path in allpages.items()]
        for i,t in enumerate(as_completed(tasks),1):
            key,result=t.result()
            pages[key]=result
            if i%40==0:print("OCR",i,len(tasks),flush=True)
    core.DEST.mkdir(parents=True,exist_ok=True)
    for n,book in enumerate(core.ARCHIVE["images"],1):
        path=core.DEST/f"{n:03d}.json"
        record=core.process_story(book,pages)
        record["en"]["kind"]="modern-machine-translation-of-1768-ocr-offline"
        record["ru"]["kind"]="modern-offline-machine-translation-of-1768-ocr"
        record["editorial"]["translation_engine"]="Argos Translate, de→en→ru (English pivot for Russian)"
        if any(len(record[lang]["text"])<150 for lang in ("de","en","ru")):
            raise ValueError(f"Short text for chapter {n}")
        path.write_text(json.dumps(record,ensure_ascii=False,separators=(",",":")),"utf-8")
        print("BACKUP STORY",n,"chars",*[len(record[k]["text"]) for k in ("de","en","ru")],flush=True)
    n=len(list(core.DEST.glob("*.json")))
    assert n==104
    core.DATA.joinpath("text-coverage.json").write_text(
        json.dumps({"total":104,"text_complete":104,
                    "witness":"Giessen 1768, Universitätsbibliothek Heidelberg",
                    "german_kind":"uncorrected Fraktur OCR of printed originals",
                    "english_kind":"modern offline machine translation from 1768 German OCR",
                    "russian_kind":"modern offline de→en→ru machine translation via English",
                    "proofread":False},
            ensure_ascii=False,indent=2),encoding="utf-8")
    print("PASS: BACKUP 104 SOURCE CHAPTERS, 312 LANGUAGE RECORDS",flush=True)

if __name__=="__main__":main()
