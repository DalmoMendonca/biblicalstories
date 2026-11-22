import { stories } from "./catalog.js";

const main = document.querySelector("#main");
const lightbox = document.querySelector("#lightbox");
const lightboxImage = document.querySelector("#lightbox-image");
const lightboxSource = document.querySelector("#lightbox-source");
const languages = ["en","de","ru"];
const text = {
  en:{all:"All 104",old:"Old Testament",new:"New Testament",search:"Search",back:"All stories",folio:"German source pages · 1768",none:"Text not yet imported for this chapter.",edition:"English · modern translation from 1768 German OCR",book:"1765 historical edition",original:"Original scan",about:"Edition"},
  de:{all:"Alle 104",old:"Altes Testament",new:"Neues Testament",search:"Suchen",back:"Alle Historien",folio:"Originalseiten",none:"Text dieser Historie noch nicht importiert.",edition:"Deutsch · Gießen, 1768 · unkorrigierte OCR",book:"Originalausgabe",original:"Originalscan",about:"Edition"},
  ru:{all:"Все 104",old:"Ветхий Завет",new:"Новый Завет",search:"Поиск",back:"Все истории",folio:"Немецкие страницы · 1768",none:"Проверенная транскрипция русского перевода пока недоступна.",edition:"Русский · новый перевод с немецкого OCR 1768 года",book:"Цифровая копия · 1825",original:"Оригинальный скан",about:"Издание"}
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
  filter: "all", search: "", plates: [], byId: new Map(), content: {}
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
  if(!p.folios?.length)return "";
  return `<h2 class="folio-heading">${esc(messages().folio)}</h2><div class="folios">
    ${p.folios.map((leaf,i)=>`<button type="button" class="folio-btn" data-folio="${p.id}:${i}" aria-label="Page ${esc(leaf.label)}"><img src="${esc(leaf.image)}" alt="Printed German page ${esc(leaf.label)}" loading="lazy" width="500"><small>${esc(leaf.label)}</small></button>`).join("")}
  </div>`;
}
function textParagraphs(value){
  const blocks=String(value||"").trim().split(/\n\s*\n/).filter(Boolean);
  return blocks.map(p=>"<p>"+esc(p.replace(/\n/g," ").replace(/ {2,}/g," "))+"</p>").join("");
}
function chapterContent(p){
  const data=s.content[p.id];
  const lang=s.lang;
  const m=messages();
  if(data && data[lang] && data[lang].text && data[lang].text.length>150){
    const witness=lang==="de" ? "Giessen, 1768 · Fraktur OCR, uncorrected"
      : lang==="en" ? "Modern English translation of uncorrected German OCR · 1768"
      : "Современный перевод с непроверенного немецкого OCR · 1768";
    return '<div class="source-heading">'+esc(witness)+'</div>'
      +'<div class="edition-prose" lang="'+lang+'">'+textParagraphs(data[lang].text)+'</div>';
  }
  return '<p class="source-absence">'+esc(m.none)+'</p>';
}
function editionText(p){
  const m=messages();
  const archivalLink=s.lang==="en"?sourceEnglish:(s.lang==="ru"?sourceRussian1825[p.book==="old"?0:1]:sourceGerman);
  return '<div id="story-prose" aria-live="polite">'+chapterContent(p)+'</div>'
    +'<details class="source-facsimile"><summary>'+esc(m.folio)+'</summary>'
    +'<p class="source-heading">Giessen 1768 · <a href="'+esc(p.plate_source)+'" target="_blank" rel="noopener">'+esc(m.original)+'</a></p>'
    +folios(p)+'</details>'
    +(s.lang==="de"?'':'<p class="source-heading"><a href="'+esc(archivalLink)+'" target="_blank" rel="noopener">'+esc(m.book)+' ↗</a></p>');
}
async function loadChapter(id){
  const p=item(id);
  if(!p || s.content[id])return;
  try{
    const response=await fetch("/texts/"+number(id)+".json");
    if(!response.ok)throw new Error("Text not yet available");
    const data=await response.json();
    if(data.id!==id)throw new Error("Mismatched source chapter");
    s.content[id]=data;
    if(view()==="story" && idParam()===id){
      const pane=document.querySelector("#story-prose");
      if(pane)pane.innerHTML=chapterContent(p);
    }
  }catch(e){
    // Source image facsimiles remain fully readable, even when a text import fails.
    console.warn("Source text unavailable for chapter",id);
  }
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
  loadChapter(id);
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
  <p class="short">The illustrations displayed here come from the Giessen edition of 1768, not the unverified Russian image set of 1815. Chapter titles in the English and Russian indexes are modern navigation labels, not purported transcriptions. English and Russian chapter texts, when available, are modern translations of uncorrected German source OCR and are not identical to the eighteenth- or nineteenth-century historical translations.</p>
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