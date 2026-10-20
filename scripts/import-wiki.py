"""Build offline reference entries from a fixed, attributed Wiki archive.
Requires beautifulsoup4 + Pillow. Optional local translation runs separately.
Never treat the archive date as a current game-version verification.
"""
import pathlib,json,re,urllib.parse,subprocess,concurrent.futures,io
from bs4 import BeautifulSoup
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1];WEB=ROOT/'web';RAW=pathlib.Path('/tmp/blockwise-wiki');BASE='https://wiki.ronlab.site/content/minecraftwiki_en_all_maxi_2025-11/';SNAPSHOT='2025-11-05';(WEB/'reference-images').mkdir(exist_ok=True)
source=json.load(open('/tmp/blockwise-mob-sources.json'));tax=json.load(open(WEB/'taxonomy.json'));existing={a['id']:a for a in json.load(open(WEB/'media-catalog.json'))['assets']};eslang=json.load(open('/tmp/es_es.json'))
def clean(n):
 if isinstance(n,str):return n
 text=n.get_text(' ',strip=True);text=re.sub(r'\s+',' ',text).replace('\u200b','').replace('‌','');text=re.sub(r'\s+([,.;:!?])',r'\1',text);text=text.replace('[ JE only ]','[Java Edition only]').replace('[ BE only ]','[Bedrock Edition only]');return text.strip()
def fetch(url,path):
 if path.exists():return True
 return subprocess.run(['curl','--fail','--silent','--location','--retry','1','--max-time','25','--output',str(path),url],capture_output=True).returncode==0
def title_id(title):return re.sub('[^a-z0-9]+','-',title.lower()).strip('-')
def ename(title):
 key=title.lower().replace(' ','_');return eslang.get('entity.minecraft.'+key,eslang.get('item.minecraft.'+key,eslang.get('block.minecraft.'+key,title)))
def table(n):
 rows=[]
 for row in n.find_all('tr'):
  cells=row.find_all(['th','td'],recursive=False)
  if cells:rows.append([{'text':clean(c),'header':c.name=='th','colspan':int(c.get('colspan',1)),'rowspan':int(c.get('rowspan',1))} for c in cells])
 return rows

def parse(id,title,kind='mob'):
 slug=title.replace(' ','_');path=RAW/(id+'.html')
 if not fetch(BASE+urllib.parse.quote(slug),path):return None
 soup=BeautifulSoup(path.read_text(),'html.parser');main=soup.select_one('.mw-parser-output') or soup
 for n in main.select('script,style,.mw-editsection,.reference,.navbox,.toc,.hatnote,.references,.droptable-references,.infobox-json'):n.decompose()
 info=main.select_one('.infobox');image=None
 if info:
  im=info.find('img')
  if im and im.get('src'):
   imageurl=urllib.parse.urljoin(BASE+slug,im['src']);tmp=RAW/(id+'.image')
   if fetch(imageurl,tmp):
    try:
     img=Image.open(tmp).convert('RGBA');img.thumbnail((360,360));out=WEB/'reference-images'/(id+'.webp');img.save(out,'WEBP',quality=83,method=4);image={'src':'/reference-images/'+id+'.webp','originalUrl':imageurl,'sourcePage':'https://minecraft.wiki/w/'+slug,'credit':'Minecraft Wiki contributors / Mojang Studios · '+SNAPSHOT,'type':'wiki-game-render','alt':{'en':title,'es':ename(title)}}
    except Exception:pass
 if not image and id in existing:image=existing[id]
 if not image:image={'src':None,'credit':'Image not yet verified','alt':{'en':title,'es':ename(title)}}
 blocks=[];section='Overview';sub='';edition='';seen_tables=set();stats=[]
 if info:
  for r in info.find_all('tr'):
   cells=r.find_all(['th','td'],recursive=False)
   if len(cells)==2:stats.append({'label':clean(cells[0]),'value':clean(cells[1])})
 keep=['Overview','Spawning','Behavior','Drops','Trading','Bartering','Usage','Breeding','Taming','Healing','Development','History','Trivia','Professions','Schedules','Transformation','Transportation','Riding','Variants']
 for n in main.children:
  if not getattr(n,'name',None):continue
  if n.name=='h2':section=clean(n);sub='';edition=''
  elif n.name=='h3':sub=clean(n)
  elif section in keep or (kind=='item' and section in ['Obtaining','Crafting','Natural generation','Mob loot','Achievements']):
   if n.name in ['p','ul','ol']:
    text=clean(n)
    if not text:continue
    if text in ['Java Edition:','Bedrock Edition:']:edition=text[:-1];continue
    # Drop lists: keep individual coherent bullets.
    elements=n.find_all('li',recursive=False) if n.name in ['ul','ol'] else [n]
    for el in elements:
     text=clean(el)
     if len(text)>20 and not re.search(r'\[\s*(verify|more information needed|needs testing|citation needed)',text,re.I):blocks.append({'section':section,'subheading':sub,'edition':edition,'kind':'text','text':text,'links':[{ 'title':a.get('title',clean(a)),'href':a['href']} for a in el.find_all('a',href=True) if not a['href'].startswith(('http','#'))]})
   # First decimal loot table per edition; fractional/percentage duplicates are presentation alternatives.
   tables=[n] if n.name=='table' else (n.find_all('table',class_='wikitable')[:1] if n.name=='div' and 'droptable-tabber' in n.get('class',[]) else [])
   if section in ['Drops','Trading','Bartering','History','Obtaining','Crafting']:
    for tb in tables:
     rows=table(tb);key=json.dumps(rows)
     if key in seen_tables:continue
     seen_tables.add(key);blocks.append({'section':section,'subheading':sub,'edition':edition,'kind':'table','rows':rows,'links':[{'title':a.get('title',clean(a)),'href':a['href']} for a in tb.find_all('a',href=True) if not a['href'].startswith(('http','#'))]})
 intro=[b['text'] for b in blocks if b['section']=='Overview' and b['kind']=='text'][:2]
 # Select concise, source-contained claims. Avoid uncertain, obsolete trivia and fragments.
 candidates=[]
 for b in blocks:
  if b['kind']!='text' or b['section'] not in ['Behavior','Spawning','Drops','Trading','Bartering','Usage','Breeding','Taming','Healing','Transformation','Transportation','Riding','Variants','Development']:continue
  paragraph=b['text']
  if any(x in paragraph.lower() for x in ['[ until','upcoming','planned','[ verify','citation needed','more information needed']):continue
  sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z])',paragraph)
  for sent in sentences:
   if not (35<=len(sent)<=240 and 6<=len(sent.split())<=42):continue
   if not sent.endswith(('.', '!', '?')) or re.search(r'\b(See also|Main article|For other|For more|This article|The following|shown below|shown above|listed below|these values|as follows|in the table|For example)\b',sent,re.I):continue
   if re.match(r'(Although |Occasionally,|Furthermore,|In this state|The variant |Any picked-up|Any naturally spawned|The pregnant frog)',sent):continue
   if sent.startswith(('This ','These ','Those ','However,','Otherwise,','Additionally,','Also,','For ','Because ')) or re.search(r'\b(they|them|it|its|their)\b',sent.split(' ',1)[0],re.I):continue
   if '=' in sent or '/' in sent or 'experience points' in sent or ' XP' in sent:continue
   # Avoid context loss where an earlier sentence establishes an edition or a condition.
   if len(sentences)>1 and sent!=sentences[0] and re.search(r'In (Java|Bedrock) Edition|only|unless|except|if ',paragraph,re.I):continue
   candidates.append({'text':sent,'context':paragraph,'section':b['section'],'subheading':b['subheading'],'edition':b['edition']})
 # Round-robin source sections ensures mechanics/behavior are not displaced by ten spawn variants.
 groups={sec:[c for c in candidates if c['section']==sec] for sec in ['Behavior','Usage','Taming','Breeding','Spawning','Drops','Trading','Bartering','Transformation','Riding','Development','Variants']};chosen=[]
 while len(chosen)<10 and any(groups.values()):
  for sec,group in groups.items():
   if not group or len(chosen)>=10:continue
   c=group.pop(0);words=set(re.findall('[a-z]+',c['text'].lower()))
   if any(len(words&set(re.findall('[a-z]+',x['text'].lower())))/max(1,len(words|set(re.findall('[a-z]+',x['text'].lower()))))>.64 for x in chosen):continue
   chosen.append(c)
 return {'id':id,'kind':kind,'title':{'en':title,'es':ename(title)},'source':'https://minecraft.wiki/w/'+slug,'archive':BASE+slug,'snapshot':SNAPSHOT,'description':{'en':intro,'es':[]},'image':image,'stats':stats,'blocks':blocks,'facts':chosen,'translation':'machine-draft'}

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:entries=[x for x in pool.map(lambda m:parse(m['id'],m.get('title',m['id'].title())),[m for m in source if not m.get('missing')]) if x]
# Include real drop/trade resources as neutral reference pages, not discovery-card placeholders.
resource_titles=['Gunpowder','TNT','Emerald','Music Disc','Saddle','Lead','Shears','Flint and Steel','Ender Pearl','Blaze Rod','Slimeball','String','Bone','Arrow','Rotten Flesh','Leather','Feather','Wool','Milk Bucket','Gold Nugget','Gold Ingot','Iron Ingot','Copper Ingot','Prismarine Shard','Prismarine Crystals','Ink Sac','Glow Ink Sac','Nautilus Shell','Nether Star','Totem of Undying','Phantom Membrane','Rabbit Foot','Rabbit Hide','Rabbit','Shulker Shell','Spider Eye','Fermented Spider Eye','Magma Cream','Breeze Rod','Armadillo Scute','Turtle Scute','Scute','Wind Charge','Experience','Trading','Bartering','Carved Pumpkin','Honey Block','Sponge','Bed','Pufferfish','Cod','Salmon','Tropical Fish','Wheat','Carrot','Golden Carrot','Raw Beef','Raw Porkchop','Raw Chicken','Raw Mutton','Amethyst Shard','Name Tag','Golden Apple','Potion of Weakness','Shield','Lightning','Firework Rocket','Creeper Head','Snowball','Bucket of Axolotl','Bucket of Tadpole','Froglight','Potato','Poisonous Potato','Bamboo','Sweet Berries','Glow Berries','Allium','Dandelion','Wither Rose','Torchflower Seeds','Pitcher Pod','Ominous Bottle']
# Extra resources are collected only when linked by a real drop/trade table.
for e in entries:
 for b in e['blocks']:
  if b['section'] in ['Drops','Trading','Bartering']:
   for a in b['links']:
    title=a['title']
    if title and ':' not in title and not any(x in title for x in ['.png','Edition','Looting','File','Tutorial']) and len(title)<45:resource_titles.append(title)
known={e['id'] for e in entries};resources=[]
for title in dict.fromkeys(resource_titles):
 id=title_id(title)
 if id not in known and id not in [x[0] for x in resources]:resources.append((id,title))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:items=[x for x in pool.map(lambda pair:parse(pair[0],pair[1],'item'),resources[:155]) if x]
allentries=entries+items;(pathlib.Path('/tmp/blockwise-entries-en.json')).write_text(json.dumps(allentries,ensure_ascii=False,indent=2));print(json.dumps({'mobs':len(entries),'items':len(items),'facts':sum(len(e['facts']) for e in entries),'short':[{'id':e['id'],'facts':len(e['facts'])} for e in entries if len(e['facts'])<10]}))
