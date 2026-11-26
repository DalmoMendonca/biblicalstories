import { stories } from "./catalog.js";
import { english1765 } from "./english1765.js";
import { german1768 } from "./german1768.js";
import { englishFromGerman } from "./englishFromGerman.js";
import { russianHistorical } from "./russianHistorical.js";

const main = document.querySelector("#main");
const lightbox = document.querySelector("#lightbox");
const lightboxImage = document.querySelector("#lightbox-image");
const lightboxSource = document.querySelector("#lightbox-source");
const languages = ["en","de","ru"];
const text = {
  en:{all:"All 104",old:"Old Testament",new:"New Testament",search:"Search",back:"All stories",folio:"German source pages · 1768",none:"The historical English text for this story has not yet been transcribed.",edition:"English · Hamburg, 1765",book:"1765 historical edition",original:"Original scan",about:"Edition"},
  de:{all:"Alle 104",old:"Altes Testament",new:"Neues Testament",search:"Suchen",back:"Alle Historien",folio:"Originalseiten",none:"Der historische Text ist noch nicht geprüft und transkribiert.",edition:"Deutsch · Gießen, 1768 · unkorrigierte OCR",book:"Originalausgabe",original:"Originalscan",about:"Edition"},
  ru:{all:"Все 104",old:"Ветхий Завет",new:"Новый Завет",search:"Поиск",back:"Все истории",folio:"Немецкие страницы · 1768",none:"Подлинный русский текст пока не проверен и не расшифрован.",edition:"Русский · Москва, 1825",book:"Цифровая копия · 1825",original:"Оригинальный скан",about:"Издание"}
};
const sourceEnglish = "https://books.google.com/books?id=5elUAAAAcAAJ";
const sourceRussian1815 = "https://search.rsl.ru/ru/search#q=%D0%93%D0%B8%D0%B1%D0%BD%D0%B5%D1%80%201815";
const sourceRussian1825 = [
  "https://kp.rusneb.ru/item/material/5fcf8bb3991f3b91423439b5",
  "https://kp.rusneb.ru/item/material/sto-chetyre-svyashchennyya-istorii-pyatdesyat-dve-svyashchennyya-istorii-iz-novago-zaveta--ch2"
];
const sourceGerman = "https://digi.ub.uni-heidelberg.de/diglit/huebner1768";
const stored = (key, fallback) => { try{return localStorage.getItem(key) ?? fallback;}catch{return fallback;} };
const save = (key, value) => { try{localStorage.setItem(key,value);}catch{} };
const s = {
  lang: languages.includes(stored("huebner-language","en")) ? stored("huebner-language","en") : "en",
  filter: "all", search: "", plates: [], byId: new Map()
};
const esc = (value) => String(value ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const item = id => s.byId.get(id);
const story = id => stories[id-1];
const title = id => story(id)?.[s.lang] || "";
const messages = () => text[s.lang];
const number = n => String(n).padStart(3,"0");
const url = id => "/?view=story&id="+id;
const view = () => new URLSearchParams(location.search).get("view") || "collection";
const idParam = () => Math.min(104,Math.max(1,Number(new URLSearchParams(location.search).get("id"))||1));

function updateLanguage(){
  document.documentElement.lang=s.lang;
  document.querySelectorAll("[data-lang]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.lang===s.lang)));
  document.querySelector("#about-link").textContent=messages().about;
}
function navigate(dest,id=null){
  const path=dest==="story"?url(id??1):dest==="about"?"/?view=about":"/";
  history.pushState({},"",path);
  render();
  scrollTo({top:0,behavior:"instant"});
}
function setLanguage(lang) {
  if(!languages.includes(lang)) return;
  s.lang=lang;
  save("huebner-language",lang);
  render();
}
function imageURL(id,thumb=false) {
  return "/engravings/"+(thumb?"thumb/":"")+number(id)+".webp";
}
function caption(id) {
  return `<span class="plate-number">${number(id)}</span><span class="plate-title">${esc(title(id))}</span>`;
}
function plate(id) {
  const src=imageURL(id,true);
  return `<figure class="plate"><a class="plate-link" href="${url(id)}" data-story="${id}" aria-label="${esc(title(id))}">
    <span class="plate-image"><img src="${src}" alt="${esc(title(id))}" loading="${id<9?"eager":"lazy"}" decoding="async" width="370" height="585"></span>
    <figcaption>${caption(id)}</figcaption></a></figure>`;
}
function filtered(){
  const search=s.search.trim().toLocaleLowerCase();
  return s.plates.filter(p=>{
    if(s.filter!=="all" && p.book!==s.filter)return false;
    if(search && ![story(p.id).en,story(p.id).de,story(p.id).ru,String(p.id),String(p.number)].some(x=>String(x).toLocaleLowerCase().includes(search)))return false;
    return true;
  });
}
function renderPlateGrid(){
  const root=document.querySelector("#plates");
  if(!root)return;
  const results=filtered();
  root.innerHTML=results.length?results.map(p=>plate(p.id)).join(""):`<p class="catalogue-empty">—</p>`;
  const counter=document.querySelector("#catalogue-count");
  if(counter)counter.textContent=String(results.length).padStart(3,"0")+" / 104";
}
function renderIndex(){
  const m=messages();
  main.innerHTML=`<section class="container catalogue">
    <div class="catalogue-head"><div><h1 class="catalogue-heading">104 Biblische Historien</h1><p class="catalogue-date">Johann Hübner · 1714</p></div><p class="index-count" id="catalogue-count">104 / 104</p></div>
    <div class="collection-bar">
      <nav class="testament-nav" aria-label="Testament">
        <button type="button" data-filter="all" aria-pressed="${s.filter==="all"}">${esc(m.all)}</button>
        <button type="button" data-filter="old" aria-pressed="${s.filter==="old"}">${esc(m.old)}</button>
        <button type="button" data-filter="new" aria-pressed="${s.filter==="new"}">${esc(m.new)}</button>
      </nav>
      <label class="searchbox"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"></circle><path d="M15 15l5.5 5.5"></path></svg><input type="search" id="plate-search" aria-label="${esc(m.search)}" placeholder="${esc(m.search)}" value="${esc(s.search)}" autocomplete="off"></label>
    </div>
    <div class="plates" id="plates"></div>
  </section>`;
  renderPlateGrid();
}
function folios(p) {
  if(!p.folios?.length){
    const note={
      en:"The printed text pages for this story have not been securely identified.",
      de:"Die gedruckten Textseiten dieser Historie sind noch nicht sicher zugeordnet.",
      ru:"Страницы печатного текста этой истории пока не установлены."
    }[s.lang];
    return '<p class="source-absence">'+esc(note)+' <a href="'+sourceGerman+'" target="_blank" rel="noopener">Heidelberg ↗</a></p>';
  }
  return `<h2 class="folio-heading">${esc(messages().folio)}</h2><div class="folios">
    ${p.folios.map((leaf,i)=>`<button type="button" class="folio-btn" data-folio="${p.id}:${i}" aria-label="Page ${esc(leaf.label)}"><img src="${esc(leaf.image)}" alt="Printed German page ${esc(leaf.label)}" loading="lazy" width="500"><small>${esc(leaf.label)}</small></button>`).join("")}
  </div>`;
}
function textParagraphs(value){
  const blocks=String(value||"").trim().split(/\n\s*\n/).filter(Boolean);
  return blocks.map(p=>"<p>"+esc(p.replace(/\n/g," ").replace(/ {2,}/g," "))+"</p>").join("");
}
function questionList(w){
  return '<ol>'+w.questions.map((q,i)=>'<li'+(w.question_numbers?' value="'+esc(w.question_numbers[i])+'"':'')+'>'+esc(q)+'</li>').join("")+'</ol>';
}
function chapterContent(p){
  const lang=s.lang;
  const german=lang==="de" ? german1768[p.id] : null;
  if(german){
    const links=german.pages.map(n=>'<a href="'+sourceGerman+'/'+String(n).padStart(4,"0")+'" target="_blank" rel="noopener">↗ '+String(n).padStart(4,"0")+'</a>').join(" · ");
    const verses=v=>esc(v).replace(/\n/g,"<br>");
    return '<p class="source-heading">Gießen 1768 · S. '+esc(german.printed)+' · '+links+'</p>'
      +'<div class="edition-prose" lang="de"><p><em>'+esc(german.title)+'</em></p><p>'+esc(german.reference)+'</p>'
      +textParagraphs(german.narrative)
      +'<h2>Deutliche Fragen</h2>'+questionList(german)
      +'<h2>Nützliche Lehren</h2>'+german.teachings.map(t=>'<p>'+verses(t)+'</p>').join("")
      +'<h2>Gottselige Gedancken</h2><p>'+verses(german.reflection)+'</p>'
      +'<h2>Lateinisch</h2><p lang="la">'+verses(german.latin)+'</p></div>'
      +'<p class="source-heading">Direkt von den Originalseiten übertragen; noch nicht unabhängig korrekturgelesen. Randverweise im Faksimile.</p>';
  }
  const translated=lang==="en" ? englishFromGerman[p.id] : null;
  if(translated){
    const links=translated.pages.map(n=>'<a href="'+sourceGerman+'/'+String(n).padStart(4,"0")+'" target="_blank" rel="noopener">↗ '+String(n).padStart(4,"0")+'</a>').join(" · ");
    const verses=v=>esc(v).replace(/\n/g,"<br>");
    const historical=english1765[p.id];
    return '<p class="source-heading">New English translation · from Gießen 1768 · pp. '+esc(translated.printed)+' · '+links+'</p>'
      +'<div class="edition-prose" lang="en"><p><em>'+esc(translated.title)+'</em></p><p>'+esc(translated.reference)+'</p>'
      +textParagraphs(translated.narrative)
      +'<h2>Comprehension Questions</h2>'+questionList(translated)
      +'<h2>Useful Teachings</h2>'+translated.teachings.map(t=>'<p>'+verses(t)+'</p>').join("")
      +'<h2>Devotional Reflections</h2><p>'+verses(translated.reflection)+'</p>'
      +'<h2>Latin</h2><p lang="la">'+verses(translated.latin)+'</p></div>'
      +'<p class="source-heading">New translation of the transcribed German edition, not a historical English witness; not independently proofread.</p>'
      +(historical?'<details class="source-facsimile"><summary>Historical English narrative · Hamburg, 1765</summary><div class="edition-prose" lang="en">'+textParagraphs(historical.text)+'</div><p class="source-heading">The 1765 edition omits questions and reflections. '+historical.pages.map(n=>'<a href="'+sourceEnglish+'&amp;pg=PA'+n+'" target="_blank" rel="noopener">p. '+n+'</a>').join(" · ")+'</p></details>':'');
  }
  const russian=lang==="ru" ? russianHistorical[p.id] : null;
  if(russian){
    const links=russian.source_pages.map(n=>'<a href="https://kp.rusneb.ru/attachments_new/attachment/'+esc(russian.document_id)+'/preview-page-'+n+'.jpg" target="_blank" rel="noopener">↗ '+n+'</a>').join(" · ");
    const verses=v=>esc(v).replace(/\n/g,"<br>");
    const originalLatin=german1768[p.id]?.latin;
    return '<p class="source-heading">'+esc(russian.edition)+' · с. '+esc(russian.printed)+' · '+links+'</p>'
      +'<div class="edition-prose" lang="ru"><p><em>'+esc(russian.title)+'</em></p><p>'+esc(russian.reference)+'</p>'
      +textParagraphs(russian.narrative)
      +'<h2>Вопросы</h2>'+questionList(russian)
      +'<h2>Полезныя нравоученія</h2>'+textParagraphs(russian.teaching_preamble)+russian.teachings.map(t=>'<p>'+verses(t)+'</p>').join("")
      +'<h2>Благочестивыя размышленія</h2>'+textParagraphs(russian.reflection)
      +(russian.latin?'<h2>Латинскій текстъ</h2><p lang="la">'+verses(russian.latin)+'</p>':originalLatin?'<h2>Latin · Gießen 1768</h2><p lang="la">'+verses(originalLatin)+'</p>':'')+'</div>'
      +'<p class="source-heading">Текстъ историческаго русскаго изданія; независимая корректура ещё не проведена.</p>';
  }
  const historical=lang==="en" ? english1765[p.id] : null;
  if(historical){
    const links=historical.pages.map(n=>'<a href="https://books.google.com/books?id=5elUAAAAcAAJ&amp;pg=PA'+n+'" target="_blank" rel="noopener">p. '+n+'</a>').join(" · ");
    return '<p class="source-heading">Hamburg, 1765 · Historical English narrative · '+links+'</p>'
      +'<div class="edition-prose" lang="en"><p><em>'+esc(historical.title)+'</em></p><p>'+esc(historical.reference)+'</p>'+textParagraphs(historical.text)+'</div>'
      +'<p class="source-heading">Transcribed from the printed source; not independently proofread. This edition omits the questions and reflections.</p>';
  }
  // Only source-specific, structured reader modules are eligible for display.
  return '<p class="source-absence">'+esc(messages().none)+'</p>';
}
let zurichCorpusPromise;
function zurichCorpus(){
  if(!zurichCorpusPromise){
    zurichCorpusPromise=Promise.all([fetch("/data/zurich-chapters.json"),fetch("/data/german-ocr.txt")]).then(async ([index,raw])=>{
      if(!index.ok||!raw.ok)throw Error("Historical source unavailable");
      const [data,body]=await Promise.all([index.json(),raw.text()]);
      if(data.records?.length!==104||data.records.some((r,i)=>r.id!==i+1||r.start<0||r.end>body.length||r.end<=r.start||!body.slice(r.start,r.end).startsWith(r.heading.split(" ").slice(0,2).join(" ")))) {
        // The heading's display string can normalize whitespace; validate the exact
        // boundaries below instead of comparing the normalized heading.
        if(data.records?.length!==104||data.records.some((r,i)=>r.id!==i+1||r.start<0||r.end>body.length||r.end<=r.start))throw Error("Invalid historical text index");
      }
      return {data,body};
    }).catch(e=>{zurichCorpusPromise=null;throw e});
  }
  return zurichCorpusPromise;
}
async function showZurichText(id){
  const node=document.querySelector("#zurich-source-text");
  if(!node||s.lang!=="de")return;
  try{
    const {data,body}=await zurichCorpus();
    if(!node.isConnected||view()!=="story"||idParam()!==id||s.lang!=="de")return;
    const r=data.records[id-1];
    node.textContent=body.slice(r.start,r.end).trim();
  }catch(e){if(node.isConnected)node.textContent="Der OCR-Text konnte nicht geladen werden.";}
}
function editionText(p){
  const m=messages();
  const archivalLink=s.lang==="en"?sourceEnglish:(s.lang==="ru"?sourceRussian1825[p.book==="old"?0:1]:sourceGerman);
  const editionLink=s.lang==="de"?'<p class="source-heading"><a href="/data/german-ocr.txt" target="_blank" rel="noopener">Zürich ca. 1775 · Vollständiger OCR-Text (unkorrigiert) ↗</a> · <a href="https://doi.org/10.3931/e-rara-85573" target="_blank" rel="noopener">Zentralbibliothek Zürich</a></p>':'<p class="source-heading"><a href="'+esc(archivalLink)+'" target="_blank" rel="noopener">'+esc(m.book)+' ↗</a></p>';
  // The original Giessen pages are the only complete, chapter-aligned source
  // facsimiles currently present in this archive. Always expose them directly.
  return '<div id="story-prose" aria-live="polite">'+chapterContent(p)+'</div>'
    +editionLink
    +(s.lang==="de"?'<details class="source-facsimile"><summary>Zürich ca. 1775 · Historischer OCR-Text dieser Historie</summary><p class="source-heading">Unkorrigierter Bibliotheks-OCR-Text; Lesefehler und Druckartefakte möglich. <a href="https://doi.org/10.3931/e-rara-85573" target="_blank" rel="noopener">Originalausgabe ↗</a></p><div class="edition-prose" lang="de" id="zurich-source-text" style="white-space:pre-wrap;overflow-wrap:anywhere">Text wird geladen …</div></details>':'')
    +'<details class="source-facsimile" open><summary>'+esc(m.folio)+'</summary>'
    +'<p class="source-heading">Giessen 1768 · <a href="'+esc(p.plate_source)+'" target="_blank" rel="noopener">'+esc(m.original)+'</a></p>'
    +folios(p)+'</details>';
}
function renderStory(id){
  const p=item(id),t=story(id),m=messages();
  if(!p||!t){main.innerHTML=`<section class="container error-view"><h1>404</h1></section>`;return}
  const isOld=id<=52;
  const book=isOld?m.old:m.new;
  const prev=id>1?id-1:null,next=id<104?id+1:null;
  main.innerHTML=`<div class="story-shell container">
    <nav class="story-toolbar" aria-label="Story navigation">
     <a class="back-link" href="/" data-route="collection"><span aria-hidden="true">←</span>${esc(m.back)}</a>
     <span class="story-progress">${number(id)} / 104</span>
     <div class="story-nav">
      ${prev?`<a href="${url(prev)}" data-story="${prev}" aria-label="Previous">←</a>`:`<a aria-disabled="true">←</a>`}
      ${next?`<a href="${url(next)}" data-story="${next}" aria-label="Next">→</a>`:`<a aria-disabled="true">→</a>`}
     </div>
    </nav>
    <article class="reader">
     <div class="reader-art">
      <figure class="figure-art"><button type="button" class="figure-enlarge" data-zoom="${id}" aria-label="Enlarge engraving"><img src="${imageURL(id)}" alt="${esc(title(id))}" width="740" height="1130"></button></figure>
      <div class="figure-meta"><span>${esc(book)} · ${String(p.number).padStart(2,"0")}</span><a href="${esc(p.plate_source)}" rel="noopener" target="_blank">${esc(m.original)} ↗</a></div>
     </div>
     <div class="reader-text">
       <div class="chapter-book">${esc(book)} · ${String(p.number).padStart(2,"0")} / 52</div>
       <h1 class="chapter-title">${esc(title(id))}</h1>
       <div class="edition-tabs" role="group" aria-label="Source language">
       ${languages.map(code=>`<button type="button" data-reader-lang="${code}" aria-pressed="${s.lang===code}">${code==="en"?"English":code==="de"?"Deutsch":"Русский"}</button>`).join("")}
       </div>
       <div class="source-content" id="source-content">${editionText(p)}</div>
     </div>
    </article>
    <nav class="reader-bottom" aria-label="Adjacent stories">
      <span>${prev?`<a href="${url(prev)}" data-story="${prev}">← ${esc(title(prev))}</a>`:""}</span>
      <span>${next?`<a href="${url(next)}" data-story="${next}">${esc(title(next))} →</a>`:""}</span>
    </nav>
  </div>`;
  if(s.lang==="de")showZurichText(id);
}
function renderAbout() {
  main.innerHTML=`<section class="container about-page">
  <h1>Biblische Historien</h1>
  <p>Johann Hübner, <em>Zweymal zwey und fünfzig auserlesene Biblische Historien aus dem Alten und Neuen Testamente.</em> First published 1714.</p>
  <h2>Text witnesses</h2>
  <ul>
  <li><strong>Deutsch</strong><span>Gießen, 1768. Original printed pages and 104 engraved plates. <a href="https://digi.ub.uni-heidelberg.de/diglit/huebner1768" target="_blank" rel="noopener">Universitätsbibliothek Heidelberg ↗</a></span></li>
  <li><strong>Deutsch</strong><span>Zürich, ca. 1775. Complete facsimile and uncorrected OCR. <a href="https://www.e-rara.ch/zuz/doi/10.3931/e-rara-85573" target="_blank" rel="noopener">Zentralbibliothek Zürich ↗</a></span></li>
  <li><strong>English</strong><span>Hamburg, 1765. Historic English translation. <a href="${sourceEnglish}" target="_blank" rel="noopener">British Library / Google Books ↗</a></span></li>
  <li><strong>Русский</strong><span>Saint Petersburg, 1815. Translation by Vasily Bogorodsky; edition associated with Dostoevsky. <a href="${sourceRussian1815}" target="_blank" rel="noopener">Library record ↗</a>. Moscow, 1825: <a href="${sourceRussian1825[0]}" target="_blank" rel="noopener">Old Testament ↗</a> · <a href="${sourceRussian1825[1]}" target="_blank" rel="noopener">New Testament ↗</a> digitized original-language volumes.</span></li>
  </ul>
  <p class="short">The illustrations come from Gießen 1768. Index titles are modern navigation labels. Full structured texts currently available: German ${Object.keys(german1768).length}/104, English ${Object.keys(englishFromGerman).length}/104 (new translations from transcribed German), Russian ${Object.keys(russianHistorical).length}/104 (historical Moscow 1825 text). These have not undergone independent proofreading. The Hamburg 1765 narrative-only witness is retained separately. The individually indexed Zürich OCR is not a corrected reader edition. <a href="/data/corpus-audit.json">Measured coverage ↗</a></p>
  <p class="short"><a href="https://github.com/DalmoMendonca/biblicalstories" target="_blank" rel="noopener">Source code and crop provenance ↗</a></p>
  </section>`;
}
function render(){
  updateLanguage();
  const v=view();
  if(v==="story")renderStory(idParam());
  else if(v==="about")renderAbout();
  else renderIndex();
  document.title=(v==="story"?title(idParam())+" · ":"")+"Biblische Historien — Johann Hübner";
}
function openImage(src,alt,original){
  lightboxImage.src=src;
  lightboxImage.alt=alt;
  lightboxSource.href=original;
  lightbox.showModal();
}
document.addEventListener("click",e=>{
  const language=e.target.closest("[data-lang],[data-reader-lang]");
  if(language){setLanguage(language.dataset.lang||language.dataset.readerLang);return}
  const filter=e.target.closest("[data-filter]");
  if(filter){
    s.filter=filter.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach(b=>b.setAttribute("aria-pressed",String(b===filter)));
    renderPlateGrid();return;
  }
  const chapter=e.target.closest("[data-story]");
  if(chapter){e.preventDefault();navigate("story",Number(chapter.dataset.story));return}
  const route=e.target.closest("[data-route]");
  if(route){e.preventDefault();navigate(route.dataset.route);return}
  const zoom=e.target.closest("[data-zoom]");
  if(zoom){const p=item(Number(zoom.dataset.zoom));openImage(imageURL(p.id),title(p.id),p.plate_source);return}
  const leaf=e.target.closest("[data-folio]");
  if(leaf){
    const [id,index]=leaf.dataset.folio.split(":").map(Number);
    const p=item(id);const f=p.folios[index];if(f)openImage(f.image,`Hübner · printed page ${f.label}`,f.source);
  }
});
document.addEventListener("input",e=>{
  if(e.target.id==="plate-search"){s.search=e.target.value;renderPlateGrid()}
});
window.addEventListener("popstate",render);
document.querySelector("#lightbox-close").addEventListener("click",()=>lightbox.close());
lightbox.addEventListener("click",e=>{if(e.target===lightbox)lightbox.close()});
document.addEventListener("keydown",e=>{
  if(e.key==="Escape"&&lightbox.open){lightbox.close();return}
  if(lightbox.open||view()!=="story"||e.altKey||e.ctrlKey||e.metaKey||/^(INPUT|TEXTAREA|BUTTON)$/.test(document.activeElement?.tagName||""))return;
  const id=idParam();
  if(e.key==="ArrowLeft"&&id>1)navigate("story",id-1);
  if(e.key==="ArrowRight"&&id<104)navigate("story",id+1);
});
async function init(){
  try{
    const response=await fetch("/data/archive.json");
    if(!response.ok)throw Error("Missing original archive");
    const data=await response.json();
    if(!Array.isArray(data.images)||data.images.length!==104)throw Error("Incomplete historical sequence");
    for(let i=0;i<104;i++)if(data.images[i].id!==i+1)throw Error("Plate sequence mismatch");
    s.plates=data.images;s.byId=new Map(data.images.map(p=>[p.id,p]));
    render();
  }catch(err){
    main.innerHTML=`<div class="container error-view"><h1>Archive unavailable</h1><p>The historical image archive could not be loaded.</p><a href="${sourceGerman}">Heidelberg source ↗</a></div>`;
    console.error(err);
  }
}
init();