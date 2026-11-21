# Boda Lista design tokens (Direction A, "Izote y Barro")

Files in `tokens/`:
- `tokens.css`: drop-in for `src/styles/tokens.css`. It holds the `@font-face` rules and the CSS variables.
- `tokens.json`: the same values in JSON, for scripts and tests.
- `fonts/`: Fraunces and Figtree as self-hosted woff2 (latin and latin-ext subsets, OFL-1.1).
- `LICENSES.md`: fonts, icons and reference repos with their licenses.
- `config.json`: the **single source** for confidence bands, keyed by the `task` values in `data/schema.json` (`guest_question`, `rsvp`, `song`; the prompt log, `/rollup` and the eval output use the same keys, with no mapping table), and for the panel minimum (`analytics.min_sample`). See §4 and §8.

The reference component CSS lives in `screens/components.css` and uses semantic tokens only.

**Install:**
1. Copy `tokens/tokens.css` to `src/styles/tokens.css`.
2. Copy `tokens/fonts/` to `src/styles/fonts/`.
3. Import tokens.css once at the app root.

The fonts load from `./fonts/`, so the guest view keeps its fonts offline. Precache `fonts/*.woff2` in the service worker.

**Switching to Direction B:** replace `tokens.css`, `tokens.json` and `fonts/`, and nothing else. This works because components may only use these token groups: `--color-*`, `--font-*`, `--text-*`, `--space-*`, `--radius-*`, `--shadow-*`, `--duration-*`, `--ease-*`, `--tap-*` and `--pattern-*`. They never use `--palette-*` or raw hex values.

## 1. Colour

### Raw palette (not for components)
| Token | Hex | Name / origin |
|---|---|---|
| `--palette-izote` | #FBF5EC | Linen cream (flor de izote) |
| `--palette-cacao` | #33221C | Cacao brown ink |
| `--palette-cacao-muted` | #6B5148 | Muted ink |
| `--palette-barro` | #A3442A | Ilobasco red clay |
| `--palette-barro-deep` | #86361F | Clay, pressed/hover |
| `--palette-barro-soft` | #F3DCCF | Clay wash |
| `--palette-cafetal` / `-soft` | #2F5A2B / #E3EDD9 | Coffee-leaf green |
| `--palette-maiz` / `-ink` / `-soft` | #C9962B / #7A5410 / #F6E7C4 | Corn gold (#C9962B is decor only) |
| `--palette-maquilishuat` / `maqui-ink` / `maqui-soft` | #EDBFCB / #8E3553 / #F7DDE4 | Maquilishuat blossom |
| `--palette-white` | #FFFDF9 | Warm white |
| `--palette-line` | #E6D6C6 | Hairline |

### Semantic roles
| Token | Value | Alias of |
|---|---|---|
| `--color-bg` | `#FBF5EC` | --palette-izote |
| `--color-surface` | `#FFFDF9` | --palette-white |
| `--color-surface-alt` | `#F3DCCF` | --palette-barro-soft |
| `--color-surface-inverse` | `#33221C` | --palette-cacao |
| `--color-text` | `#33221C` | --palette-cacao |
| `--color-text-muted` | `#6B5148` | --palette-cacao-muted |
| `--color-text-inverse` | `#FBF5EC` | --palette-izote |
| `--color-border` | `#E6D6C6` | --palette-line |
| `--color-border-strong` | `#6B5148` | --palette-cacao-muted |
| `--color-primary` | `#A3442A` | --palette-barro |
| `--color-primary-hover` | `#86361F` | --palette-barro-deep |
| `--color-primary-soft` | `#F3DCCF` | --palette-barro-soft |
| `--color-on-primary` | `#FFFFFF` | — |
| `--color-accent` | `#EDBFCB` | --palette-maquilishuat |
| `--color-accent-soft` | `#F7DDE4` | --palette-maqui-soft |
| `--color-accent-ink` | `#8E3553` | --palette-maqui-ink |
| `--color-decor-gold` | `#C9962B` | --palette-maiz |
| `--color-success-bg` | `#E3EDD9` | --palette-cafetal-soft |
| `--color-success-fg` | `#2F5A2B` | --palette-cafetal |
| `--color-warning-bg` | `#F6E7C4` | --palette-maiz-soft |
| `--color-warning-fg` | `#7A5410` | --palette-maiz-ink |
| `--color-danger-bg` | `#F9E1DE` | — |
| `--color-danger-fg` | `#9B2C2C` | — |
| `--color-neutral-bg` | `#EFE6DB` | — |
| `--color-neutral-fg` | `#33221C` | --palette-cacao |
| `--color-device-bg` | `#E3EDD9` | --palette-cafetal-soft |
| `--color-device-fg` | `#2F5A2B` | --palette-cafetal |
| `--color-cloud-bg` | `#F6E7C4` | --palette-maiz-soft |
| `--color-cloud-fg` | `#7A5410` | --palette-maiz-ink |
| `--color-offline-bg` | `#33221C` | --palette-cacao |
| `--color-offline-fg` | `#FBF5EC` | --palette-izote |
| `--color-focus` | `#8E3553` | --palette-maqui-ink |

### Contrast (WCAG 2.1, measured)
| Pair | Colours | Ratio | Passes |
|---|---|---|---|
| text / bg | `#33221C` on `#FBF5EC` | 13.97:1 | AA text |
| text / surface | `#33221C` on `#FFFDF9` | 14.91:1 | AA text |
| text / surface-alt | `#33221C` on `#F3DCCF` | 11.5:1 | AA text |
| text-muted / bg | `#6B5148` on `#FBF5EC` | 6.69:1 | AA text |
| text-muted / surface | `#6B5148` on `#FFFDF9` | 7.14:1 | AA text |
| text-muted / surface-alt | `#6B5148` on `#F3DCCF` | 5.51:1 | AA text |
| text-muted / danger-bg | `#6B5148` on `#F9E1DE` | 5.82:1 | AA text |
| text-inverse / surface-inverse | `#FBF5EC` on `#33221C` | 13.97:1 | AA text |
| on-primary / primary | `#FFFFFF` on `#A3442A` | 6.14:1 | AA text |
| on-primary / primary-hover | `#FFFFFF` on `#86361F` | 8.2:1 | AA text |
| primary / bg | `#A3442A` on `#FBF5EC` | 5.67:1 | AA text |
| primary / surface | `#A3442A` on `#FFFDF9` | 6.05:1 | AA text |
| primary / surface-alt | `#A3442A` on `#F3DCCF` | 4.67:1 | AA text |
| device-fg / device-bg | `#2F5A2B` on `#E3EDD9` | 6.64:1 | AA text |
| cloud-fg / cloud-bg | `#7A5410` on `#F6E7C4` | 5.53:1 | AA text |
| danger-fg / danger-bg | `#9B2C2C` on `#F9E1DE` | 6.04:1 | AA text |
| accent-ink / accent-soft | `#8E3553` on `#F7DDE4` | 5.9:1 | AA text |
| text / accent-soft | `#33221C` on `#F7DDE4` | 11.84:1 | AA text |
| neutral-fg / neutral-bg | `#33221C` on `#EFE6DB` | 12.27:1 | AA text |
| success-fg / surface | `#2F5A2B` on `#FFFDF9` | 7.89:1 | AA text |
| border-strong / surface (UI 3:1) | `#6B5148` on `#FFFDF9` | 7.14:1 | AA text |
| focus ring / bg (UI 3:1) | `#8E3553` on `#FBF5EC` | 6.96:1 | AA text |
| focus ring / surface (UI 3:1) | `#8E3553` on `#FFFDF9` | 7.42:1 | AA text |
| chip-on border / primary-soft (UI) | `#A3442A` on `#F3DCCF` | 4.67:1 | AA text |
| border (decorative only) | `#E6D6C6` on `#FFFDF9` | 1.4:1 | decorative only |

Rules:
- Text only ever uses a pair from this table that passes AA (4.5:1 or more).
- `--color-border` (#E6D6C6) is decorative only. Inputs, chips and switches use `--color-border-strong` (7.1:1).
- Gold `--color-decor-gold` and pink `--color-accent` are never used for text.
- Status never relies on colour alone. Every badge carries a text label, and AI badges also carry an icon.

## 2. Type
- **Display: Fraunces.** Variable, weights 300–800, with `font-variation-settings: "SOFT" 100, "WONK" 1`. Use it for names, page titles, card titles and big numbers.
- **Body/UI: Figtree.** Variable, weights 400–800.
- **Minimum body size is 18px** (`--text-base`). `--text-sm` (16px) is only for meta text, badges, hints and secondary table lines, never for paragraphs.

| Token | rem | px | Use |
|---|---|---|---|
| `--text-sm` | 1rem | 16 | badges, hints, captions |
| `--text-base` | 1.125rem | 18 | body, inputs, buttons |
| `--text-lg` | 1.25rem | 20 | lead, answer titles, large buttons |
| `--text-xl` | 1.5rem | 24 | card titles |
| `--text-2xl` | 1.875rem | 30 | stepper value, section titles |
| `--text-3xl` | 2.375rem | 38 | page titles |
| `--text-4xl` | 3rem | 48 | mobile KPI numbers (guest hero names use 2.5rem / 40px) |
| `--text-5xl` | 3.75rem | 60 | desktop KPI numbers |

- **Leading:** display 1.1, snug 1.3, body 1.5.
- **Eyebrow:** 16px semibold, uppercase, tracking 0.14em, in the primary colour.
- **Date line:** uppercase with 0.22em letter-spacing (`.date-spaced`), for example "SÁB · 12 · DIC · 2026".

## 3. Space, size, radius, shadow, focus, motion
- **Space:** 4px base. `--space-1` to `--space-20` cover 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 and 80px.
- **Touch:**
  - `--tap-min` is 48px and applies to every interactive element.
  - `--tap-comfy` is 56px, for primary buttons, inputs and the send button on mobile.
- **Containers:**
  - `--container-mobile` is 480px. The guest column centres at this width on desktop.
  - `--container-desktop` is 1280px.
- **Radius:**
  - sm: 8px.
  - md: 14px, for inputs and choice cards.
  - lg: 22px, for cards and chat bubbles.
  - xl: 28px, for the hero.
  - pill: 999px, for buttons, chips and badges.
- **Shadow:** warm cacao tint. Use sm for KPI tiles, md for cards and answers, and lg for dialogs.
- **Focus:**
  - Every control gets `:focus-visible { box-shadow: var(--focus-ring) }`.
  - The ring is a 3px gap in the background colour plus a 3px maquilishuat-ink ring, which measures 6.96:1 on the background.
  - Never remove outlines without adding this ring.
- **Motion:**
  - Durations are fast 120ms (hover), base 200ms (toggles and chips) and slow 320ms (sheets and answer reveal), all with `--ease-standard`.
  - Reduced motion has two triggers: the OS `prefers-reduced-motion` setting, and an in-app **"Menos movimiento"** switch that sets `<html data-motion="reduced">`. Either one sets every duration to 0ms.
  - Music and envelope animations never auto-play.

## 4. Components (see `screens/components.css`)

### AI source badge
This is the key hybrid-AI element. It goes on every AI answer and every parsed row.
- **Variants:** **"En tu teléfono"** is `.badge-device` (green, phone icon). **"En la nube"** is `.badge-cloud` (gold, cloud icon).
- **Exact wording:** use these exact strings, even on desktop. In English they are "On your phone" and "In the cloud".
- **Placement:** bottom-left of the answer, with "Fuente: {tema}" bottom-right (for example "Fuente: Vestimenta").
- **Size:** 32px tall, 16px semibold text.
- **Explaining it:** the badge itself isn't interactive. To explain it, wrap it in a 48px button that opens a short sheet ("Se respondió en tu teléfono, sin internet").

### Answer states
- **Offline:** a `.banner-offline` banner (cacao background, wifi-off icon) at the top of the chat reads "Sin señal. Igual te respondemos desde tu teléfono…". The composer stays enabled, and the answers carry "En tu teléfono".
- **Cloud fallback:** a `.banner-info` banner (gold) appears once per session when the device has no on-device model.
- **I don't know:**
  - The bubble has an accent-soft background and border, and the title exactly "No tengo esa información, pregúntale a los novios" (locked copy, must match the eval gold answer).
  - It has a primary **"Pregúntale a los novios"** button, which opens WhatsApp to the couple's contact from `wedding_info.json → contacts`.
  - Below it is a quiet "Hacer otra pregunta" button.
  - It still carries the source badge.
- **Loading:** `.typing` (three dots) plus "Buscando en la información de la boda…", inside an `aria-live="polite"` container with `aria-busy`.

### Confidence chip and Revisar flag
- **Chip:** `.conf.high|mid|low` shows a 3-bar meter, a label and a percentage, in green, gold or red.
- **Thresholds come from one config file, never from CSS.** `tokens/config.json` has this exact shape (ML's eval PR writes the same file on Tue Nov 24):
  ```json
  {
    "guest_question": { "high": null, "cloud_cutoff": null, "min_n": 20 },
    "rsvp":           { "high": null, "cloud_cutoff": null, "min_n": 20 },
    "song":           { "high": null, "cloud_cutoff": null, "min_n": 20 },
    "analytics": { "min_sample": 20 }
  }
  ```
  - **Bands:** score ≥ `high` → **Alta** (`.conf.high`); `cloud_cutoff` ≤ score < `high` → **Media** (`.conf.mid`); score < `cloud_cutoff` → **Baja** (`.conf.low`) and the item goes **to the cloud**. There is no separate `mid` key.
  - **`high` and `cloud_cutoff` may be `null`** (a number from 0 to 1, or null). ML's `threshold.py` writes both or neither, and if either is null the task has **no threshold** and no partial split. **All three are null now.** Captain's rule is that null stays null until ML's PR writes dev-tuned cut-offs on Tue Nov 24. When a task has no threshold, `band()` returns none, chips render the neutral `.conf-none` "Sin umbral aún" pill instead of Alta / Media / Baja, and routing follows §8 (`no_threshold` / `offline_no_threshold`). Never substitute a default.
  - Mock screens don't read these values for chips. They use `EXAMPLE_BAND` (0.85 / 0.60) in `common.py → conf_example()`, labelled "de ejemplo" (a `title` on each chip plus a dashed mock chip on the screen).
  - `min_n` is ML's **eval** threshold (minimum rows to trust a cut-off). It is not used by the UI.
  - `analytics.min_sample` is the **panel's** "Pocos datos aún" minimum (§8). Keep the two separate.
  - The values stay null until ML posts dev-tuned cut-offs (Tue Nov 24, 6 PM SV). Nothing else changes.
  - Keys match `data/schema.json → task` exactly. `budget` and `seating` have **no key and no fallback** until they're built; any chip they show in mockups uses a design-example band and is labelled as such.
- **How it works:** the app imports `config.json` once and a single helper picks the band: `band(score, feature)` returns `high | mid | low`, and the component renders `.conf.<band>` with `data-confidence="0.71"`. `components.css` only styles the three classes and contains no numbers. The screen generator (`screens/src/common.py → cfg(task)/band(pct, task)/conf(pct, task)`, `MIN_SAMPLE`; `cfg` raises on an unknown key) reads the same file, so the mockups follow the config too.
- **Consistency rule:** a row is routed to the cloud only when its score is below its feature's `cloud_cutoff` (or the reason is `no_model` / `long_input`), so "Media 71% · En la nube" should never appear.
- **Revisar flag:** rows with `ambiguous: true` or low confidence get the **Revisar** badge (`.badge-review`), a red row tint and a 4px left rule.

### Status badges
| Status | Class |
|---|---|
| Confirmado (Sí) | `.badge-yes` |
| No asiste (No) | `.badge-no` |
| Tal vez | `.badge-maybe` |
| Pendiente | `.badge-pending` |
| Revisar | `.badge-review` |

### Buttons and chips
- **Buttons:**
  - `.btn-primary` is clay with white text, `.btn-secondary` has a clay outline, and `.btn-quiet` has an ink outline.
  - They are 48px tall, or 56px with `.btn-lg`.
  - Use one primary button per view.
- **Chips:** `.chip` is 48px tall and toggles with `aria-pressed`. The selected state adds a clay-soft fill and a ✓, so it doesn't rely on colour. Chips are used for quick questions, filters and meal multi-select.

### Form controls
- **Inputs:** `.input` is 56px tall with a 2px strong border and md radius. Labels are always visible above the field, and a placeholder is never the only label.
- **Choice cards:** `.choice` is a 64px radio, used for attending: "Sí, ahí estaremos", "Tal vez, les aviso" and "No podremos ir".
- **Switch:** `.switch` is 60×34px inside a 64px row. It's used for group RSVP members, transport (`needs_ride`) and "Menos movimiento".

### RSVP form
- **Group RSVP:**
  - One form covers the whole invitation, with a switch per member.
  - `party_size` is the number of members switched on.
  - `kids_count` is the number of members flagged as children.
  - Both are shown as summary badges.
  - The deadline line reads "Confirma antes del 1 de diciembre".
- **Songs:** up to 3, each with Título and Artista fields (`songs[i].title`, `songs[i].artist`).

### DJ playlist
- **Rows:** each row is at least 64px, with the number, title and artist, a 5-bar energy meter (`energy` 1–5), and the request count (×n).
- **Sections:**
  - "Lentas · para la cena" (energy 1–2).
  - "Para calentar" (3).
  - "Para bailar" (4–5).
- **Order:** sorted by energy, ascending.
- **Deduplication:** by normalised title and artist.
- **Ambiguous requests:** songs with `title: null` go last, flagged Revisar, with an Editar button.
- **Actions:** **Descargar CSV** and **Imprimir**. The print stylesheet uses black text and no tints.

### Empty, error and decoration
- **Empty states:**
  - No answers: "Aún no hay respuestas. Pega los mensajes de WhatsApp para empezar.", with the izote illustration and a primary button.
  - No songs: "Nadie ha pedido canciones todavía."
- **Error state:** a `.banner` with `--color-danger-*`, reading "No pudimos leer este mensaje. Intenta de nuevo o edítalo a mano." Never show raw errors.
- **Decoration:**
  - `--pattern-weave` is an 8px woven stripe at the top of every screen.
  - The flor de izote line illustration is original.
  - Never use photos of real people.

## 5. Data mapping (locked contract)
| UI | Field |
|---|---|
| Asiste (Sí / No / Tal vez) | `attending`: yes / no / maybe |
| Personas | `party_size` |
| Niños | `kids_count` |
| Comida chips | `meal_restrictions`: vegetarian, vegan, gluten_free, kids_menu, `allergy:<x>` (+ free text) |
| ¿Necesitan transporte? | `needs_ride` |
| Canciones (≤3) | title + artist; `energy` sets the order; `ambiguous` sets Revisar |
| Revisar flag | `ambiguous: true` or low confidence |
| Quick-question chips | the `wedding_info.json` topics: Horario (schedule), Lugar (venue), Vestimenta (dress code), Parqueo (parking), Regalos (gifts), Contactos (contacts) |

## 6. Accessibility checklist
- **Size and contrast:** body text is at least 18px, tap targets are at least 48px, and every text pair passes AA (see the contrast table).
- **Focus:** `:focus-visible` shows a ring on every control, and the tab order follows the visual order.
- **No colour-only meaning:** every badge and status shows text alongside any icon.
- **Language:** `lang="es"` is set, and the ES/EN toggle (`role="group"`, `aria-pressed`) switches `lang`.
- **ARIA:** the chat uses `aria-live="polite"`, radio groups use `role="radiogroup"`, and switches use `role="switch"` with `aria-checked`.
- **Motion:** reduced motion is honoured, both from the OS setting and the in-app switch.
- **Zoom:** at 200% zoom, the 390px mobile layouts must not scroll horizontally.

## 7. Screen index (`screens/png/`, generated by `screens/src/*.py`)
| Screen | Width | Generator |
|---|---|---|
| guest-qa-device, guest-qa-cloud, guest-qa-offline, guest-qa-idk, rsvp-form, rsvp-success, sign-in | 390 | `guest.py` |
| couple-parse, headcount-desktop | 1440 | `couple.py` |
| headcount-mobile | 390 | `couple.py` |
| ai-loaded / ai-loading / ai-empty / ai-error / ai-offline / ai-few / ai-no-threshold `-desktop` | 1440 | `ai.py` |
| ai-loaded / ai-loading / ai-empty / ai-error / ai-offline / ai-few / ai-no-threshold `-mobile` | 390 | `ai.py` |
| budget-quote-desktop, budget-board-desktop | 1440 | `budget.py` |
| budget-quote-mobile, budget-board-mobile | 390 | `budget.py` |

Rebuild: `cd screens/src && python3 guest.py && python3 couple.py && python3 ai.py && python3 budget.py && cd .. && python3 src/render.py && python3 src/overview.py`. `render.py` uses 1440 for names that start with `couple` or end with `desktop`, and 390 for everything else. The checks print loaded fonts, horizontal overflow, clipping and any text under 16px.

**Navigation:** the desktop top nav is Resumen · Respuestas · Invitados · Presupuesto · Cómo responde la IA (`common.topnav`). The mobile tab bar is Inicio · Invitados · Presupuesto · IA (`common.mobile_tabs`).

## 8. "Cómo responde la IA" tab (follows Hack Analytics' panel spec v1.1)
> **All numbers on these screens are EXAMPLE DATA ("Datos de ejemplo").** They are round and invented on purpose (400 answers, 300 on the phone, 0.4 s versus 1.8 s). The mockups show a dashed `.mock-chip` reading "Datos de ejemplo · solo en el diseño". **Do not build the chip or these values.** The real panel renders only the `/rollup` JSON (source = live), as the spec requires.

- **Header:** the eyebrow "Inteligencia híbrida", H1 "Cómo responde la IA", and a period `.seg` toggle with **Todo** and **Últimas 24 h** (the spec's two windows).
- **Three tiles** (`.tile`, in that order):
  1. **Respondido en tu teléfono:** the device share as a % plus "300 de 400 respuestas".
  2. **Llamadas a la nube ahorradas:** the count of device answers.
  3. **Rapidez (mediana):** device p50 versus cloud p50, each labelled with the exact badge, plus p95 as a sub-line.
- **Bar by feature** (`.split`): exactly one row per `/rollup` `by_feature` key, which are the schema `task` values: `guest_question` → **Preguntas de invitados**, `rsvp` → **Confirmaciones**, `song` → **Canciones**. There are no Presupuesto or Mesas rows; budget and seating get rows only once they're built and have keys.
  - **Example numbers:** guest_question 160 / 40, rsvp 90 / 30, song 50 / 30 (device / cloud). The tiles are their sums: 300 of 400 on the phone (75%), 300 cloud calls saved, 100 to the cloud, and the reasons add up to 100 (50 / 35 / 15). `ai.py` computes the tiles from the rows and asserts this.
  - The green segment is `--color-device-fg` (En tu teléfono) and the gold one is `--color-cloud-fg` (En la nube). Both carry white % labels (8.0:1 and 6.8:1), the row carries the text "160 en tu teléfono · 40 en la nube", and the total sits on the right. The meaning never relies on colour alone.
  - The badge legend sits above the rows.
- **Reasons list** ("¿Por qué fue a la nube?"):
  - `no_model` → "El teléfono no tiene el asistente integrado"
  - `low_confidence` → "Respuesta poco segura (bajo el umbral de cada función)". No percentage is shown, because each task has its own cut-off (and some may be null).
  - `no_threshold` → "Sin umbral aún". The task's `high` / `cloud_cutoff` is null, so **every answer goes to cloud Gemini** (Captain's routing rule). The row only appears when some task has no threshold.
  - **Device-side reason `offline_no_threshold`** (not in this list, because the answer didn't go to the cloud): the task has no threshold and the phone is offline, so Nano answers anyway. The reply is labelled "Respuesta poco segura" and logged as route `device`, reason `offline_no_threshold`. The panel names it on the feature row.
  - `long_input` → "Texto muy largo para el teléfono"
  - Each reason shows its count, its share and a thin bar. The raw reason key is shown for the team.
- **Footer:** "Actualizado: 21 nov, 11:00 a. m. (hora SV) · 400 filas", with the model mix as a footnote ("Gemini Nano 300 · Gemini en la nube 100 · Solo uso real").
- **Minimum sample** (`config.json → analytics.min_sample`, 20; not `min_n`): below it, show the raw count plus the `.few-note` "Pocos datos aún" pill, and never a % or percentile. A feature row below it shows a hatched `.split .few` bar reading "Pocos datos aún · 8 respuestas", or "Sin respuestas todavía" at 0. Use `null` from `/rollup` (never 0) as the signal, as the spec says.
- **States:**
  | State | File | What shows |
  |---|---|---|
  | Loaded | ai-loaded-* | as above |
  | Loading | ai-loading-* | `.skeleton` blocks in the exact tile/row/reason shapes, `aria-busy="true"` and "Cargando…" in `aria-live="polite"`. The shimmer stops under reduced motion. |
  | Empty | ai-empty-* | izote, "Aún no hay preguntas", the explanation, a primary "Compartir enlace con invitados" button and a secondary "Pegar respuestas" button |
  | Error | ai-error-* | a `.banner-error` (`role="alert"`) reading "No pudimos actualizar. Te mostramos la última copia guardada, del 21 nov a las 9:00 a. m.", plus "Reintentar". The last snapshot sits below it under `.is-stale` (greyscale filter, so text contrast is unchanged), and the footer says "copia guardada". |
  | Offline | ai-offline-* | a `.banner-offline` (`role="status"`, wifi-off icon) reading "Sin conexión. Te mostramos la última copia guardada, del 21 nov a las 11:00 a. m. Se actualiza sola al volver la señal." The last snapshot sits below under `.is-stale`, and the footer says "copia guardada". There's no retry button, because it refreshes on reconnect. |
  | Sin umbral aún (**fallback only**) | ai-no-threshold-* | Captain says `guest_question` gets a real cut-off on Tue Nov 24 from Data's dev split, so this state only shows if a task's cut-off is still null. Example data (mock chip kept): `guest_question` is null, so 8 answers on the phone (offline, `offline_no_threshold`) and 192 in the cloud (`no_threshold`). `rsvp` 90 / 30 and `song` 50 / 30 use design-example cut-offs, with chips reading "Umbral 60% (ejemplo)" and "Alta desde 85%". Tiles: 148 of 400 on the phone (37%), 148 cloud calls saved, 252 to the cloud. Reasons: no_threshold 192 (76%), no_model 30 (12%), low_confidence 20 (8%), long_input 10 (4%), summing to 252. `ai.py` asserts these totals, and that no_threshold equals guest_question's cloud count and the other reasons equal rsvp + song's cloud count. A `.banner-info` (`role="status"`) reads "Preguntas de invitados aún no tiene umbral. Mientras tanto, sus respuestas van a la nube. Sin conexión responde el teléfono y las marca como «Respuesta poco segura». No las clasificamos en Alta, Media o Baja hasta que haya un umbral." The null row shows the grey `.conf-none` "Sin umbral aún" chip, "No clasificamos en Alta / Media / Baja" and the offline note. **Only the Alta / Media / Baja split is hidden.** The device/cloud bar, latency and cloud reasons still show, because they come from the log's `route` field, not from the cut-off. |
  | Pocos datos aún | ai-few-* | the "Últimas 24 h" window with 12 answers (guest_question 6 / 2, rsvp 3 / 1, song 0 / 0): tiles show "9 de 12", every feature row is hatched, and the reasons show counts only (2 / 1 / 0) |

## 9. Vendors and budget (feature 3)
> **The quotes come from the data pack: `data/vendor_quotes.jsonl` on `main` at `643e68d`** (8 rows, `synthetic: true`, USD). They are synthetic test data, so the screens keep the dashed chip "Datos de ejemplo · cotizaciones de prueba de data/". `screens/src/budget.py` reads the repo file when it exists and otherwise a pinned copy, `screens/src/vendor_quotes.snapshot.jsonl`. **Planeado ($13,000) is a design assumption, not data**, and is always labelled "(ejemplo)". Confidence % on the parsed lines are example values.

- **Status mapping** (from the `status` field):
  | `status` | UI | Badge |
  |---|---|---|
  | `deposit_paid` | **Pendiente**, sub-line "Anticipo pagado" (balance still due) | `.badge-maybe` |
  | `quoted` | **Por aprobar** (not yet accepted) | `.badge-pending` |
  | (none in the pack) | **Pagado** | `.badge-yes`, reserved for a future `paid` status |
  The pack has no deposit amounts or due dates, so the screens show no "Pagado $" amount and no next-payment date. Nothing is invented to fill them.
- **Paste a quote** (budget-quote-*), using `vendor-02` Catering La Cosecha ($3,750, `quoted`):
  - The paste field holds the quote's own text: name, description and total.
  - **What we found:** Proveedor and Categoría (`vendor_type` → Comida), then the concepts the description names (Cena · 150 platos, Cóctel, Barra de café, Menú infantil · Incluido). Each has the "En tu teléfono" badge, a confidence chip and Editar. Budget has no `config.json` key, so the chip uses a **design-example band** (0.85 / 0.60, `EXAMPLE_BAND` in `common.py`, never read from config) and the footnote says "Confianza y bandas de ejemplo de diseño". Prices show "—" / "incluido" because the quote has no per-line prices.
  - **No sum check, IVA or Revisar prompt:** the quote is a single amount with no line prices, no tax note and nothing ambiguous. Instead, a warning-tinted note reads "Un solo monto, sin desglose…" and suggests asking for a per-plate price. The sum check and the IVA/Revisar prompts stay in the component set (`.check`, `.iva`) for quotes that warrant them.
  - **Impact:** "Con esta cotización, el total cotizado es $12,350 de $13,000 planeado (ejemplo)."
  - Actions: Descartar, and **Guardar como "Por aprobar"**. The short quote is read on the device, so there is no cloud terms card.
- **Budget board** (budget-board-*), computed from the 8 rows:
  - KPIs: **Planeado (ejemplo) $13,000** · **Total cotizado $12,350** (8 proveedores) · **Con anticipo pagado $5,800** (2: Hacienda El Sauce $4,200, Luz de Tarde Studio $1,600) · **Disponible $650** "si apruebas todo lo cotizado". Por aprobar: $6,550 (6).
  - **Money bar:** Con anticipo pagado $5,800 / Por aprobar $6,550 / Disponible $650.
  - **Por categoría:** one row per `vendor_type` with its amount and share of the total (Lugar 34%, Comida 30%, Foto y video 13%, Música 7%, Flores 7%, Transporte 4%, Belleza 3%, Pastel 2%).
  - **Proveedores:** Proveedor/categoría | Total | Estado | Qué incluye (`description`), with filter chips Todos 8 / Pendiente 2 / Por aprobar 6. Mobile uses one card per vendor.
  - Actions **Exportar CSV** and **Pegar cotización**; the footnote names the source file and says "Los pagos los marcas tú; la app no mueve dinero."
- **Data consistency (asserted in `budget.py`):** 8 synthetic USD rows; Con anticipo + Por aprobar = Total cotizado ($5,800 + $6,550 = $12,350).
- **Suggested app fields:** the data-pack row as-is (`id, vendor_type, vendor_name, description, amount_usd, status, currency`), plus parser output `items[{concept, qty, confidence, route}]` and optional `paid_amount` / `next_payment` once the pack has them.

## 10. Example data label
Every mock number in `screens/` is fake: the guests, the AI analytics (§8), and the vendor quotes (§9), which are the data pack's synthetic test rows. Only Ana & Diego, Sat Dec 12, 2026, Finca Los Almendros, Santa Tecla are used. No real people or businesses.
