import { stories, dictionary } from "./catalog.js";

const main = document.querySelector("#main");
const header = document.querySelector("#site-header");
const dialog = document.querySelector("#art-dialog");
const dialogImage = document.querySelector("#dialog-image");
const dialogTitle = document.querySelector("#dialog-title");
const dialogCredit = document.querySelector("#dialog-credit");
const prefersReducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

const safelyStored = (key, fallback) => {
  try { return localStorage.getItem(key) ?? fallback; }
  catch { return fallback; }
};
const safelySave = (key, value) => {
  try { localStorage.setItem(key, value); } catch { /* private browsing */ }
};
const state = {
  lang: ["en", "de", "ru"].includes(safelyStored("huebner-language", "en"))
    ? safelyStored("huebner-language", "en") : "en",
  saved: new Set(JSON.parse(safelyStored("huebner-saved", "[]"))),
  testament: "all",
  search: "",
  images: [],
  byId: new Map(),
  germanOcr: null,
};
const q = (key) => new URLSearchParams(location.search).get(key);
const ui = () => dictionary[state.lang];
const roman = (number) => {
  const digits = [[50,"L"],[40,"XL"],[10,"X"],[9,"IX"],[5,"V"],[4,"IV"],[1,"I"]];
  let out = "";
  for (const [value, symbol] of digits) while (number >= value) { out += symbol; number -= value; }
  return out;
};
const title = (s) => s[state.lang];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, ch => ({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" })[ch]);
const storyURL = (id) => "/?view=story&id=" + id;
const collectionURL = "/?view=collection";
const anchor = (s) => s?.plate_source || "https://digi.ub.uni-heidelberg.de/diglit/huebner1768";
const record = (id) => state.byId.get(id);
const art = (s, useThumb = false) => useThumb ? s?.thumb : s?.image;
const textOf = (t) => esc(t);
function setLanguage(lang) {
  if (!dictionary[lang]) return;
  state.lang = lang;
  safelySave("huebner-language", lang);
  document.documentElement.lang = lang;
  render();
}
function setNavigation(view, id = undefined, replace = false) {
  let url = "/";
  if (view === "story") url = storyURL(id ?? 1);
  else if (view === "collection") url = collectionURL;
  else if (view === "about") url = "/?view=about";
  history[replace ? "replaceState" : "pushState"]({}, "", url);
  render();
  window.scrollTo({ top: 0, behavior: "instant" });
  header.classList.remove("menu-open");
  document.querySelector("#menu-toggle").setAttribute("aria-expanded", "false");
}
function syncHeader(view) {
  document.documentElement.lang = state.lang;
  document.querySelector("#nav-library").textContent = ui().library;
  document.querySelector("#nav-read").textContent = ui().read;
  document.querySelector("#nav-about").textContent = ui().about;
  for (const el of document.querySelectorAll("[data-nav]")) {
    const active = el.dataset.nav === view;
    el.classList.toggle("active", active);
    if (active) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  }
  for (const button of document.querySelectorAll("[data-lang]")) {
    const active = button.dataset.lang === state.lang;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  }
}
function imageTag(s, thumb = false, lazy = true, extra = "") {
  return `<img src="${esc(art(s,thumb))}" data-fallback="${esc(s.original_image)}" alt="${esc(title(stories[s.id-1]))} — original engraving, Giessen 1768" loading="${lazy?"lazy":"eager"}" decoding="async" ${extra}>`;
}
function card(s, bookmark = true) {
  const st = stories[s.id-1];
  const bookmarked = state.saved.has(s.id);
  const label = (st.testament === "old" ? ui().old : ui().new) + " · " + String(st.number).padStart(2,"0");
  return `<article class="art-card" data-story-id="${s.id}">
    <div class="art-frame">${imageTag(s,true)}</div>
    <div class="art-meta">
      <div class="art-number">${esc(label)}</div>
      <h3>${textOf(title(st))}</h3>
      <p>Johann Hübner · 1768</p>
    </div>
    <a class="card-hit" href="${storyURL(s.id)}" data-open-story="${s.id}" aria-label="${esc(title(st))}"></a>
    ${bookmark ? `<button class="bookmark ${bookmarked?"is-saved":""}" type="button" data-save="${s.id}" aria-label="${bookmarked?"Remove saved story":"Save story"}" aria-pressed="${bookmarked}">${bookmarked?"◆":"◇"}</button>` : ""}
  </article>`;
}
function renderHome() {
  const t = ui();
  const hero = record(1);
  const picks = [43, 6, 32, 84, 100].map(record);
  return `<section class="hero">
    <div class="hero-copy">
      <div>
        <div class="hero-epigraph">Johann Hübner · 1714 / 1768</div>
        <h1 class="hero-title">${state.lang==="en"?"One hundred and four <em>sacred histories.</em>":state.lang==="de"?"Hundertvier <em>biblische Historien.</em>":"Сто четыре <em>священные истории.</em>"}</h1>
        <p class="hero-description">${esc(t.strap)} ${state.lang==="en"?"The complete 104-engraving series, preserved as it appeared in an eighteenth-century printing.":state.lang==="de"?"Alle 104 Originalkupferstiche aus einer historischen Ausgabe.":"Все 104 подлинные гравюры исторического издания."}</p>
        <div class="hero-actions">
          <a href="${collectionURL}" class="action-primary" data-nav="collection">${esc(t.explore)} <span aria-hidden="true">↗</span></a>
          <a href="${storyURL(1)}" class="action-secondary" data-open-story="1">${esc(t.begin)}</a>
        </div>
      </div>
      <div class="hero-colophon"><span>52 ${esc(t.old)}</span><span>52 ${esc(t.new)}</span><span>104 original copperplates</span></div>
    </div>
    <div class="hero-art">
      <div class="plate-frame">${imageTag(hero,false,false)}</div>
      <div class="hero-art-caption"><span>${esc(t.old)} / I</span><span>Giessen, 1768</span></div>
    </div>
  </section>
  <section class="section-wrap" aria-labelledby="highlights-title">
    <div class="section-header">
      <div><div class="small-label">${esc(t.origin)}</div><h2 id="highlights-title">${state.lang==="en"?"An entire <em>world in engravings.</em>":state.lang==="de"?"Eine Welt <em>in Kupferstichen.</em>":"Целый мир <em>в гравюрах.</em>"}</h2><p>${state.lang==="en"?"Every image here belongs to the historical Hübner edition—not an AI re-creation, not a modern substitute.":state.lang==="de"?"Jedes Bild stammt aus der historischen Hübner-Ausgabe – keine KI-Rekonstruktion.":"Все изображения взяты из исторического издания Гюбнера, а не созданы искусственным интеллектом."}</p></div>
      <a href="${collectionURL}" class="text-link" data-nav="collection">${esc(t.browse)} ↗</a>
    </div>
    <div class="featured-grid">${picks.map(s=>card(s,false)).join("")}</div>
  </section>
  <section class="museum-strip" aria-label="Edition summary">
    <div><strong>104</strong><p>${state.lang==="en"?"Every plate individually numbered and checked against Heidelberg's archival manifest.":state.lang==="de"?"Jede Tafel nummeriert und gegen das Heidelberger Archiv geprüft.":"Каждая гравюра сверена с каталогом Гейдельбергского университета."}</p></div>
    <div><strong>1768</strong><p>${state.lang==="en"?"A complete German illustrated printing: Giessen, Johann Christoph Schröder.":state.lang==="de"?"Vollständige illustrierte deutsche Ausgabe aus Gießen.":"Полное иллюстрированное немецкое издание из Гиссена."}</p></div>
    <div><strong>3</strong><p>${state.lang==="en"?"Language-aware navigation with historical texts kept separate from editorial translations.":state.lang==="de"?"Dreisprachige Navigation mit streng getrennten Quellentexten.":"Навигация на трёх языках с чётким разделением оригиналов и переводов."}</p></div>
  </section>`;
}
function galleryItems() {
  let list = state.images;
  if (state.testament !== "all") list = list.filter(s => s.book === state.testament);
  const term = state.search.trim().toLocaleLowerCase();
  if (term) list = list.filter(s => {
    const catalog = stories[s.id-1];
    return [catalog.en,catalog.de,catalog.ru,String(s.id),String(catalog.number)].some(v => v.toLocaleLowerCase().includes(term));
  });
  return list;
}
function renderGrid() {
  const root = document.querySelector("#collection-results");
  if (!root) return;
  const list = galleryItems();
  const count = document.querySelector("#collection-count");
  if (count) count.textContent = list.length + " / 104 " + ui().stories;
  if (!list.length) {
    root.innerHTML = `<div class="empty-search"><h2>${state.lang==="en"?"No stories found":state.lang==="de"?"Keine Historien gefunden":"Истории не найдены"}</h2><p>${state.lang==="en"?"Try a different name or clear the testament filter.":state.lang==="de"?"Versuchen Sie einen anderen Begriff.":"Попробуйте другой запрос."}</p></div>`;
    return;
  }
  root.innerHTML = `<div class="collection-grid">${list.map(x=>card(x)).join("")}</div>`;
}
function renderCollection() {
  const t = ui();
  return `<section class="collection-hero">
    <span class="small-label">Johann Hübner · Giessen 1768</span>
    <h1>${esc(t.intro)}.</h1>
    <p>${state.lang==="en"?"A complete visual atlas of the Old and New Testaments. Explore 104 surviving engravings in their original narrative sequence.":state.lang==="de"?"Die vollständige Bilderwelt des Alten und Neuen Testaments. 104 Originalkupferstiche in ihrer Reihenfolge.":"Полная иллюстрированная коллекция Ветхого и Нового Заветов: 104 гравюры в исходном порядке."}</p>
  </section>
  <div class="collection-tools">
    <div class="filters" role="group" aria-label="Filter by testament">
      ${[["all",t.all],["old",t.old],["new",t.new]].map(([key,label])=>`<button class="filter ${state.testament===key?"active":""}" data-filter="${key}" type="button" aria-pressed="${state.testament===key}">${esc(label)}</button>`).join("")}
    </div>
    <label class="search-box"><input id="gallery-search" type="search" placeholder="${esc(t.search)}" value="${esc(state.search)}" autocomplete="off" aria-label="${esc(t.search)}"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke-width="1.8" aria-hidden="true"><circle cx="10.6" cy="10.6" r="6.4"/><path d="m15.5 15.5 5.4 5.4"/></svg></label>
    <div class="collection-count" id="collection-count" aria-live="polite"></div>
  </div>
  <section class="collection-section" id="collection-results" aria-label="Illustrated story gallery"></section>`;
}
function renderDocument(s) {
  const t=ui();
  const german = state.lang==="de";
  let body = "";
  if (german) {
    body = `<h2>Deutscher Originaltext · 1768</h2>
      <p>Die gedruckten Originalseiten dieser Historie sind unten als Faksimiles zugänglich. Die Texte werden nicht durch ungeprüfte, automatisch erzeugte Transkriptionen ersetzt.</p>
      <div class="document-alert"><p>Die OCR der Zürcher Ausgabe (um 1775) ist als vollständiges, <strong>unkorrigiertes</strong> Dokument verfügbar. Sie stammt nicht aus der hier abgebildeten Gießener Ausgabe von 1768.</p></div>
      <a class="document-link" href="/data/german-ocr.txt" target="_blank" rel="noopener">Zürcher OCR im Original ansehen ↗</a>`;
  } else if (state.lang==="en") {
    body = `<h2>English historical text</h2>
      <div class="document-alert"><p><strong>Not yet verified against the printed translation.</strong> An English version was published in 1765, but a complete, correctly segmented transcription has not been verified. Rather than display an invented translation as eighteenth-century English, this reader keeps the historical German folios available below.</p></div>
      <a class="document-link" href="https://books.google.com/books?id=5elUAAAAcAAJ" target="_blank" rel="noopener">Examine the 1765 English edition ↗</a>`;
  } else {
    body = `<h2>Исторический русский текст</h2>
      <div class="document-alert"><p><strong>Текст перевода Василия Богородского 1815 года пока не прошёл сверку.</strong> Сохранившиеся русские издания имеют собственную историю иллюстраций. Мы не подменяем оригинальный перевод современным пересказом.</p></div>
      <a class="document-link" href="https://kp.rusneb.ru/item/material/5fcf8bb3991f3b91423439b5" target="_blank" rel="noopener">Изучить русский выпуск 1825 года ↗</a>`;
  }
  return `<div class="document-panel" aria-live="polite">${body}<p style="margin-top:25px"><strong>${esc(t.note)}</strong></p></div>`;
}
function renderStory(id) {
  const t=ui(); const s=record(id), st=stories[id-1];
  if (!s || !st) return `<div class="error-state"><h1>History not found.</h1><a href="${collectionURL}" data-nav="collection">${t.back}</a></div>`;
  const label = st.testament === "old" ? t.old : t.new;
  const prev = id > 1 ? stories[id-2] : null;
  const next = id < 104 ? stories[id] : null;
  const folios = s.folios || [];
  return `<article class="reader">
    <div class="reader-top">
      <div class="breadcrumb"><a href="${collectionURL}" data-nav="collection">${esc(t.back)}</a><i aria-hidden="true"></i><span>${esc(label)} · ${roman(st.number)}</span></div>
      <div class="reader-arrows">
        <button class="arrow-button" type="button" aria-label="${esc(t.prev)}" ${prev?`data-next-story="${prev.id}"`:"disabled"}>←</button>
        <button class="arrow-button" type="button" aria-label="${esc(t.next)}" ${next?`data-next-story="${next.id}"`:"disabled"}>→</button>
      </div>
    </div>
    <div class="reader-layout">
      <section class="reader-image-pane" aria-label="Original historical engraving">
        <div class="reader-kicker"><span>${esc(t.original)}</span><span>${esc(s.plate_label)} · 1768</span></div>
        <div class="main-plate"><button data-zoom="${id}" type="button" aria-label="Enlarge original engraving">${imageTag(s,false,false)}</button><span class="image-zoom-label">${state.lang==="en"?"Tap to enlarge":state.lang==="de"?"Zum Vergrößern berühren":"Нажмите для увеличения"} ↗</span></div>
        <div class="image-attribution"><p>Johann Hübner · ${esc(s.edition)}<br>Universitätsbibliothek Heidelberg · VD18 14362627</p><a href="${esc(anchor(s))}" target="_blank" rel="noopener">${esc(t.source)} ↗</a></div>
      </section>
      <div class="reader-copy-pane">
        <span class="reader-number">${esc(label)} · ${roman(st.number)} / LII</span>
        <h1>${textOf(title(st))}</h1>
        <p class="reader-de-title" lang="de">${textOf(st.de)}</p>
        <div class="reader-language-selector" role="group" aria-label="${esc(t.language)}">
          ${[["en","English"],["de","Deutsch"],["ru","Русский"]].map(([lng,lab])=>`<button type="button" data-reader-lang="${lng}" class="${state.lang===lng?"active":""}" aria-pressed="${state.lang===lng}">${lab}</button>`).join("")}
        </div>
        ${renderDocument(s)}
        <div class="reader-save"><button class="bookmark-large ${state.saved.has(id)?"is-saved":""}" data-save="${id}" type="button" aria-pressed="${state.saved.has(id)}">${state.saved.has(id)?esc(t.saved):esc(t.save)} ${state.saved.has(id)?"◆":"◇"}</button></div>
      </div>
    </div>
    <section class="reader-folios" aria-label="Original book pages">
      <span class="small-label">Giessen · 1768 · Originaldruck</span>
      <h2>${esc(t.scan)}</h2>
      <p>${state.lang==="en"?"The printed German pages immediately following this numbered engraving in Heidelberg's historical copy. Open any leaf to inspect the precise historical wording.":state.lang==="de"?"Die Originalseiten der Gießener Ausgabe von 1768, unmittelbar nach der entsprechenden Kupfertafel.":"Оригинальные страницы немецкого издания 1768 года, следующие за этой гравюрой."}</p>
      <div class="folio-grid">${folios.length?folios.map((f,i)=>`<a class="folio" href="${esc(f.source)}" target="_blank" rel="noopener"><figure style="margin:0"><img src="${esc(f.image)}" loading="lazy" alt="Original German page ${esc(f.label)}"><figcaption>${state.lang==="en"?"Printed page":state.lang==="de"?"Druckseite":"Страница"} ${esc(f.label)} ↗</figcaption></figure></a>`).join(""):`<p><a class="document-link" href="${esc(anchor(s))}" target="_blank" rel="noopener">${esc(t.archive)} ↗</a></p>`}</div>
    </section>
    <nav class="reader-footer-nav" aria-label="Adjacent stories">
      ${prev?`<a href="${storyURL(prev.id)}" data-open-story="${prev.id}"><small>← ${esc(t.prev)}</small><strong>${textOf(title(prev))}</strong></a>`:"<div></div>"}
      ${next?`<a href="${storyURL(next.id)}" data-open-story="${next.id}"><small>${esc(t.next)} →</small><strong>${textOf(title(next))}</strong></a>`:"<div></div>"}
    </nav>
  </article>`;
}
function renderAbout() {
  const hero=record(43);
  const copy = state.lang==="de" ? {
    headline:"Ein Buch. Drei Sprachen. <em>Ein historisches Gewissen.</em>",
    intro:"Johann Hübner veröffentlichte seine 104 Biblischen Historien erstmals 1714. Die eindrucksvollen Kupfertafeln aus der Gießener Ausgabe von 1768 sind das Herzstück dieses digitalen Projekts.",
    note:"Diese Edition unterscheidet sorgfältig zwischen historischen Textzeugen, moderner Navigation und unkorrigierter Texterkennung.",
    history:"Das Buch und Dostojewski",historyText:"In den Brüdern Karamasow erinnert sich Starez Sossima an ein Buch der 104 heiligen Geschichten mit schönen Bildern. Eine russische Ausgabe von 1815 mit 35 Bildtafeln und einem Frontispiz ist bibliographisch belegt. Bis ihre Bilder nachgewiesen und verglichen werden können, bleiben sie getrennt von den deutschen Kupferstichen.",
    policy:"Editionsprinzipien",policyText:"Keine fiktiven alten Texte. Keine KI-Kupferstiche. Jede Abbildung ist mit ihrer nachgewiesenen Quellausgabe verknüpft; maschinell erkannte Texte bleiben als solche gekennzeichnet."
  } : state.lang==="ru" ? {
    headline:"Одна книга. Три языка. <em>Историческая точность.</em>",
    intro:"Иоганн Гюбнер впервые издал 104 библейские истории в 1714 году. Все 104 гравюры из немецкого издания 1768 года составляют основу нашего цифрового архива.",
    note:"Мы отделяем исторические первоисточники от современных названий и непроверенного распознавания текста.",
    history:"Достоевский и эта книга",historyText:"В «Братьях Карамазовых» старец Зосима вспоминает книгу «Сто четыре священные истории» с прекрасными картинками. Для русского издания 1815 года документированы 35 иллюстраций и фронтиспис. Пока они не сопоставлены с оригиналом, мы не выдаём немецкие гравюры за русские.",
    policy:"Принципы издания",policyText:"Без вымышленных исторических текстов и искусственно созданных «старинных» гравюр. Каждое изображение снабжено указанием источника; OCR не выдаётся за проверенную транскрипцию."
  } : {
    headline:"One book. Three languages. <em>One obligation to the original.</em>",
    intro:"Johann Hübner first published his 104 selected biblical histories in 1714. This project restores their remarkable pictorial life through every surviving engraving of the fully illustrated Giessen printing of 1768.",
    note:"We distinguish source manuscripts, printed editions, modern editorial navigation, and uncorrected machine transcription. They are not interchangeable.",
    history:"The book Dostoevsky remembered",historyText:"In The Brothers Karamazov, Elder Zosima recalls an illustrated book of 104 biblical histories. Dostoevsky's family also remembered it as a childhood reading book. The Russian 1815 edition has been catalogued with 35 plates and a separate frontispiece. We have not yet established that those images are identical to the German engraving series. They will remain separately attributed until verified.",
    policy:"Editorial principles",policyText:"No invented old texts. No AI-generated engravings passed off as antiques. Every plate is linked to its source, and OCR is labeled uncorrected. The 1765 English translation and the 1815 Russian translation are documented but their complete, verified transcriptions are not yet integrated."
  };
  return `<div class="about-main">
    <section class="about-cover">
      <div class="about-copy"><div class="small-label">Johann Hübner · An open edition</div><h1>${copy.headline}</h1><p>${esc(copy.intro)}</p></div>
      <div class="about-visual">${imageTag(hero,false,false)}</div>
    </section>
    <div class="prose">
      <p>${esc(copy.note)}</p>
      <blockquote>“One hundred and four sacred histories of the Old and New Testament, with beautiful pictures.”</blockquote>
      <h2>${esc(copy.history)}</h2><p>${esc(copy.historyText)}</p>
      <h2>${esc(copy.policy)}</h2><p>${esc(copy.policyText)}</p>
      <hr>
      <h2>Historical witnesses and source credits</h2>
      <table class="source-table"><thead><tr><th>Edition</th><th>Evidence</th><th>Digital source</th></tr></thead><tbody>
        <tr><td><strong>German · Giessen 1768</strong><br>Johann Christoph Schröder. Historical plates associated with Georg Peter Monath.</td><td>All 104 explicitly numbered engravings, 52 per Testament; original German text preserved as page images.</td><td><a href="https://digi.ub.uni-heidelberg.de/diglit/huebner1768" target="_blank" rel="noopener">Heidelberg University Library ↗</a></td></tr>
        <tr><td><strong>German · Zürich c.1775</strong><br>Bürklische Druckerei.</td><td>Additional illustrated facsimile and uncorrected machine OCR. PDM license.</td><td><a href="https://www.e-rara.ch/zuz/doi/10.3931/e-rara-85573" target="_blank" rel="noopener">Zentralbibliothek Zürich, AWZ 727 ↗</a></td></tr>
        <tr><td><strong>Russian · St Petersburg 1815</strong><br>Translation by Vasily Bogorodsky.</td><td>35 engraved leaves and one frontispiece documented; complete image and text scans not yet verified.</td><td><a href="https://search.rsl.ru/ru/search#q=%D0%B3%D0%B8%D0%B1%D0%BD%D0%B5%D1%80%201815" target="_blank" rel="noopener">Russian State Library catalog ↗</a></td></tr>
        <tr><td><strong>English · Hamburg 1765</strong><br>German–French–English parallel edition.</td><td>Publication identified. Complete verified transcription not yet incorporated.</td><td><a href="https://books.google.com/books?id=5elUAAAAcAAJ" target="_blank" rel="noopener">Google Books facsimile ↗</a></td></tr>
      </tbody></table>
      <p>This edition is an evolving open-access archival project. Source pages and historical image files are public-domain works; reproductions are credited to the libraries that preserve them. Original eighteenth-century spellings are retained in facsimile; navigation labels are modern editorial interpretations.</p>
      <p><a href="https://github.com/DalmoMendonca/biblicalstories" target="_blank" rel="noopener">Browse the open-source repository and provenance data ↗</a></p>
    </div>
  </div>`;
}
function render() {
  const view=q("view") || "home";
  syncHeader(view);
  if (view==="story") {
    const id=Math.min(104,Math.max(1,parseInt(q("id")||"1",10)||1));
    main.innerHTML=renderStory(id);
    document.title=title(stories[id-1])+" — 104 Sacred Histories";
  } else if (view==="collection") {
    main.innerHTML=renderCollection();
    renderGrid();
    document.title=ui().library+" — 104 Sacred Histories";
  } else if (view==="about") {
    main.innerHTML=renderAbout();
    document.title=ui().about+" — 104 Sacred Histories";
  } else {
    main.innerHTML=renderHome();
    document.title="104 Sacred Histories — Johann Hübner";
  }
}
function toggleSaved(id) {
  if (state.saved.has(id)) state.saved.delete(id);
  else state.saved.add(id);
  safelySave("huebner-saved",JSON.stringify([...state.saved]));
  const current = q("view") || "home";
  if (current === "collection") { renderGrid(); }
  else { render(); }
}
function showArt(id) {
  const s=record(id), st=stories[id-1];
  if (!s) return;
  dialogTitle.textContent=title(st)+" · "+s.plate_label;
  dialogImage.src=s.original_image;
  dialogImage.alt=title(st)+" — original engraved illustration, 1768";
  dialogCredit.textContent="Giessen, 1768 · Universitätsbibliothek Heidelberg · "+s.plate_label+" · public-domain historical artwork";
  if (!dialog.open) dialog.showModal();
}
document.addEventListener("click",event=>{
  const lang=event.target.closest("[data-lang],[data-reader-lang]");
  if (lang) { setLanguage(lang.dataset.lang || lang.dataset.readerLang); return; }
  const save=event.target.closest("[data-save]");
  if (save) { toggleSaved(Number(save.dataset.save)); return; }
  const filter=event.target.closest("[data-filter]");
  if (filter) {
    state.testament=filter.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach(x=>{
      const active=x===filter;x.classList.toggle("active",active);x.setAttribute("aria-pressed",String(active));
    });
    renderGrid();return;
  }
  const next=event.target.closest("[data-next-story]");
  if (next) { setNavigation("story",Number(next.dataset.nextStory));return; }
  const zoom=event.target.closest("[data-zoom]");
  if (zoom) { showArt(Number(zoom.dataset.zoom));return; }
  const chapter=event.target.closest("[data-open-story]");
  if (chapter) { event.preventDefault();setNavigation("story",Number(chapter.dataset.openStory));return; }
  const nav=event.target.closest("[data-nav]");
  if (nav) { event.preventDefault();setNavigation(nav.dataset.nav);return; }
});
document.addEventListener("input",event=>{
  if (event.target.id==="gallery-search") { state.search=event.target.value;renderGrid(); }
});
window.addEventListener("popstate",render);
document.addEventListener("keydown",event=>{
  if (dialog.open || event.altKey || event.ctrlKey || event.metaKey || /INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName||"")) return;
  if(q("view")!=="story") return;
  const id=Math.min(104,Math.max(1,Number(q("id"))||1));
  if(event.key==="ArrowRight" && id<104){event.preventDefault();setNavigation("story",id+1);}
  if(event.key==="ArrowLeft" && id>1){event.preventDefault();setNavigation("story",id-1);}
});
document.querySelector("#dialog-close").addEventListener("click",()=>dialog.close());
dialog.addEventListener("click",event=>{if(event.target===dialog)dialog.close();});
document.querySelector("#menu-toggle").addEventListener("click",event=>{
  const expanded=header.classList.toggle("menu-open");
  event.currentTarget.setAttribute("aria-expanded",String(expanded));
});
document.addEventListener("error",event=>{
  if(event.target.tagName!=="IMG")return;
  const el=event.target;
  if(el.dataset.fallback && el.src!==el.dataset.fallback){el.src=el.dataset.fallback;return;}
  if(el.closest(".folio")) el.style.visibility="hidden";
},true);

async function init() {
  try {
    const response=await fetch("/data/archive.json",{cache:"no-store"});
    if(!response.ok) throw new Error("Archival data not yet published (HTTP "+response.status+")");
    const archive=await response.json();
    if (!Array.isArray(archive.images)||archive.images.length!==104) throw new Error("The collection failed the 104-plate integrity check.");
    for (let i=0;i<104;i++) {
      const im=archive.images[i];
      if(im.id!==i+1||im.number!==i%52+1||!im.verified||!im.original_image) throw new Error("An illustration's provenance record is incomplete.");
    }
    state.images=archive.images;
    state.byId=new Map(state.images.map(r=>[r.id,r]));
    document.documentElement.lang=state.lang;
    render();
  } catch(error) {
    console.error("Archival data failed to load:",error);
    main.innerHTML=`<div class="error-state"><span class="small-label">The source archive</span><h1>The illustrated archive is temporarily unavailable.</h1><p>The site requires the 104 verified plate files to render correctly. Its contents are being preserved from Heidelberg's original 1768 edition, and we will not display substitute imagery.</p><p><a href="https://digi.ub.uni-heidelberg.de/diglit/huebner1768" target="_blank" rel="noopener">View the original digital book at Heidelberg ↗</a></p></div>`;
  }
}
init();