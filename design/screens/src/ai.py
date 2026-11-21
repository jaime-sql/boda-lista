from common import *
MIN=cfg('qa')['min_n']
def min_n(k): return cfg(k)['min_n']
# MOCK example data (round, obviously fake). Real panel reads /rollup JSON (source=live only).
FEAT=[('qa','Preguntas de invitados',156,38),('rsvp','Respuestas (RSVP)',90,30),('songs','Canciones',40,20),('budget','Presupuesto',10,10),('seating','Mesas',4,2)]
FEAT24=[('qa','Preguntas de invitados',6,2),('rsvp','Respuestas (RSVP)',3,1),('songs','Canciones',0,0),('budget','Presupuesto',0,0),('seating','Mesas',0,0)]
REASONS=[('no_model','El teléfono no tiene el asistente integrado',50),('low_confidence',f'Respuesta poco segura (menos de {round(cfg("qa")["cloud_cutoff"]*100)}%)',35),('long_input','Texto muy largo para el teléfono',15)]

CSS='''
.wrapd{padding:var(--space-8) var(--space-10) var(--space-12)}
.ph{display:flex;align-items:flex-end;justify-content:space-between;gap:var(--space-6);margin-bottom:var(--space-6);flex-wrap:wrap}
.ph h1{font-size:var(--text-3xl);margin-top:var(--space-1)}
.ph p{color:var(--color-text-muted);margin-top:var(--space-1)}
.cardh{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4);padding:var(--space-5) var(--space-6);border-bottom:1px solid var(--color-border);flex-wrap:wrap}
.cardh h2{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;font-size:var(--text-xl)}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-4)}
.tile{padding:var(--space-5) var(--space-6);display:flex;flex-direction:column;gap:var(--space-1);box-shadow:var(--shadow-sm)}
.tile .k{font-weight:600;color:var(--color-text-muted);font-size:var(--text-sm);display:flex;align-items:center;gap:8px}
.tile .v{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;font-size:var(--text-5xl);line-height:1}
.tile .v small{font-size:var(--text-xl)}
.tile .s{color:var(--color-text-muted);font-size:var(--text-sm)}
.speed{display:flex;gap:var(--space-6);align-items:flex-end}
.speed div{display:flex;flex-direction:column;gap:6px}
.speed .v{font-size:var(--text-3xl)}
.grid2{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:var(--space-6);margin-top:var(--space-6);align-items:start}
.frow{display:grid;grid-template-columns:270px 1fr 60px;align-items:center;gap:var(--space-4);padding:var(--space-3) var(--space-6);min-height:64px;border-top:1px solid var(--color-border)}
.frow .lab b{display:block}
.frow .lab span{font-size:var(--text-sm);color:var(--color-text-muted)}
.frow .n{text-align:right;font-weight:600;font-variant-numeric:tabular-nums;font-size:var(--text-sm);color:var(--color-text-muted)}
.split span{display:flex;align-items:center;padding:0 10px;color:var(--color-on-primary);font-weight:700;font-size:var(--text-sm);white-space:nowrap}
.split .few{color:var(--color-text);font-weight:600;justify-content:center}
.legend2{display:flex;gap:var(--space-3);padding:var(--space-4) var(--space-6) 0;flex-wrap:wrap}
.rs{list-style:none}
.rs li{display:grid;grid-template-columns:1fr auto;gap:var(--space-1) var(--space-3);padding:var(--space-4) var(--space-6);border-top:1px solid var(--color-border)}
.rs li .bar{grid-column:1/-1;height:10px;border-radius:999px;background:var(--color-neutral-bg);overflow:hidden}
.rs li .bar i{display:block;height:100%;background:var(--color-cloud-fg)}
.rs code{font-size:var(--text-sm);color:var(--color-text-muted);font-family:var(--font-body);font-weight:600;font-size:1rem}
.foot{display:flex;justify-content:space-between;gap:var(--space-4);flex-wrap:wrap;margin-top:var(--space-6);color:var(--color-text-muted);font-size:var(--text-sm)}
.emp{text-align:center;padding:var(--space-16) var(--space-6);display:flex;flex-direction:column;align-items:center;gap:var(--space-3)}
.emp h2{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-size:var(--text-2xl);font-weight:600}
.emp p{max-width:520px;color:var(--color-text-muted)}
.few-note{align-self:flex-start;display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:var(--radius-pill);background:var(--color-neutral-bg);font-size:var(--text-sm);font-weight:600}
'''
M_CSS='''
.wrapd{padding:var(--space-4) var(--space-4) var(--space-6)}
.ph h1{font-size:var(--text-2xl)}
.tiles{grid-template-columns:1fr}
.tile .v{font-size:var(--text-4xl)}
.grid2{grid-template-columns:1fr}
.frow{grid-template-columns:1fr 44px;grid-template-areas:"lab n" "bar bar";padding:var(--space-3) var(--space-5);gap:var(--space-2)}
.frow .lab{grid-area:lab}.frow .n{grid-area:n}.frow .split{grid-area:bar}
.cardh{padding:var(--space-4) var(--space-5)}
.rs li,.legend2{padding-left:var(--space-5);padding-right:var(--space-5)}
.emp{padding:var(--space-10) var(--space-5)}
.banner-error{flex-wrap:wrap}.banner-error>div{min-width:calc(100% - 40px)}.banner-error .btn{width:100%}
.emp .row{flex-direction:column;width:100%}.emp .btn{width:100%;white-space:normal}
'''
def header(mobile,state):
    seg='<div class="seg" role="group" aria-label="Periodo"><span class="'+('' if state=='few' else 'on')+'">Todo</span><span class="'+('on' if state=='few' else '')+'">Últimas 24 h</span></div>'
    mock='<span class="mock-chip">Datos de ejemplo · solo en el diseño</span>' if state in('loaded','few','error') else ''
    return f'''<div class="ph"><div><p class="eyebrow">Inteligencia híbrida</p><h1 class="display">Cómo responde la IA</h1><p>Qué se respondió en el teléfono y qué tuvo que ir a la nube.</p></div><div class="row wrap gap-3">{mock}{seg}</div></div>'''

def tiles(state):
    if state=='loading':
        sk=lambda: '<div class="card tile"><span class="skeleton" style="width:60%;height:18px"></span><span class="skeleton" style="width:45%;height:56px;margin-top:8px"></span><span class="skeleton" style="width:70%;height:16px;margin-top:6px"></span></div>'
        return f'<div class="tiles" aria-busy="true">{sk()}{sk()}{sk()}</div>'
    if state=='few':
        fn='<span class="few-note">'+I('info',16)+'Pocos datos aún</span>'
        return f'''<div class="tiles">
<div class="card tile"><span class="k">{I("phone",18)}Respondido en tu teléfono</span><span class="v">9 <small>de 12</small></span>{fn}<span class="s">Mostramos el porcentaje desde {MIN} preguntas.</span></div>
<div class="card tile"><span class="k">{I("cloud",18)}Llamadas a la nube ahorradas</span><span class="v">9</span><span class="s">Respuestas sin usar la nube en las últimas 24 h</span></div>
<div class="card tile"><span class="k">{I("clock",18)}Rapidez</span><div class="speed"><div><span class="badge badge-device">En tu teléfono</span><b>9 respuestas</b></div><div><span class="badge badge-cloud">En la nube</span><b>3 respuestas</b></div></div>{fn}</div></div>'''
    return f'''<div class="tiles">
<div class="card tile"><span class="k">{I("phone",18)}Respondido en tu teléfono</span><span class="v">75%</span><span class="s">300 de 400 respuestas</span></div>
<div class="card tile"><span class="k">{I("cloud",18)}Llamadas a la nube ahorradas</span><span class="v">300</span><span class="s">Respuestas que no necesitaron la nube</span></div>
<div class="card tile"><span class="k">{I("clock",18)}Rapidez (mediana)</span><div class="speed"><div><span class="badge badge-device">En tu teléfono</span><span class="v display" style="font-weight:600">0,4 s</span></div><div><span class="badge badge-cloud">En la nube</span><span class="v display" style="font-weight:600">1,8 s</span></div></div><span class="s">p95: 0,9 s en el teléfono · 3,6 s en la nube</span></div></div>'''

def featbars(state):
    rows=''
    data=FEAT24 if state=='few' else FEAT
    for k,name,d,c in data:
        n=d+c
        if state=='loading':
            rows+=f'<div class="frow"><div class="lab"><span class="skeleton" style="width:150px;height:18px"></span></div><span class="skeleton" style="height:28px"></span><span class="skeleton" style="height:16px"></span></div>'; continue
        if n<min_n(k):
            bar=f'<div class="split"><span class="few">{"Sin respuestas todavía" if n==0 else "Pocos datos aún · "+str(n)+(" respuesta" if n==1 else " respuestas")}</span></div>'
        else:
            bar=f'<div class="split" role="img" aria-label="{d} en tu teléfono, {c} en la nube"><span class="dev" style="flex:{d}">{round(d*100/n)}%</span><span class="cld" style="flex:{c}">{round(c*100/n)}%</span></div>'
        rows+=f'<div class="frow"><div class="lab"><b>{name}</b><span>{d} en tu teléfono · {c} en la nube</span></div>{bar}<span class="n">{n}</span></div>'
    leg=f'<div class="legend2">{DEVICE}{CLOUD}</div>'
    return f'<section class="card"><div class="cardh"><h2>Por función</h2><span class="sm muted">Total de respuestas a la derecha</span></div>{leg}<div style="margin-top:var(--space-3)">{rows}</div></section>'

def reasons(state):
    if state=='loading':
        li=''.join('<li><span class="skeleton" style="width:80%;height:18px"></span><span class="skeleton" style="width:40px;height:18px"></span><span class="skeleton bar" style="height:10px"></span></li>' for _ in range(3))
    elif state=='few':
        li=f'<li><span>El teléfono no tiene el asistente integrado <code>no_model</code></span><b>2</b></li><li><span>Respuesta poco segura <code>low_confidence</code></span><b>1</b></li><li><span>Texto muy largo <code>long_input</code></span><b>0</b></li><li style="display:block"><span class="few-note">{I("info",16)}Pocos datos aún: solo contamos, sin porcentajes</span></li>'
    else:
        li=''.join(f'<li><span>{t} <code>{k}</code></span><b>{v} · {v}%</b><span class="bar"><i style="width:{v}%"></i></span></li>' for k,t,v in REASONS)
    return f'<section class="card"><div class="cardh"><h2>¿Por qué fue a la nube?</h2>{CLOUD}</div><ul class="rs">{li}</ul></section>'

def foot(state):
    if state=='loading': return '<div class="foot" aria-live="polite"><span>Cargando…</span></div>'
    t={'loaded':'21 nov, 11:00 a. m. (hora SV) · 400 filas','few':'21 nov, 11:00 a. m. (hora SV) · 12 filas en 24 h','error':'21 nov, 9:00 a. m. (hora SV) · 400 filas · copia guardada'}[state]
    return f'<div class="foot"><span>Actualizado: {t}</span><span>Modelos: Gemini Nano 300 · Gemini en la nube 100 · Solo uso real (sin pruebas de carga)</span></div>' if state!='few' else f'<div class="foot"><span>Actualizado: {t}</span><span>Modelos: Gemini Nano 9 · Gemini en la nube 3 · Solo uso real</span></div>'

def body(state,mobile):
    if state=='empty':
        inner=f'''<section class="card emp">{izote(90,118)}<h2>Aún no hay preguntas</h2><p>Cuando los invitados pregunten o pegues respuestas de WhatsApp, aquí verás cuánto se respondió en el teléfono y cuánto en la nube.</p><div class="row wrap gap-3" style="justify-content:center;margin-top:var(--space-2)"><button class="btn btn-primary btn-lg">{I("send")}Compartir enlace con invitados</button><button class="btn btn-secondary btn-lg">Pegar respuestas</button></div></section>'''
    else:
        pre=''
        if state=='error':
            pre=f'<div class="banner banner-error" role="alert" style="margin-bottom:var(--space-4)">{I("info",22)}<div style="flex:1"><b>No pudimos actualizar.</b> Te mostramos la última copia guardada, del 21 nov a las 9:00 a. m.</div><button class="btn btn-secondary" style="background:var(--color-surface)">{I("refresh")}Reintentar</button></div>'
        stale=' is-stale' if state=='error' else ''
        inner=pre+f'<div class="{stale.strip()}">'+tiles(state if state!='error' else 'loaded')+f'<div class="grid2">{featbars(state if state!="error" else "loaded")}{reasons(state if state!="error" else "loaded")}</div>{foot(state)}</div>'
    return header(mobile,state)+inner

STATES=['loaded','loading','empty','error','few']
for st in STATES:
    d=topnav('Cómo responde la IA')+f'<main class="wrapd">{body(st,False)}</main>'
    open(f'../ai-{st}-desktop.html','w').write(page(f'Cómo responde la IA · {st}',d,1440,CSS))
    m=mobile_appbar()+f'<main class="wrapd">{body(st,True)}</main>'+mobile_tabs('IA')
    open(f'../ai-{st}-mobile.html','w').write(page(f'Cómo responde la IA (móvil) · {st}',m,390,CSS+M_CSS))
