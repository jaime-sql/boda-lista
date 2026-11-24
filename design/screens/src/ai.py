from common import *
MIN=MIN_SAMPLE
# MOCK example data (round, obviously fake). Real panel reads /rollup JSON (source=live only).
# by_feature keys = schema task values (panel spec v1.2): guest_question, rsvp, song only. EXAMPLE numbers.
# Spec v1.2: sheet rows (route="sheet", model=null, confidence=null) are excluded from AI metrics 1-5 and shown as their own count (sheet_answers).
FEAT=[('guest_question','Preguntas de invitados',160,40),('rsvp','Confirmaciones',90,30),('song','Canciones',50,30)]
FEAT24=[('guest_question','Preguntas de invitados',6,2),('rsvp','Confirmaciones',3,1),('song','Canciones',0,0)]
DEV=sum(f[2] for f in FEAT); CLD=sum(f[3] for f in FEAT); N=DEV+CLD
DEV24=sum(f[2] for f in FEAT24); CLD24=sum(f[3] for f in FEAT24); N24=DEV24+CLD24
SHEET_N=60; SHEET24=4
REASONS=[('no_model','El teléfono no tiene el asistente integrado',50),('low_confidence','Respuesta poco segura (bajo el umbral de cada función)',35),('long_input','Texto muy largo para el teléfono',15)]
# Optional lang split (es / en / sin idioma) for fairness check (spec v1.2, metric 6).
# Rows without lang count in totals and show as "sin idioma" in the split; cells < 20 show raw count + "Pocos datos aún".
LANG_LOADED=[
    ('es','Español (es)',216,64,14,'5%','0,4 s','1,7 s'),
    ('en','Inglés (en)',76,32,8,'7%','0,4 s','1,9 s'),
    ('none','sin idioma',8,4,1,None,None,None),
]
LANG_24=[
    ('es','Español (es)',6,2,0,None,None,None),
    ('en','Inglés (en)',3,1,1,None,None,None),
    ('none','sin idioma',0,0,0,None,None,None),
]
assert sum(r[2] for r in REASONS)==CLD and N>=MIN and N24<MIN
assert sum(x[2] for x in LANG_LOADED)==DEV and sum(x[3] for x in LANG_LOADED)==CLD and sum(x[2]+x[3] for x in LANG_LOADED)==N
assert sum(x[2] for x in LANG_24)==DEV24 and sum(x[3] for x in LANG_24)==CLD24 and sum(x[2]+x[3] for x in LANG_24)==N24
OFF={}
LOADED=dict(FEAT=FEAT,REASONS=REASONS,DEV=DEV,CLD=CLD,N=N,OFF={},SHEET_ANS=SHEET_N,LANG_ROWS=LANG_LOADED)

# No-threshold EXAMPLE (spec v1.2):
# - guest_question has null high/cloud_cutoff -> cloud (no_threshold), or Nano when offline (offline_no_threshold).
# - offline_no_threshold is OUT of BOTH numerator and denominator of on-phone share and cloud calls saved,
#   and shows only as its own count + bar segment "Sin conexión, sin umbral". Still counted in Gemini Nano model mix.
NT_OFFLINE=8
NT_FEAT=[('guest_question','Preguntas de invitados',0,200),('rsvp','Confirmaciones',100,20),('song','Canciones',60,20)]
NT_OFF={'guest_question':NT_OFFLINE}
NT_DEV=sum(f[2] for f in NT_FEAT); NT_CLD=sum(f[3] for f in NT_FEAT); NT_N=NT_DEV+NT_CLD
NT_SHEET=60
NT_REASONS=[('no_threshold','Sin umbral aún',200),('no_model','El teléfono no tiene el asistente integrado',24),('low_confidence','Respuesta poco segura (bajo el umbral de cada función)',12),('long_input','Texto muy largo para el teléfono',4)]
NT_LANG=[
    ('es','Español (es)',114,166,14,'5%','0,4 s','1,8 s'),
    ('en','Inglés (en)',42,66,8,'7%','0,4 s','2,0 s'),
    ('none','sin idioma',4,8,1,None,None,None),
]
NOTHR=dict(FEAT=NT_FEAT,REASONS=NT_REASONS,DEV=NT_DEV,CLD=NT_CLD,N=NT_N,OFF=NT_OFF,SHEET_ANS=NT_SHEET,LANG_ROWS=NT_LANG)
EXAMPLE_THR={'rsvp':{'high':0.85,'cloud_cutoff':0.60},'song':{'high':0.85,'cloud_cutoff':0.60}}  # design example only
assert NT_N==400 and (NT_DEV,NT_CLD,NT_OFFLINE)==(160,240,8) and round(NT_DEV*100/NT_N)==40
assert sum(r[2] for r in NT_REASONS)==NT_CLD and sum(NT_OFF.values())==NT_OFFLINE
assert dict((r[0],r[2]) for r in NT_REASONS)['no_threshold']==NT_FEAT[0][3]
assert sum(r[2] for r in NT_REASONS if r[0]!='no_threshold')==sum(f[3] for f in NT_FEAT[1:])
assert sum(x[2] for x in NT_LANG)==NT_DEV and sum(x[3] for x in NT_LANG)==NT_CLD and sum(x[2]+x[3] for x in NT_LANG)==NT_N
assert not has_threshold(cfg('guest_question'))

def use(ds):
    globals().update(ds)
use(LOADED)

CSS='''
.wrapd{padding:var(--space-8) var(--space-10) var(--space-12)}
.ph{display:flex;align-items:flex-end;justify-content:space-between;gap:var(--space-6);margin-bottom:var(--space-6);flex-wrap:wrap}
.ph h1{font-size:var(--text-3xl);margin-top:var(--space-1)}
.ph p{color:var(--color-text-muted);margin-top:var(--space-1)}
.cardh{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4);padding:var(--space-5) var(--space-6);border-bottom:1px solid var(--color-border);flex-wrap:wrap}
.cardh code{font-family:var(--font-body);font-weight:600;font-size:var(--text-sm)}
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
.lrow{display:grid;grid-template-columns:190px 1fr;align-items:center;gap:var(--space-4);padding:var(--space-4) var(--space-6);border-top:1px solid var(--color-border)}
.lrow:first-child{border-top:0}
.llab b{display:block}
.llab span{font-size:var(--text-sm);color:var(--color-text-muted)}
.lmetrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--space-3);align-items:start}
.lmet{display:flex;flex-direction:column;gap:2px}
.lmet .k{font-size:var(--text-sm);color:var(--color-text-muted)}
.lmet .val{font-size:var(--text-base);font-weight:700;font-variant-numeric:tabular-nums}
.lmet .sub{font-size:var(--text-sm);color:var(--color-text-muted);font-variant-numeric:tabular-nums}
.lfew{display:flex;flex-wrap:wrap;align-items:center;gap:var(--space-2) var(--space-3)}
.lfew .sub{font-size:var(--text-sm);color:var(--color-text-muted);font-variant-numeric:tabular-nums}
.sheet-body{padding:var(--space-5) var(--space-6);display:flex;flex-direction:column;gap:var(--space-2)}
.sheet-body .v{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;font-size:var(--text-5xl);line-height:1}
.sheet-body .s{color:var(--color-text-muted);font-size:var(--text-sm)}
.sheet-note{margin-top:var(--space-2);padding-top:var(--space-3);border-top:1px solid var(--color-border);font-size:var(--text-sm);color:var(--color-text-muted)}
.sheet-note code{font-family:var(--font-body);font-weight:600;font-size:var(--text-sm);color:var(--color-text)}
.foot{display:flex;justify-content:space-between;gap:var(--space-4);flex-wrap:wrap;margin-top:var(--space-6);color:var(--color-text-muted);font-size:var(--text-sm)}
.emp{text-align:center;padding:var(--space-16) var(--space-6);display:flex;flex-direction:column;align-items:center;gap:var(--space-3)}
.emp h2{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-size:var(--text-2xl);font-weight:600}
.emp p{max-width:520px;color:var(--color-text-muted)}
.thr{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;margin-top:8px}
.thr code{font-family:var(--font-body);font-weight:600;font-size:var(--text-sm)}
.thr>span:last-child{font-size:var(--text-sm);color:var(--color-text-muted)}
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
.lrow{grid-template-columns:1fr;padding:var(--space-4) var(--space-5);gap:var(--space-3)}
.lmetrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--space-3)}
.lmetrics .lmet-lat{grid-column:1/-1}
.sheet-body{padding:var(--space-4) var(--space-5)}
.sheet-body .v{font-size:var(--text-4xl)}
.cardh{padding:var(--space-4) var(--space-5)}
.rs li,.legend2{padding-left:var(--space-5);padding-right:var(--space-5)}
.emp{padding:var(--space-10) var(--space-5)}
.banner-error{flex-wrap:wrap}.banner-error>div{min-width:calc(100% - 40px)}.banner-error .btn{width:100%}
.emp .row{flex-direction:column;width:100%}.emp .btn{width:100%;white-space:normal}
'''
def header(mobile,state):
    seg='<div class="seg" role="group" aria-label="Periodo"><span class="'+('' if state=='few' else 'on')+'">Todo</span><span class="'+('on' if state=='few' else '')+'">Últimas 24 h</span></div>'
    mock='<span class="mock-chip">Datos de ejemplo · solo en el diseño</span>' if state in('loaded','few','error','offline','nothr') else ''
    return f'''<div class="ph"><div><p class="eyebrow">Inteligencia híbrida</p><h1 class="display">Cómo responde la IA</h1><p>Qué se respondió en el teléfono y qué tuvo que ir a la nube.</p></div><div class="row wrap gap-3">{mock}{seg}</div></div>'''

def off_line():
    o=sum(OFF.values())
    return f'<span class="s" style="display:flex;align-items:center;gap:8px;margin-top:4px"><i class="swatch-off" aria-hidden="true"></i>{o} respondidas sin conexión, sin umbral (marcadas poco seguras)</span>' if o else ''
def tiles(state):
    if state=='loading':
        sk=lambda: '<div class="card tile"><span class="skeleton" style="width:60%;height:18px"></span><span class="skeleton" style="width:45%;height:56px;margin-top:8px"></span><span class="skeleton" style="width:70%;height:16px;margin-top:6px"></span></div>'
        return f'<div class="tiles" aria-busy="true">{sk()}{sk()}{sk()}</div>'
    if state=='few':
        fn='<span class="few-note">'+I('info',16)+'Pocos datos aún</span>'
        return f'''<div class="tiles">
<div class="card tile"><span class="k">{I("phone",18)}Respondido en tu teléfono</span><span class="v">{DEV24} <small>de {N24}</small></span>{fn}<span class="s">Mostramos el porcentaje desde {MIN} respuestas.</span></div>
<div class="card tile"><span class="k">{I("cloud",18)}Llamadas a la nube ahorradas</span><span class="v">{DEV24}</span><span class="s">Respuestas sin usar la nube en las últimas 24 h</span></div>
<div class="card tile"><span class="k">{I("clock",18)}Rapidez</span><div class="speed"><div><span class="badge badge-device">En tu teléfono</span><b>{DEV24} respuestas</b></div><div><span class="badge badge-cloud">En la nube</span><b>{CLD24} respuestas</b></div></div>{fn}</div></div>'''
    return f'''<div class="tiles">
<div class="card tile"><span class="k">{I("phone",18)}Respondido en tu teléfono</span><span class="v">{round(DEV*100/N)}%</span><span class="s">{DEV} de {N} respuestas</span>{off_line()}</div>
<div class="card tile"><span class="k">{I("cloud",18)}Llamadas a la nube ahorradas</span><span class="v">{DEV}</span><span class="s">Respuestas que no necesitaron la nube</span></div>
<div class="card tile"><span class="k">{I("clock",18)}Rapidez (mediana)</span><div class="speed"><div><span class="badge badge-device">En tu teléfono</span><span class="v display" style="font-weight:600">0,4 s</span></div><div><span class="badge badge-cloud">En la nube</span><span class="v display" style="font-weight:600">1,8 s</span></div></div><span class="s">p95: 0,9 s en el teléfono · 3,6 s en la nube</span></div></div>'''

# No-threshold example: guest_question has no dev split yet (null), rsvp/song use design-example cut-offs.
THR={'guest_question':cfg('guest_question'),**EXAMPLE_THR}
def featbars(state):
    rows=''
    data=FEAT24 if state=='few' else FEAT
    for k,name,d,c in data:
        o=OFF.get(k,0) if state=='nothr' else 0
        n=d+c+o
        if state=='loading':
            rows+=f'<div class="frow"><div class="lab"><span class="skeleton" style="width:150px;height:18px"></span></div><span class="skeleton" style="height:28px"></span><span class="skeleton" style="height:16px"></span></div>'; continue
        if n<MIN:
            bar=f'<div class="split"><span class="few">{"Sin respuestas todavía" if n==0 else "Pocos datos aún · "+str(n)+(" respuesta" if n==1 else " respuestas")}</span></div>'
        else:
            if o:
                segs=(f'<span class="dev" style="flex:{d}">{round(d*100/n)}%</span>' if d else '')+f'<span class="off" style="flex:{o}" title="Sin conexión, sin umbral"></span><span class="cld" style="flex:{c}">{round(c*100/n)}%</span>'
                bar=f'<div class="split" role="img" aria-label="{d} en tu teléfono, {o} sin conexión sin umbral, {c} en la nube">{segs}</div>'
            else:
                bar=f'<div class="split" role="img" aria-label="{d} en tu teléfono, {c} en la nube"><span class="dev" style="flex:{d}">{round(d*100/n)}%</span><span class="cld" style="flex:{c}">{100-round(d*100/n)}%</span></div>'
        thr=''
        if state=='nothr':
            b=THR[k]
            thr=(f'<div class="thr">{NO_THRESHOLD}<span>No clasificamos en Alta / Media / Baja</span></div><div class="thr"><span>{o} sin conexión, sin umbral, marcadas «Respuesta poco segura» <code>offline_no_threshold</code>. No cuentan en el porcentaje ni en llamadas ahorradas.</span></div>' if not has_threshold(b)
                 else f'<div class="thr"><span class="conf-none" style="background:var(--color-surface-alt)" title="Umbral de ejemplo de diseño">Umbral {round(b["cloud_cutoff"]*100)}% (ejemplo)</span><span>Alta desde {round(b["high"]*100)}%</span></div>')
        rows+=f'<div class="frow"><div class="lab"><b>{name}</b><span>{d} en tu teléfono · {(str(o)+" sin conexión, sin umbral · ") if o else ""}{c} en la nube</span>{thr}</div>{bar}<span class="n">{n}</span></div>'
    leg=f'<div class="legend2">{DEVICE}{CLOUD}'+('<span class="sm" style="display:inline-flex;align-items:center;gap:8px;font-weight:600"><i class="swatch-off" aria-hidden="true"></i>Sin conexión, sin umbral</span>' if state=='nothr' and OFF else '')+'</div>'
    return f'<section class="card"><div class="cardh"><h2>Por función</h2><span class="sm muted">Total de respuestas a la derecha</span></div>{leg}<div style="margin-top:var(--space-3)">{rows}</div></section>'

def reasons(state):
    if state=='loading':
        li=''.join('<li><span class="skeleton" style="width:80%;height:18px"></span><span class="skeleton" style="width:40px;height:18px"></span><span class="skeleton bar" style="height:10px"></span></li>' for _ in range(3))
    elif state=='few':
        li=f'<li><span>El teléfono no tiene el asistente integrado <code>no_model</code></span><b>2</b></li><li><span>Respuesta poco segura <code>low_confidence</code></span><b>1</b></li><li><span>Texto muy largo <code>long_input</code></span><b>0</b></li><li style="display:block"><span class="few-note">{I("info",16)}Pocos datos aún: solo contamos, sin porcentajes</span></li>'
    else:
        li=''.join(f'<li><span>{t} <code>{k}</code></span><b>{v} · {round(v*100/CLD)}%</b><span class="bar"><i style="width:{v*100/CLD:.1f}%"></i></span></li>' for k,t,v in REASONS)
    return f'<section class="card"><div class="cardh"><h2>¿Por qué fue a la nube?</h2>{CLOUD}</div><ul class="rs">{li}</ul></section>'

def lang_split(state):
    if state=='loading':
        rows=''.join('<div class="lrow"><div class="llab"><span class="skeleton" style="width:120px;height:18px"></span></div><div class="lmetrics"><span class="skeleton" style="height:36px"></span><span class="skeleton" style="height:36px"></span><span class="skeleton" style="height:36px"></span></div></div>' for _ in range(3))
    else:
        data=LANG_24 if state=='few' else LANG_ROWS
        rows=''
        for code,label,d,c,ref,ref_pct,ld,lc in data:
            n=d+c
            note='Filas sin campo lang (cuentan en los totales)' if code=='none' else f'{d} en tu teléfono · {c} en la nube'
            if n==0:
                right=f'<div class="lfew"><span class="few-note">Sin respuestas todavía</span></div>'
            elif n<MIN:
                right=f'<div class="lfew"><span class="few-note">{I("info",16)}Pocos datos aún</span><span class="sub">{d} de {n} en tu teléfono · {ref} sin respuesta</span></div>'
            else:
                right=f'''<div class="lmetrics">
<div class="lmet"><span class="k">En tu teléfono</span><span class="val">{round(d*100/n)}%</span><span class="sub">{d} de {n}</span></div>
<div class="lmet"><span class="k">Sin respuesta</span><span class="val">{ref_pct}</span><span class="sub">{ref} de {n}</span></div>
<div class="lmet lmet-lat"><span class="k">Rapidez (mediana)</span><span class="val">{ld} tel · {lc} nube</span><span class="sub">Solo respuestas con IA</span></div>
</div>'''
            rows+=f'<div class="lrow"><div class="llab"><b>{label}</b><span>{n} filas · {note}</span></div>{right}</div>'
    return f'<section class="card"><div class="cardh"><h2>Por idioma del invitado</h2><span class="sm muted">Equidad · campo opcional <code>lang</code></span></div><div>{rows}</div></section>'

def sheet_card(state):
    if state=='loading':
        inner='<div class="sheet-body"><span class="skeleton" style="width:45%;height:56px"></span><span class="skeleton" style="width:85%;height:18px"></span><span class="skeleton" style="width:90%;height:36px;margin-top:8px"></span></div>'
    else:
        cnt=SHEET24 if state=='few' else SHEET_ANS
        sub='respuestas con temas rápidos en las últimas 24 h' if state=='few' else 'respuestas con temas rápidos (sin llamar a la IA)'
        inner=f'''<div class="sheet-body">
<span class="v">{cnt}</span>
<span class="s">{sub}</span>
<p class="sheet-note">Registradas como <code>route = "sheet"</code> (<code>model</code> y <code>confidence</code> en <code>null</code>). Excluidas del porcentaje en tu teléfono, llamadas ahorradas, rapidez, motivos de nube y mezcla de modelos.</p>
</div>'''
    return f'<section class="card"><div class="cardh"><h2>Respondido desde la ficha</h2>{SHEET}</div>{inner}</section>'

def foot(state):
    if state=='loading': return '<div class="foot" aria-live="polite"><span>Cargando…</span></div>'
    o=sum(OFF.values())
    if state=='nothr':
        t=f'24 nov, 11:00 a. m. (hora SV) · {N+o+SHEET_ANS} filas ({N} en cálculo · {o} sin conexión, sin umbral · {SHEET_ANS} desde la ficha)'
        return f'<div class="foot"><span>Actualizado: {t}</span><span>Modelos: Gemini Nano {DEV+o} · Gemini en la nube {CLD} · Solo uso real (sin pruebas de carga)</span></div>'
    if state=='few':
        t=f'24 nov, 11:00 a. m. (hora SV) · {N24+SHEET24} filas en 24 h ({N24} con IA · {SHEET24} desde la ficha)'
        return f'<div class="foot"><span>Actualizado: {t}</span><span>Modelos: Gemini Nano {DEV24} · Gemini en la nube {CLD24} · Solo uso real</span></div>'
    t={
        'loaded':f'24 nov, 11:00 a. m. (hora SV) · {N+SHEET_ANS} filas ({N} con IA · {SHEET_ANS} desde la ficha)',
        'error':f'24 nov, 9:00 a. m. (hora SV) · {N+SHEET_ANS} filas ({N} con IA · {SHEET_ANS} desde la ficha) · copia guardada',
        'offline':f'24 nov, 11:00 a. m. (hora SV) · {N+SHEET_ANS} filas ({N} con IA · {SHEET_ANS} desde la ficha) · copia guardada',
    }[state]
    return f'<div class="foot"><span>Actualizado: {t}</span><span>Modelos: Gemini Nano {DEV} · Gemini en la nube {CLD} · Solo uso real (sin pruebas de carga)</span></div>'

def body(state,mobile):
    if state=='empty':
        inner=f'''<section class="card emp">{izote(90,118)}<h2>Aún no hay preguntas</h2><p>Cuando los invitados pregunten o pegues respuestas de WhatsApp, aquí verás cuánto se respondió en el teléfono y cuánto en la nube.</p><div class="row wrap gap-3" style="justify-content:center;margin-top:var(--space-2)"><button class="btn btn-primary btn-lg">{I("send")}Compartir enlace con invitados</button><button class="btn btn-secondary btn-lg">Pegar respuestas</button></div></section>'''
    else:
        pre=''
        if state=='error':
            pre=f'<div class="banner banner-error" role="alert" style="margin-bottom:var(--space-4)">{I("info",22)}<div style="flex:1"><b>No pudimos actualizar.</b> Te mostramos la última copia guardada, del 24 nov a las 9:00 a. m.</div><button class="btn btn-secondary" style="background:var(--color-surface)">{I("refresh")}Reintentar</button></div>'
        if state=='nothr':
            pre=f'<div class="banner banner-info" role="status" style="margin-bottom:var(--space-4)">{I("info",22)}<div style="flex:1"><b>Preguntas de invitados aún no tiene umbral.</b> Mientras tanto, sus respuestas van a la nube. Sin conexión responde el teléfono y las marca como «Respuesta poco segura». No las clasificamos en Alta, Media o Baja hasta que haya un umbral.</div></div>'
        if state=='offline':
            pre=f'<div class="banner banner-offline" role="status" style="margin-bottom:var(--space-4)">{I("wifioff",22)}<div style="flex:1"><b>Sin conexión.</b> Te mostramos la última copia guardada, del 24 nov a las 11:00 a. m. Se actualiza sola al volver la señal.</div></div>'
        snap=state in ('error','offline')
        ds='loaded' if snap else state
        if state=='nothr': ds='loaded'; use(NOTHR)
        inner=(pre+f'<div class="{"is-stale" if snap else ""}">'
               +tiles(ds)
               +f'<div class="grid2">{featbars("nothr" if state=="nothr" else ds)}{reasons(ds)}</div>'
               +f'<div class="grid2">{lang_split(ds)}{sheet_card(ds)}</div>'
               +f'{foot(state)}</div>')
    use(LOADED)
    return header(mobile,state)+inner

STATES=['loaded','loading','empty','error','offline','few','nothr']
FILE={'nothr':'no-threshold'}
for st in STATES:
    d=topnav('Cómo responde la IA')+f'<main class="wrapd">{body(st,False)}</main>'
    open(f'../ai-{FILE.get(st,st)}-desktop.html','w').write(page(f'Cómo responde la IA · {st}',d,1440,CSS))
    m=mobile_appbar()+f'<main class="wrapd">{body(st,True)}</main>'+mobile_tabs('IA')
    open(f'../ai-{FILE.get(st,st)}-mobile.html','w').write(page(f'Cómo responde la IA (móvil) · {st}',m,390,CSS+M_CSS))
