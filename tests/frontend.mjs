import vm from 'node:vm';import fs from 'node:fs';import assert from 'node:assert/strict';import {webcrypto} from 'node:crypto';
const facts=[...JSON.parse(fs.readFileSync('web/facts.json')),...JSON.parse(fs.readFileSync('web/catalog-supplement.json')).facts],entries=JSON.parse(fs.readFileSync('web/entries.json')),els=new Map(),storage=new Map();function element(sel){if(!els.has(sel))els.set(sel,{innerHTML:'',textContent:'',style:{},classList:{toggle(){}},querySelectorAll:()=>[],querySelector:()=>null,addEventListener(){},setAttribute(){},focus(){},setSelectionRange(){},getBoundingClientRect:()=>({left:100,bottom:120}),showModal(){this.open=true},close(){this.open=false}});return els.get(sel)}
const context=vm.createContext({document:{documentElement:{},body:{classList:{toggle(){}},append(){}},querySelector:element,querySelectorAll:()=>[],getElementById:()=>({scrollIntoView(){}}),createElement:()=>({innerHTML:'',style:{},setAttribute(){},querySelector:()=>element('popover-action')})},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},navigator:{language:'en-US'},location:{hash:'',origin:'https://example.test'},history:{replaceState(){},pushState(){}},window:{speechSynthesis:{cancel(){}},scrollTo(){},innerWidth:1280,innerHeight:720},speechSynthesis:{cancel(){}},crypto:webcrypto,fetch:async u=>({json:async()=>JSON.parse(fs.readFileSync('web'+u))}),setTimeout,clearTimeout,console,URL,Blob});
vm.runInContext(fs.readFileSync('web/catalog.js','utf8'),context);vm.runInContext(fs.readFileSync('web/encyclopedia.js','utf8'),context);vm.runInContext(fs.readFileSync('web/game-catalog.js','utf8'),context);vm.runInContext(fs.readFileSync('web/inventory-index.js','utf8'),context);vm.runInContext(fs.readFileSync('web/crafting-data.js','utf8'),context);vm.runInContext(fs.readFileSync('web/structures.js','utf8'),context);vm.runInContext(fs.readFileSync('web/tools.js','utf8'),context);vm.runInContext(fs.readFileSync('web/games.js','utf8'),context);vm.runInContext(fs.readFileSync('web/crafting-game.js','utf8'),context);vm.runInContext(fs.readFileSync('web/gallery.js','utf8'),context);vm.runInContext(fs.readFileSync('web/app.js','utf8'),context);await new Promise(r=>setTimeout(r,0));assert.match(element('#main').innerHTML,/Discover something new/);assert.equal((element('#main').innerHTML.match(/class="card"/g)||[]).length,Math.min(36,facts.length));
vm.runInContext("state.language='es';render()",context);assert.match(element('#main').innerHTML,/Descubre algo nuevo/);assert.match(element('#nav').innerHTML,/Enciclopedia/);assert.equal(vm.runInContext('JSON.stringify(Object.keys(words.en).sort())===JSON.stringify(Object.keys(words.es).sort())',context),true);
vm.runInContext("page='saved';category='all';state.saved=['cat'];render()",context);assert.equal((element('#main').innerHTML.match(/class="card"/g)||[]).length,1);
vm.runInContext("state.language='en';page='home';selectedTag='creeper';category='all';render()",context);assert.ok((element('#main').innerHTML.match(/class="card"/g)||[]).length>=1);
const creeperFacts=facts.filter(f=>f.targetId==='creeper');assert.ok(creeperFacts.length>=2);vm.runInContext(`openFact(${JSON.stringify(creeperFacts[0].id)})`,context);assert.equal(vm.runInContext('currentEntry',context),'creeper');assert.match(element('#main').innerHTML,/entry-discovery/);vm.runInContext(`openFact(${JSON.stringify(creeperFacts[1].id)})`,context);assert.equal(vm.runInContext('currentEntry',context),'creeper');assert.equal(vm.runInContext('currentFact',context),creeperFacts[1].id);
assert.match(vm.runInContext("referenceText('A creeper can drop gunpowder.','creeper')",context),/href="#entry\/gunpowder"/);vm.runInContext("state.language='es';prepareReferences()",context);assert.match(vm.runInContext("referenceText('La pólvora sirve para fabricar objetos.','creeper')",context),/data-entry="gunpowder"/);
vm.runInContext("state.language='en';showReferencePreview('gunpowder',document.querySelector('#test-anchor'))",context);assert.match(vm.runInContext('popoverNode.innerHTML',context),/Gunpowder/);assert.match(vm.runInContext('popoverNode.innerHTML',context),/Open the full page/);assert.ok(!vm.runInContext('popoverNode.hidden',context));vm.runInContext('hideReferencePreview()',context);assert.equal(vm.runInContext('popoverNode.hidden',context),true);
vm.runInContext("navigateEntry('gunpowder')",context);assert.match(element('#main').innerHTML,/General reference/);assert.match(element('#main').innerHTML,/Description/);
assert.equal(vm.runInContext("validRange({edition:'java',mode:'range',from:'1.20',to:'1.21.4'})",context),true);assert.equal(vm.runInContext("validRange({edition:'java',mode:'range',from:'1.21',to:'1.20'})",context),false);assert.equal(vm.runInContext("validRange({edition:'java',mode:'exact',from:'24w14a',to:''})",context),true);assert.equal(vm.runInContext("versionCompare('1.21.10','1.21.9')",context),1);
for(const page of ['library','topics','settings','community']){vm.runInContext(`page='${page}';render()`,context);assert.ok(element('#main').innerHTML.length>400)}
vm.runInContext("window.BlockwiseNative={};page='settings';render()",context);assert.match(element('#main').innerHTML,/backendurl/);assert.throws(()=>vm.runInContext('validate({saved:[]})',context));
assert.ok(facts.every(f=>f.en.summary&&f.es.summary&&new URL(f.source).hostname==='minecraft.wiki'));assert.ok(entries.every(e=>e.description.en.length&&e.description.es.length));assert.ok(facts.filter(f=>f.targetId).every(f=>entries.some(e=>e.id===f.targetId)));assert.ok(entries.filter(e=>e.kind==='mob').every(e=>e.sections.some(s=>s.id==='history')));assert.ok(facts.find(f=>f.id==='bed').image.src.includes('reference-images/bed'));
console.log('Frontend: bilingual feed, pagination, canonical mob pages, multiple fact routes to one page, English/Spanish resource links, neutral hover previews, reference navigation, source provenance, history sections and existing settings/submissions passed (JS harness; no browser/device QA).');
// The database uses the same live fact collection and never truncates an export to its page size.
vm.runInContext("state.language='en';page='database';category='all';selectedTag='';editionFilter='all';versionFilter='';databaseQuery='';render()",context);
assert.match(element('#main').innerHTML,/fact-table/);assert.equal((element('#main').innerHTML.match(/<tr>/g)||[]).length,51);
const exported=JSON.parse(vm.runInContext('JSON.stringify(databaseRows().map(factRecord))',context));assert.equal(exported.length,facts.length);assert.ok(exported.every(r=>r.minecraft_wiki_url.startsWith('https://minecraft.wiki/')&&r.page_url.startsWith('https://example.test/app/#')));
assert.ok(exported.every(r=>Array.isArray(r.edition_versions)&&Array.isArray(r.tags)&&r.description_en&&r.description_es));
assert.match(vm.runInContext('databaseCSV(databaseRows())',context),/minecraft_wiki_url/);assert.match(vm.runInContext("csvValue('=SUM(A1)')",context),/^"'/);
vm.runInContext("databaseQuery='creeper';render()",context);assert.ok(vm.runInContext('databaseRows().length',context)>0);assert.ok(vm.runInContext('databaseRows().length',context)<facts.length);
const versions=JSON.parse(fs.readFileSync('web/versions.json'));assert.ok(versions.editions.length>=20);assert.ok(versions.editions.find(e=>e.id==='java').versions.length>900);assert.ok(versions.editions.find(e=>e.id==='bedrock').versions.some(v=>v.channel==='preview'));assert.ok(versions.editions.find(e=>e.id==='xbox360').versions.some(v=>v.id==='TU1'));
assert.equal(vm.runInContext("validRange({edition:'ps3',mode:'exact',from:'1.83',to:''})",context),true);assert.equal(vm.runInContext("validRange({edition:'pocket',mode:'range',from:'v0.9.0 alpha build 1',to:'v0.9.0 alpha build 9'})",context),true);assert.equal(vm.runInContext("validRange({edition:'bogus',mode:'exact',from:'1.0',to:''})",context),false);
assert.equal(vm.runInContext("includeUnknown=false;scopedMatch({mode:'unknown',verified:false},'1.21')",context),false);assert.equal(vm.runInContext("scopedMatch({mode:'exact',verified:true,from:'Preview 1.21.130.26'},'Preview 1.21.130.26')",context),true);
vm.runInContext("discoveryPrevious=[];state.read=[];discoverySeed=0.12",context);const first=vm.runInContext('discoveryRank(facts).slice(0,36).map(f=>f.id).join()',context);vm.runInContext('discoverySeed=0.84',context);const second=vm.runInContext('discoveryRank(facts).slice(0,36).map(f=>f.id).join()',context);assert.notEqual(first,second);assert.equal(vm.runInContext('new Set(discoveryRank(facts).map(f=>f.id)).size',context),facts.length);assert.ok(vm.runInContext('new Set(discoveryRank(facts).slice(0,20).map(f=>f.targetId||f.category)).size',context)>15);
assert.equal((element('#mobile-nav').innerHTML.match(/<button/g)||[]).length,4);assert.match(element('#mobile-nav').innerHTML,/moremenu/);
console.log('Catalogue: live rows, complete filtered exports, CSV escaping, historical editions, development builds, conservative compatibility, diverse session rankings and four-item mobile navigation passed.');

// The image gallery deduplicates shared thumbnails and searches their fact titles.
vm.runInContext("state.language='en';page='images';galleryScope='facts';galleryQuery='';render()",context);
assert.match(element('#main').innerHTML,/Review the artwork/);
const inventory=JSON.parse(vm.runInContext('JSON.stringify(galleryRows())',context));
assert.equal(new Set(inventory.map(row=>row.image.src)).size,inventory.length);
assert.equal(inventory.reduce((n,row)=>n+row.factIds.length,0),facts.length);
assert.ok(inventory.length<facts.length);
vm.runInContext("galleryQuery='saddle';render()",context);assert.ok(vm.runInContext('galleryRows().length',context)>0);assert.match(element('#main').innerHTML,/data-image-report/);
vm.runInContext("state.language='es';galleryQuery='';render()",context);assert.match(element('#main').innerHTML,/Revisa las imágenes/);
console.log('Image gallery: unique image grouping, complete fact usage, search, change/report controls and bilingual navigation passed.');


// The registry is complete for the declared snapshot, not an illustrated shortlist.
assert.equal(vm.runInContext('ArcadeCatalog.blocks.length',context),1168);
assert.equal(vm.runInContext('ArcadeCatalog.items.length',context),1506);
assert.equal(vm.runInContext('ArcadeCatalog.mobs.length',context),89);
for(const mode of ['mobs','blocks','items']){
 vm.runInContext(`state.language='en';page='games';arcadeStart('${mode}',true)`,context);
 assert.ok(!element('#main').innerHTML.includes('<img'),'no answer image or silhouette before solving');
 const answer=vm.runInContext('arcadeGame.answer',context);
 const wrong=vm.runInContext('arcadePool(arcadeMode).filter(e=>e.id!==arcadeGame.answer).slice(0,7).map(e=>e.id)',context);
 for(const id of wrong)vm.runInContext(`arcadeGuess(${JSON.stringify(id)})`,context);
 assert.equal(vm.runInContext('arcadeGame.done',context),false,'full registries use unlimited attempts');
 vm.runInContext(`arcadeGuess(${JSON.stringify(answer)})`,context);
 assert.equal(vm.runInContext('arcadeGame.won',context),true);
 assert.ok(element('#main').innerHTML.includes('Solved!'));
}
assert.equal(vm.runInContext("arcadeCompare(1,2).mark",context),'↑');
assert.equal(vm.runInContext("arcadeCompare(2,1).mark",context),'↓');
assert.equal(vm.runInContext("arcadeCompare(false,false).kind",context),'match');
assert.equal(vm.runInContext("arcadePool('items').find(e=>e.id==='diamond_pickaxe').props.durability",context),1561);
assert.equal(vm.runInContext("arcadePool('blocks').find(e=>e.id==='stone').props.hardness",context),1.5);
assert.ok(vm.runInContext("arcadePool('blocks').some(e=>e.id==='cherry_trapdoor')&&arcadePool('items').some(e=>e.id==='creeper_spawn_egg')",context));
vm.runInContext("arcadeStart('items');arcadeGame.hints=2;arcadeSave()",context);const savedAnswer=vm.runInContext('arcadeGame.answer',context);vm.runInContext("arcadeStart('items')",context);assert.equal(vm.runInContext('arcadeGame.hints',context),2);assert.equal(vm.runInContext('arcadeGame.answer',context),savedAnswer);
for(const language of ['en','es']){
 vm.runInContext(`state.language='${language}'`,context);
 for(let seed=1;seed<=80;seed++){
  const cw=JSON.parse(vm.runInContext(`JSON.stringify(arcadeNumberCrossword(arcadeCrossword(${seed})))`,context));assert.ok(cw.words.length>=4);
  const seen=new Set(),queue=[Object.keys(cw.cells)[0]];while(queue.length){const k=queue.pop();if(seen.has(k))continue;seen.add(k);const [r,c]=k.split(',').map(Number);for(const [y,x] of [[r+1,c],[r-1,c],[r,c+1],[r,c-1]])if(cw.cells[y+','+x]&&!seen.has(y+','+x))queue.push(y+','+x)}assert.equal(seen.size,Object.keys(cw.cells).length);
  for(const w of cw.words)for(let i=0;i<w.word.length;i++)assert.equal(cw.cells[(w.r+(w.d==='down'?i:0))+','+(w.c+(w.d==='across'?i:0))],w.word[i]);
  const ordered=[...cw.words].sort((a,b)=>a.r-b.r||a.c-b.c);assert.ok(ordered.every((w,i)=>i===0||w.n>=ordered[i-1].n),'standard crossword numbering');
 }
 vm.runInContext("arcadeStart('crossword',true)",context);assert.match(element('#main').innerHTML,/<table class="arcade-cross-table"/);assert.ok(!element('#main').innerHTML.includes('style='));
 vm.runInContext("arcadeGame.letters={...arcadeGame.crossword.cells}",context);assert.equal(vm.runInContext('arcadeCrosswordSolved()',context),true);vm.runInContext("arcadeGame.letters[Object.keys(arcadeGame.letters)[0]]='?'",context);assert.equal(vm.runInContext('arcadeCrosswordSolved()',context),false);
 vm.runInContext("arcadeStart('memory',true)",context);const cards=JSON.parse(vm.runInContext('JSON.stringify(arcadeGame.cards)',context));assert.equal(new Set(cards).size,8);assert.ok(cards.every(id=>cards.filter(v=>v===id).length===2));
 const a=0,b=cards.findIndex(v=>v!==cards[a]);vm.runInContext(`arcadeFlip(${a});arcadeFlip(${b});arcadeFlip(15)`,context);assert.equal(vm.runInContext('arcadeGame.flips.length',context),2,'third card cannot flip while a pair is visible');assert.equal(vm.runInContext('arcadeGame.moves',context),1);assert.ok(!element('#main').innerHTML.includes('arcade-hide'));
 await new Promise(r=>setTimeout(r,1200));assert.equal(vm.runInContext('arcadeGame.flips.length',context),0,'mismatches flip back automatically');
 for(const id of new Set(cards)){const pair=cards.map((v,i)=>v===id?i:-1).filter(i=>i>=0);vm.runInContext(`arcadeFlip(${pair[0]});arcadeFlip(${pair[1]})`,context)}assert.equal(vm.runInContext('arcadeGame.won',context),true);
}
console.log('Arcade: complete 26.1 registries, hidden answers, property comparisons, unlimited guesses, daily resume, 160 connected/numbered crosswords, automatic mismatches, input locking and eight-pair wins passed.');
// Crafting game uses real recipes and adds each discovery to the local book once.
vm.runInContext("state.language='en';page='games';arcadeStart('crafting',true)",context);
assert.match(element('#main').innerHTML,/Crafting challenge/);assert.equal(vm.runInContext('arcadeGame.kit.length',context),7);
assert.ok(vm.runInContext('craftingTargets(arcadeGame.kit).length',context)>10);
vm.runInContext("var testRecipe=CraftingRecipes.find(r=>recipeParts(r).length>1&&recipeParts(r).every(id=>arcadeGame.kit.includes(id)));arcadeGame.grid=recipeGrid(testRecipe);craftDiscover()",context);
assert.equal(vm.runInContext("arcadeGame.found.includes(testRecipe.out)",context),true);
assert.equal(vm.runInContext("readCollection().crafting.filter(id=>id===testRecipe.out).length",context),1);
vm.runInContext("arcadeGame.grid=recipeGrid(testRecipe);craftDiscover()",context);assert.equal(vm.runInContext('arcadeGame.found.length',context),1);
for(const pageName of ['tools','games']){vm.runInContext(`page='${pageName}';arcadeMode='';render()`,context);assert.ok(element('#main').innerHTML.length>500)}
vm.runInContext("page='tools';toolPage='hub';render()",context);assert.match(element('#main').innerHTML,/Structure inspector/);assert.equal(vm.runInContext("communityToolsHTML('','structures').includes('HoloPrint')",context),true);
vm.runInContext("page='games';arcadeMode='collection';render()",context);assert.match(element('#main').innerHTML,/Collection books/);
console.log('Crafting challenge: seven-ingredient kit, real recipe discovery, duplicate prevention, persistent collection books and Tools navigation passed.');
