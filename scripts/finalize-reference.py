"""Add a separately sourced 2026 mob, retain canonical links, and write coverage."""
import json,pathlib,hashlib,subprocess,io,re
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1];W=ROOT/'web';entries=json.load(open(W/'entries.json'));facts=json.load(open(W/'facts.json'))
# This mob postdates the Wiki archive. Claims below are limited to the Java 26.2 release notes.
source='https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2';wiki='https://minecraft.wiki/w/Sulfur_Cube';imageurl='https://www.minecraft.net/content/dam/minecraftnet/games/minecraft/background-images/SGD-26_Media-Block-B_realms-offer-cube_160x80_2x.png';path=pathlib.Path('/tmp/sulfur-cube.png')
if not path.exists():subprocess.run(['curl','--fail','--silent','--location','--max-time','30','--output',str(path),imageurl],check=True)
im=Image.open(path).convert('RGBA');im.thumbnail((360,360));im.save(W/'reference-images/sulfur-cube.webp','WEBP',quality=85)
image={'src':'/reference-images/sulfur-cube.webp','originalUrl':imageurl,'sourcePage':'https://www.minecraft.net/en-us/updates/chaos-cubed-drop','credit':'Mojang Studios / Microsoft · Minecraft.net','type':'official-game-image','alt':{'en':'Sulfur Cube','es':'Cubo de azufre'}}
rows=[
('Sulfur cubes spawn in sulfur caves.','Los cubos de azufre aparecen en cuevas de azufre.'),
('Absorbing a block disables a sulfur cube’s normal AI.','Al absorber un bloque, se desactiva la inteligencia artificial normal del cubo de azufre.'),
('A sulfur cube with an absorbed block can be punched and pushed as a physical object.','Un cubo de azufre que absorbió un bloque se puede golpear y empujar como un objeto físico.'),
('Shears remove a sulfur cube’s absorbed block and re-enable its AI.','Las tijeras retiran el bloque absorbido y reactivan su inteligencia artificial.'),
('Sulfur cubes follow players holding a block they can absorb.','Los cubos de azufre siguen a jugadores que llevan un bloque que pueden absorber.'),
('Sulfur cubes can move toward dropped block items and absorb them.','Los cubos de azufre pueden acercarse a bloques que están como objetos en el suelo y absorberlos.'),
('Killing a large sulfur cube splits it into two smaller sulfur cubes.','Al matar un cubo de azufre grande, se divide en dos cubos más pequeños.'),
('Small sulfur cubes grow when fed slimeballs.','Los cubos de azufre pequeños crecen al alimentarlos con bolas de slime.'),
('An empty bucket can pick up a large sulfur cube.','Un cubo vacío permite recoger un cubo de azufre grande.'),
('Sulfur cubes cannot enter boats, but they can ride minecarts.','Los cubos de azufre no pueden entrar en botes, pero sí pueden viajar en vagonetas.')]
e={'id':'sulfur-cube','kind':'mob','scope':'java-26.2-changelog','title':{'en':'Sulfur Cube','es':'Cubo de azufre'},'description':{'en':['A block-absorbing creature introduced in the Chaos Cubed release. The block it holds changes its physical behavior.'],'es':['Una criatura que absorbe bloques, introducida en Chaos Cubed. El bloque que lleva cambia su comportamiento físico.']},'source':wiki,'supplementalSource':source,'archive':None,'snapshot':'2026-06-16','image':image,'translation':'editorial','stats':[{'label':{'en':'Documented edition','es':'Edición documentada'},'value':{'en':'Java Edition 26.2','es':'Java Edition 26.2'}}],'sections':[{'id':'behavior','title':{'en':'Behavior','es':'Comportamiento'},'paragraphs':{'en':['Different absorbed blocks create different physical archetypes. These release notes describe changes to speed, bounce, friction and buoyancy.'],'es':['Los bloques absorbidos producen distintos tipos de comportamiento físico. Las notas de esta versión describen cambios en velocidad, rebote, fricción y flotación.']},'tables':[]},{'id':'drops','title':{'en':'Death & drops','es':'Muerte y botín'},'paragraphs':{'en':['The release notes describe splitting into two smaller cubes when killed. They do not provide a complete item-drop table here.'],'es':['Las notas describen que se divide en dos cubos pequeños al morir. No ofrecen aquí una tabla completa de objetos que suelta.']},'tables':[]},{'id':'history','title':{'en':'Selected history','es':'Historia seleccionada'},'paragraphs':{'en':['Introduced in Java Edition 26.2, released on June 16, 2026.'],'es':['Introducido en Java Edition 26.2, publicada el 16 de junio de 2026.']},'tables':[]}],'factIds':[],'related':['slimeball','shears','bucket']}
killer=next((x for x in entries if x['id']=='killer-bunny'),None)
if killer and not any(x['id']=='history' for x in killer['sections']):
 killer['sections'].append({'id':'history','title':{'en':'Selected history','es':'Historia seleccionada'},'paragraphs':{'en':['The hostile rabbit variant was revealed as the Killer Rabbit of Caerbannog on July 1, 2014. It was later renamed the Killer Bunny and removed from natural spawning.'],'es':['La variante hostil se presentó como Killer Rabbit of Caerbannog el 1 de julio de 2014. Después se cambió su nombre a Killer Bunny y se eliminó su aparición natural.']},'tables':[]})
entries=[x for x in entries if x['id']!='sulfur-cube'];facts=[x for x in facts if x.get('targetId')!='sulfur-cube']
for i,(en,es) in enumerate(rows):
 fid='discovery-sulfur-cube-'+str(i+1);e['factIds'].append(fid);facts.append({'id':fid,'targetId':e['id'],'targetSection':'facts','category':'mobs','topics':['mobs','survival','technical'],'tags':['sulfur-cube','sulfur-caves','physics'],'image':image,'source':wiki,'supplementalSource':source,'sourceSnapshot':'2026-06-16','status':'release-notes','versionRanges':[{'edition':'java','mode':'exact','from':'26.2','to':'','verified':True}],'versionNotes':{'en':'Documented by the Java Edition 26.2 release notes; no broader version range is claimed.','es':'Documentado en las notas de Java Edition 26.2; no se afirma un rango más amplio.'},'context':{'en':en,'es':es},'sectionLabel':{'en':'Java 26.2 mechanics','es':'Mecánica de Java 26.2'},'en':{'title':'Sulfur Cube · '+str(i+1),'summary':en,'body':[]},'es':{'title':'Cubo de azufre · '+str(i+1),'summary':es,'body':[]},'imported':True})
entries.append(e);byid={x['id']:x for x in entries};e['related']=[id for id in e['related'] if id in byid]
# Keep fallback images honest. A missing item portrait uses a text placeholder, never a random mob.
for f in facts:
 if f['id']=='bed':f['targetId']='bed';f['image']=byid['bed']['image']
# All source entities get language-independent tags, including command-only and Education entries.
tax=json.load(open(W/'taxonomy.json'));ids={t['id'] for t in tax['tags']}
for item in entries:
 if item['kind']=='mob' and item['id'] not in ids:tax['tags'].append({'id':item['id'],'en':item['title']['en'],'es':item['title']['es'],'group':'mobs'})
for id,en,es in [('sulfur-caves','Sulfur caves','Cuevas de azufre'),('physics','Physics','Física')]:
 if id not in ids:tax['tags'].append({'id':id,'en':en,'es':es,'group':'mechanics'})
for e in entries:e['related']=[id for id in e.get('related',[]) if id in byid]
for e in entries:
 if e['description']['en']:continue
 canonical={'tamed-wolf':'wolf','shear':'shears','wet-sponge':'sponge','tag':'name-tag','verdant-froglight':'froglight','ochre-froglight':'froglight','pearlescent-froglight':'froglight'}.get(e['id']);target=byid.get(canonical)
 if target:e['description']={k:list(v) for k,v in target['description'].items()};e['canonicalId']=canonical
 elif e['id']=='lightning':e['description']={'en':['Lightning is an electrical weather event during thunderstorms. It can affect creatures and blocks when it strikes.'],'es':['Los rayos son fenómenos eléctricos que ocurren durante las tormentas. Al caer, pueden afectar a criaturas y bloques.']}
coverage={'sourceSnapshot':'2025-11-05','supplementalRelease':'2026-06-16','mobPages':sum(e['kind']=='mob' for e in entries),'referencePages':len(entries),'facts':len(facts),'atLeastTen':sum(e['kind']=='mob' and len(e['factIds'])>=10 for e in entries),'belowTen':[{'id':e['id'],'count':len(e['factIds'])} for e in entries if e['kind']=='mob' and len(e['factIds'])<10]}
for name,data in [('entries.json',entries),('facts.json',facts),('taxonomy.json',tax),('coverage.json',coverage)]: (W/name).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
print(json.dumps(coverage,indent=2))
