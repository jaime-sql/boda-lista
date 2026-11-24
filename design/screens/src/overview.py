# Contact sheet of every screen -> screens/overview.png
from playwright.sync_api import sync_playwright
D='/workspace/hack-ux/boda-lista/screens'
G=[('Invitados · F1 preguntas y F2 RSVP (390)',['guest-qa-device','guest-qa-sheet','guest-qa-cloud','guest-qa-offline','guest-qa-idk','rsvp-form','rsvp-success','sign-in'],'m'),
   ('Novios · respuestas y lista (1440 / 390)',['couple-parse','headcount-desktop','headcount-mobile'],'x'),
   ('Cómo responde la IA · escritorio 1440 (cargado, cargando, vacío, error, sin conexión, pocos datos, sin umbral aún)',['ai-loaded-desktop','ai-loading-desktop','ai-empty-desktop','ai-error-desktop','ai-offline-desktop','ai-few-desktop','ai-no-threshold-desktop'],'d'),
   ('Cómo responde la IA · móvil 390',['ai-loaded-mobile','ai-loading-mobile','ai-empty-mobile','ai-error-mobile','ai-offline-mobile','ai-few-mobile','ai-no-threshold-mobile'],'m'),
   ('Proveedores y presupuesto · F3 (1440)',['budget-quote-desktop','budget-board-desktop'],'d'),
   ('Proveedores y presupuesto · F3 (390)',['budget-quote-mobile','budget-board-mobile'],'m')]
sec=''
for t,fs,k in G:
    W=lambda f:300 if (k=='m' or f.endswith('mobile')) else 740
    items=''.join(f'<figure><img src="{f}.png" style="width:{W(f)}px"><figcaption>{f}</figcaption></figure>' for f in fs)
    sec+=(f'<h2>{t}</h2>' if t else '')+f'<div class="row">{items}</div>'
html=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><link rel="stylesheet" href="../../tokens/tokens.css"><style>
body{{margin:0;background:var(--color-bg);color:var(--color-text);font-family:var(--font-body);width:2400px;padding:56px;box-sizing:border-box}}
h1{{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-size:56px;margin:0}}
p.lead{{font-size:22px;color:var(--color-text-muted);margin:8px 0 24px}}
h2{{font-family:var(--font-display);font-size:30px;font-weight:600;margin:48px 0 16px;border-top:2px solid var(--color-border);padding-top:24px}}
.row{{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start}}
figure{{margin:0}} img{{display:block;border-radius:14px;box-shadow:0 6px 24px rgba(51,34,28,.14);border:1px solid var(--color-border)}}
figcaption{{font-size:18px;color:var(--color-text-muted);margin-top:8px;font-weight:600}}
</style></head><body><h1>Boda Lista · Izote y Barro</h1><p class="lead">Todas las pantallas · datos ficticios (Ana &amp; Diego, sáb 12 dic 2026, Finca Los Almendros, Santa Tecla) · números de IA y cotizaciones = datos de ejemplo</p>{sec}</body></html>'''
open(D+'/png/_overview.html','w').write(html)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    pg=b.new_page(viewport={'width':2400,'height':1200})
    pg.goto(f'file://{D}/png/_overview.html',wait_until='networkidle'); pg.evaluate('document.fonts.ready')
    pg.screenshot(path=D+'/overview.png',full_page=True); b.close()
