import { chromium } from "playwright";
const browser=await chromium.launch({headless:true,args:["--no-sandbox","--disable-dev-shm-usage"]});
const page=await browser.newPage({viewport:{width:1100,height:760}});
const found=[];
const responsePromises=[];
page.on("response",r=>{
 const url=r.url();
 if(url.includes("books.google.com/books/content?")&&url.includes("&pg=")){
  const pg=(url.match(/[?&]pg=([^&]+)/)||[])[1];
  found.push({pg,status:r.status(),type:r.headers()["content-type"],url:url.slice(0,220)});
 }
});
for(const pg of ["PA1","PA10","PA30","PA60","PA100","PA150","PA200","PA240"]){
 try{
  let u="https://books.google.com/books?id=5elUAAAAcAAJ&pg="+pg;
  let r=await page.goto(u,{waitUntil:"domcontentloaded",timeout:35000});
  await page.waitForTimeout(2300);
  console.log("PAGE",pg,"HTML",r?.status(),"URL",page.url(),"IMAGES",JSON.stringify(found.splice(0)));
 }catch(e){console.log("ERROR",pg,String(e).slice(0,300));}
}
await browser.close();
