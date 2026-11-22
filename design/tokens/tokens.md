# Boda Lista design tokens (Direction A, "Izote y Barro")

Files in `tokens/`:
- `tokens.css`: drop-in for `src/styles/tokens.css`. It holds the `@font-face` rules and the CSS variables.
- `tokens.json`: the same values in JSON, for scripts and tests.
- `fonts/`: Fraunces and Figtree as self-hosted woff2 (latin and latin-ext subsets, OFL-1.1).
- `LICENSES.md`: fonts, icons and reference repos with their licenses.

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
- **Placement:** bottom-left of the answer, with "Fuente: <tema>" bottom-right.
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
- **Thresholds:** suggested values are high ≥ 85%, mid 60–84% and low < 60%. ML owns the real cut-off.
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
