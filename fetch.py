#!/usr/bin/env python3
"""Fetch real contribution days via GitHub GraphQL; never invent activity."""
import datetime as dt, json, os, pathlib, urllib.request
root=pathlib.Path(__file__).resolve().parent
username=os.getenv('GH_USER','krishanurastogi06-byte'); token=os.getenv('GH_TOKEN')
if not token: raise SystemExit('Set GH_TOKEN (Actions secret PROFILE_TOKEN) to fetch contributions')
now=dt.datetime.now(dt.timezone.utc); begin=now-dt.timedelta(days=364)
query='''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
payload=json.dumps({'query':query,'variables':{'login':username,'from':begin.isoformat(),'to':now.isoformat()}}).encode()
req=urllib.request.Request('https://api.github.com/graphql',data=payload,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'profile-card-renderer'})
with urllib.request.urlopen(req,timeout=30) as res: data=json.load(res)
if data.get('errors') or not data.get('data',{}).get('user'): raise RuntimeError(str(data.get('errors', 'User not found')))
weeks=data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
days=[{'date':d['date'],'count':d['contributionCount']} for w in weeks for d in w['contributionDays']]
(root/'data/contributions.json').write_text(json.dumps({'generated_at':now.date().isoformat(),'days':days},indent=2)+'\n')
print('Fetched',len(days),'days')
