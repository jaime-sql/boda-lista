def I(name,size=20,stroke=2):
    p={
    'phone':'<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
    'cloud':'<path d="M7 18h10a4 4 0 0 0 .6-8A6 6 0 0 0 6 11a3.5 3.5 0 0 0 1 7z"/>',
    'wifioff':'<path d="M2 8.5a15 15 0 0 1 20 0M5.5 12a10 10 0 0 1 13 0M9 15.5a5 5 0 0 1 6 0M12 19h.01M3 3l18 18"/>',
    'cal':'<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    'pin':'<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    'send':'<path d="M5 12h14M13 6l6 6-6 6"/>',
    'chat':'<path d="M4 18.5V6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v8a2.5 2.5 0 0 1-2.5 2.5H8z"/>',
    'check':'<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    'edit':'<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    'search':'<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    'download':'<path d="M12 4v11M7 10.5l5 5 5-5M5 20h14"/>',
    'print':'<path d="M7 9V3.5h10V9M7 17H4.5V9h15v8H17M7 14h10v6.5H7z"/>',
    'music':'<path d="M9 18V5.5l11-2V16"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
    'users':'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.6"/><path d="M16.5 14.2A5 5 0 0 1 21.5 19"/>',
    'home':'<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-5h4v5"/>',
    'list':'<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>',
    'question':'<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .8-1 1.5v.7M12 17h.01"/>',
    'car':'<path d="M5 16V11l2-5h10l2 5v5M5 16h14M5 16v2.5M19 16v2.5"/><circle cx="8" cy="13.5" r=".8"/><circle cx="16" cy="13.5" r=".8"/>',
    'info':'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
    'heart':'<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10C19.5 15.4 12 20 12 20z"/>',
    'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'flag':'<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
    'lock':'<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>',
    'sparkle':'<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/>',
    'gift':'<rect x="3.5" y="8" width="17" height="4" rx="1"/><path d="M5 12v8.5h14V12M12 8v12.5M12 8S10.5 3.5 8 4.5 9 8 12 8zm0 0s1.5-4.5 4-3.5S15 8 12 8z"/>',
    'shirt':'<path d="M8 3.5l-4.5 3 2 4 2-1V20.5h9V9.5l2 1 2-4-4.5-3c-.5 1.5-2 2.5-4 2.5s-3.5-1-4-2.5z"/>',
    'parking':'<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M9.5 17V7h3.5a3 3 0 0 1 0 6H9.5"/>',
    'phonecall':'<path d="M5 4h3.5l1.5 4.5-2 1.5a11 11 0 0 0 6 6l1.5-2L20 15.5V19a1.5 1.5 0 0 1-1.6 1.5C10.5 20 4 13.5 3.5 5.6A1.5 1.5 0 0 1 5 4z"/>',
    'minus':'<path d="M6 12h12"/>','plus':'<path d="M12 6v12M6 12h12"/>',
    'wallet':'<path d="M4 7.5A2.5 2.5 0 0 1 6.5 5H18v3"/><rect x="4" y="8" width="16" height="11.5" rx="2.5"/><path d="M15.5 13.8h.01"/>',
    'chart':'<path d="M4 20V4M4 20h16M8 16v-5M12 16V8M16 16v-3"/>',
    'refresh':'<path d="M20 11a8 8 0 1 0-2.3 5.7M20 5v6h-6"/>',
    'receipt':'<path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h3"/>',
    'filter':'<path d="M4 5h16l-6 7.5V19l-4-2v-4.5z"/>',
    }[name]
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>'

DEVICE=f'<span class="badge badge-device">{I("phone",18)}En tu teléfono</span>'
CLOUD=f'<span class="badge badge-cloud">{I("cloud",18)}En la nube</span>'
REVIEW=f'<span class="badge badge-review">{I("flag",16)}Revisar</span>'

IZOTE='''<svg width="{w}" height="{h}" viewBox="0 0 92 120" fill="none" stroke="var(--color-primary)" stroke-width="1.4" aria-hidden="true"><path d="M46 120V30"/><g fill="var(--color-bg)"><path d="M46 30c-7-4-9-13-4-20 3 6 5 9 4 20z"/><path d="M46 30c7-4 9-13 4-20-3 6-5 9-4 20z"/><path d="M46 48c-10-2-15-10-11-18 4 5 8 7 11 18z"/><path d="M46 48c10-2 15-10 11-18-4 5-8 7-11 18z"/><path d="M46 66c-11 0-18-8-16-17 5 4 10 6 16 17z"/><path d="M46 66c11 0 18-8 16-17-5 4-10 6-16 17z"/></g><path d="M46 112c-10-6-26-6-38 0M46 112c10-6 26-6 38 0" stroke="var(--color-success-fg)"/></svg>'''
def izote(w=92,h=120): return IZOTE.format(w=w,h=h)

def page(title,body,width,extra_css=''):
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Boda Lista</title>
<link rel="stylesheet" href="../tokens/tokens.css">
<link rel="stylesheet" href="components.css">
<style>body{{width:{width}px}} {extra_css}</style>
</head><body>
{body}
</body></html>'''

LANG='<div class="seg" role="group" aria-label="Idioma"><span class="on">ES</span><span>EN</span></div>'

def guest_header(hero=True):
    top=f'''<div class="weave"></div>
<header class="appbar"><div class="mono">A&amp;D</div>{LANG}</header>'''
    if not hero: return top
    return top+f'''
<section class="g-hero">
  <div class="g-hero-art">{izote(50,66)}</div>
  <p class="eyebrow">Nos casamos</p>
  <h1 class="display g-names">Ana <i>&amp;</i> Diego</h1>
  <p class="date-spaced g-date">Sáb · 12 · Dic · 2026</p>
  <p>4:00 p. m.<br>Finca Los Almendros, Santa Tecla</p>
  <div class="row gap-2 g-hero-actions"><a class="btn btn-secondary">{I("cal")}Al calendario</a><a class="btn btn-secondary">{I("pin")}Cómo llegar</a></div>
</section>'''

GUEST_CSS='''
.g-hero{margin:0 var(--space-4);padding:var(--space-5);border-radius:var(--radius-xl);background:var(--color-surface-alt);position:relative;overflow:hidden}
.g-hero-art{position:absolute;right:16px;top:14px}
.g-names{font-size:2.5rem;margin:var(--space-1) 0 var(--space-2)}
.g-names i{color:var(--color-primary);font-weight:400}
.g-date{font-size:var(--text-sm);margin-bottom:2px}
.g-hero-actions{margin-top:var(--space-4)}
.g-hero-actions .btn{padding:0 var(--space-4);font-size:var(--text-sm);flex:1}
.g-main{padding:var(--space-5) var(--space-4) var(--space-2);display:flex;flex-direction:column;gap:var(--space-3)}
.g-quick{padding:var(--space-3) var(--space-4) 0}
.g-quick h2{font-size:var(--text-sm);font-weight:600;color:var(--color-text-muted);margin-bottom:var(--space-2)}
.g-composer{display:flex;gap:var(--space-2);padding:var(--space-4)}
.g-composer .input{border-radius:var(--radius-pill);padding:0 var(--space-5)}
.g-composer .btn-icon{background:var(--color-primary);color:var(--color-on-primary)}
.sched{list-style:none;margin-top:var(--space-2)}
.sched li{display:flex;gap:var(--space-3);padding:6px 0;border-top:1px dashed var(--color-border)}
.sched b{min-width:84px;font-variant-numeric:tabular-nums}
'''
def guest_quick(active=None):
    topics=[('clock','Horario'),('pin','Lugar'),('shirt','Vestimenta'),('parking','Parqueo'),('gift','Regalos'),('phonecall','Contactos')]
    chips=''.join(f'<button class="chip{" on" if t==active else ""}">{"" if t==active else I(ic,18)}{t}</button>' for ic,t in topics)
    return f'<section class="g-quick"><h2>Preguntas rápidas</h2><div class="row wrap gap-2">{chips}</div></section>'
def guest_composer(ph='Escribe tu pregunta…'):
    return f'<div class="g-composer"><div class="input placeholder">{ph}</div><button class="btn btn-icon" aria-label="Enviar">{I("send",24,2.4)}</button></div>'
def guest_tabs(active='Preguntar'):
    t=[('question','Preguntar'),('heart','Confirmar'),('info','Detalles')]
    return '<nav class="tabbar">'+''.join(f'<a class="{"on" if n==active else ""}">{I(i,24)}{n}</a>' for i,n in t)+'</nav>'

import json as _json, os as _os
CONFIG=_json.load(open(_os.path.join(_os.path.dirname(__file__),'../../tokens/config.json')))
# Features not yet in config.json (budget, seating) use the qa entry until ML adds them.
FEATURE_KEY={'qa':'qa','rsvp':'rsvp','song':'song','songs':'song'}
def cfg(feature='qa'):
    return CONFIG.get(FEATURE_KEY.get(feature,'qa'),CONFIG['qa'])
def band(pct,feature='qa'):
    b=cfg(feature); p=pct/100
    # high >= high; medium >= cloud_cutoff and < high; below cloud_cutoff -> cloud
    return 'high' if p>=b['high'] else ('mid' if p>=b['cloud_cutoff'] else 'low')
BAND_LABEL={'high':'Alta','mid':'Media','low':'Baja'}
def conf(pct,feature='qa'):
    c=band(pct,feature)
    return f'<span class="conf {c}" data-confidence="{pct/100:.2f}"><i><b></b><b></b><b></b></i>{BAND_LABEL[c]} {pct}%</span>'

NAV=['Resumen','Respuestas','Invitados','Presupuesto','Cómo responde la IA']
def topnav(active):
    l=''.join(f'<a class="{"on" if x==active else ""}">{x}</a>' for x in NAV)
    return f'''<div class="weave"></div><header class="topnav"><div class="brand"><span class="mono">A&amp;D</span>Boda Lista</div><nav class="navlinks">{l}</nav>{LANG}<div class="avatar" aria-label="Ana">AN</div></header>'''
def mobile_appbar():
    return f'''<div class="weave"></div><header class="appbar"><div class="brand" style="font-size:var(--text-lg)"><span class="mono">A&amp;D</span>Boda Lista</div>{LANG}</header>'''
def mobile_tabs(active):
    t=[('home','Inicio'),('users','Invitados'),('wallet','Presupuesto'),('chart','IA')]
    return '<nav class="tabbar" style="grid-template-columns:repeat(4,1fr)">'+''.join(f'<a class="{"on" if n==active else ""}">{I(i,24)}{n}</a>' for i,n in t)+'</nav>'
