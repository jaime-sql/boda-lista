from common import *
def qa(fname,title,chat,active=None,ph='Escribe tu pregunta…'):
    body=guest_header()+f'<main class="g-main" aria-live="polite">{chat}</main>'+guest_quick(active)+guest_composer(ph)+guest_tabs()
    open(f'../{fname}.html','w').write(page(title,body,390,GUEST_CSS))

qa('guest-qa-device','Preguntas · respuesta en el teléfono',f'''
<div class="bubble-q">¿Cuál es el código de vestimenta?</div>
<div class="bubble-a"><h4>Formal de verano</h4>Ellos con guayabera o camisa clara; ellas con vestido midi o largo en tonos claros. El blanco, solo para la novia. Es en jardín: mejor tacón ancho.
<div class="foot">{DEVICE}<span class="sm muted">Fuente: Vestimenta</span></div></div>''','Vestimenta')

qa('guest-qa-offline','Preguntas · sin señal',f'''
<div class="banner banner-offline" role="status">{I("wifioff",22)}<div><b>Sin señal.</b> Igual te respondemos desde tu teléfono con la información guardada.</div></div>
<div class="bubble-q">¿A qué hora empieza la ceremonia?</div>
<div class="bubble-a"><h4>La ceremonia es a las 4:00 p. m.</h4>Te recomendamos llegar 30 minutos antes.
<ul class="sched"><li><b>3:30 p. m.</b>Llegada y bienvenida</li><li><b>4:00 p. m.</b>Ceremonia en el jardín</li><li><b>5:30 p. m.</b>Cóctel</li><li><b>7:00 p. m.</b>Cena y baile</li></ul>
<div class="foot">{DEVICE}<span class="sm muted">Fuente: Horario</span></div></div>''','Horario')

qa('guest-qa-idk','Preguntas · pregúntale a los novios',f'''
<div class="bubble-q">¿Puedo llevar a mi perrito?</div>
<div class="bubble-a" style="border-color:var(--color-accent);background:var(--color-accent-soft)"><h4>No tengo esa información, pregúntale a los novios</h4>No está en la información de la boda y no queremos inventarte una respuesta.
<div class="stack gap-2" style="margin-top:var(--space-4)"><a class="btn btn-primary btn-block">{I("chat")}Pregúntale a los novios</a><a class="btn btn-quiet btn-block">Hacer otra pregunta</a></div>
<div class="foot">{DEVICE}<span class="sm muted">Sin fuente</span></div></div>''')

qa('guest-qa-cloud','Preguntas · respuesta en la nube',f'''
<div class="banner banner-info">{I("info",22)}<div>Este teléfono no tiene el asistente integrado, así que respondemos desde la nube.</div></div>
<div class="bubble-q">¿Hay parqueo? ¿Cuánto cuesta?</div>
<div class="bubble-a"><h4>Sí, y es gratis</h4>La finca tiene parqueo para 80 carros, con vigilante. Entra por el portón verde sobre la calle principal. Si se llena, hay espacio en el colegio de enfrente.
<div class="foot">{CLOUD}<span class="sm muted">Fuente: Parqueo</span></div></div>
<div class="bubble-q">¿Hay transporte desde San Salvador?</div>
<div class="bubble-a" aria-busy="true"><div class="row gap-3"><span class="typing"><b></b><b></b><b></b></span><span class="muted">Buscando en la información de la boda…</span></div></div>''','Parqueo')

# ---------- RSVP form ----------
RS_CSS=GUEST_CSS+'''
.r-head{padding:var(--space-4) var(--space-4) 0}
.r-head h1{font-size:var(--text-3xl);margin:var(--space-1) 0 var(--space-2)}
.deadline{display:inline-flex;align-items:center;gap:8px;margin-top:var(--space-3);padding:8px 14px;border-radius:var(--radius-pill);background:var(--color-warning-bg);color:var(--color-warning-fg);font-weight:700}
.r-sec{margin:var(--space-4) var(--space-4) 0;padding:var(--space-5)}
.r-sec h2{font-family:var(--font-display);font-variation-settings:var(--font-display-variation);font-size:var(--text-xl);font-weight:600;margin-bottom:var(--space-1)}
.r-sec > p.hint{margin-bottom:var(--space-4)}
.member{display:flex;align-items:center;justify-content:space-between;min-height:64px;border-top:1px solid var(--color-border);gap:var(--space-3)}
.member:first-of-type{border-top:0}
.member small{display:block;font-size:var(--text-sm);color:var(--color-text-muted)}
.sum{display:flex;gap:var(--space-2);margin-top:var(--space-3);flex-wrap:wrap}
.song{display:grid;grid-template-columns:32px 1fr;gap:var(--space-2) var(--space-3);align-items:center;padding:var(--space-3) 0;border-top:1px solid var(--color-border)}
.song:first-of-type{border-top:0}
.song .n{font-family:var(--font-display);font-size:var(--text-xl);color:var(--color-primary);grid-row:span 2}
.r-submit{padding:var(--space-6) var(--space-4) var(--space-4)}
'''
body=guest_header(False)+f'''
<section class="r-head">
  <p class="eyebrow">Confirma tu asistencia</p>
  <h1 class="display">Hola, familia Rivas</h1>
  <p>Su invitación es para <b>4 personas</b>. Una sola respuesta por toda la familia.</p>
  <p class="deadline">{I("cal",20)}Confirma antes del 1 de diciembre</p>
</section>
<section class="card r-sec">
  <h2>¿Nos acompañan?</h2><p class="hint">Sábado 12 de diciembre, 4:00 p. m.</p>
  <div class="stack gap-2" role="radiogroup">
    <div class="choice on" role="radio" aria-checked="true"><span class="dot"></span>Sí, ahí estaremos</div>
    <div class="choice" role="radio"><span class="dot"></span>Tal vez, les aviso</div>
    <div class="choice" role="radio"><span class="dot"></span>No podremos ir</div>
  </div>
</section>
<section class="card r-sec">
  <h2>¿Quiénes vienen?</h2><p class="hint">Toca para marcar quién sí llega.</p>
  <div class="member"><div>Roberto Rivas</div><span class="switch on" role="switch" aria-checked="true"></span></div>
  <div class="member"><div>Carmen de Rivas</div><span class="switch on" role="switch" aria-checked="true"></span></div>
  <div class="member"><div>Sofía Rivas<small>Niña · 7 años</small></div><span class="switch on" role="switch" aria-checked="true"></span></div>
  <div class="member"><div>Mateo Rivas<small>Niño · 3 años</small></div><span class="switch" role="switch" aria-checked="false"></span></div>
  <div class="sum"><span class="badge badge-yes">{I("users",18)}3 personas</span><span class="badge badge-pending">1 niña o niño</span></div>
</section>
<section class="card r-sec">
  <h2>¿Alguna comida especial?</h2><p class="hint">Marca todas las que apliquen.</p>
  <div class="row wrap gap-2">
    <button class="chip on" aria-pressed="true">Vegetariano</button><button class="chip">Vegano</button><button class="chip">Sin gluten</button><button class="chip on" aria-pressed="true">Menú infantil</button><button class="chip on" aria-pressed="true">Alergia</button>
  </div>
  <div class="field" style="margin-top:var(--space-4)"><label class="label">¿A qué tienen alergia?</label><div class="input">Maní (Carmen)</div></div>
</section>
<section class="card r-sec">
  <div class="row between gap-3"><div><h2>¿Necesitan transporte?</h2><p class="hint">Bus desde Metrocentro, San Salvador, 2:45 p. m.</p></div><span class="switch on" role="switch" aria-checked="true"></span></div>
</section>
<section class="card r-sec">
  <h2>{I("music",22)} Pide canciones para la fiesta</h2><p class="hint">Hasta 3. El DJ las ordena de lentas a bailables.</p>
  <div class="song"><span class="n">1</span><div class="input">Bésame mucho</div><div class="input">Luis Miguel</div></div>
  <div class="song"><span class="n">2</span><div class="input">Vivir mi vida</div><div class="input placeholder is-focus">Artista</div></div>
  <div class="song"><span class="n">3</span><div class="input placeholder">Título de la canción</div><div class="input placeholder">Artista</div></div>
</section>
<div class="r-submit stack gap-3"><button class="btn btn-primary btn-lg btn-block">Enviar respuesta</button><p class="hint" style="text-align:center">Pueden cambiarla hasta el 1 de diciembre.</p></div>
'''+guest_tabs('Confirmar')
open('../rsvp-form.html','w').write(page('Confirmar asistencia',body,390,RS_CSS))

body=guest_header(False)+f'''
<section class="ok">
  <div class="ok-art"><div class="ok-check">{I("check",44,3)}</div></div>
  <p class="eyebrow">Respuesta enviada</p>
  <h1 class="display">¡Gracias, familia Rivas!</h1>
  <p>Los esperamos el sábado 12 de diciembre en Finca Los Almendros.</p>
</section>
<section class="card r-sec">
  <h2>Su respuesta</h2>
  <dl class="dl">
    <dt>Asisten</dt><dd><span class="badge badge-yes">Sí</span> 3 personas, 1 niña</dd>
    <dt>Comida</dt><dd>Vegetariano, menú infantil, alergia al maní</dd>
    <dt>Transporte</dt><dd>Sí, bus de las 2:45 p. m.</dd>
    <dt>Canciones</dt><dd>Bésame mucho · Luis Miguel<br>Vivir mi vida · Marc Anthony</dd>
  </dl>
  <a class="btn btn-quiet btn-block" style="margin-top:var(--space-4)">{I("edit")}Cambiar mi respuesta</a>
</section>
<section class="r-submit stack gap-3">
  <a class="btn btn-primary btn-lg btn-block">{I("cal",22)}Agregar al calendario</a>
  <a class="btn btn-secondary btn-lg btn-block">{I("pin",22)}Abrir en Maps</a>
</section>
<section class="card r-sec" style="margin-bottom:var(--space-4)"><div class="row between gap-3"><div><b>Menos movimiento</b><p class="hint">Quita las animaciones de la app.</p></div><span class="switch" role="switch" aria-checked="false"></span></div></section>
'''+guest_tabs('Confirmar')
OK_CSS=RS_CSS+'''
.ok{text-align:center;padding:var(--space-6) var(--space-6) var(--space-2)}
.ok h1{font-size:var(--text-3xl);margin:var(--space-2) 0}
.ok-art{display:grid;place-items:center;margin-bottom:var(--space-4)}
.ok-check{width:104px;height:104px;border-radius:50%;background:var(--color-success-bg);color:var(--color-success-fg);display:grid;place-items:center;box-shadow:0 0 0 10px var(--color-surface-alt)}
.dl{display:grid;grid-template-columns:110px 1fr;gap:var(--space-3) var(--space-3);margin-top:var(--space-3)}
.dl dt{font-weight:600;color:var(--color-text-muted)}
'''
open('../rsvp-success.html','w').write(page('Confirmación enviada',body,390,OK_CSS))

# ---------- Sign-in ----------
G='<svg width="22" height="22" viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.6 5.4 2.6 13.2l7.9 6.2C12.4 13.6 17.7 9.5 24 9.5z"/><path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.2 5.3-4.6 6.9l7.5 5.8c4.4-4 6.8-10 6.8-17.2z"/><path fill="#FBBC05" d="M10.5 28.6c-.5-1.4-.8-3-.8-4.6s.3-3.2.8-4.6l-7.9-6.2C.9 16.6 0 20.2 0 24s.9 7.4 2.6 10.8l7.9-6.2z"/><path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.5-5.8c-2.1 1.4-4.9 2.3-8.4 2.3-6.3 0-11.6-4.1-13.5-9.9l-7.9 6.2C6.6 42.6 14.6 48 24 48z"/></svg>'
body=f'''<div class="weave"></div>
<header class="appbar"><div class="brand" style="font-size:var(--text-lg)"><span class="mono">A&amp;D</span>Boda Lista</div>{LANG}</header>
<main class="si">
  <div class="si-art">{izote(110,144)}</div>
  <p class="eyebrow">Para los novios</p>
  <h1 class="display">Entra a tu boda</h1>
  <p>Mira quién confirmó, qué comida piden y las canciones para el DJ.</p>
  <button class="btn btn-lg btn-block btn-google">{G}Continuar con Google</button>
  <button class="btn btn-lg btn-block btn-quiet">Probar con la cuenta demo</button>
  <p class="hint" style="text-align:center">{I("lock",16)} Solo entran Ana, Diego y quien ellos inviten.</p>
  <div class="si-guest card pad">
    <b>¿Eres invitado?</b>
    <p>No necesitas cuenta. Abre el enlace que te mandaron por WhatsApp.</p>
    <a class="btn btn-secondary btn-block" style="margin-top:var(--space-3)">Ir a las preguntas</a>
  </div>
</main>'''
SI_CSS='''
.si{padding:var(--space-4) var(--space-5) var(--space-8);display:flex;flex-direction:column;gap:var(--space-4)}
.si-art{display:grid;place-items:center;height:180px;border-radius:var(--radius-xl);background:var(--color-surface-alt);position:relative;overflow:hidden}
.si-art::after{content:"";position:absolute;left:0;right:0;bottom:0;height:8px;background:var(--pattern-weave)}
.si h1{font-size:var(--text-3xl);margin-top:calc(-1*var(--space-2))}
.btn-google{background:var(--color-surface);color:var(--color-text);border-color:var(--color-border-strong);gap:var(--space-3)}
.si-guest{margin-top:var(--space-2);box-shadow:none}
.si .hint svg{vertical-align:-2px}
'''
open('../sign-in.html','w').write(page('Entrar',body,390,SI_CSS))
