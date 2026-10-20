"""Compact the reviewed archive into bilingual offline pages and discovery cards.
Translation uses a local en→es CTranslate2 model; weights are not part of the app.
"""
import pathlib,json,re,hashlib,collections,time,os
ROOT=pathlib.Path(__file__).resolve().parents[1];WEB=ROOT/'web';SOURCE=pathlib.Path('/tmp/blockwise-entries-en.json');CACHE=pathlib.Path('/tmp/blockwise-translation-cache.json')
raw=json.load(open(SOURCE));old=json.load(open(WEB/'facts.json'));old=[f for f in old if not f.get('imported')]
# The killer bunny is a Java-only rabbit variant, not a second copy of the rabbit page.
for e in raw:
 if e['id']=='killer-bunny':
  e['title']={'en':'Killer Bunny','es':'Conejo asesino'};e['blocks']=[b for b in e['blocks'] if 'killer' in (b.get('subheading','')+' '+b.get('text','')).lower()];e['description']['en']=[b['text'] for b in e['blocks'] if b['kind']=='text'][:1];e['facts']=[f for f in e['facts'] if 'killer' in f['context'].lower()];e['stats']=[];e['scope']='java-command-only'
 if e['id'] in ['giant','illusioner']:e['scope']='java-command-only'
 if e['id'] in ['npc','agent']:e['scope']='education-bedrock'
 # Exclude statements that lose their referent or are merely generic equipment rules.
 e['facts']=[f for f in e['facts'] if not re.match(r'(Although |Occasionally,|Furthermore,|In this state|The variant |Any picked-up|Any naturally spawned|The pregnant frog)',f['text'])]
# Re-select short, self-contained claims before applying the target of ten.
for e in raw:
 groups=collections.OrderedDict((k,[]) for k in ['Behavior','Usage','Taming','Breeding','Spawning','Drops','Trading','Bartering','Transformation','Riding','Development','Variants'])
 for b in e['blocks']:
  if b['kind']!='text' or b['section'] not in groups:continue
  paragraph=b['text']
  if any(t in paragraph.lower() for t in ['[ until','upcoming','planned','[ verify','citation needed','more information needed']):continue
  sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z])',paragraph)
  for sent in sentences:
   if not (35<=len(sent)<=240 and 6<=len(sent.split())<=42) or not sent.endswith(('.', '!', '?')):continue
   if re.match(r'(Although |Occasionally,|Furthermore,|In this state|The variant |Any picked-up|Any naturally spawned|The pregnant frog|This |These |Those |However,|Otherwise,|Additionally,|Also,|For |Because |They |Their |It |Its )',sent):continue
   if re.search(r'\b(See also|Main article|For other|For more|This article|The following|shown below|shown above|listed below|these values|as follows|in the table|For example)\b',sent,re.I) or '=' in sent or '/' in sent:continue
   if ' XP' in sent and 'no' not in sent.lower():continue
   if len(sentences)>1 and sent!=sentences[0] and re.search(r'In (Java|Bedrock) Edition|only|unless|except|if ',paragraph,re.I):continue
   groups[b['section']].append({'text':sent,'context':paragraph,'section':b['section'],'subheading':b['subheading'],'edition':b['edition']})
 chosen=[]
 while len(chosen)<10 and any(groups.values()):
  for group in groups.values():
   if not group or len(chosen)>=10:continue
   candidate=group.pop(0);words=set(re.findall('[a-z]+',candidate['text'].lower()))
   if any(len(words&set(re.findall('[a-z]+',f['text'].lower())))/max(1,len(words|set(re.findall('[a-z]+',f['text'].lower()))))>.64 for f in chosen):continue
   chosen.append(candidate)
 e['facts']=chosen
names={t['id']:t['es'] for t in json.load(open(WEB/'taxonomy.json'))['tags'] if t.get('group')=='mobs'}
for e in raw:
 if e['id'] in names:e['title']['es']=names[e['id']]
# Localized section headings are editorial navigation, not extra factual claims.
HEAD={'Spawning':'Aparición','Behavior':'Comportamiento','Drops':'Botín','Trading':'Intercambios','Bartering':'Trueque','Usage':'Usos e interacciones','Breeding':'Reproducción','Taming':'Domesticación','Healing':'Curación','Development':'Desarrollo','History':'Historia seleccionada','Trivia':'Detalles adicionales','Professions':'Profesiones','Schedules':'Horarios','Variants':'Variantes','Obtaining':'Obtención','Crafting':'Fabricación','Natural generation':'Generación natural','Mob loot':'Botín de criaturas','Transformation':'Transformación','Transportation':'Transporte','Riding':'Montura','Achievements':'Logros'}
STAT={'Health points':'Puntos de vida','Behavior':'Comportamiento','Mob type':'Tipo de criatura','Attack strength':'Fuerza de ataque','Hitbox size':'Tamaño de colisión','Spawn':'Aparición','Usable items':'Objetos utilizables','Armor points':'Puntos de armadura','Speed':'Velocidad','Stackable':'Apilable','Renewable':'Renovable','Rarity color':'Rareza','Durability':'Durabilidad','Flammable':'Inflamable'}
def short(text,limit=1000):
 if len(text)<=limit:return text
 sentences=re.split(r'(?<=[.!?])\s+',text);out=''
 for s in sentences:
  if len(out)+len(s)>limit:break
  out+=(' ' if out else '')+s
 return out or text[:limit].rsplit(' ',1)[0]+'…'
def flatten(rows):
 grid=[];pending={}
 for row in rows:
  expanded=[];col=0;nextpending={}
  for idx,(text,count) in pending.items():
   if count>1:nextpending[idx]=(text,count-1)
  for c in row:
   while col in pending:expanded.append(pending[col][0]);col+=1
   for j in range(c.get('colspan',1)):
    expanded.append(c['text']);
    if c.get('rowspan',1)>1:nextpending[col]=(c['text'],c['rowspan']-1)
    col+=1
  while col in pending:expanded.append(pending[col][0]);col+=1
  grid.append(expanded);pending=nextpending
 return grid
entries=[];translations=set();fact_inputs=[]
for e in raw:
 sections=[];groups=collections.OrderedDict()
 for b in e['blocks']:
  if b['section']=='Overview':continue
  groups.setdefault(b['section'],[]).append(b)
 for name,blocks in groups.items():
  paras=[short(b['text']) for b in blocks if b['kind']=='text'][:(4 if name in ['Behavior','Usage','Trading'] else 3)]
  tables=[]
  for b in [b for b in blocks if b['kind']=='table'][:(3 if name=='History' else 2)]:
   rows=b['rows']
   if name=='History':
    flat=flatten(rows);useful=[r for r in flat if len(r)>=2 and any(len(t)>20 for t in r)]
    chosen=useful if len(useful)<=7 else useful[:3]+[useful[len(useful)//2]]+useful[-3:]
    rows=[[{'text':' / '.join(dict.fromkeys(r[:-1])),'header':False,'colspan':1,'rowspan':1},{'text':short(r[-1],550),'header':False,'colspan':1,'rowspan':1}] for r in chosen]
   if rows:tables.append({'label':{'en':b.get('edition') or b.get('subheading') or name,'es':b.get('edition') or HEAD.get(b.get('subheading'),HEAD.get(name,name))},'rows':rows})
  if paras or tables:
   section={'id':re.sub('[^a-z0-9]+','-',name.lower()),'title':{'en':'Selected history' if name=='History' else name,'es':HEAD.get(name,name)},'paragraphs':{'en':paras,'es':[]},'tables':tables};sections.append(section)
  translations.update(paras)
  for table in tables:
   for row in table['rows']:
    for c in row:translations.add(c['text'])
 desc=[short(t,700) for t in e['description']['en'][:2]];translations.update(desc)
 stats=[s for s in e['stats'] if s['label'] in STAT and len(s['value'])<600][:8]
 for s in stats:translations.add(s['value'])
 entry={k:e[k] for k in ['id','kind','title','source','archive','snapshot','image']};entry['description']={'en':desc,'es':[]};entry['sections']=sections;entry['stats']=stats;entry['translation']='machine-draft';entry['scope']=e.get('scope','archived-reference');entry['factIds']=[];entry['related']=[];entries.append(entry)
 if e['kind']=='mob':
  for i,f in enumerate(e['facts']):
   f=dict(f);f['id']='discovery-'+e['id']+'-'+hashlib.sha1(f['text'].encode()).hexdigest()[:8];f['targetId']=e['id'];f['source']=e['source']+'#'+f['section'].replace(' ','_');fact_inputs.append(f);translations.add(f['text']);translations.add(short(f['context'],1600));
# Translations are generated locally, cached, and labeled as drafts in the UI.
import ctranslate2,sentencepiece
sp=sentencepiece.SentencePieceProcessor(model_file='/tmp/blockwise-es-model/en_es/sentencepiece.model');tr=ctranslate2.Translator('/tmp/blockwise-es-model/en_es/model',device='cpu',compute_type='int8',inter_threads=4,intra_threads=4)
enlang=json.load(open('/tmp/en_us.json'));eslang=json.load(open('/tmp/es_es.json'));glossary={}
for key,en in enlang.items():
 if key.startswith(('item.minecraft.','block.minecraft.','entity.minecraft.','biome.minecraft.')) and key in eslang and len(en)>2 and len(en)<55:glossary[en.lower()]=eslang[key]
for e in entries:
 glossary[e['title']['en'].lower()]=e['title']['es']
 if e['kind']=='mob':
  en=e['title']['en'].lower();es=e['title']['es'];plural=en[:-1]+'ies' if en.endswith('y') else en+'es' if en.endswith(('s','x','ch','sh')) else en+'s';esp=es+'s' if es[-1:].lower() in 'aeiouáéíóú' else es+'es';glossary[plural]=esp
for a,b in {'mob':'criatura','mobs':'criaturas','tamed':'domesticado','untamed':'no domesticado','Java Edition':'Java Edition','Bedrock Edition':'Bedrock Edition','Health points':'Puntos de vida','HP':'HP','XP':'XP'}.items():glossary[a.lower()]=b
pattern=re.compile(r'(?<![\w])('+ '|'.join(re.escape(k) for k in sorted(glossary,key=len,reverse=True)) +r')(?![\w])',re.I)
cache=json.load(open(CACHE)) if CACHE.exists() else {}
# Exact game names and numeric table cells do not need neural translation.
for text in translations:
 if text in cache:continue
 if text.lower() in glossary:cache[text]=glossary[text.lower()];continue
 if not re.search('[A-Za-z]{3}',text):cache[text]=text;continue
 stripped=pattern.sub('',text)
 if not re.search('[A-Za-z]{3}',stripped):cache[text]=pattern.sub(lambda m:glossary[m[0].lower()],text)
todo=sorted([s for s in translations if s not in cache],key=len);print('Translating',len(todo),'unique source strings',flush=True)
def protect(s):
 terms=[]
 def repl(m):
  token='QZX'+str(len(terms))+'QZX';terms.append(glossary[m[0].lower()]);return token
 return pattern.sub(repl,s),terms
fallback=0
for start in range(0,len(todo),32):
 chunk=todo[start:start+32];work=[]
 for text in chunk:
  if not re.search('[A-Za-z]{3}',text):cache[text]=text;continue
  text2,terms=protect(text);work.append((text,text2,terms))
 if work:
  results=tr.translate_batch([sp.encode(text2,out_type=str) for _,text2,_ in work],beam_size=1,max_batch_size=32,max_decoding_length=600)
  for (text,_,terms),result in zip(work,results):
   translated=sp.decode(result.hypotheses[0]);good=True
   for i,term in enumerate(terms):
    rx=re.compile(r'QZX\s*'+str(i)+r'\s*QZX',re.I)
    if not rx.search(translated):good=False;break
    translated=rx.sub(lambda _:term,translated)
   if not good or 'QZX' in translated.upper():translated=text;fallback+=1
   cache[text]=translated
 CACHE.write_text(json.dumps(cache,ensure_ascii=False))
 if start%160==0:print('Translated',min(start+32,len(todo)),'/',len(todo),'fallbacks',fallback,flush=True)
for e in entries:
 e['description']['es']=[cache.get(x,x) for x in e['description']['en']]
 for s in e['stats']:s['label']={'en':s['label'],'es':STAT.get(s['label'],s['label'])};s['value']={'en':s['value'],'es':cache.get(s['value'],s['value'])}
 for sec in e['sections']:
  sec['paragraphs']['es']=[cache.get(x,x) for x in sec['paragraphs']['en']]
  for table in sec['tables']:
   for row in table['rows']:
    for c in row:c['text']={'en':c['text'],'es':cache.get(c['text'],c['text'])}
 byid={x['id']:x for x in entries}
# Related links are limited to local pages that actually exist; no fake empty reference stubs.
for original in raw:
 e=byid.get(original['id'])
 if not e:continue
 ids=set()
 for b in original['blocks']:
  for a in b.get('links',[]):
   linked=re.sub('[^a-z0-9]+','-',a['title'].lower()).strip('-')
   if linked in byid and linked!=e['id']:ids.add(linked)
 e['related']=sorted(ids)
new=[]
for f in fact_inputs:
 e=byid[f['targetId']];text=f['text'];context=short(f['context'],1600);es=cache.get(text,text);ctes=cache.get(context,context);editions=['java'] if e['scope']=='java-command-only' else ['bedrock'] if e['scope']=='education-bedrock' else ['java','bedrock'];edition=f.get('edition','')
 if edition=='Java Edition':editions=['java']
 if edition=='Bedrock Edition':editions=['bedrock']
 record={'id':f['id'],'targetId':e['id'],'targetSection':'facts','category':'mobs','topics':['mobs','survival'] if e['scope']=='archived-reference' else ['mobs','commands'],'tags':[e['id'],f['section'].lower().replace(' ','-')],'image':e['image'],'source':f['source'],'status':'archive','sourceSnapshot':e['snapshot'],'sectionLabel':{'en':f['section'],'es':HEAD.get(f['section'],f['section'])},'versionRanges':[{'edition':ed,'mode':'unknown','from':'','to':'','verified':False} for ed in editions],'versionNotes':{'en':'Source snapshot '+e['snapshot']+'. No current-version range has been verified.','es':'Fuente archivada del '+e['snapshot']+'. El rango actual de versiones no está verificado.'},'context':{'en':context,'es':ctes},'en':{'title':text if len(text)<110 else e['title']['en']+' · '+f['section'],'summary':text,'body':[]},'es':{'title':es if len(es)<110 else e['title']['es']+' · '+HEAD.get(f['section'],f['section']),'summary':es,'body':[]},'imported':True,'translation':'machine-draft'}
 new.append(record);e['factIds'].append(record['id'])
# Preserve existing bookmarks and point older cards at the same canonical pages.
oldtargets={'cat':'cat','pumpkin':'enderman','honey':'honey-block','sheep':'sheep','sponge':'sponge','mushroom':'mooshroom','bed':'bed'}
for f in old:
 target=oldtargets.get(f['id'])
 if target in byid:f['targetId']=target;byid[target]['factIds'].append(f['id'])
 if f['id']=='bed' and 'bed' in byid:f['image']=byid['bed']['image']
# Spread the first screen across different mobs instead of ten neighboring cards for the same page.
queues={e['id']:[f for f in new if f['targetId']==e['id']] for e in entries if e['kind']=='mob'};ordered=[]
while any(queues.values()):
 for q in queues.values():
  if q:ordered.append(q.pop(0))
(WEB/'entries.json').write_text(json.dumps(entries,ensure_ascii=False,separators=(',',':')));(WEB/'facts.json').write_text(json.dumps(old+ordered,ensure_ascii=False,separators=(',',':')))
coverage={'sourceSnapshot':'2025-11-05','mobPages':sum(e['kind']=='mob' for e in entries),'referencePages':len(entries),'facts':len(old+ordered),'atLeastTen':sum(e['kind']=='mob' and len(e['factIds'])>=10 for e in entries),'belowTen':[{'id':e['id'],'count':len(e['factIds'])} for e in entries if e['kind']=='mob' and len(e['factIds'])<10]};(WEB/'coverage.json').write_text(json.dumps(coverage,indent=2));print(json.dumps(coverage),flush=True)
