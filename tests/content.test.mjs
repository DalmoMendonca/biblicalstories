import {test} from "node:test";
import assert from "node:assert/strict";
import {existsSync,readFileSync,readdirSync} from "node:fs";

const location="public/texts";
test("Every published chapter has an original German witness and two explicitly modern translations",()=>{
  if(!existsSync(location))return; // historical archive may precede text import
  const files=readdirSync(location).filter(x=>x.endsWith(".json")).sort();
  assert.equal(files.length,104,"Partial trilingual edition must never ship.");
  const seen={de:new Set(),en:new Set(),ru:new Set()};
  for(let index=0;index<104;index++){
    const chapter=JSON.parse(readFileSync(location+"/"+files[index],"utf8"));
    assert.equal(chapter.id,index+1);
    assert.equal(files[index],String(index+1).padStart(3,"0")+".json");
    for(const language of ["de","en","ru"]){
      assert.ok(typeof chapter[language]?.text==="string" && chapter[language].text.length>150,
        "Missing full "+language+" text for chapter "+chapter.id);
    }
    assert.equal(chapter.de.kind,"uncorrected-fraktur-ocr");
    assert.match(chapter.en.kind,/modern-machine-translation/);
    assert.match(chapter.ru.kind,/modern-machine-translation/);
    assert.ok(chapter.de.source_pages.length>0, "Original folio provenance missing "+chapter.id);
    for(const language of ["de","en","ru"]){
      const value=chapter[language].text.trim();
      assert.ok(!seen[language].has(value),"Duplicated "+language+" text in chapter "+chapter.id);
      seen[language].add(value);
    }
    assert.notEqual(chapter.en.text,chapter.de.text,"English must not be unmodified German OCR");
    assert.notEqual(chapter.ru.text,chapter.de.text,"Russian must not be unmodified German OCR");
  }
});
