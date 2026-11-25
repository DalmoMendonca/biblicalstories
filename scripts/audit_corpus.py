#!/usr/bin/env python3
"""Audit real structured source witnesses, never count machine OCR drafts as complete."""
import argparse, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIELDS=("narrative","questions","teachings","reflection")
def module(filename, name):
    p=ROOT/"src"/filename
    if not p.exists(): return {}
    return json.loads(p.read_text("utf8").split("export const "+name+" = ",1)[1].strip().removesuffix(";"))
def present(record,field):
    x=record.get(field)
    return (isinstance(x,str) and bool(x.strip())) if field in ("narrative","reflection") else (isinstance(x,list) and bool(x) and all(isinstance(v,str) and v.strip() for v in x))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--release",action="store_true")
    args=parser.parse_args()
    de=module("german1768.js","german1768")
    en=module("englishFromGerman.js","englishFromGerman")
    historical=module("english1765.js","english1765")
    ru=module("russianHistorical.js","russianHistorical")
    idx=json.loads((ROOT/"public/data/zurich-chapters.json").read_text("utf8"))
    raw=(ROOT/"public/data/german-ocr.txt").read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert sha==idx["source_git_blob"], "OCR source changed without reindexing"
    assert [r["id"] for r in idx["records"]]==list(range(1,105))
    rows=[]
    for i in range(1,105):
        key=str(i); g=de.get(key,{}); e=en.get(key,{}); r=ru.get(key,{})
        if e:
            assert g and e["kind"]=="new-translation-from-transcribed-german"
            assert e["pages"]==g["pages"]
            assert e["latin"]==g["latin"]
            for field in ("questions","teachings"):
                assert len(e[field])==len(g[field]),(i,field)
            assert len(e["reflection"].splitlines())==len(g["reflection"].splitlines()),i
        if r:
            assert r["kind"]=="historical-transcription" and r.get("source_pages") and r.get("edition")
        row={"id":i,"german_library_ocr_available":True,"historical_english_narrative":bool(historical.get(key))}
        for lang,witness in (("de",g),("en",e),("ru",r)):
            row[lang]={field:present(witness,field) for field in FIELDS}
            row[lang]["source_compared"]=bool(witness) and witness.get("independent_review") is True
        rows.append(row)
    counts={lang:{field:sum(row[lang][field] for row in rows) for field in FIELDS} for lang in ("de","en","ru")}
    complete=sum(sum(v.values()) for v in counts.values())
    reviewed=sum(sum(row[lang][f] for f in FIELDS) for row in rows for lang in ("de","en","ru") if row[lang]["source_compared"])
    report={"required_sections":1248,"structured_sections_present":complete,"independently_reviewed_sections":reviewed,"counts":counts,"german_ocr_indexed":104,"historical_english_narratives":sum(row["historical_english_narrative"] for row in rows),"rows":rows,"note":"Section presence does not guarantee fidelity. OCR-only and historical narrative-only witnesses are excluded from structured completion."}
    (ROOT/"public/data/corpus-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
    if args.release and (complete!=1248 or reviewed!=1248):
        raise SystemExit("RELEASE BLOCKED: incomplete or not independently source-reviewed")
if __name__=="__main__": main()
