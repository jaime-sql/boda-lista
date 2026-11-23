# Boda Lista: Devpost visuals (Izote y Barro)

Everything here is made from the real design screens on `design/izote-y-barro` (re-shot at 2x by `src/build.py`), using `tokens/tokens.css` and the self-hosted OFL fonts (Fraunces, Figtree). There are no third-party logos, and product names appear as plain text only.

| File | Size | Use |
| --- | --- | --- |
| `thumbnail-1200x800.png` | 1200×800 (3:2) | Devpost **thumbnail** (Project overview, step 2). PNG, under 5 MB. |
| `thumbnail-1920x1280.png` | 1920×1280 (3:2) | Same thumbnail at higher resolution, if Devpost accepts the larger file. |
| `gallery-1-guest-qa-1920x1280.png` | 1920×1280 | Gallery: guest Q&A answered on the phone vs. in the cloud. |
| `gallery-2-offline-idk-1920x1280.png` | 1920×1280 | Gallery: offline answer on the phone, plus the "No tengo esa información, pregúntale a los novios" card. |
| `gallery-3-rsvp-1920x1280.png` | 1920×1280 | Gallery: household RSVP. |
| `gallery-4-chat-parsing-1920x1280.png` | 1920×1280 | Gallery: couple pastes guest replies and reviews the AI parse (labelled "Confianza de ejemplo"). |
| `gallery-5-ai-tab-1920x1280.png` | 1920×1280 | Gallery: "Cómo responde la IA" tab (example numbers, labelled "Datos de ejemplo"). |
| `video-open-1920x1080.png` | 1920×1080 | Demo video open card (name and tagline, ES + EN). |
| `video-close-1920x1080.png` | 1920×1080 | Demo video close card (repo URL, "Hecho con Firebase AI Logic · Gemini Nano + Gemini", text only). |

Rules applied (#BuildHybridAI 2026 rules and FAQ, read Mon Nov 23, 2026):
- **No third-party logos or trademarks** in the video or submission, and nothing that implies sponsorship. Firebase and Gemini appear only as plain "built with" text, and no logos are used. The sign-in screen (Google "G") is not used. The chat-parsing crop leaves out the WhatsApp wording.
- **English:** all submission materials must be in English or include an English translation, so every image carries an English line.
- **Video:** at most 3 minutes (only the first 3 are evaluated), public on YouTube, in English or with English subtitles, and showing the app working on its platform. These cards are bookends only; keep them short (about 3 s each).
- **Thumbnail** (Devpost help): JPG, PNG or GIF, 5 MB max, 3:2 ratio recommended.
- **Honesty:** these are design screens with fictional data (Ana & Diego), and each image says so. Example metrics keep a "Datos de ejemplo · Sample data" label. There are no testimonials and no real results. The rules require the project to "function as depicted", so swap in real app captures if the shipped UI differs.

Rebuild: `cd devpost/src && python3 build.py` (needs Playwright and /usr/bin/google-chrome; it reads ../../screens and ../../tokens).
