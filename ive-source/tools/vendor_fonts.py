"""Download the site's OFL-licensed Google Fonts for self-contained hosting."""
from pathlib import Path
import re,requests
out=Path(__file__).resolve().parents[1]/'site/assets/fonts';out.mkdir(parents=True,exist_ok=True)
url='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;450;500;550;600;650;700&family=Newsreader:ital,wght@0,400;0,500;1,400;1,500&display=swap'
r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 Chrome/124.0.0.0 Safari/537.36'},timeout=30);r.raise_for_status()
blocks=re.findall(r'/\* latin \*/\s*(@font-face\s*\{.*?\})',r.text,re.S)
if not blocks:blocks=re.findall(r'@font-face\s*\{.*?\}',r.text,re.S)
assert blocks,'No Latin font CSS found'
files={};css=[]
for block in blocks:
 for remote in re.findall(r'url\((https://[^)]+)\)',block):
  if remote not in files:
   name=f'font-{len(files)}.woff2';response=requests.get(remote,timeout=30);response.raise_for_status();(out/name).write_bytes(response.content);files[remote]=name
  block=block.replace(remote,files[remote])
 css.append(block)
(out/'fonts.css').write_text('\n'.join(css))
for family in ['dmsans','newsreader']:
 response=requests.get(f'https://raw.githubusercontent.com/google/fonts/main/ofl/{family}/OFL.txt',timeout=30);response.raise_for_status();(out/f'{family}-LICENSE.txt').write_text(response.text)
print('Vendored',len(files),'font assets and their licenses.')
