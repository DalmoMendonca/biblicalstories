#!/usr/bin/env python3
"""Create lossless, page-aligned editorial packets for the 1825 Russian witness.

No OCR, translation, or source modification occurs here. All original OCR words
and coordinates are retained. Candidates are explicitly not publication text.
Exact boundaries and reading order must be checked against the facsimile.
"""
import csv, hashlib, json, re, statistics, sys
from collections import defaultdict, Counter
from difflib import SequenceMatcher
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"sources"
OUT=SRC/"russian-editorial"
OUT.mkdir(exist_ok=True)
def load(path):
    return json.loads(path.read_text("utf8"))
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):
    data=json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n"
    if not path.exists() or path.read_text("utf8")!=data:
        tmp=path.with_suffix(".tmp")
        tmp.write_text(data,"utf8");tmp.replace(path)
def normalized(s):
    return re.sub(r"[^а-яё]", "",s.lower().replace("ѣ","е").replace("і","и").replace("ѳ","ф"))
def similar(a,b):
    a,b=normalized(a),normalized(b)
    return SequenceMatcher(None,a,b).ratio() if a and b else 0
HEADS={"questions":"Вопросы","teachings":"Полезныя нравоученія","reflection":"Благочестивыя размышленія","chapter-heading":"Исторія"}
def get_lines(path):
    groups=defaultdict(list)
    dims=None
    with path.open(encoding="utf8",newline="") as f:
        for row in csv.DictReader(f,delimiter="\t",quoting=csv.QUOTE_NONE):
            level=int(row["level"])
            if level==1:dims=[int(row["width"]),int(row["height"])]
            if level!=5 or not row["text"]:continue
            k=tuple(int(row[n]) for n in ("block_num","par_num","line_num"))
            groups[k].append({"text":row["text"],"box":[int(row[n]) for n in ("left","top","width","height")],"confidence":float(row["conf"])})
    lines=[]
    for k,words in groups.items():
        x=min(w["box"][0] for w in words);y=min(w["box"][1] for w in words)
        x1=max(w["box"][0]+w["box"][2] for w in words);y1=max(w["box"][1]+w["box"][3] for w in words)
        lines.append({"id":".".join(map(str,k)),"box":[x,y,x1-x,y1-y],"ocr":" ".join(w["text"] for w in words),"words":words})
    return dims,lines
def annotate(lines,dims):
    if not lines:return []
    # This is a diagnostic heuristic, not a deletion/filtering stage.
    h=statistics.median(l["box"][3] for l in lines if l["box"][3]>0)
    headings=[]
    for i,l in enumerate(lines):
        for name,label in HEADS.items():
            score=similar(l["ocr"],label)
            if name=="chapter-heading":score=similar(l["ocr"].split()[0],label)
            if score>=.66:
                headings.append((i,name,score));break
    candidates={i:(name,score) for i,name,score in headings}
    active="unassigned"
    for i,l in enumerate(lines):
        flags=[]
        if i in candidates:
            active,score=candidates[i]
            l["candidate_section"]="heading-"+active
            l["heading_similarity"]=round(score,3)
        else:
            x,y,w,lh=l["box"]
            if active=="questions" or (y>dims[1]*.55 and lh<h*.85):
                l["candidate_section"]="questions"
            elif active in ("teachings","reflection"):
                l["candidate_section"]=active
            elif active=="chapter-heading":
                l["candidate_section"]="narrative-or-title"
            else:
                l["candidate_section"]="narrative-or-continuation"
            if w<dims[0]*.12:flags.append("possible-margin-or-page-number")
        if any(w["confidence"]<40 for w in l["words"]):flags.append("low-confidence-word")
        l["flags"]=flags
    return headings
def main():
    expected={"ot":260,"nt":196}
    allpages={}; receipts=[]; errors=[]
    for book,count in expected.items():
        prov=load(ROOT/f"public/data/russian-1825-{book}-provenance.json")
        assert prov["page_count"]==count
        indexed={p["page"]:p for p in prov["images"]}
        for n in range(1,count+1):
            base=SRC/f"russian-1825-ocr/{book}/{n:03d}"
            try:
                rec=load(base.with_suffix(".json"))
                assert rec["page"]==n
                assert rec["image_sha256"]==indexed[n]["archived_sha256"]==digest(ROOT/rec["image"])
                assert digest(base.with_suffix(".txt"))==rec["text_sha256"]
                assert digest(base.with_suffix(".tsv"))==rec["tsv_sha256"]
                dims,lines=get_lines(base.with_suffix(".tsv"))
                assert dims
                heads=annotate(lines,dims)
                page={"page":n,"book":book,"image":rec["image"],"source":indexed[n]["source"],"image_sha256":rec["image_sha256"],"ocr_sha256":rec["text_sha256"],"tsv_sha256":rec["tsv_sha256"],"dimensions":dims,"lines":lines,"heading_candidates":[{"line":lines[i]["id"],"section":s,"score":round(v,3)} for i,s,v in heads]}
                allpages[book,n]=page
                receipts.append({"book":book,"page":n,"lines":len(lines),"characters":rec["characters"],"headings":page["heading_candidates"]})
            except Exception as exc:
                errors.append({"book":book,"page":n,"error":str(exc)})
    records=[]
    for book in ("ot","nt"):
        idx=load(SRC/f"russian-1825-{book}-chapters.json")
        for entry in idx["records"]:
            first=entry.get("scan_start_verified",entry["scan_start_candidate"])
            last=entry.get("scan_end_verified",entry["scan_end_candidate"])
            pages=[allpages[book,n] for n in range(first,last+1) if (book,n) in allpages]
            missing=[n for n in range(first,last+1) if (book,n) not in allpages]
            heads=Counter(h["section"] for p in pages for h in p["heading_candidates"])
            packet={"id":entry["id"],"status":"unreviewed-editorial-candidates-not-reader-text","edition":idx["edition"],"document_id":idx["document_id"],"toc_entry":entry,"pages":pages,"missing_pages":missing,"boundary_status":"source-compared-range" if "scan_start_verified" in entry else "overlapping-toc-candidate-range","warning":"Candidate sections and OCR words are not verified; shared pages intentionally overlap; inspect the printed scans before accepting any text."}
            save(OUT/f'{entry["id"]:03d}.json',packet)
            records.append({"id":entry["id"],"book":book,"first":first,"last":last,"missing_pages":missing,"lines":sum(len(p["lines"]) for p in pages),"heading_candidates":dict(heads),"boundary_status":packet["boundary_status"]})
    assert [r["id"] for r in records]==list(range(1,105))
    report={"status":"unreviewed-editorial-candidates-not-reader-text","expected_source_pages":sum(expected.values()),"verified_page_checksums":len(allpages),"source_page_errors":errors,"chapter_packets":len(records),"records":records,"pages":receipts}
    save(OUT/"index.json",report)
    print(json.dumps({k:v for k,v in report.items() if k not in ("records","pages")},ensure_ascii=False))
    if errors:raise SystemExit("Source checksum or OCR receipt errors; partial packets preserved")
if __name__=="__main__":main()
