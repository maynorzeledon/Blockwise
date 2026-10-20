"""Regenerate Spanish drafts locally with a stronger model and gameplay terminology.
This is an editorial helper; no weights or remote translation API ship in the app.
"""
import json,pathlib,re
import ctranslate2
from transformers import AutoTokenizer
R=pathlib.Path(__file__).resolve().parents[1];W=R/'web';entries=json.load(open(W/'entries.json'));facts=json.load(open(W/'facts.json'));cachepath=pathlib.Path('/tmp/blockwise-opus-translations.json');cache=json.load(open(cachepath)) if cachepath.exists() else {}
tokenizer=AutoTokenizer.from_pretrained('/tmp/blockwise-opus-model');translator=ctranslate2.Translator('/tmp/blockwise-opus-ct',compute_type='int8',inter_threads=4,intra_threads=4)
strings=set()
for f in facts:
 if f.get('translation')=='machine-draft':strings.add(f['en']['summary']);strings.add(f['context']['en'])
for e in entries:
 if e.get('translation')!='machine-draft':continue
 strings.update(e['description']['en'])
 for sec in e['sections']:
  strings.update(sec['paragraphs']['en'])
  for table in sec['tables']:
   for row in table['rows']:
    for c in row:
     if len(c['text']['en'])>70:strings.add(c['text']['en'])
 for stat in e['stats']:
  if len(stat['value']['en'])>50:strings.add(stat['value']['en'])
# Make technical English unambiguous before translation; English source text is retained unchanged.
def plain(s):
 s=re.sub(r'\bspawning\b','appearing',s,flags=re.I);s=re.sub(r'\bspawns\b','appears',s,flags=re.I);s=re.sub(r'\bspawn\b','appear',s,flags=re.I);s=re.sub(r'\bdespawns?\b','disappears',s,flags=re.I)
 s=re.sub(r'\bdrop(s)?\b',lambda m:'leaves behind' if m[1] else 'leave behind',s,flags=re.I);s=re.sub(r'\bmobs?\b',lambda m:'creatures' if m[0].lower().endswith('s') else 'creature',s,flags=re.I);s=s.replace('mob cap','maximum number of creatures');s=re.sub(r'\b(Creepers|Endermites|Endermen|Allays|Blazes|Wardens|Vexes)\b',lambda m:m[0].upper(),s);s=re.sub(r'\b(creeper|endermite|enderman|allay|blaze|warden|vex)\b',lambda m:m[0].upper(),s,flags=re.I);return s

def fix(original,s):
 s=re.sub(r'\bCR[EI]+PERS\b','creepers',s,flags=re.I);s=re.sub(r'\bCREEPER\b','creeper',s,flags=re.I)
 for name in ['Endermite','Enderman','Allay','Blaze','Warden','Vex']:
  s=re.sub(r'\b'+name.upper()+r'S?\b',lambda m:name+('s' if m[0].upper().endswith('S') and not name.endswith('s') else ''),s)
 if re.search(r'\bblocks?\b',original,re.I):s=re.sub(r'\b(cuadras|manzanas)\b','bloques',s,flags=re.I)
 if 'ticks' in original:s=s.replace('garrapatas de juego','ticks del juego').replace('garrapatas','ticks')
 return s
items=sorted([s for s in strings if s not in cache],key=len);print('Spanish review:',len(items),'strings',flush=True)
for start in range(0,len(items),32):
 part=items[start:start+32];inputs=[tokenizer.convert_ids_to_tokens(tokenizer.encode(plain(x),truncation=True,max_length=500)) for x in part];results=translator.translate_batch(inputs,beam_size=1,max_decoding_length=512,max_batch_size=32)
 for text,result in zip(part,results):cache[text]=fix(text,tokenizer.decode(tokenizer.convert_tokens_to_ids(result.hypotheses[0]),skip_special_tokens=True))
 cachepath.write_text(json.dumps(cache,ensure_ascii=False))
 if start%320==0:print('Reviewed',min(start+32,len(items)),'/',len(items),flush=True)
for f in facts:
 if f.get('translation')!='machine-draft':continue
 f['es']['summary']=cache[f['en']['summary']];e=next(e for e in entries if e['id']==f['targetId']);f['en']['title']=e['title']['en']+' · '+f['sectionLabel']['en'];f['es']['title']=e['title']['es']+' · '+f['sectionLabel']['es'];f['context']['es']=cache[f['context']['en']]
for e in entries:
 if e.get('translation')!='machine-draft':continue
 e['description']['es']=[cache[x] for x in e['description']['en']]
 for sec in e['sections']:
  sec['paragraphs']['es']=[cache[x] for x in sec['paragraphs']['en']]
  for table in sec['tables']:
   for row in table['rows']:
    for c in row:
     if c['text']['en'] in cache:c['text']['es']=cache[c['text']['en']]
 for s in e['stats']:
  if s['value']['en'] in cache:s['value']['es']=cache[s['value']['en']]
(W/'entries.json').write_text(json.dumps(entries,ensure_ascii=False,separators=(',',':')));(W/'facts.json').write_text(json.dumps(facts,ensure_ascii=False,separators=(',',':')));print('Spanish review completed',flush=True)
