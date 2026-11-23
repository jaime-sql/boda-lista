# Devpost visuals for Boda Lista (Izote y Barro). Run from devpost/src: python3 build.py
# 1) re-shoots real design screens at 2x into ./shots  2) writes card HTML  3) renders PNGs into ../
import asyncio, os, sys
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(HERE+'/../..'); SCR=ROOT+'/screens'
sys.path.insert(0,SCR+'/src'); from common import izote
SHOTS={'guest-qa-device':390,'guest-qa-cloud':390,'guest-qa-offline':390,'guest-qa-idk':390,'rsvp-form':390,
       'ai-loaded-mobile':390,'ai-loaded-desktop':1440,'couple-parse':1440}

CSS='''*{box-sizing:border-box;margin:0}
body{width:1200px;height:800px;overflow:hidden;background:var(--color-bg);color:var(--color-text);font-family:var(--font-body);position:relative}
.weave{position:absolute;left:0;right:0;top:0;height:12px;background:var(--pattern-weave)}
.weave.b{top:auto;bottom:0}
.word{display:flex;align-items:center;gap:14px;font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;color:var(--color-text)}
.mono{border-radius:50%;border:2px solid var(--color-primary);display:grid;place-items:center;font-family:var(--font-display);font-style:italic;font-weight:600;color:var(--color-primary)}
.eyebrow{font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--color-primary)}
.display{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600}
.en{color:var(--color-text-muted)}
.phone{position:absolute;overflow:hidden;border-radius:34px;border:8px solid var(--palette-cacao);background:var(--color-bg);box-shadow:0 24px 48px rgba(51,34,28,.22)}
.phone img,.shot img{display:block}
.shot{position:absolute;overflow:hidden;border-radius:16px;border:1px solid var(--color-border);background:var(--color-bg);box-shadow:0 18px 40px rgba(51,34,28,.18)}
.tag{white-space:nowrap;display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;font-weight:700;font-size:18px}
.tag.ex{border:2px dashed var(--color-text-muted);background:var(--color-surface);color:var(--color-text)}
.cap{position:absolute;left:56px;right:56px;bottom:30px}
.cap h2{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;font-size:34px;line-height:1.15}
.cap p{font-size:20px;margin-top:6px}
.foot{font-size:16px;color:var(--color-text-muted);margin-top:8px}
'''
def doc(body,w=1200,h=800,extra=''):
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><link rel="stylesheet" href="../../tokens/tokens.css">
<style>{CSS}body{{width:{w}px;height:{h}px}}{extra}</style></head><body>{body}</body></html>'''
def word(size=56,mono=64):
    return f'<div class="word" style="font-size:{size}px"><span class="mono" style="width:{mono}px;height:{mono}px;font-size:{max(16,round(mono*.36))}px">A&amp;D</span>Boda Lista</div>'
def phone(name,x,y,w=390,h=640,top=0,scale=1,z=1,rot=0):
    # w/h are the visible screen area in CSS px of the original 390px screen; scale shrinks the whole phone
    return f'<div class="phone" style="left:{x}px;top:{y}px;width:{w*scale+16}px;height:{h*scale+16}px;z-index:{z};transform:rotate({rot}deg)"><img src="shots/{name}.png" style="width:{SHOTS[name]*scale}px;margin-top:{-top*scale}px" alt=""></div>'
def shot(name,x,y,cw,ch,sx=0,sy=0,scale=1):
    return f'<div class="shot" style="left:{x}px;top:{y}px;width:{cw}px;height:{ch}px"><img src="shots/{name}.png" style="width:{SHOTS[name]*scale}px;margin-left:{-sx*scale}px;margin-top:{-sy*scale}px" alt=""></div>'
EXAMPLE='<span class="tag ex">Datos de ejemplo · Sample data</span>'
MOCK='Pantallas del diseño con datos ficticios (Ana &amp; Diego) · Design screens, fictional sample data'
TAG_ES='Asistente de boda con IA híbrida: en tu teléfono y en la nube'
TAG_EN='A hybrid-AI wedding assistant, on your phone and in the cloud'

def cover():
    left=f'''<div style="position:absolute;left:64px;top:96px;width:520px">{word()}
<p class="display" style="font-size:44px;line-height:1.12;margin-top:40px;text-wrap:balance">{TAG_ES}</p>
<p class="en" style="font-size:22px;margin-top:18px">{TAG_EN}</p>
<div style="display:flex;gap:10px;margin-top:34px;flex-wrap:wrap"><span class="tag" style="background:var(--color-device-bg);color:var(--color-device-fg)">En tu teléfono</span><span class="tag" style="background:var(--color-cloud-bg);color:var(--color-cloud-fg)">En la nube</span></div>
<div style="margin-top:40px">{izote(56,74)}</div></div>'''
    ph=phone('guest-qa-device',590,74,390,760,top=0,scale=.8,z=2,rot=-2)+phone('ai-loaded-mobile',858,64,390,780,top=40,scale=.8,z=1,rot=2)
    ex=f'<div style="position:absolute;right:28px;bottom:26px;z-index:3">{EXAMPLE}</div>'
    return doc('<div class="weave"></div>'+left+ph+ex+'<div class="weave b"></div>')

def gallery(title_es,title_en,inner,extra_tag=''):
    cap=f'<div class="cap"><div style="display:flex;align-items:flex-end;justify-content:space-between;gap:20px"><div><h2>{title_es}</h2><p class="en">{title_en}</p></div>{extra_tag}</div><p class="foot">{MOCK}</p></div>'
    hdr=f'<div style="position:absolute;left:56px;top:34px">{word(28,40)}</div>'
    return doc('<div class="weave"></div>'+hdr+inner+cap)

G={}
G['gallery-1-guest-qa']=gallery('Los invitados preguntan y la IA responde','Guests ask; answers come from the phone or, if needed, the cloud',
    phone('guest-qa-device',190,96,390,520,top=230,scale=1,rot=0)+phone('guest-qa-cloud',620,96,390,520,top=230,scale=1))
G['gallery-2-offline-idk']=gallery('Sin señal responde el teléfono, y no inventa','Offline answers stay on the phone; unknowns go to the couple',
    phone('guest-qa-offline',190,96,390,520,top=330,scale=1)+phone('guest-qa-idk',620,96,390,520,top=230,scale=1))
G['gallery-3-rsvp']=gallery('Confirmar asistencia, para toda la familia','One RSVP per household, with meals and allergies',
    phone('rsvp-form',190,96,390,520,top=0,scale=1)+phone('rsvp-form',620,96,390,520,top=640,scale=1))
G['gallery-4-chat-parsing']=gallery('Pegan el chat; la IA lo ordena para revisar','Couples paste guest replies and review what the AI understood',
    shot('couple-parse',56,96,1088,520,sx=405,sy=262,scale=1),f'<span class="tag ex">Confianza de ejemplo · Sample confidence</span>')
G['gallery-5-ai-tab']=gallery('Cómo responde la IA: teléfono vs. nube','How the AI answered: on-device vs. cloud, and why',
    shot('ai-loaded-desktop',56,96,1088,520,sx=22,sy=78,scale=.78),EXAMPLE)

def video(kind):
    if kind=='open':
        b=f'''<div class="weave" style="height:16px"></div><div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:28px">{izote(92,120)}{word(112,120)}
<p class="display" style="font-size:60px;line-height:1.15;max-width:1300px;text-wrap:balance">{TAG_ES}</p><p class="en" style="font-size:36px">{TAG_EN}</p></div><div class="weave b" style="height:16px"></div>'''
    else:
        b=f'''<div class="weave" style="height:16px"></div><div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:30px">{word(104,112)}
<p style="font-size:40px;font-weight:600">https://github.com/jaime-sql/boda-lista</p>
<p class="display" style="font-size:44px">Hecho con Firebase AI Logic · Gemini Nano + Gemini</p>
<p class="en" style="font-size:30px">Built with Firebase AI Logic · Gemini Nano + Gemini · Apache-2.0</p></div><div class="weave b" style="height:16px"></div>'''
    return doc(b,1920,1080)

async def main():
    os.makedirs(HERE+'/shots',exist_ok=True)
    async with async_playwright() as p:
        br=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        for k,w in SHOTS.items():
            pg=await br.new_page(viewport={'width':w,'height':900},device_scale_factor=2)
            await pg.goto(f'file://{SCR}/{k}.html',wait_until='networkidle'); await pg.evaluate('document.fonts.ready')
            await pg.screenshot(path=f'{HERE}/shots/{k}.png',full_page=True); await pg.close()
        jobs=[('thumbnail-1200x800',cover(),1200,800,1),('thumbnail-1920x1280',cover(),1200,800,1.6)]
        jobs+=[(k+'-1920x1280',v,1200,800,1.6) for k,v in G.items()]
        jobs+=[('video-open-1920x1080',video('open'),1920,1080,1),('video-close-1920x1080',video('close'),1920,1080,1)]
        for name,html,w,h,s in jobs:
            f=f'{HERE}/{name}.html'; open(f,'w').write(html)
            pg=await br.new_page(viewport={'width':w,'height':h},device_scale_factor=s)
            await pg.goto('file://'+f,wait_until='networkidle'); await pg.evaluate('document.fonts.ready')
            small=await pg.evaluate('''[...new Set([...document.querySelectorAll("body *")].filter(e=>[...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim())&&parseFloat(getComputedStyle(e).fontSize)<16).map(e=>e.className+":"+getComputedStyle(e).fontSize))]''')
            fams=await pg.evaluate('[...new Set([...document.fonts].filter(f=>f.status=="loaded").map(f=>f.family))]')
            await pg.screenshot(path=f'{ROOT}/devpost/{name}.png'); await pg.close()
            print(name,'fonts',fams,'<16px',small)
        await br.close()
asyncio.run(main())
