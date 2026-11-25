#!/usr/bin/env python3
"""Align each library OCR page to its existing ALTO line geometry.

This is an editorial index, never a proofread edition. Every line is preserved,
including running headers, marginal notes and ambiguous chapter boundaries.
"""
import json, re, unicodedata, hashlib
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"public/data"
LAYOUT=ROOT/"sources/zurich-layout"
OUT=ROOT/"sources/zurich-editorial"
raw=(DATA/"german-ocr.txt").read_text(encoding="utf8")
draft=json.loads((OUT/"index.json").read_text(encoding="utf8"))
manifest=json.loads((LAYOUT/"manifest.json").read_text(encoding="utf8"))
assert hashlib.sha1(("blob "+str(len(raw.encode()))+"\0").encode()+raw.encode()).hexdigest()==draft["source_git_blob"]
def utf16_len(s):
    return len(s.encode("utf-16-le"))//2
def norm_map(s,offset=0):
    out=[]; positions=[]; pos=offset
    for c in s:
        for ch in unicodedata.normalize("NFKD",c.lower().replace("ſ","s")):
            if ch.isalnum():
                out.append(ch);positions.append(pos)
        pos+=utf16_len(c)
    return "".join(out),positions
spans=[];pos=0
for m in re.finditer(r"\n\s*\n",raw):
    spans.append((pos,m.start()));pos=m.end()
spans.append((pos,len(raw)))
pages=[p for p in manifest["page_index"] if p["lines"]]
assert len(spans)==len(pages)
segments=defaultdict(list)
for rec in draft["records"]:
    for p,a,b,section,reason,marker in rec["segments"]:
        segments[p].append((a,b,rec["id"],section,marker))
records=defaultdict(list); page_reports=[]
for p,(a,b) in zip(pages,spans):
    page=p["page"]
    layout=json.loads((LAYOUT/f"{page:03d}.json").read_text(encoding="utf8"))
    lines=[line for block in layout["blocks"] for line in block["lines"]]
    line_texts=[norm_map(line["text"])[0] for line in lines]
    joined="".join(line_texts)
    original,mapping=norm_map(raw[a:b],utf16_len(raw[:a]))
    matcher=SequenceMatcher(None,joined,original,autojunk=False)
    matched={}
    for block in matcher.get_matching_blocks():
        for i in range(block.size):matched[block.a+i]=mapping[block.b+i]
    matched_n=len(matched); offset=0
    chapter_lines=Counter(); ambiguities=0
    for line,norm in zip(lines,line_texts):
        matches=[matched[i] for i in range(offset,offset+len(norm)) if i in matched]
        offset+=len(norm)
        counts=Counter()
        for i in matches:
            for sa,sb,ch,sect,mark in segments[page]:
                if sa<=i<sb:
                    counts[(ch,sect,mark)]+=1
                    break
        ranked=counts.most_common()
        score=round(len(matches)/max(len(norm),1),4)
        flags=[]
        if score<0.8:flags.append("weak-ocr-to-alto-match")
        if not ranked:flags.append("unassigned-line")
        if len(ranked)>1 and ranked[1][1]>=max(3,0.15*ranked[0][1]):flags.append("mixed-section-or-boundary")
        if line["height"]<=0.018*layout["height"] and line["vpos"]<0.12*layout["height"]:flags.append("possible-running-header")
        if line["width"]<0.2*layout["width"] and line["height"]<0.018*layout["height"]:flags.append("possible-marginal-reference")
        row={"page":page,"line_id":line["id"],"box":[line["hpos"],line["vpos"],line["width"],line["height"]],"ocr":line["text"],"raw_match_ratio":score,"candidate_sections":[{"chapter":c,"section":s,"marker":m,"matched_characters":n} for (c,s,m),n in ranked],"flags":flags}
        if ranked:
            for ch in sorted({k[0] for k in counts}):
                records[ch].append(row);chapter_lines[ch]+=1
        else:
            for ch in sorted({s[2] for s in segments[page]}):records[ch].append(row)
        ambiguities+=bool(flags)
    page_reports.append({"page":page,"line_count":len(lines),"raw_match_ratio":round(matched_n/max(len(joined),1),4),"chapters":dict(chapter_lines),"flagged_lines":ambiguities})
assert set(records)==set(range(1,105)), sorted(set(range(1,105))-set(records))
target=OUT/"geometry";target.mkdir(exist_ok=True)
for ch,rows in sorted(records.items()):
    (target/f"{ch:03d}.json").write_text(json.dumps({"id":ch,"status":"unreviewed-editorial-draft","source":draft["source"],"lines":rows},ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf8")
summary={"status":"unreviewed-editorial-draft","source_git_blob":draft["source_git_blob"],"chapters":len(records),"pages":len(page_reports),"lines":sum(p["line_count"] for p in page_reports),"flagged_lines":sum(p["flagged_lines"] for p in page_reports),"pages_with_match_below_80_percent":sum(p["raw_match_ratio"]<0.8 for p in page_reports),"page_reports":page_reports}
(target/"manifest.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps({k:v for k,v in summary.items() if k!="page_reports"},ensure_ascii=False))
