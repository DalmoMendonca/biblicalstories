#!/usr/bin/env python3
"""Audit the actual reader modules; drafts and corrupted legacy files never count."""
import argparse, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDS=("narrative","questions","teachings","reflection")
LANGS=("de","en","ru")
def module(filename,name):
    p=ROOT/"src"/filename
    return json.loads(p.read_text("utf8").split("export const "+name+" = ",1)[1].strip().removesuffix(";")) if p.exists() else {}
def present(w,f):
    x=w.get(f)
    return bool(isinstance(x,str) and x.strip()) if f in ("narrative","reflection") else bool(isinstance(x,list) and x and all(isinstance(v,str) and v.strip() for v in x))
def sha(v):return hashlib.sha256(v.encode("utf8")).hexdigest()
def numbered(w,lang):
    t=w["narrative"]
    # Russian creation has the printed joint initial markers 1, 2).
    if lang=="ru" and t.startswith("1, 2)"):t="1) 2)"+t[5:]
    # A chapter may contain other numbered quotations. Preserve the matching
    # subsequence and reject missing/reversed main markers.
    nums=[int(n) for n in re.findall(r"(?<!\w)(\d+)[.)](?=\s)",t)]
    expected=list(range(1,len(w["questions"])+1))
    if "question_numbers" in w:
        expected=w["question_numbers"]
        if (not isinstance(expected,list) or len(expected)!=len(w["questions"])
            or not expected or any(type(n) is not int or n<1 for n in expected)
            or expected!=sorted(set(expected)) or expected[0]!=1
            or not w.get("editorial_notes")
            or nums!=list(range(1,expected[-1]+1))):
            return False,nums
    pos=0
    for n in nums:
        if pos<len(expected) and n==expected[pos]:pos+=1
    return pos==len(expected),nums
def main():
    p=argparse.ArgumentParser();p.add_argument("--release",action="store_true");p.add_argument("--output",type=Path,default=ROOT/"public/data/corpus-audit.json");args=p.parse_args()
    de=module("german1768.js","german1768");en=module("englishFromGerman.js","englishFromGerman");ru=module("russianHistorical.js","russianHistorical");historical=module("english1765.js","english1765")
    idx=json.loads((ROOT/"public/data/zurich-chapters.json").read_text("utf8"));raw=(ROOT/"public/data/german-ocr.txt").read_bytes()
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==idx["source_git_blob"]
    assert [r["id"] for r in idx["records"]]==list(range(1,105))
    archive=json.loads((ROOT/"public/data/archive.json").read_text("utf8"))
    assert [r["id"] for r in archive["images"]]==list(range(1,105))
    for m in (de,en,ru,historical):assert set(m)<=set(map(str,range(1,105)))
    rows=[];seen={l:{} for l in LANGS};issues=[]
    for i in range(1,105):
        k=str(i);g,e,r=de.get(k,{}),en.get(k,{}),ru.get(k,{})
        row={"id":i,"german_library_ocr_available":True,"historical_english_narrative":bool(historical.get(k))}
        for lang,w in (("de",g),("en",e),("ru",r)):
            fields={f:present(w,f) for f in FIELDS};checks={};errors=[]
            if w:
                if not all(fields.values()):errors.append("missing-required-section")
                if not w.get("title") or not w.get("reference"):errors.append("missing-title-or-reference")
                pages=w.get("source_pages") if lang=="ru" else w.get("pages")
                if not pages or not all(isinstance(x,int) and x>0 for x in pages):errors.append("missing-specific-source-pages")
                if lang=="ru" and (w.get("kind")!="historical-transcription" or not w.get("edition") or not w.get("document_id")):errors.append("nonhistorical-russian-or-missing-edition")
                if lang=="de" and not (w.get("printed") and w.get("latin")):errors.append("missing-printed-pages-or-latin")
                if lang=="en" and (not g or w.get("kind")!="new-translation-from-transcribed-german" or w.get("pages")!=g.get("pages") or w.get("latin")!=g.get("latin")):errors.append("translation-provenance-or-latin-mismatch")
                if all(fields.values()):
                    checks["narrative_numbering"],checks["numbered_passages"]=numbered(w,lang)
                    if not checks["narrative_numbering"]:errors.append("numbered-passages-do-not-correspond-to-questions")
                    checks["question_count"]=len(w["questions"]);checks["teaching_count"]=len(w["teachings"]);checks["reflection_lines"]=len(w["reflection"].splitlines());checks["latin_lines"]=len(w.get("latin","").splitlines())
                    checks["source_expected_counts"]=w.get("expected")
                    if w.get("expected"):
                        for field in ("questions","teachings"):
                            if w["expected"].get(field)!=len(w[field]):errors.append("source-count-mismatch-"+field)
                    if lang=="en" and g:
                        if w.get("question_numbers")!=g.get("question_numbers"):errors.append("german-english-question-number-mismatch")
                        if any(len(w[f])!=len(g[f]) for f in ("questions","teachings")) or len(w["reflection"].splitlines())!=len(g["reflection"].splitlines()):errors.append("german-english-section-count-mismatch")
                    for f in FIELDS:
                        value=w[f] if isinstance(w[f],str) else "\n".join(w[f])
                        if re.search(r"\b(?:TODO|TBD|PLACEHOLDER|LOREM IPSUM|INSERT TEXT HERE)\b",value,re.I):errors.append("placeholder-"+f)
                        digest=sha(value)
                        if f=="narrative" and digest in seen[lang]:errors.append("duplicate-narrative-"+str(seen[lang][digest]))
                        if f=="narrative":seen[lang][digest]=i
                    checks["section_sha256"]={f:sha(w[f] if isinstance(w[f],str) else "\n".join(w[f])) for f in FIELDS}
                if errors:issues.append({"id":i,"language":lang,"errors":errors})
            source_compared=bool(w) and (w.get("source_compared") is True or lang in ("de","en"))
            independently_reviewed=bool(w) and w.get("independent_review") is True
            row[lang]={**fields,"source_compared":source_compared,"independently_reviewed":independently_reviewed,"structurally_valid":bool(w) and not errors and all(fields.values()),"checks":checks}
        rows.append(row)
    counts={l:{f:sum(row[l][f] for row in rows) for f in FIELDS} for l in LANGS}
    complete=sum(sum(v.values()) for v in counts.values())
    reviewed=sum(sum(row[l][f] for f in FIELDS) for row in rows for l in LANGS if row[l]["independently_reviewed"])
    all_chapters={l:sum(row[l]["structurally_valid"] for row in rows) for l in LANGS}
    report={"required_sections":1248,"structured_sections_present":complete,"independently_reviewed_sections":reviewed,"counts":counts,"structurally_valid_chapters":all_chapters,"german_ocr_indexed":104,"historical_english_narratives":sum(row["historical_english_narrative"] for row in rows),"latin_chapters":{l:sum(row[l]["checks"].get("latin_lines",0)>0 for row in rows) for l in LANGS},"issues":issues,"release_ready":complete==1248 and reviewed==1248 and all(v==104 for v in all_chapters.values()) and not issues,"rows":rows,"note":"Structure is not fidelity. Source-compared transcriptions and new English translations are distinguished from independent review. Unreviewed OCR, legacy machine translations, and narrative-only witnesses are excluded. Russian printed prose reflections are preserved in their historical form; German Latin is displayed separately if absent in the Russian source."}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},ensure_ascii=False,indent=2))
    if issues:raise SystemExit("STRUCTURAL VALIDATION FAILED")
    if args.release and not report["release_ready"]:raise SystemExit("RELEASE BLOCKED: incomplete or not independently source-reviewed")
if __name__=="__main__":main()
