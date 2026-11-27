import {test} from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {german1768} from "../src/german1768.js";
import {englishFromGerman} from "../src/englishFromGerman.js";
import {russianHistorical} from "../src/russianHistorical.js";

test("Structured editions retain real source provenance and all required sections",()=>{
  const seen={de:new Set(),en:new Set(),ru:new Set()};
  for(const [lang,records] of Object.entries({de:german1768,en:englishFromGerman,ru:russianHistorical})){
    assert.equal(Object.keys(records).length,104);
    for(const [id,w] of Object.entries(records)){
      assert.ok(+id>=1&&+id<=104);
      for(const key of ["title","reference","narrative","reflection"])assert.ok(w[key]?.trim(),lang+" "+id+" "+key);
      for(const key of ["questions","teachings"])assert.ok(Array.isArray(w[key])&&w[key].length>0&&w[key].every(x=>x.trim()));
      assert.ok((w.pages||w.source_pages)?.length);
      assert.ok(!seen[lang].has(w.narrative));seen[lang].add(w.narrative);
      if(lang==="en"){
        const de=german1768[id];
        assert.ok(de);assert.equal(w.questions.length,de.questions.length);
        assert.equal(w.teachings.length,de.teachings.length);
        assert.equal(w.latin,de.latin);
      }
      if(lang==="ru")assert.match(w.kind,/historical/);
    }
  }
});
test("Reader excludes rejected machine translation files and distinguishes provenance",()=>{
  const source=readFileSync("src/app.js","utf8");
  assert.doesNotMatch(source,/fetch\(["'`][^\n]*\/texts\//);
  assert.match(source,/not a historical English witness/);
  assert.match(source,/Unkorrigierter Bibliotheks-OCR-Text/);
  assert.match(source,/ru:russianHistorical/);
  assert.match(source,/source-absence/);
});

test("Reader has one language switch and no redundant source chrome",()=>{
 const source=readFileSync("src/app.js","utf8");
 const html=readFileSync("index.html","utf8");
 assert.doesNotMatch(source,/data-reader-lang|class="figure-meta"|class="chapter-book"/);
 assert.equal((html.match(/data-lang=/g)||[]).length,3);
 assert.doesNotMatch(html,/id="lightbox-source"/);
 assert.match(source,/storyEditionNotes/);
 assert.match(source,/class="original-pages"/);
});
