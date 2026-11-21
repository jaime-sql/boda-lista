from common import *
CONF=lambda pct,task: conf_example(pct)  # config.json is null until ML's PR; mock rows use design-example bands
D_CSS='''
.wrapd{padding:var(--space-8) var(--space-10) var(--space-12)}
.ph{display:flex;align-items:flex-end;justify-content:space-between;gap:var(--space-6);margin-bottom:var(--space-6)}
.ph h1{font-size:var(--text-3xl);margin-top:var(--space-1)}
.ph p{color:var(--color-text-muted);margin-top:var(--space-1)}
.cardh{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4);padding:var(--space-5) var(--space-6);border-bottom:1px solid var(--color-border)}
.cardh h2{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;font-size:var(--text-xl)}
.quote{display:block;font-size:var(--text-sm);color:var(--color-text-muted);font-style:italic;max-width:270px;margin-top:2px}
.num{font-variant-numeric:tabular-nums;font-weight:600}
.acts{display:flex;gap:var(--space-2)}
.acts .btn{min-height:var(--tap-min);padding:0 var(--space-4);font-size:var(--text-sm)}
.done{display:inline-flex;align-items:center;gap:6px;color:var(--color-success-fg);font-weight:700;font-size:var(--text-sm)}
'''
# ---------- Paste & parse ----------
msgs='''[20/11 7:42 p. m.] Tía Marta Fuentes: vamos 3, mi hijo es vegetariano 🌱
[20/11 8:05 p. m.] Rolando Vides: no podemos llegar, abrazos a los novios ❤️
[20/11 8:31 p. m.] Chepe Alvarado: yo y mi esposa confirmados!!
[21/11 9:10 a. m.] Karla Menjívar: Confirmo, voy sola. Soy celiaca, sin gluten porfa 🙏
[21/11 9:44 a. m.] Efraín Portillo: todavía no sé si me dan permiso en el trabajo, le aviso
[21/11 10:02 a. m.] Lucía Hernández: We'll be there! 2 of us, no shellfish please
[21/11 10:15 a. m.] Beto Rivas: ahí vamos a estar con los cipotes, somos 5. ¿hay bus?
[21/11 10:20 a. m.] Ximena Ayala: 👍 ahí nos vemos!! pongan Suavemente'''
def kn(k):
    return '1 niño' if str(k)=='1' else ('—' if k=='—' else f'{k} niños')
def row(name,quote,att,ps,kids,meal,ride,conf,src,state='todo',review=False,song=None):
    attb={'Sí':'badge-yes','No':'badge-no','Tal vez':'badge-maybe'}[att]
    c={'high':'Alta','mid':'Media','low':'Baja'}[conf[0]]
    srcb=DEVICE if src=='d' else CLOUD
    if state=='done': act=f'<span class="done">{I("check",18,2.6)}Confirmado</span>'
    else: act=f'<div class="acts"><button class="btn btn-quiet">{I("edit",18)}Editar</button><button class="btn btn-primary">{I("check",18,2.6)}Confirmar</button></div>'
    flag=(f'<span class="sub" style="margin-top:4px">{I("music",16)} {song}</span>' if song else '')+(f'<div style="margin-top:6px">{REVIEW}</div>' if review else '')
    return f'''<tr class="{"review" if review else ""}"><td><b>{name}</b><span class="quote">“{quote}”</span>{flag}</td><td><span class="badge {attb}">{att}</span></td><td class="num">{ps}<span class="sub">{kn(kids)}</span></td><td>{meal}</td><td>{ride}</td><td>{CONF(conf[1],'rsvp')}<div style="margin-top:6px">{srcb}</div></td><td>{act}</td></tr>'''
rows=''.join([
 row('Tía Marta Fuentes','vamos 3, mi hijo es vegetariano','Sí',3,1,'Vegetariano','No',('high',96),'d','done'),
 row('Rolando Vides','no podemos llegar, abrazos','No',0,0,'—','—',('high',98),'d','done'),
 row('Chepe Alvarado','yo y mi esposa confirmados!!','Sí',2,0,'—','No',('high',94),'d'),
 row('Karla Menjívar','Confirmo, voy sola. Soy celiaca…','Sí',1,0,'Sin gluten','No',('high',95),'d'),
 row('Efraín Portillo','todavía no sé si me dan permiso…','Tal vez',1,0,'—','No',('mid',74),'d'),
 row('Lucía Hernández',"We'll be there! 2 of us, no shellfish",'Sí',2,0,'Alergia: mariscos','No',('high',92),'d'),
 row('Beto Rivas','con los cipotes, somos 5. ¿hay bus?','Sí',5,'¿3?','—','Sí',('low',48),'c',review=True),
 row('Ximena Ayala','👍 ahí nos vemos!! pongan Suavemente','Sí','¿1?',0,'—','No',('low',57),'c',review=True,song='Suavemente · Elvis Crespo'),
])
body=topnav('Respuestas')+f'''<main class="wrapd">
<div class="ph"><div><p class="eyebrow">Respuestas de WhatsApp</p><h1 class="display">Pega los mensajes y revisa</h1><p>Leemos cada mensaje en tu dispositivo. Solo los dudosos van a la nube, sin números de teléfono.</p></div>
<div class="row wrap gap-2"><span class="mock-chip">Confianza de ejemplo · solo en el diseño</span><span class="badge badge-device">{I("phone",18)}En tu teléfono · 6</span><span class="badge badge-cloud">{I("cloud",18)}En la nube · 2</span><span class="badge badge-review">{I("flag",16)}Revisar · 2</span></div></div>
<div class="pgrid">
  <section class="card">
    <div class="cardh"><h2>1. Pega los mensajes</h2></div>
    <div class="pad stack gap-4">
      <label class="label" for="paste">Copia el chat de WhatsApp y pégalo aquí</label>
      <textarea id="paste" class="input paste" rows="16">{msgs}</textarea>
      <div class="stack gap-2"><button class="btn btn-primary btn-lg btn-block">{I("sparkle",22)}Leer respuestas</button><button class="btn btn-quiet btn-block">Limpiar</button></div>
      <p class="hint">{I("lock",16)} El texto no se guarda; solo guardamos lo que confirmes.</p>
    </div>
  </section>
  <section class="card">
    <div class="cardh"><h2>2. Revisa lo que entendimos</h2>
      <div class="row gap-2 fchips"><button class="chip on">Todas <span class="count">8</span></button><button class="chip">Revisar <span class="count">2</span></button><button class="chip">Listas <span class="count">6</span></button></div></div>
    <table class="table"><thead><tr><th>Invitado y mensaje</th><th>Asiste</th><th>Personas</th><th>Comida</th><th>Transp.</th><th>Confianza</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table>
    <div class="row between pad" style="border-top:1px solid var(--color-border)"><p class="muted">2 confirmadas · 4 listas para confirmar · 2 por revisar</p><button class="btn btn-primary btn-lg">{I("check",22,2.6)}Confirmar las 4 listas</button></div>
  </section>
</div></main>'''
P_CSS=D_CSS+'''
.pgrid{display:grid;grid-template-columns:360px minmax(0,1fr);gap:var(--space-6);align-items:start}
.paste{font-size:var(--text-sm);line-height:1.55;resize:none;min-height:640px;font-family:var(--font-body)}
.table td{font-size:var(--text-sm)}
.table td b{font-size:var(--text-base)}
.table td:first-child{padding-left:var(--space-6)}
.table th:first-child{padding-left:var(--space-6)}
.table td{padding:var(--space-3) var(--space-3)}.table th{padding:var(--space-3)}
.hint svg{vertical-align:-2px}
.sub{display:block;font-weight:400;font-size:var(--text-sm);color:var(--color-text-muted)}
.fchips .chip{min-height:var(--tap-min);font-size:var(--text-sm);padding:0 var(--space-3)}
.acts{flex-direction:column}
.quote{max-width:220px}
'''
open('../couple-parse.html','w').write(page('Respuestas',body,1440,P_CSS))

# ---------- Headcount data ----------
KPI=[('Confirmados','96','personas','badge-yes'),('Pendientes','31','sin responder','badge-pending'),('No asisten','18','personas','badge-no'),('Total invitados','145','en 52 invitaciones','')]
MEALS=[('Vegetariano',11),('Vegano',3),('Sin gluten',5),('Menú infantil',14),('Alergia',4)]
SONGS=[ # (title, artist, energy 1-5, requests, section)
 ('Bésame mucho','Luis Miguel',1,4,'Lentas · para la cena'),
 ('Perfect','Ed Sheeran',1,3,None),
 ('Sabor a mí','Trío Los Panchos',2,2,None),
 ('Ojalá que llueva café','Juan Luis Guerra',3,2,'Para calentar'),
 ('La flaca','Jarabe de Palo',3,1,None),
 ('La gota fría','Carlos Vives',4,2,'Para bailar'),
 ('Suavemente','Elvis Crespo',5,3,None),
 ('Vivir mi vida','Marc Anthony',5,5,None),
]
GUESTS=[('Familia Rivas','Sí','3','1','Vegetariano, infantil, alergia','Sí','18 nov','d'),
 ('Tía Marta Fuentes','Sí','3','1','Vegetariano','No','20 nov','d'),
 ('Chepe Alvarado','Sí','2','0','—','No','20 nov','d'),
 ('Efraín Portillo','Tal vez','1','0','—','No','21 nov','d'),
 ('Rolando Vides','No','0','0','—','—','20 nov','d'),
 ('Ximena Ayala','Revisar','¿1?','0','—','No','21 nov','c'),
 ('Familia Menjívar','Pendiente','—','—','—','—','—',None),
 ('Lucía Hernández','Sí','2','0','Alergia: mariscos','No','21 nov','d')]
def stbadge(s):
    m={'Sí':'badge-yes','No':'badge-no','Tal vez':'badge-maybe','Pendiente':'badge-pending','Revisar':'badge-review'}
    lab={'Sí':'Confirmado','No':'No asiste'}.get(s,s)
    return f'<span class="badge {m[s]}">{lab}</span>'
def energy(e):
    return '<span class="eq" aria-label="Energía '+str(e)+' de 5">'+''.join(f'<b class="{"on" if i<e else ""}" style="height:{6+i*3}px"></b>' for i in range(5))+'</span>'
def playlist(compact=False):
    out='';n=0
    for t,a,e,r,sec in SONGS:
        if sec: out+=f'<li class="sec">{sec}</li>'
        n+=1
        out+=f'<li class="trk"><span class="tn">{n:02d}</span><span class="tt"><b>{t}</b><span class="muted">{a}</span></span>{energy(e)}<span class="req">×{r}</span></li>'
    out+=f'<li class="trk amb"><span class="tn">{I("flag",18)}</span><span class="tt"><b>“la de la boda de mi prima”</b><span>Sin título claro · Revisar</span></span><button class="btn btn-quiet" style="min-height:48px;padding:0 14px;font-size:16px">Editar</button></li>'
    return f'<ol class="playlist">{out}</ol>'
DJ_CSS='''
.playlist{list-style:none}
.playlist .sec{font-size:var(--text-sm);font-weight:700;letter-spacing:var(--tracking-eyebrow);text-transform:uppercase;color:var(--color-primary);padding:var(--space-4) var(--space-6) var(--space-2)}
.trk{display:grid;grid-template-columns:44px 1fr 64px 44px;align-items:center;gap:var(--space-3);min-height:64px;padding:var(--space-2) var(--space-6);border-top:1px solid var(--color-border)}
.trk .tn{font-family:var(--font-display);font-size:var(--text-lg);color:var(--color-text-muted);font-variant-numeric:tabular-nums}
.trk .tt{display:flex;flex-direction:column;line-height:1.3}
.trk .tt .muted{font-size:var(--text-sm)}
.trk .req{font-weight:700;color:var(--color-text-muted);text-align:right;font-size:var(--text-sm)}
.trk.amb{background:var(--color-danger-bg);grid-template-columns:44px 1fr auto}
.trk.amb .tn,.trk.amb .tt span{color:var(--color-danger-fg);font-size:var(--text-sm)}
.eq{display:inline-flex;align-items:flex-end;gap:3px;height:20px}
.eq b{width:7px;border-radius:2px;background:var(--color-border)}
.eq b.on{background:var(--color-primary)}
.arrow{display:flex;justify-content:space-between;padding:var(--space-2) var(--space-6) 0;font-size:var(--text-sm);color:var(--color-text-muted);font-weight:600}
'''
def meals():
    mx=96
    return ''.join(f'<div class="mrow"><span>{m}</span><span class="bar"><i style="width:{v/14*100:.0f}%"></i></span><b class="num">{v}</b></div>' for m,v in MEALS)
M_CSS='''
.mrow{display:grid;grid-template-columns:130px 1fr 36px;align-items:center;gap:var(--space-3);min-height:40px}
.bar{height:12px;border-radius:999px;background:var(--color-neutral-bg);overflow:hidden}
.bar i{display:block;height:100%;background:var(--color-primary);border-radius:999px}
.stackbar{display:flex;height:16px;border-radius:999px;overflow:hidden;gap:3px}
.stackbar i{display:block}
.legend{display:flex;gap:var(--space-4);flex-wrap:wrap;font-size:var(--text-sm);margin-top:var(--space-2);color:var(--color-text-muted)}
.legend span::before{content:"";display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:var(--c)}
'''
SB='<div class="stackbar"><i style="flex:96;background:var(--color-success-fg)"></i><i style="flex:31;background:var(--color-border-strong)"></i><i style="flex:18;background:var(--color-accent-ink)"></i></div><div class="legend"><span style="--c:var(--color-success-fg)">Confirmados 96</span><span style="--c:var(--color-border-strong)">Pendientes 31</span><span style="--c:var(--color-accent-ink)">No asisten 18</span></div>'

# ---------- Headcount desktop ----------
kp=''.join(f'<div class="card kpi"><span class="sm muted" style="font-weight:600">{k}</span><b class="display">{v}</b><span class="muted sm">{s}</span></div>' for k,v,s,_ in KPI)
trs=''.join(f'<tr class="{"review" if s=="Revisar" else ""}"><td><b>{n}</b></td><td>{stbadge(s)}<span class="sub" style="margin-top:4px">{"Respondió "+d if d!="—" else "Sin respuesta"}</span></td><td class="num">{p}<span class="sub">{kn(k)}</span></td><td>{m}</td><td>{r}</td><td>{(DEVICE if src=="d" else CLOUD) if src else "<span class=muted>—</span>"}</td></tr>' for n,s,p,k,m,r,d,src in GUESTS)
body=topnav('Invitados')+f'''<main class="wrapd">
<div class="ph"><div><p class="eyebrow">Sáb 12 dic · faltan 21 días</p><h1 class="display">¿Quién viene?</h1><p>Las confirmaciones cierran el 1 de diciembre.</p></div>
<div class="row gap-3"><button class="btn btn-secondary">{I("chat")}Recordar a pendientes</button><button class="btn btn-primary">{I("plus")}Pegar respuestas</button></div></div>
<div class="kpis">{kp}</div>
<div class="card pad" style="margin-top:var(--space-4)">{SB}</div>
<div class="hgrid">
 <section class="card">
  <div class="cardh"><h2>Invitados</h2><div class="input placeholder search">{I("search")}Buscar por nombre…</div></div>
  <div class="row wrap gap-2 pad" style="padding-bottom:0"><button class="chip on">Todos <span class="count">52</span></button><button class="chip">Confirmados <span class="count">34</span></button><button class="chip">Pendientes <span class="count">11</span></button><button class="chip">No asisten <span class="count">6</span></button><button class="chip">Revisar <span class="count">1</span></button></div>
  <table class="table" style="margin-top:var(--space-3)"><thead><tr><th>Invitación</th><th>Estado</th><th>Personas</th><th>Comida</th><th>Transporte</th><th>Leído</th></tr></thead><tbody>{trs}</tbody></table>
  <div class="row between pad"><span class="muted">Mostrando 8 de 52 invitaciones</span><div class="row gap-2"><button class="btn btn-quiet">Anterior</button><button class="btn btn-quiet">Siguiente</button></div></div>
 </section>
 <aside class="stack gap-6">
  <section class="card"><div class="cardh"><h2>Comida especial</h2><span class="sm muted">de 96 confirmados</span></div><div class="pad">{meals()}<p class="hint" style="margin-top:var(--space-3)">Una persona puede tener más de una. 22 necesitan transporte.</p></div></section>
  <section class="card"><div class="cardh"><div><h2>{I("music",22)} Lista para el DJ</h2><span class="sm muted">8 canciones únicas de 23 pedidos</span></div>{DEVICE}</div>
   <div class="arrow"><span>Lentas</span><span>→</span><span>Para bailar</span></div>
   {playlist()}
   <div class="row gap-3 pad" style="border-top:1px solid var(--color-border)"><button class="btn btn-primary" style="flex:1">{I("download")}Descargar CSV</button><button class="btn btn-secondary" style="flex:1">{I("print")}Imprimir</button></div>
  </section>
 </aside>
</div></main>'''
H_CSS=D_CSS+DJ_CSS+M_CSS+'''
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--space-4)}
.kpi{padding:var(--space-5) var(--space-6);display:flex;flex-direction:column;gap:2px;box-shadow:var(--shadow-sm)}
.kpi b{font-size:var(--text-5xl);line-height:1}
.hgrid{display:grid;grid-template-columns:minmax(0,1fr) 440px;gap:var(--space-6);margin-top:var(--space-6);align-items:start}
.sub{display:block;font-weight:400;font-size:var(--text-sm);color:var(--color-text-muted)}
.search{width:300px;gap:var(--space-2);border-radius:var(--radius-pill);min-height:var(--tap-min)}
.table td{font-size:var(--text-base)}
.table td:first-child,.table th:first-child{padding-left:var(--space-6)}
'''
open('../headcount-desktop.html','w').write(page('Invitados',body,1440,H_CSS))

# ---------- Headcount mobile ----------
kpm=''.join(f'<div class="card kpi"><span class="sm muted" style="font-weight:600">{k}</span><b class="display">{v}</b><span class="muted sm">{s}</span></div>' for k,v,s,_ in KPI)
cards=''.join(f'<li class="gcard{" review" if s=="Revisar" else ""}"><div class="row between gap-2"><b>{n}</b>{stbadge(s)}</div><div class="muted">{p} {'persona' if p=='1' else 'personas'} · {kn(k)} · {m}</div></li>' for n,s,p,k,m,r,d,src in GUESTS[:5])
body=f'''<div class="weave"></div><header class="appbar"><div class="brand" style="font-size:var(--text-lg)"><span class="mono">A&amp;D</span>Boda Lista</div>{LANG}</header>
<main class="mwrap stack gap-4">
 <div><p class="eyebrow">Sáb 12 dic · faltan 21 días</p><h1 class="display" style="font-size:var(--text-3xl)">¿Quién viene?</h1></div>
 <div class="kpim">{kpm}</div>
 <div class="card pad">{SB}</div>
 <section class="card"><div class="cardh"><h2>Comida especial</h2></div><div class="pad">{meals()}</div></section>
 <section class="card"><div class="cardh"><h2>Invitados</h2></div>
  <div class="pad stack gap-3"><div class="input placeholder" style="border-radius:var(--radius-pill);gap:8px">{I("search")}Buscar por nombre…</div>
  <div class="row wrap gap-2"><button class="chip on">Todos</button><button class="chip">Confirmados</button><button class="chip">Pendientes</button><button class="chip">No asisten</button></div></div>
  <ul class="glist">{cards}</ul><div class="pad"><button class="btn btn-quiet btn-block">Ver los 52</button></div></section>
 <section class="card"><div class="cardh"><div><h2>{I("music",22)} Lista para el DJ</h2><span class="sm muted">8 canciones · de lentas a bailables</span></div></div>
  <div class="pad" style="padding-bottom:0">{DEVICE}</div>
  {playlist()}
  <div class="stack gap-2 pad" style="border-top:1px solid var(--color-border)"><button class="btn btn-primary btn-block">{I("download")}Descargar CSV</button><button class="btn btn-secondary btn-block">{I("print")}Imprimir</button></div>
 </section>
</main>
{mobile_tabs("Invitados")}'''
HM_CSS=D_CSS+DJ_CSS+M_CSS+'''
.mwrap{padding:var(--space-4) var(--space-4) var(--space-6)}
.kpim{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-3)}
.kpi{padding:var(--space-4);display:flex;flex-direction:column;box-shadow:var(--shadow-sm)}
.kpi b{font-size:var(--text-4xl);line-height:1.05}
.cardh{padding:var(--space-4) var(--space-5)}
.mrow{grid-template-columns:120px 1fr 30px}
.glist{list-style:none}
.gcard{padding:var(--space-3) var(--space-5);border-top:1px solid var(--color-border);display:flex;flex-direction:column;gap:4px}
.gcard.review{background:var(--color-danger-bg)}
.gcard .muted{font-size:var(--text-sm)}
.trk{grid-template-columns:30px 1fr 44px 34px;padding:var(--space-2) var(--space-4);gap:var(--space-2)}
.playlist .sec{padding-left:var(--space-4)}
.trk.amb{grid-template-columns:30px 1fr auto}
.eq b{width:5px}
'''
open('../headcount-mobile.html','w').write(page('Invitados (móvil)',body,390,HM_CSS))
