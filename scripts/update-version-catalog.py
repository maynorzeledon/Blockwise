"""Refresh the attributed version picker. Requires Python 3 and curl; no API key.
Archive indexes are dated. Missing versions remain enterable without inventing them.
"""
from pathlib import Path
from html.parser import HTMLParser
import json,re,subprocess,urllib.parse,concurrent.futures,tempfile
ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'web/versions.json'
v=json.loads(CATALOG.read_text())
class Links(HTMLParser):
 def __init__(self,text):
  super().__init__();self.links=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='a' and d.get('href'):self.links.append(urllib.parse.unquote(d['href'].split('#')[0]).removeprefix('./'))
base='https://wiki.ronlab.site/content/minecraftwiki_en_all_maxi_2025-11/'
cache=Path(tempfile.gettempdir())/'blockwise-version-index';cache.mkdir(exist_ok=True)
prefixes=[(urllib.parse.unquote(e['source'].split('/w/')[1]),e['id']) for e in v['editions'] if e['id']!='other']
pages={'Version_history','Legacy_Console_Edition_version_history','Pocket_Edition_Alpha','Pocket_Edition_Alpha_version_history','Bedrock_Edition_Alpha','Java_Edition_version_history/Development_versions','Bedrock_Edition_version_history/Development_versions','Pi_Edition'}
for prefix,id in prefixes:pages.update([prefix,prefix+'_version_history'])
def fetch(title):
 p=cache/(title.replace('/','__')+'.html')
 if not p.exists():subprocess.run(['curl','--max-time','20','-fsSL',base+urllib.parse.quote(title,safe='/'),'-o',str(p)],capture_output=True)
 return title,Links(p.read_text() if p.exists() else '').links
results=list(concurrent.futures.ThreadPoolExecutor(max_workers=12).map(fetch,sorted(pages)))
extra=set(h for _,links in results for h in links if 'version_history/' in h and not h.startswith(('http','../')))
results+=list(concurrent.futures.ThreadPoolExecutor(max_workers=12).map(fetch,sorted(extra-pages)))
records={e['id']:{r['id']:r for r in e['versions']} for e in v['editions']}
def channel(label):
 l=label.lower()
 return 'snapshot' if re.search(r'\d\dw\d\d',l) else 'preview' if 'preview' in l else 'beta' if 'beta' in l else 'alpha' if 'alpha' in l else 'pre-release' if re.search(r'pre[- ]?release|pre\d',l) else 'release-candidate' if re.search(r'rc\d|release.candidate',l) else 'historical' if re.search(r'classic|indev|infdev|rd-|c0\.|a1\.|b1\.',l) else 'release'
for _,links in results:
 for title in links:
  for prefix,id in prefixes:
   if not title.startswith((prefix+'_',prefix+'/')):continue
   label=title[len(prefix)+1:].replace('_',' ')
   if '/' in label or len(label)>60 or not re.match(r'(?:\d|v\d|[abc]\d|rd-|TU\d|CU\d|Patch |Update |Preview |beta |Beta |Alpha |alpha |Indev |Infdev |Classic |Pre-Classic |Build )',label):break
   if re.search(r'guide|history|hardware|server|development|unused|removed|mention|planned|protocol|sound|terrain',label,re.I):break
   records[id][label]={'id':label,'channel':channel(label),'source':'https://minecraft.wiki/w/'+urllib.parse.quote(title,safe='/')};break
# Current launcher index, with release timestamps for chronological presentation.
r=subprocess.run(['curl','--max-time','20','-fsSL','https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'],capture_output=True,text=True)
try:
 for item in json.loads(r.stdout)['versions']:
  label=item['id'];records['java'][label]={'id':label,'channel':item['type'],'date':item['releaseTime'],'source':'https://minecraft.wiki/w/Java_Edition_'+urllib.parse.quote(label),'manifest':item['url']}
except (ValueError,KeyError):pass
for e in v['editions']:e['versions']=sorted(records[e['id']].values(),key=lambda r:(r.get('date',''),r['id']),reverse=True)
v['indexSources']=['https://minecraft.wiki/w/'+urllib.parse.quote(title,safe='/') for title,links in results if links]
CATALOG.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')))
print({e['id']:len(e['versions']) for e in v['editions']})
