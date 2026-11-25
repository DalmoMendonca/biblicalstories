// Deterministic editorial workspace. Never publish these unreviewed classifications.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
function buildDraft(raw,index,manifest){
  const nonempty=manifest.page_index.filter(p=>p.lines);
  const pages=[];let prev=0;for(const m of raw.matchAll(/\n\s*\n/g)){pages.push({start:prev,end:m.index});prev=m.index+m[0].length}pages.push({start:prev,end:raw.length});
  if(pages.length!==nonempty.length)throw Error("ALTO/text page count mismatch");
  pages.forEach((p,i)=>{p.page=nonempty[i].page;p.source_id=nonempty[i].id});
  const q=/^\s*[^a-zA-ZäöüÄÖÜ]{0,4}Deutliche\s+[FK8][rvt][aä][gctz][eä][n»!.]*/i;
  const t=/^\s*[^a-zA-ZäöüÄÖÜ]{0,4}N[üu]tzliche\s+Lehr[eä][nstr.!»]*/i;
  const v=/^\s*[^a-zA-ZäöüÄÖÜ]{0,4}G[oö]tt?se?li[gct]e\s+Gedan[ck]+[eä]n/i;
  const qstart=/^\s*[-'»]?\s*[0-9irlozsS]{1,3}\s*[.?)»;]\s*(?:W[aeiouäöü]|WaS|Wie|Wer|Wor|Wod|Wem|Wes|Woz|Ist|Sind|Hat|Hatte|Kan|Kann|Muß|Durf|That|Thut|Thaten|Ließ|Soll|Solle|War|Waren|Kam|Gieng|Ging|Gab|Sahe|Sprach|Sagte|Konnte|Machte|Fiel|Blieb|Wurde|Ward|Glaub|Fand|Lebt|Stund|Stand|Hielt|Nahm|Nahmen|W[äa]r|Rief|Redete|Nahm|Kamen|Haben|Hatten)/i;
  const questionLike=x=>qstart.test(x)&&x.includes("?");
  const latin=/^\s*(?:Lat[eia][ij]nisch|Versus\s+Latini|Lateinische\s+Verse)\b/i;
  const result=[];
  for(const r of index.records){
    let state="narrative", segments=[], flags=[];
    for(const p of pages.filter(x=>x.start<r.end&&x.end>r.start)){
      const start=Math.max(p.start,r.start),end=Math.min(p.end,r.end);
      const fragment=raw.slice(start,end);let lines=[],offset=start;
      for(const line of fragment.split("\n")){lines.push({start:offset,end:offset+line.length,text:line});offset+=line.length+1}
      if(state==="questions")state="narrative";
      const first=start===r.start;
      const firstLine=lines.findIndex(l=>l.text.trim());
      let explicitQuestion=lines.some(l=>q.test(l.text));
      const reviewed=r.marker_review||{};
      for(let i=0;i<lines.length;i++){
        const l=lines[i];let marker=null,classification=state,reason="section-continuation";
        const reviewedMarker=Object.entries(reviewed).find(([k,m])=>m.source_offset>=l.start&&m.source_offset<l.end);
        if(reviewedMarker){marker=reviewedMarker[0];reason="indexed-damaged-marker";}
        else if(q.test(l.text)){marker="questions";reason="printed-heading-pattern"}
        else if(t.test(l.text)){marker="teachings";reason="printed-heading-pattern"}
        else if(v.test(l.text)){marker="reflection";reason="printed-heading-pattern"}
        else if(latin.test(l.text)){marker="latin";reason="printed-heading-pattern"}
        if(marker){
          state=marker;classification="section-heading";
          if(reviewedMarker?.[1].kind.includes("numbered question"))classification=marker;
        }else if(i===firstLine&&first){classification="chapter-heading";reason="indexed-chapter-start"}
        else if(i===firstLine&&start===p.start&&/Historie|Hiftorie|Hlstorie/i.test(l.text)){classification="running-header-candidate";reason="first-page-line"}
        else if(state==="narrative"&&!explicitQuestion&&questionLike(l.text)&&lines.slice(i+1,i+5).some(x=>questionLike(x.text))){
          state=classification="questions";reason="repeated-numbered-interrogative";
        }else if(!l.text.trim()){classification="unassigned";reason="whitespace"}
        else if(state==="narrative"&&/^[\s*'»"„]+(?:[A-Z][a-z]{1,8}\s*\.)/.test(l.text)){classification="marginal-reference-candidate";reason="footnote-pattern"}
        else if(!first&&lines.length<11&&state==="narrative"){classification="unassigned";reason="sparse-page-possible-illustration"}
        segments.push({page:p.page,start:l.start,end:l.end,section:classification,...(reason!=="section-continuation"?{reason}:{}),...(marker?{marker}:{})});
      }
    }
    const counts={};for(const s of segments)counts[s.section]=(counts[s.section]||0)+1;
    for(const k of ["narrative","questions","teachings","reflection"])if(!counts[k])flags.push("missing-candidate-"+k);
    if(!counts.latin)flags.push("latin-not-detected-compare-Heidelberg");
    result.push({id:r.id,book:r.book,number:r.number,heading:r.heading,start:r.start,end:r.end,pages:[...new Set(segments.map(s=>s.page))],counts,flags,segments});
  }
  return {schema:1,status:"unreviewed-editorial-segmentation-not-publication",source:index.source,source_git_blob:index.source_git_blob,offset_units:"UTF-16",page_alignment:{text_pages:pages.length,nonempty_alto_pages:nonempty.length,method:"order and count; verify individual ALTO line correspondence before editorial acceptance"},records:result};
}

function fixEmbeddedMarkers(raw,draft){
 const patterns={questions:/Deutliche\s+[FK8][rvt][aä][gctz][eä][n»!.]*/gi,teachings:/N[üu]tzliche\s+Lehr[eä][nstr.!»]*/gi,reflection:/Gottselige\s+Geda[nm][ck]{0,2}[eä][n»]?[\s.,!]*/gi};
 for(const rec of draft.records){
  let phase=null,out=[];
  for(const s of rec.segments){
   let [page,start,end,section,reason,marker]=s;
   const matches=[];const line=raw.slice(start,end);
   for(const [k,p] of Object.entries(patterns))for(const m of line.matchAll(p))matches.push({k,a:start+m.index,b:start+m.index+m[0].length});
   matches.sort((a,b)=>a.a-b.a);
   if(matches.length){
    let at=start;
    for(const m of matches){
     if(m.a>at)out.push([page,at,m.a,phase||section,reason,null]);
     out.push([page,m.a,m.b,"section-heading","embedded-or-exact-heading",m.k]);
     at=m.b;phase=m.k==="questions"?null:m.k;
    }
    if(at<end)out.push([page,at,end,phase||matches.at(-1).k,"same-line-section-content",null]);
   } else {
    if(marker==="teachings"||marker==="reflection")phase=marker;
    if(section!=="section-heading"&&section!=="running-header-candidate"&&section!=="unassigned"&&phase)section=phase;
    out.push([page,start,end,section,reason,marker]);
   }
  }
  rec.segments=out;rec.counts={};for(const [page,start,end,section] of out)if(raw.slice(start,end).trim())rec.counts[section]=(rec.counts[section]||0)+1;
  rec.flags=rec.flags.filter(f=>!f.startsWith("missing-candidate"));for(const k of ["narrative","questions","teachings","reflection"])if(!rec.counts[k])rec.flags.push("missing-candidate-"+k);
 }
 return draft;
}

const root=process.cwd();
const read=p=>fs.readFileSync(path.join(root,p),"utf8");
const raw=read("public/data/german-ocr.txt"),idx=JSON.parse(read("public/data/zurich-chapters.json")),manifest=JSON.parse(read("sources/zurich-layout/manifest.json"));
const blob=crypto.createHash("sha1").update("blob "+Buffer.byteLength(raw)+"\0").update(raw).digest("hex");
if(blob!==idx.source_git_blob)throw Error("Source checksum mismatch");
const draft=buildDraft(raw,idx,manifest);
for(const rec of draft.records)rec.segments=rec.segments.map(({page,start,end,section,reason,marker})=>[page,start,end,section,reason||null,marker||null]);
draft.segment_columns=["page","start","end","section","reason","marker"];
fixEmbeddedMarkers(raw,draft);
const dest=path.join(root,"sources/zurich-editorial");fs.mkdirSync(dest,{recursive:true});
for(const rec of draft.records){fs.writeFileSync(path.join(dest,String(rec.id).padStart(3,"0")+".json"),JSON.stringify(rec)+"\n");}
const {records,...meta}=draft;fs.writeFileSync(path.join(dest,"manifest.json"),JSON.stringify({...meta,records:records.map(({segments,...r})=>r)},null,2)+"\n");
fs.writeFileSync(path.join(dest,"index.json"),JSON.stringify(draft)+"\n");
console.log("Draft chapter records:",records.length,"all four candidate sections:",records.filter(r=>!r.flags.some(x=>x.startsWith("missing"))).length);
