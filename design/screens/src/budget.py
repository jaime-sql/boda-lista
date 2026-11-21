from common import *
import json, os
# Vendor quotes: the data pack's data/vendor_quotes.jsonl (synthetic test data, on main at 643e68d).
# Reads the repo copy when present, else the pinned snapshot next to this file.
_here=os.path.dirname(os.path.abspath(__file__))
_src=[os.path.join(_here,'../../../data/vendor_quotes.jsonl'),os.path.join(_here,'vendor_quotes.snapshot.jsonl')]
QUOTES=[json.loads(l) for l in open(next(p for p in _src if os.path.exists(p))) if l.strip()]
assert len(QUOTES)==8 and all(q['synthetic'] and q['currency']=='USD' for q in QUOTES)
def usd(x): return '$'+f'{x:,.0f}' if float(x).is_integer() else '$'+f'{x:,.2f}'
TYPE={'venue':'Lugar','catering':'Comida','music':'Música','photo_video':'Foto y video','flowers':'Flores','cake':'Pastel','beauty':'Belleza','transport':'Transporte'}
PLAN=13000  # DESIGN ASSUMPTION, shown as "ejemplo". The data pack has no planned budget.
TOTAL=sum(q['amount_usd'] for q in QUOTES)
HIRED=sum(q['amount_usd'] for q in QUOTES if q['status']=='deposit_paid')
OPEN=sum(q['amount_usd'] for q in QUOTES if q['status']=='quoted')
LEFT=PLAN-TOTAL
assert HIRED+OPEN==TOTAL
N_HIRED=sum(q['status']=='deposit_paid' for q in QUOTES); N_OPEN=len(QUOTES)-N_HIRED
ST={'deposit_paid':'<span class="badge badge-yes">'+I("check",16)+'Anticipo pagado</span>','quoted':'<span class="badge badge-pending">'+I("receipt",16)+'Por aprobar</span>'}
MOCK='<span class="mock-chip">Cotizaciones de prueba · data/ del repo</span>'
# The quote shown in the paste flow: catering (status quoted)
Q=next(q for q in QUOTES if q['id']=='vendor-02')
QUOTE=f"{Q['vendor_name']}\n{Q['description']}\nTotal: {usd(Q['amount_usd'])} USD"
# What the parser can honestly pull from that text: concepts, no per-line prices.
ITEMS=[('Cena','150 platos',95),('Cóctel','—',91),('Barra de café','—',90),('Menú infantil','Incluido',88)]
CSS='''
.wrapd{padding:var(--space-8) var(--space-10) var(--space-12)}
.ph{display:flex;align-items:flex-end;justify-content:space-between;gap:var(--space-6);margin-bottom:var(--space-6);flex-wrap:wrap}
.ph h1{font-size:var(--text-3xl);margin-top:var(--space-1)}
.ph p{color:var(--color-text-muted);margin-top:var(--space-1)}
.cardh{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4);padding:var(--space-5) var(--space-6);border-bottom:1px solid var(--color-border);flex-wrap:wrap}
.cardh h2{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;font-size:var(--text-xl)}
.paste{font-size:var(--text-sm);line-height:1.55;resize:none;min-height:560px;font-family:var(--font-body);padding:var(--space-4);white-space:pre-wrap;align-items:flex-start}
.qgrid{display:grid;grid-template-columns:minmax(0,0.85fr) minmax(0,1.4fr);gap:var(--space-6);align-items:start}
.items{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(0,1.1fr) 90px 110px minmax(0,1.5fr) 72px;align-items:stretch}
.items>div{padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--color-border);min-height:72px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.items>.th{min-height:auto;font-size:var(--text-sm);font-weight:600;color:var(--color-text-muted);border-bottom:1.5px solid var(--color-border-strong)}
.items>.rv{background:var(--color-danger-bg)}
.items>.rv.first{box-shadow:inset 4px 0 0 var(--color-danger-fg)}
.num{justify-content:flex-end;font-variant-numeric:tabular-nums}
.check{display:flex;gap:var(--space-3);align-items:center;padding:var(--space-4) var(--space-6);background:var(--color-success-bg);color:var(--color-success-fg);font-weight:600}
.total{display:flex;justify-content:space-between;align-items:baseline;padding:var(--space-4) var(--space-6);border-top:1px solid var(--color-border)}
.total b{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-size:var(--text-3xl);font-weight:600}
.iva{margin:var(--space-4) var(--space-6);padding:var(--space-4);border-radius:var(--radius-md);background:var(--color-danger-bg);display:flex;gap:var(--space-4);align-items:center;flex-wrap:wrap}
.iva p{flex:1;min-width:240px}
.terms{list-style:none;padding:0 var(--space-6) var(--space-4)}
.terms li{display:flex;gap:var(--space-3);padding:var(--space-2) 0;align-items:flex-start}
.terms li svg{flex:none;margin-top:3px;color:var(--color-cloud-fg)}
.vf{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--space-4);padding:var(--space-5) var(--space-6)}
.impact{padding:var(--space-4) var(--space-6);border-top:1px solid var(--color-border);display:flex;gap:var(--space-3);align-items:center;flex-wrap:wrap}
.acts{display:flex;gap:var(--space-3);justify-content:flex-end;padding:var(--space-5) var(--space-6);border-top:1px solid var(--color-border);flex-wrap:wrap}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--space-4)}
.kpi{padding:var(--space-5) var(--space-6);box-shadow:var(--shadow-sm);display:flex;flex-direction:column;gap:4px}
.kpi .k{font-size:var(--text-sm);font-weight:600;color:var(--color-text-muted)}
.kpi .v{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-weight:600;font-size:var(--text-4xl);line-height:1.05;font-variant-numeric:tabular-nums}
.kpi .s{font-size:var(--text-sm);color:var(--color-text-muted)}
.kpi.hl{background:var(--color-success-bg)}
.money-bar{display:flex;height:36px;border-radius:var(--radius-sm);overflow:hidden;gap:2px;margin:var(--space-5) 0 var(--space-2)}
.money-bar span{display:flex;align-items:center;padding:0 12px;font-weight:700;font-size:var(--text-sm);white-space:nowrap}
.mb-paid{background:var(--color-success-fg);color:var(--color-on-primary)}
.mb-due{background:var(--color-warning-fg);color:var(--color-on-primary)}
.mb-left{background:repeating-linear-gradient(135deg,var(--color-neutral-bg) 0 8px,var(--color-surface) 8px 16px);border:1px dashed var(--color-border-strong);color:var(--color-text)}
.mlegend{display:flex;gap:var(--space-5);flex-wrap:wrap;font-size:var(--text-sm);color:var(--color-text-muted)}
.mlegend i{display:inline-block;width:14px;height:14px;border-radius:4px;margin-right:6px;vertical-align:-2px}
.bgrid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.9fr);gap:var(--space-6);margin-top:var(--space-6);align-items:start}
.cat{padding:var(--space-3) var(--space-6);border-top:1px solid var(--color-border);display:grid;grid-template-columns:1fr auto;gap:6px var(--space-3)}
.cat .bar{grid-column:1/-1;height:12px;border-radius:999px;background:var(--color-neutral-bg);overflow:hidden}
.cat .bar i{display:block;height:100%;background:var(--color-primary)}
.cat .meta{grid-column:1/-1;font-size:var(--text-sm);color:var(--color-text-muted);display:flex;justify-content:space-between;gap:var(--space-3);flex-wrap:wrap}
.vt{display:grid;grid-template-columns:minmax(0,1.3fr) 100px minmax(0,1fr) minmax(0,1.9fr)}
.vt>div{padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--color-border);min-height:72px;display:flex;flex-direction:column;justify-content:center;gap:2px}
.vt>.th{min-height:auto;font-size:var(--text-sm);font-weight:600;color:var(--color-text-muted);border-bottom:1.5px solid var(--color-border-strong)}
.vt .badge{align-self:flex-start}
.vt .sub{font-size:var(--text-sm);color:var(--color-text-muted)}
.vt .num{align-items:flex-end;text-align:right}
.filters{display:flex;gap:var(--space-2);flex-wrap:wrap}
'''
M_CSS='''
.wrapd{padding:var(--space-4) var(--space-4) var(--space-8)}
.ph h1{font-size:var(--text-2xl)}
.kpis{grid-template-columns:1fr 1fr;gap:var(--space-3)}
.kpi{padding:var(--space-4)}
.kpi .v{font-size:var(--text-2xl)}
.bgrid,.qgrid{grid-template-columns:1fr}
.cardh{padding:var(--space-4) var(--space-5)}
.cat{padding:var(--space-3) var(--space-5)}
.vc{padding:var(--space-4) var(--space-5);border-top:1px solid var(--color-border);display:grid;grid-template-columns:1fr auto;gap:6px var(--space-3);align-items:center}
.vc .sub{font-size:var(--text-sm);color:var(--color-text-muted)}
.vc .full{grid-column:1/-1;display:flex;justify-content:space-between;gap:var(--space-3);font-size:var(--text-sm);color:var(--color-text-muted);flex-wrap:wrap}
.paste{min-height:0;height:240px;overflow:hidden}
.ic{padding:var(--space-4) var(--space-5);border-top:1px solid var(--color-border);display:grid;grid-template-columns:1fr auto;gap:8px var(--space-3)}
.ic.rv{background:var(--color-danger-bg);box-shadow:inset 4px 0 0 var(--color-danger-fg)}
.ic .row2{grid-column:1/-1;display:flex;gap:var(--space-2);flex-wrap:wrap;align-items:center}
.ic .sub{font-size:var(--text-sm);color:var(--color-text-muted)}
.iva,.check{margin-left:var(--space-5);margin-right:var(--space-5)}
.check{margin:0;padding:var(--space-4) var(--space-5)}
.terms{padding:0 var(--space-5) var(--space-4)}
.vf{grid-template-columns:1fr;padding:var(--space-4) var(--space-5)}
.total,.impact{padding-left:var(--space-5);padding-right:var(--space-5)}
.impact{flex-wrap:nowrap;align-items:flex-start}
.sticky{position:static;background:var(--color-surface);border-top:1px solid var(--color-border);padding:var(--space-3) var(--space-4);display:flex;gap:var(--space-3)}
.sticky .btn{flex:1}
'''
EDIT=f'<button class="btn btn-icon btn-quiet" aria-label="Editar línea">{I("edit",20)}</button>'
def vendor_fields():
    return f'''<div class="vf" style="grid-template-columns:repeat(2,minmax(0,1fr))"><div class="field"><label class="label">Proveedor</label><div class="input">{Q['vendor_name']}</div></div><div class="field"><label class="label">Categoría</label><div class="input">{TYPE[Q['vendor_type']]}</div></div></div>'''
NODESG=f'''<div class="iva" style="background:var(--color-warning-bg);color:var(--color-warning-fg)">{I("info",22)}<p><b>Un solo monto, sin desglose.</b> La cotización no trae precio por línea, así que no hay suma que comprobar. Si quieres comparar con otro proveedor, pídeles el precio por plato.</p></div>'''
def impact():
    return f'Con esta cotización, el total cotizado es <b>{usd(TOTAL)}</b> de <b>{usd(PLAN)}</b> planeado (ejemplo).'
def quote_desktop():
    th=''.join(f'<div class="th">{h}</div>' for h in ['Concepto','Cantidad','Precio','Subtotal','Leído y confianza',''])
    rows=''.join(f'<div class="first"><b>{n}</b></div><div>{q}</div><div class="num muted">—</div><div class="num muted">incluido</div><div>{DEVICE}{conf(c,"budget")}</div><div>{EDIT}</div>' for n,q,c in ITEMS)
    return f'''{topnav("Presupuesto")}<main class="wrapd">
<div class="ph"><div><p class="eyebrow">Proveedores y presupuesto</p><h1 class="display">Pegar una cotización</h1><p>Pega el texto que te mandó el proveedor. Lo ordenamos para que lo revises.</p></div><div class="row wrap gap-3">{MOCK}</div></div>
<div class="qgrid">
<section class="card pad" style="display:flex;flex-direction:column;gap:var(--space-4)"><label class="label" for="q">Texto de la cotización (WhatsApp, correo o PDF copiado)</label><div id="q" class="input paste" style="min-height:260px">{QUOTE}</div><div class="banner banner-info">{I("phone",22)}<span>Las cotizaciones cortas se leen en tu teléfono, sin internet.</span></div><div class="row gap-3 wrap"><button class="btn btn-primary btn-lg">{I("sparkle")}Leer cotización</button><button class="btn btn-quiet btn-lg">Borrar</button></div></section>
<div style="display:flex;flex-direction:column;gap:var(--space-6)">
<section class="card"><div class="cardh"><h2>Lo que encontramos</h2>{DEVICE}</div>{vendor_fields()}<div class="items">{th}{rows}</div>
{NODESG}
<div class="total"><span>Total de la cotización</span><b>{usd(Q['amount_usd'])}</b></div>
<div class="impact">{I("wallet",22)}<span>{impact()}</span></div>
<div class="acts"><button class="btn btn-quiet btn-lg">Descartar</button><button class="btn btn-primary btn-lg">{I("check")}Guardar como “Por aprobar”</button></div></section>
<p class="sm muted">Los porcentajes de confianza son de ejemplo. El texto viene de <code>data/vendor_quotes.jsonl</code> ({Q['id']}), datos de prueba.</p>
</div></div></main>'''
def quote_mobile():
    cards=''.join(f'<div class="ic"><div><b>{n}</b><div class="sub">{q}</div></div><span class="sub">incluido</span><div class="row2">{DEVICE}{conf(c,"budget")}</div></div>' for n,q,c in ITEMS)
    return f'''{mobile_appbar()}<main class="wrapd">
<div class="ph"><div><p class="eyebrow">Presupuesto</p><h1 class="display">Pegar una cotización</h1></div>{MOCK}</div>
<section class="card pad" style="display:flex;flex-direction:column;gap:var(--space-3)"><label class="label" for="q">Texto de la cotización</label><div id="q" class="input paste" style="height:auto;min-height:180px">{QUOTE}</div><button class="btn btn-primary btn-lg btn-block">{I("sparkle")}Leer cotización</button></section>
<section class="card" style="margin-top:var(--space-5)"><div class="cardh"><h2>Lo que encontramos</h2>{DEVICE}</div>{vendor_fields().replace('repeat(2,minmax(0,1fr))','1fr')}{cards}
{NODESG}<div class="total"><span>Total</span><b>{usd(Q['amount_usd'])}</b></div><div class="impact">{I("wallet",22)}<span>Total cotizado: {usd(TOTAL)} de {usd(PLAN)} (ejemplo).</span></div></section>
<p class="sm muted" style="margin-top:var(--space-3)">Confianza de ejemplo · texto de data/ ({Q['id']}).</p></main>
<div class="sticky"><button class="btn btn-secondary btn-lg">Descartar</button><button class="btn btn-primary btn-lg">Guardar</button></div>{mobile_tabs("Presupuesto")}'''

def kpis():
    return f'''<div class="kpis"><div class="card kpi"><span class="k">Planeado (ejemplo)</span><span class="v">{usd(PLAN)}</span><span class="s">Supuesto de diseño</span></div><div class="card kpi"><span class="k">Total cotizado</span><span class="v">{usd(TOTAL)}</span><span class="s">{len(QUOTES)} proveedores</span></div><div class="card kpi"><span class="k">Con anticipo pagado</span><span class="v">{usd(HIRED)}</span><span class="s">{N_HIRED} proveedores · Por aprobar: {usd(OPEN)}</span></div><div class="card kpi hl"><span class="k">Disponible</span><span class="v">{usd(LEFT)}</span><span class="s">Si apruebas todo lo cotizado</span></div></div>'''
def mbar():
    return f'''<div class="money-bar" role="img" aria-label="Con anticipo {usd(HIRED)}, por aprobar {usd(OPEN)}, disponible {usd(LEFT)} de {usd(PLAN)}"><span class="mb-paid" style="flex:{HIRED}">{usd(HIRED)}</span><span class="mb-due" style="flex:{OPEN}">{usd(OPEN)}</span><span class="mb-left" style="flex:{max(LEFT,0)}">{usd(LEFT)}</span></div><div class="mlegend"><span><i style="background:var(--color-success-fg)"></i>Con anticipo pagado</span><span><i style="background:var(--color-warning-fg)"></i>Por aprobar</span><span><i style="background:var(--color-neutral-bg);border:1px dashed var(--color-border-strong)"></i>Disponible</span></div>'''
def cats():
    out=''
    for q in sorted(QUOTES,key=lambda q:-q['amount_usd']):
        a=q['amount_usd']
        out+=f'<div class="cat"><b>{TYPE[q["vendor_type"]]}</b><span class="money">{usd(a)}</span><span class="bar"><i style="width:{a*100/TOTAL:.0f}%"></i></span><span class="meta"><span>{a*100/TOTAL:.0f}% del total cotizado</span></span></div>'
    return f'<section class="card"><div class="cardh"><h2>Por categoría</h2></div>{out}</section>'
def board_desktop():
    th=''.join(f'<div class="th{" num" if h=="Total" else ""}">{h}</div>' for h in ['Proveedor','Total','Estado','Qué incluye'])
    rows=''.join(f'<div><b>{q["vendor_name"]}</b><span class="sub">{TYPE[q["vendor_type"]]}</span></div><div class="num money"><b>{usd(q["amount_usd"])}</b></div><div>{ST[q["status"]]}</div><div class="sub" style="color:var(--color-text)">{q["description"]}</div>' for q in QUOTES)
    return f'''{topnav("Presupuesto")}<main class="wrapd">
<div class="ph"><div><p class="eyebrow">Proveedores y presupuesto</p><h1 class="display">Presupuesto</h1><p>Total cotizado contra lo planeado, y qué proveedores ya tienen anticipo.</p></div><div class="row wrap gap-3">{MOCK}<button class="btn btn-secondary btn-lg">{I("download")}Exportar CSV</button><button class="btn btn-primary btn-lg">{I("receipt")}Pegar cotización</button></div></div>
{kpis()}<section class="card pad" style="margin-top:var(--space-6)"><div class="row" style="justify-content:space-between;flex-wrap:wrap;gap:var(--space-3)"><h2 class="display" style="font-size:var(--text-xl);font-weight:600">{usd(TOTAL)} cotizados de {usd(PLAN)} (ejemplo)</h2><span class="muted">{TOTAL*100/PLAN:.0f}% del presupuesto</span></div>{mbar()}</section>
<div class="bgrid">{cats()}<section class="card"><div class="cardh"><h2>Proveedores · {len(QUOTES)}</h2><div class="filters"><span class="chip on">Todos {len(QUOTES)}</span><span class="chip">Anticipo pagado {N_HIRED}</span><span class="chip">Por aprobar {N_OPEN}</span></div></div><div class="vt">{th}{rows}</div></section></div>
<p class="sm muted" style="margin-top:var(--space-6)">Montos en dólares (USD). Cotizaciones de prueba de <code>data/vendor_quotes.jsonl</code>; el planeado es un ejemplo de diseño. Los pagos los marcas tú; la app no mueve dinero.</p></main>'''
def board_mobile():
    vc=''.join(f'<div class="vc"><div><b>{q["vendor_name"]}</b><div class="sub">{TYPE[q["vendor_type"]]} · {usd(q["amount_usd"])}</div></div>{ST[q["status"]]}<div class="full"><span>{q["description"]}</span></div></div>' for q in QUOTES)
    return f'''{mobile_appbar()}<main class="wrapd">
<div class="ph"><div><p class="eyebrow">Proveedores</p><h1 class="display">Presupuesto</h1></div>{MOCK}</div>
{kpis()}<section class="card pad" style="margin-top:var(--space-4)"><b>{usd(TOTAL)} cotizados de {usd(PLAN)} (ejemplo)</b>{mbar()}</section>
<button class="btn btn-primary btn-lg btn-block" style="margin-top:var(--space-4)">{I("receipt")}Pegar cotización</button>
<section class="card" style="margin-top:var(--space-5)"><div class="cardh"><h2>Proveedores · {len(QUOTES)}</h2></div><div class="filters" style="padding:var(--space-3) var(--space-5)"><span class="chip on">Todos</span><span class="chip">Anticipo {N_HIRED}</span><span class="chip">Por aprobar {N_OPEN}</span></div>{vc}</section>
<div style="margin-top:var(--space-5)">{cats()}</div></main>{mobile_tabs("Presupuesto")}'''
for name,html,w,css in [('budget-quote-desktop',quote_desktop(),1440,CSS),('budget-quote-mobile',quote_mobile(),390,CSS+M_CSS),('budget-board-desktop',board_desktop(),1440,CSS),('budget-board-mobile',board_mobile(),390,CSS+M_CSS)]:
    open(f'../{name}.html','w').write(page(name,html,w,css))
