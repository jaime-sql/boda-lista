# Boda Lista: mood directions, sources

Phase 1 deliverable. All names, dates and venues in the mockups are fake ("Ana & Diego", "Finca Los Almendros, Santa Tecla", 12 Dec 2026).

## Direction A: Izote y Barro (warm, botanical, Salvadoran)
- Palette: Izote #FBF5EC (bg), Cacao #33221C (text), Barro #A3442A (primary), Cafetal #2F5A2B (on-device badge text, on #E3EDD9), Maíz #C9962B (decor; cloud badge #7A5410 on #F6E7C4), Maquilishuat #EDBFCB (accent; ink #8E3553 on #F7DDE4), Barro suave #F3DCCF (surface).
- Fonts: Fraunces (display, SOFT 100 / WONK) + Figtree (body/UI).
- Why: 2026 trend reports put terracotta, warm cream and sage/olive at the centre of the year's palettes; A grounds that trend in Salvadoran sources: Ilobasco red clay (barro), the flor de izote (national flower), the maquilishuat (national tree, pink blossoms), coffee-farm green and woven San Sebastián textile stripes.

## Direction B: Papel Picado Editorial (modern, editorial, romantic)
- Palette: Papel #F8F3F0 (bg), Ciruela #3B1A2A (text), Rosa maquilishuat #9E3A5F (primary), Rubor #F2D5DD (surface), Champaña #D8C3A0 (decor; ink #7A5E2E), Olivo #4A5530 (on-device badge, on #E6E9D8), Lila #5B4A7A (cloud badge, on #ECE6F3).
- Fonts: Bodoni Moda (display, used at 28px and up only; hairlines are too thin below that) + Jost (body/UI).
- Why: 2026 stationery trend writing reports a move from script calligraphy to high-contrast editorial serifs paired with a quiet sans, and toward muted rose, plum and merlot tones. B uses that with papel picado (Latin American cut-paper banners) as the single ornament, tinted in maquilishuat pink.

## Contrast (WCAG 2.1, computed with mood/contrast.py)
| Pair | A | B |
|---|---|---|
| Body text on background | 13.97:1 | 13.95:1 |
| Muted text on background | 6.69:1 | 6.09:1 |
| White on primary button | 6.14:1 | 6.51:1 |
| Primary as text on background | 5.67:1 | 5.91:1 |
| On-device badge | 6.64:1 | 6.46:1 |
| Cloud badge | 5.53:1 | 6.35:1 |
All pairs pass AA for normal text (4.5:1). Maíz #C9962B and Champaña #D8C3A0 are decorative only and are never used for text.

## Accessibility baked into both phone samples
Body text 18px, chips, toggle and send button at least 48px tall (composer 56px), and the device/cloud badge has an icon plus a text label, so it never relies on color alone.

## Trend and culture references
- Bridal Guide, "The Wedding Color Palettes You're Going to See Everywhere in 2026": https://bridalguide.com/planning/color/wedding-color-palettes-2026/ (terracotta, saffron, garden greens as lead colors)
- Vavril, "2026 Wedding Color Trends: Mocha, Terracotta & Sage": https://vavril.fr/en/wedding-color-trends-mocha-terracotta-sage/ (terracotta + sage + warm white; natural materials)
- Joy, "Fall Wedding Colors 2026": https://withjoy.com/blog/fall-wedding-colors-2026-10-palettes-with-swatches-flowers-styling-tips/ (muted terracotta and dusty rose, plum, merlot)
- Paperlust, "Terracotta Wedding": https://paperlust.co/blog/terracotta-wedding/ (terracotta/olive/cream palette logic)
- Paperlust, "2026 Wedding Invitation Trends": https://paperlust.co/blog/2026-wedding-invitation-trends/ (editorial serif + neutral sans)
- e-invitationwedding, "Wedding Invitation Trends 2026": https://e-invitationwedding.com/blog/wedding-invitation-trends-2026 (script replaced by Didone/editorial serifs)
- ThePerfectWedding, "Wedding Invitation Fonts": https://www.theperfectwedding.com/articles/5966/wedding-invitation-fonts (readability rules: expressive font only for names, info in a clean face)
- Diario El Salvador, "Símbolos patrios": https://diarioelsalvador.com/depais/simbolos-patrios-que-enmarcan-los-203-anos-de-independencia-de-el-salvador/565297 (flor de izote, maquilishuat with pink flowers)
- Ministerio de Cultura, "El maquilíshuat": https://www.cultura.gob.sv/el-maquilishuat-de-arbol-nacional-a-arbol-de-vida/
- Guanacos, "Artesanías de El Salvador": https://guanacos.com/artesanias-de-el-salvador/ (Ilobasco red clay, San Sebastián textiles)
- XPOT, "Artesanos de la Navidad": https://xpot.sv/artesanos-de-la-navidad/ (Ilobasco barro colorado and añil mantles)
- Google Fonts: https://fonts.google.com/specimen/Fraunces · https://fonts.google.com/specimen/Figtree · https://fonts.google.com/specimen/Bodoni+Moda · https://fonts.google.com/specimen/Jost

## References: open-source wedding / RSVP sites (ideas only, nothing copied)
Demos checked live (HTTP 200) on Sat Nov 21, 2026.
1. **rampatra/wedding-website** (about 1.85k stars, GPL-3.0: ideas only, no code). Repo: https://github.com/rampatra/wedding-website · Demo: https://wedding.rampatra.com. **Borrow:** the RSVP flow gated by an invite code, plus one-tap "Add to calendar" and "Get directions" actions next to the event details.
2. **dewanakl/undangan** (about 820 stars, MIT). Repo: https://github.com/dewanakl/undangan · Demo: https://ulems.my.id/?to=Invitado. **Borrow:** a personal link per guest (`?to=Name`) that greets them by name on an "open the invitation" cover, which becomes our per-guest link from the RSVP list.
3. **sakeenah-wedding/template** (about 220 stars, Apache-2.0 per its LICENSE file; React 19, Tailwind v4, Motion). Repo: https://github.com/sakeenah-wedding/template · Demo: https://invitation.sakeenah.site/. **Borrow:** the restrained card layout, a single accent CTA, gentle Motion reveal transitions, and guest attendance tracking with personalized links.
4. **retros-id/simple-wedding-invitation** (about 310 stars). Repo: https://github.com/retros-id/simple-wedding-invitation · Demo: https://simple-wedding-invitation.netlify.app/. **Borrow:** the typography-led hero with names large, date small and tracked wide, and a countdown block. (We use a serif instead of its script.)
5. **nguyenhuugiatri/iphone-wedding-invitation** (2026). Repo: https://github.com/nguyenhuugiatri/iphone-wedding-invitation · Demo: https://iphone-wedding-invitation.vercel.app. **Borrow:** information as glanceable "widgets" (time, place, map, playlist), which suits our quick-question chips and the DJ song list idea.
6. **ZEDLABS-TEKNOLOGI-INDONESIA/wedding-invitation** (Astro + React + SQLite). Repo: https://github.com/ZEDLABS-TEKNOLOGI-INDONESIA/wedding-invitation · Demo listed as https://wedding.zedlabs.id, which **did not respond** when checked. **Borrow:** an admin panel for editing content without redeploying (our info-sheet editor), real-time RSVP tracking, and light/dark mode.

## Phase 2 references (Repo Scout list; used for screens; ideas only, no code, assets or copy)
Licenses were checked through the GitHub API on Nov 21, 2026.
- **Starloss/wedding-invitation** (MIT). Repo: https://github.com/Starloss/wedding-invitation · Demo: https://wedding-invitation-seven-brown.vercel.app. **Used:** the group RSVP pattern (one form per family, a yes/no per member) and song requests in the RSVP form.
- **xsrazy/Wedify** (MIT). Repo: https://github.com/xsrazy/Wedify · Demo: https://wedify.xsrazy.web.id. **Used:** a playlist/tracklist look for the DJ song list, ordered slow to dance. We kept the Direction A colours, not its dark green theme.
- **lfrocharod/wedding-invitation-template** (MIT for code; **its illustrations are not licensed and were not used**). Repo: https://github.com/lfrocharod/wedding-invitation-template · Demo: https://lfrocharod.github.io/wedding-invitation-template/. **Used:** the headcount and RSVP deadline line ("Confirma antes del 1 de diciembre").
- **thesurajdev/wedding-invite** (MIT for code; photos and music excluded). Repo: https://github.com/thesurajdev/wedding-invite · Demo: https://thesurajdev.github.io/wedding-invite/. **Used:** the add-to-calendar button and the reduced-motion setting.
- **nerln/wedding-invite-starter-kit** (MIT). Repo: https://github.com/nerln/wedding-invite-starter-kit · Demo: https://nerln.github.io/wedding-invite-starter-kit/. **Used:** the Maps button, the letter-spaced date line and reduced motion.
- Not used: smith-wedding-demo (no license).

The full asset license list is in tokens/LICENSES.md.
