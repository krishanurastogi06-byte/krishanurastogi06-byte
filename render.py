#!/usr/bin/env python3
"""Render GitHub-profile SVGs from data/contributions.json and profile.json."""
import base64, calendar, datetime as dt, html, json, os, pathlib, subprocess, tempfile
from collections import defaultdict
from xml.sax.saxutils import escape

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'cards'; OUT.mkdir(exist_ok=True)
P=json.loads((ROOT/'profile.json').read_text())
D=json.loads((ROOT/'data/contributions.json').read_text())
STATIC=os.getenv('STATIC','0')=='1'
C=P['colors']; BG=C['background']; PANEL=C['surface']; FG=C['text']; MUTED=C['muted']; ACC=C['accent']; BORDER=C['border']
FONT='ProfileFont'; FONT_FACE=''
font_path=ROOT/P.get('font_file','assets/font.ttf')
if font_path.exists():
    glyphs=''.join(str(x) for x in [P['name'],P['tagline'],P['role'],P['links'],P.get('featured',[]), '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,;:!?&/+()-#@•—'])
    with tempfile.TemporaryDirectory() as tmp:
        dest=pathlib.Path(tmp)/'font.woff'
        try:
            subprocess.run(['pyftsubset',str(font_path),f'--output-file={dest}','--flavor=woff',f'--text={glyphs}','--layout-features=*'],check=True,capture_output=True)
            FONT_FACE=f"@font-face{{font-family:'{FONT}';src:url(data:font/woff;base64,{base64.b64encode(dest.read_bytes()).decode()}) format('woff');font-weight:100 900;}}"
        except (FileNotFoundError,subprocess.CalledProcessError):
            print('Font subsetting unavailable; falling back to system sans-serif')

def e(s): return escape(str(s),{'"':'&quot;'})
def txt(x,y,s,size=20,color=None,weight=500,extra=''):
    return f'<text x="{x}" y="{y}" fill="{color or FG}" font-size="{size}" font-weight="{weight}" {extra}>{e(s)}</text>'
def frame(w,h,content,delay=0):
    style=f'''<style>{FONT_FACE}text{{font-family:'{FONT}',Arial,sans-serif}} .reveal{{opacity:1;transform:translateY(0)}} .grow{{transform:scaleY(1)}} .draw{{stroke-dashoffset:0}}'''
    if not STATIC:
        style+=f''' .reveal{{opacity:0;animation:rise .8s cubic-bezier(.2,.8,.2,1) {delay}s both}} .grow{{transform:scaleY(0);transform-box:fill-box;transform-origin:bottom;animation:bar .75s ease-out {delay+.3}s both}} .draw{{animation:line 1.5s ease-out {delay+.2}s both}} @keyframes rise{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:translateY(0)}}}} @keyframes bar{{to{{transform:scaleY(1)}}}} @keyframes line{{to{{stroke-dashoffset:0}}}} @media(prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important}} .reveal{{opacity:1!important;transform:none!important}} .grow{{transform:none!important}} .draw{{stroke-dashoffset:0!important}}}}'''
    style+='</style>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">{style}<rect width="{w}" height="{h}" rx="22" fill="{BG}"/><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="21" fill="none" stroke="{BORDER}"/>{content}</svg>'
def save(name,w,h,content,delay): (OUT/name).write_text(frame(w,h,content,delay),encoding='utf8')

def header(label,w=1000): return txt(38,52,label.upper(),13,ACC,700,'letter-spacing="2.5"')
# hero
hero=header('hello, world')+f'<g class="reveal">{txt(38,132,P["name"],66,FG,800)}{txt(40,184,P["tagline"],23,MUTED,400)}{txt(40,239,P["role"],15,ACC,600)}</g>'
hero+=f'<circle cx="902" cy="125" r="62" fill="{PANEL}" stroke="{ACC}" stroke-width="2"/>'
portrait=ROOT/P.get('portrait','assets/portrait.png')
if portrait.is_file():
    mime='image/png' if portrait.suffix.lower()=='.png' else 'image/jpeg'
    data=base64.b64encode(portrait.read_bytes()).decode()
    hero+=f'<defs><clipPath id="avatar"><circle cx="902" cy="125" r="59"/></clipPath></defs><image x="843" y="66" width="118" height="118" clip-path="url(#avatar)" href="data:{mime};base64,{data}" preserveAspectRatio="xMidYMid slice"/>'
else: hero+=txt(875,139,'</>',27,ACC,700)
save('hero.svg',1000,280,hero,0)
# three individually linked tiles, links live in README HTML, not inside SVG
for i,item in enumerate(P['links'][:3]):
    label=item['label']; sub=item.get('subtitle','')
    body=f'<g class="reveal">{txt(25,48,f"0{i+1} / {label.upper()}",16,ACC,700)}{txt(25,90,sub[:32],14,MUTED)}{txt(280,48,"↗",26,ACC,700)}</g>'
    save(f'link-{i+1}.svg',320,116,body,.4+i*.13)
# normalize day data
rows=D.get('days',[])
counts={r['date']:int(r.get('count',0)) for r in rows}
today=dt.date.fromisoformat(D.get('generated_at',dt.date.today().isoformat())[:10]); start=today-dt.timedelta(days=364)
calendar_days=[start+dt.timedelta(days=i) for i in range(365)]
monthly=defaultdict(int)
for day in calendar_days: monthly[day.strftime('%Y-%m')]+=counts.get(day.isoformat(),0)
months=list(monthly.items()); maximum=max([v for _,v in months]+[1]); active=sum(counts.get(d.isoformat(),0)>0 for d in calendar_days)
peak=max(calendar_days,key=lambda d:counts.get(d.isoformat(),0)); peak_count=counts.get(peak.isoformat(),0)
streak=0
for d in reversed(calendar_days):
    if counts.get(d.isoformat(),0)>0: streak+=1
    elif d==today: continue
    else: break
metrics=header('contribution pulse')+f'<g class="reveal">{txt(38,112,str(streak),43,FG,800)}{txt(38,138,"CURRENT STREAK",11,MUTED,700)}{txt(300,112,str(active),43,FG,800)}{txt(300,138,"ACTIVE DAYS",11,MUTED,700)}{txt(555,112,str(peak_count),43,FG,800)}{txt(555,138,"BUSIEST DAY · "+peak.strftime("%d %b %Y"),11,MUTED,700)}</g>'
chart_top=194; base=344
for i,(m,v) in enumerate(months):
    x=44+i*76; height=round(128*v/maximum)
    metrics+=f'<rect x="{x}" y="{base-height}" width="42" height="{max(height,2)}" rx="5" fill="{ACC}" class="grow"/>'
    metrics+=txt(x,365,dt.datetime.strptime(m,'%Y-%m').strftime('%b'),11,MUTED,500)
save('activity.svg',1000,400,metrics,1.0)
# repo cards
for i,repo in enumerate(P.get('featured',[])):
    name=repo['name']; desc=repo.get('description','')
    body=header(f'featured project / {i+1:02d}')+f'<g class="reveal">{txt(38,111,name[:38],32,FG,750)}{txt(39,151,desc[:94],17,MUTED)}{txt(39,202,repo.get("language","PROJECT"),13,ACC,700)}{txt(915,203,"↗",27,ACC,700)}</g>'
    save(f'repo-{i+1}.svg',1000,236,body,1.65+i*.22)
# 53-week contribution heatmap
heat=header('365 days of building')
cell=13; gap=4; x0=49; y0=94
sunday=start-dt.timedelta(days=(start.weekday()+1)%7)
for day in calendar_days:
    weeks=(day-sunday).days//7; dow=(day.weekday()+1)%7; count=counts.get(day.isoformat(),0)
    intensity=min(4,(1 if count else 0)+(count>=3)+(count>=6)+(count>=10))
    color=[PANEL,C.get('heat1','#25463d'),C.get('heat2','#327e67'),C.get('heat3','#49b58b'),ACC][intensity]
    heat+=f'<rect x="{x0+weeks*(cell+gap)}" y="{y0+dow*(cell+gap)}" width="{cell}" height="{cell}" rx="3" fill="{color}"><title>{e(day.isoformat())}: {count} contributions</title></rect>'
heat+=txt(49,250,f'{sum(counts.get(d.isoformat(),0) for d in calendar_days):,} contributions in the last 365 days',15,MUTED)
save('graph.svg',1000,282,heat,2.1+len(P.get('featured',[]))*.22)
# README
parts=['<div align="center">','<img src="cards/hero.svg" alt="Profile introduction" width="100%" />','<p>']
for i,item in enumerate(P['links'][:3]):
    parts.append(f'<a href="{html.escape(item["url"],quote=True)}"><img src="cards/link-{i+1}.svg" alt="{html.escape(item["label"],quote=True)}" width="32.5%" /></a>')
parts+=['</p>','<img src="cards/activity.svg" alt="Contribution activity and statistics" width="100%" />']
for i,repo in enumerate(P.get('featured',[])):
    parts.append(f'<a href="{html.escape(repo["url"],quote=True)}"><img src="cards/repo-{i+1}.svg" alt="{html.escape(repo["name"],quote=True)}" width="100%" /></a>')
parts+=['<img src="cards/graph.svg" alt="Contribution heatmap for the last 365 days" width="100%" />','</div>']
(ROOT/'README.md').write_text('\n\n'.join(parts)+'\n',encoding='utf8')
print('Rendered',len(list(OUT.glob('*.svg'))),'SVG cards. STATIC=',STATIC)
