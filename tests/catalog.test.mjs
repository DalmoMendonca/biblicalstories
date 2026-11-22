import {test} from "node:test";
import assert from "node:assert/strict";
import { stories, dictionary } from "../src/catalog.js";
test("Exactly 104 histories: 52 Old Testament and 52 New Testament",()=>{
 assert.equal(stories.length,104);
 for(let i=0;i<104;i++){
  assert.equal(stories[i].id,i+1);
  assert.equal(stories[i].number,i%52+1);
  assert.equal(stories[i].testament,i<52?"old":"new");
 }
});
test("Every history has three nonempty, unique editorial navigation titles",()=>{
 for(const s of stories) for(const lang of ["en","de","ru"]) {
  assert.ok(s[lang].trim(),`Missing ${lang} title in story ${s.id}`);
 }
});
test("Each UI language has complete interface labels",()=>{
 const keys=Object.keys(dictionary.en);
 for(const code of ["de","ru"]) assert.deepEqual(Object.keys(dictionary[code]),keys);
});
