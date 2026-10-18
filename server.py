#!/usr/bin/env python3
"""INDOMIEVERSE backend (prototype, stdlib only). Run: python server.py  ->  http://127.0.0.1:8787
Env: PORT, HOST, ADMIN_EMAILS=a@x.com,b@y.com. AI provider is set by admins in the Account page (builtin | lmstudio | gemini)."""
import json,os,re,sqlite3,hashlib,secrets,urllib.request
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs
ROOT=Path(__file__).resolve().parent;DB=ROOT/'database'/'indomieverse.db'
HOST=os.environ.get('HOST','127.0.0.1');PORT=int(os.environ.get('PORT','8787'))
ADMINS={e.strip().lower() for e in os.environ.get('ADMIN_EMAILS','').split(',') if e.strip()} | {'brilyannf@gmail.com'}
CODES={'NOODLE-NUSA-2026':'nusantara','MYSTERY-GOLD-77':'secret','PEDAS-BOOST-10':'pedas','ORIGINAL-WARM-01':'original'}
START={'original':(4,62),'pedas':(2,30)}
P={'original':('Original, the Loyal Companion','friendly, humorous, warm, approachable; casual chat, comfort, creative food suggestions',
 [('joke|funny|lucu','Why did the noodle blush? It saw the sauce packet. I will be here all week!'),('cook|eat|masak|makan|lapar','Soft egg on top, crushed chips on the side, a squeeze of lime. Comfort has a recipe.'),('sad|sedih|capek|tired|rough','Come sit. A warm bowl and a friend who listens gets close to fixing it. Tell me more.')],
 ['Haha, I like the way you think. Tell me more!','You always bring the good stuff. What else is on your mind?']),
 'pedas':('Agent Pedas, the Fiery Challenger','bold, competitive, outspoken, playful; challenges, witty banter',
 [('challenge|tantang|dare','Challenge accepted. Three bites, no water, say your name out loud. Ready, rookie?'),('spic|pedas|chili|cabai','Too spicy is just a story you tell after finishing the bowl. Add one more chili.'),('rate|nyali|brave|takut','Courage score: 6 out of 10. Ten if you finish without blinking.')],
 ['Is that all you have got? Go bolder!','Not bad. Now say it like you mean it.']),
 'nusantara':('Nusantara, the Taste Explorer','curious, knowledgeable, adventurous, welcoming; regional food stories and flavour exploration',
 [('story|cerita|daerah|region','In Medan, a bowl often meets a fried egg and sweet-spicy sambal. Every street swears its recipe is the original.'),('sambal|pulau|island','Ask ten cooks, get ten answers. I lean towards Manado dabu-dabu for fresh, bright heat.'),('explor|jelajah|where|mana','Start in Sumatra for bold spice, hop to Java for sweet soy, finish in Sulawesi for fresh chili.')],
 ['Good question! Every region answers it differently. Want a story?','I have a page in my notebook about that. Ask me about a region.']),
 'secret':('Secret Recipe, the Mysterious Collector','intelligent, mysterious, secretive; riddles, hidden stories, special missions',
 [('riddle|teka','I am long, I am curled, I rest in hot water, sealed in a packet. What am I?'),('jar|secret|rahasia','Some jars hold flavours that no longer exist. Earn the key first.'),('mission|misi|quest','Your mission: open every character profile before the day ends. Collectors notice what others overlook.')],
 ['Interesting. But you have not asked the right question yet.','Hmm. I will answer when you have earned it.'])}
STAGES=[(30,'Stranger'),(50,'Acquaintance'),(70,'Friend'),(90,'Close Friend'),(101,'Best Friend')]
POS=re.compile(r'terima kasih|makasih|thanks|thank you|suka|love|keren|hebat|enak|sayang|tolong|please',re.I)
NEG=re.compile(r'bodoh|bego|stupid|idiot|benci|hate|jelek|sampah|diam|shut up',re.I)
def db():
    DB.parent.mkdir(exist_ok=True);c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
    with db() as c:c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,salt TEXT,hash TEXT,role TEXT DEFAULT 'user',flags TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS auth(th TEXT PRIMARY KEY,uid INT);CREATE TABLE IF NOT EXISTS owned(uid INT,ch TEXT,lv INT,xp INT,PRIMARY KEY(uid,ch));
CREATE TABLE IF NOT EXISTS used(uid INT,code TEXT,PRIMARY KEY(uid,code));CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY,uid INT,ch TEXT,title TEXT);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,sid INT,sender TEXT,text TEXT);CREATE TABLE IF NOT EXISTS stats(uid INT,ch TEXT,a INT,t INT,b INT,PRIMARY KEY(uid,ch));
CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT);''')
def hp(pw,salt):return hashlib.pbkdf2_hmac('sha256',pw.encode(),bytes.fromhex(salt),200000).hex()
def th(t):return hashlib.sha256(t.encode()).hexdigest()
def settings():
    s={'provider':'builtin','lm_url':'http://localhost:1234/v1','lm_model':'','gm_model':'gemini-2.5-flash','gm_key':''}
    with db() as c:s.update({r['k']:r['v'] for r in c.execute('SELECT * FROM settings')})
    return s
def post(url,payload,headers=None):
    r=urllib.request.Request(url,json.dumps(payload).encode(),{'Content-Type':'application/json',**(headers or {})})
    return json.loads(urllib.request.urlopen(r,timeout=40).read() or b'{}')
def stage(a):return next(n for lim,n in STAGES if a<lim)
def mood(a):return 'Delighted' if a>=80 else 'Warm' if a>=55 else 'Neutral' if a>=35 else 'Upset'
def builtin(ch,msg,n):
    for pat,rep in P[ch][2]:
        if re.search(pat,msg,re.I):return rep
    d=P[ch][3];return d[n%len(d)]
def ai_reply(ch,hist,msg,stg):
    s=settings();sysm=(f"You are {P[ch][0]}, a fictional collectible character in INDOMIEVERSE, a concept prototype (not an official Indomie product). Personality: {P[ch][1]}. "
      f"Reply in the user's language in 1-3 short sentences, stay in character, never claim to be a real person or official spokesperson. Your relationship stage with the user: {stg}.")
    m=[{'role':'system','content':sysm}]+hist+[{'role':'user','content':msg}]
    try:
        if s['provider']=='lmstudio':
            d=post(s['lm_url'].rstrip('/')+'/chat/completions',{'model':s['lm_model'] or 'local-model','temperature':.85,'max_tokens':300,'messages':m})
            return d['choices'][0]['message']['content'].strip(),'ai'
        if s['provider']=='gemini' and s['gm_key']:
            con=[{'role':'model' if x['role']=='assistant' else 'user','parts':[{'text':x['content']}]} for x in m[1:]]
            d=post(f"https://generativelanguage.googleapis.com/v1beta/models/{s['gm_model']}:generateContent",{'contents':con,'systemInstruction':{'parts':[{'text':sysm}]},'generationConfig':{'temperature':.85,'maxOutputTokens':300}},{'x-goog-api-key':s['gm_key']})
            return ''.join(p.get('text','') for p in d['candidates'][0]['content']['parts']).strip(),'ai'
    except Exception as e:
        print('[ai] failed:',e);return builtin(ch,msg,len(hist)),'fallback'
    return builtin(ch,msg,len(hist)),'builtin'
class H(SimpleHTTPRequestHandler):
    def __init__(s,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
    def js(s,o,code=200,cookie=None):
        d=json.dumps(o).encode();s.send_response(code);s.send_header('Content-Type','application/json; charset=utf-8')
        if cookie:s.send_header('Set-Cookie',cookie)
        s.send_header('Content-Length',str(len(d)));s.end_headers();s.wfile.write(d)
    def err(s,m,code=400):s.js({'ok':False,'error':m},code)
    def user(s):
        t=SimpleCookie(s.headers.get('Cookie','')).get('iv_session')
        if not t:return None
        with db() as c:return c.execute('SELECT u.* FROM users u JOIN auth a ON a.uid=u.id WHERE a.th=?',(th(t.value),)).fetchone()
    def pub(s,u):return {'id':u['id'],'email':u['email'],'role':u['role']}
    def do_GET(s):
        p=urlparse(s.path);q={k:v[0] for k,v in parse_qs(p.query).items()}
        if p.path.startswith('/database') or p.path.endswith('.py'):return s.send_error(404)
        if not p.path.startswith('/api/'):return super().do_GET()
        u=s.user()
        if p.path=='/api/auth/me':return s.js({'ok':True,'authenticated':bool(u),'user':s.pub(u) if u else None,'provider':settings()['provider']})
        if p.path=='/api/admin/ai-settings':
            if not u or u['role']!='admin':return s.err('Admin only',403)
            x=settings();return s.js({'ok':True,'provider':x['provider'],'lmUrl':x['lm_url'],'lmModel':x['lm_model'],'gmModel':x['gm_model'],'hasKey':bool(x['gm_key'])})
        if not u:return s.err('Login required',401)
        with db() as c:
            if p.path=='/api/collection':
                o={r['ch']:[r['lv'],r['xp']] for r in c.execute('SELECT * FROM owned WHERE uid=?',(u['id'],))}
                return s.js({'ok':True,'owned':o,'used':[r['code'] for r in c.execute('SELECT code FROM used WHERE uid=?',(u['id'],))],'flags':json.loads(u['flags'] or '{}')})
            if p.path=='/api/state':
                ch=q.get('character');
                if ch not in P:return s.err('Unknown character')
                sid=s.ensure_session(c,u['id'],ch,q.get('session_id'))
                return s.js(s.state(c,u['id'],ch,sid))
        s.err('Not found',404)
    def ensure_session(s,c,uid,ch,sid=None):
        if sid and c.execute('SELECT 1 FROM sessions WHERE id=? AND uid=? AND ch=?',(sid,uid,ch)).fetchone():return int(sid)
        r=c.execute('SELECT id FROM sessions WHERE uid=? AND ch=? ORDER BY id DESC LIMIT 1',(uid,ch)).fetchone()
        return r['id'] if r else s.new_session(c,uid,ch)
    def new_session(s,c,uid,ch):
        n=c.execute('SELECT COUNT(*) FROM sessions WHERE uid=? AND ch=?',(uid,ch)).fetchone()[0]+1
        return c.execute('INSERT INTO sessions(uid,ch,title) VALUES(?,?,?)',(uid,ch,f'Chat {n}')).lastrowid
    def stats(s,c,uid,ch):
        r=c.execute('SELECT * FROM stats WHERE uid=? AND ch=?',(uid,ch)).fetchone()
        a,t,b=(r['a'],r['t'],r['b']) if r else (50,50,50)
        return {'affinity':a,'trust':t,'bond':b,'mood':mood(a),'stage':stage(a)}
    def state(s,c,uid,ch,sid):
        return {'ok':True,'sessionId':sid,'stats':s.stats(c,uid,ch),
          'sessions':[dict(r) for r in c.execute('SELECT id,title FROM sessions WHERE uid=? AND ch=? ORDER BY id',(uid,ch))],
          'messages':[dict(r) for r in c.execute('SELECT id,sender,text FROM messages WHERE sid=? ORDER BY id',(sid,))]}
    def do_POST(s):
        p=urlparse(s.path).path
        try:b=json.loads(s.rfile.read(int(s.headers.get('Content-Length',0) or 0)) or b'{}')
        except Exception:return s.err('Invalid JSON')
        if p in('/api/auth/register','/api/auth/login'):return s.auth(p.endswith('register'),b)
        if p=='/api/auth/logout':
            t=SimpleCookie(s.headers.get('Cookie','')).get('iv_session')
            if t:
                with db() as c:c.execute('DELETE FROM auth WHERE th=?',(th(t.value),))
            return s.js({'ok':True},cookie='iv_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0')
        u=s.user()
        if p=='/api/chat':return s.chat(u,b)
        if not u:return s.err('Login required',401)
        with db() as c:
            if p=='/api/redeem':
                k=str(b.get('code','')).strip().upper();ch=CODES.get(k)
                if c.execute('SELECT 1 FROM used WHERE uid=? AND code=?',(u['id'],k)).fetchone():return s.js({'ok':False,'error':'This code was already redeemed.'})
                if not ch:return s.js({'ok':False,'error':'Code not recognised. Check for typos and try again.'})
                r=c.execute('SELECT * FROM owned WHERE uid=? AND ch=?',(u['id'],ch)).fetchone();dup=bool(r)
                if dup:
                    l,x=r['lv'],r['xp']+40
                    if x>=100:x-=100;l+=1
                    c.execute('UPDATE owned SET lv=?,xp=? WHERE uid=? AND ch=?',(l,x,u['id'],ch))
                else:
                    l,x=1,0;c.execute('INSERT INTO owned VALUES(?,?,?,?)',(u['id'],ch,l,x))
                c.execute('INSERT INTO used VALUES(?,?)',(u['id'],k))
                return s.js({'ok':True,'characterId':ch,'duplicate':dup,'progress':[l,x]})
            if p=='/api/progress':
                c.execute('UPDATE users SET flags=? WHERE id=?',(json.dumps({k:1 for k,v in (b.get('flags') or {}).items() if v}),u['id']));return s.js({'ok':True})
            if p=='/api/session/new' and b.get('character') in P:
                sid=s.new_session(c,u['id'],b['character']);return s.js(s.state(c,u['id'],b['character'],sid))
            if p=='/api/session/delete':
                r=c.execute('SELECT ch FROM sessions WHERE id=? AND uid=?',(b.get('sessionId'),u['id'])).fetchone()
                if not r:return s.err('Session not found',404)
                c.execute('DELETE FROM messages WHERE sid=?',(b['sessionId'],));c.execute('DELETE FROM sessions WHERE id=?',(b['sessionId'],))
                return s.js(s.state(c,u['id'],r['ch'],s.ensure_session(c,u['id'],r['ch'])))
            if p=='/api/admin/ai-settings':
                if u['role']!='admin':return s.err('Admin only',403)
                m={'provider':b.get('provider'),'lm_url':b.get('lmUrl'),'lm_model':b.get('lmModel'),'gm_model':b.get('gmModel'),'gm_key':b.get('gmKey')}
                if m['provider'] not in('builtin','lmstudio','gemini'):return s.err('Invalid provider')
                for k,v in m.items():
                    if v not in(None,''):c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v',(k,str(v).strip()))
                return s.js({'ok':True})
        s.err('Not found',404)
    def auth(s,reg,b):
        em=str(b.get('email','')).strip().lower();pw=str(b.get('password',''))
        with db() as c:
            if reg:
                if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',em):return s.err('Valid email is required')
                if len(pw)<6:return s.err('Password must be at least 6 characters')
                salt=secrets.token_hex(16)
                try:uid=c.execute('INSERT INTO users(email,salt,hash,role) VALUES(?,?,?,?)',(em,salt,hp(pw,salt),'admin' if em in ADMINS else 'user')).lastrowid
                except sqlite3.IntegrityError:return s.err('Email is already registered',409)
                for ch,(l,x) in START.items():c.execute('INSERT INTO owned VALUES(?,?,?,?)',(uid,ch,l,x))
            else:
                r=c.execute('SELECT * FROM users WHERE email=?',(em,)).fetchone()
                if not r or hp(pw,r['salt'])!=r['hash']:return s.err('Invalid email or password',401)
                uid=r['id']
                if em in ADMINS:c.execute("UPDATE users SET role='admin' WHERE id=?",(uid,))
            t=secrets.token_urlsafe(32);c.execute('INSERT INTO auth VALUES(?,?)',(th(t),uid))
            u=c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        s.js({'ok':True,'authenticated':True,'user':s.pub(u),'provider':settings()['provider']},cookie=f'iv_session={t}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000')
    def chat(s,u,b):
        ch=b.get('characterId');msg=str(b.get('message') or '').strip()[:2000]
        if ch not in P or not msg:return s.err('characterId and message are required')
        sid=None;hist=[];st=None;prog=None
        with db() as c:
            if u:
                if not c.execute('SELECT 1 FROM owned WHERE uid=? AND ch=?',(u['id'],ch)).fetchone():return s.err('Character is locked',403)
                sid=s.ensure_session(c,u['id'],ch,b.get('sessionId'))
                hist=[{'role':'user' if r['sender']=='user' else 'assistant','content':r['text']} for r in c.execute('SELECT sender,text FROM messages WHERE sid=? ORDER BY id DESC LIMIT 12',(sid,))][::-1]
                stg=s.stats(c,u['id'],ch)['stage']
            else:
                hist=[{'role':'assistant' if h.get('role')=='assistant' else 'user','content':str(h.get('content',''))[:2000]} for h in (b.get('history') or [])[-12:] if isinstance(h,dict)];stg='Stranger'
        reply,src=ai_reply(ch,hist,msg,stg)
        if u:
            d=(-6,-8,-5) if NEG.search(msg) else (3,2,2) if POS.search(msg) else (1,1,1)
            with db() as c:
                r=c.execute('SELECT * FROM stats WHERE uid=? AND ch=?',(u['id'],ch)).fetchone();a,t,bd=(r['a'],r['t'],r['b']) if r else (50,50,50)
                v=[max(0,min(100,x+y)) for x,y in zip((a,t,bd),d)];c.execute('INSERT INTO stats VALUES(?,?,?,?,?) ON CONFLICT(uid,ch) DO UPDATE SET a=?,t=?,b=?',(u['id'],ch,*v,*v))
                um=c.execute('INSERT INTO messages(sid,sender,text) VALUES(?,?,?)',(sid,'user',msg)).lastrowid
                bm=c.execute('INSERT INTO messages(sid,sender,text) VALUES(?,?,?)',(sid,'bot',reply)).lastrowid
                o=c.execute('SELECT * FROM owned WHERE uid=? AND ch=?',(u['id'],ch)).fetchone();prog=[o['lv'],min(99,o['xp']+5)]
                c.execute('UPDATE owned SET xp=? WHERE uid=? AND ch=?',(prog[1],u['id'],ch));st=s.stats(c,u['id'],ch)
        s.js({'ok':True,'reply':reply,'source':src,'provider':settings()['provider'],'sessionId':sid,'stats':st,'progress':prog})
if __name__=='__main__':
    init();print(f'INDOMIEVERSE running at http://{HOST}:{PORT}  (admins: {sorted(ADMINS) or "none; set ADMIN_EMAILS"})')
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
