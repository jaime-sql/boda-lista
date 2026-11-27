import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { RouteBadge } from '../components/RouteBadge';
import { Icon } from '../components/Icon';
import { ToastProvider, useToast } from '../components/ToastProvider';
import type { Route } from '../ai/types';
import { markLastPromptDetails } from '../debug/sessionLog';
import { resolveWeddingInfo } from '../data/loadWeddingInfo';
import type { WeddingInfo } from '../data/types';
import { extractRsvp } from '../features/rsvp/extract';
import { sameExtraction, type RsvpExtraction } from '../features/rsvp/parse';
import { saveRsvp, toSavedRsvp } from '../features/rsvp/save';
import { extractSong } from '../features/song/extract';
import { saveSong, toSavedSong } from '../features/song/save';
import { calendarUrl, dateLine, mapsUrl, partnerInitials, type UiLang } from '../features/qa/sheetView';
import { GUEST_FAILURE, logGuestFailure } from '../lib/guestFailure';
import { useOnline } from '../lib/useOnline';

type Lang = UiLang;
type Step = 'paste' | 'confirm' | 'songs' | 'success';

interface SubmittedSong {
  slot: number;
  title: string | null;
  artist: string | null;
  ambiguous: boolean;
  raw_text: string;
  route: Route;
  unsure: boolean;
}

const CODE_PATTERN = /^[A-Za-z0-9-]{4,40}$/;
const MEALS = ['vegetarian', 'vegan', 'gluten_free', 'kids_menu'] as const;
const MAX_SONGS = 3;

const COPY = {
  es: {
    eyebrow: 'Confirma tu asistencia',
    title: 'Tu invitación',
    hint: 'Pega la respuesta que ya le escribiste a la familia, en español o inglés.',
    deadline: (month: string) => `Confirma antes del 1 de ${month}`,
    message: 'Respuesta',
    code: 'Código de invitación',
    read: 'Leer respuesta',
    reading: 'Leyendo la respuesta…',
    revisa: 'No pude leer esa respuesta. Revisa los campos y complétalos.',
    unsure: 'Respuesta poco segura',
    check: 'Revisa estos campos antes de enviar.',
    attending: '¿Van a la boda?',
    yes: 'Sí, ahí estaremos',
    maybe: 'Todavía no sabemos',
    no: 'No podremos ir',
    party: '¿Cuántas personas?',
    kids: '¿Cuántos niños?',
    meals: 'Comida',
    allergy: 'Alergia (una palabra)',
    ride: '¿Necesitan transporte?',
    rideYes: 'Sí',
    rideNo: 'No',
    next: 'Continuar',
    savingRsvp: 'Guardando…',
    skip: 'Omitir canciones',
    send: 'Enviar respuesta',
    sent: 'Respuesta enviada',
    thanks: 'Gracias por confirmar',
    when: 'Los esperamos',
    attend: 'Asisten',
    transport: 'Transporte',
    calendar: 'Agregar al calendario',
    map: 'Cómo llegar',
    askTab: 'Preguntar',
    confirmTab: 'Confirmar',
    detailsTab: 'Detalles',
    later: 'Esa parte llega después.',
    labels: { vegetarian: 'Vegetariano', vegan: 'Vegano', gluten_free: 'Sin gluten', kids_menu: 'Menú infantil' },
    songsTitle: 'Canciones para el DJ',
    songsHint: 'Escribe hasta 3 canciones que quieras escuchar. Puedes dejarlas en blanco.',
    songsOfflineHint: 'Sin señal: las canciones se revisan en tu teléfono antes de guardarse.',
    songLabel: (n: number) => `Canción ${n}`,
    songPlaceholder: 'Título o "la de Marc Anthony"',
    savingSongs: 'Guardando canciones…',
    songAmbiguous: 'No logré identificar una canción clara, pero la anotamos para revisar.',
    songError: 'No se pudo guardar esa canción.',
    songsSummary: 'Canciones',
    songsSkipped: 'Sin canciones',
    songReviewTag: 'Revisar',
  },
  en: {
    eyebrow: 'Confirm your attendance',
    title: 'Your invitation',
    hint: 'Paste the reply you already sent the family, in Spanish or English.',
    deadline: (month: string) => `Confirm before 1 ${month}`,
    message: 'Reply',
    code: 'Invite code',
    read: 'Read reply',
    reading: 'Reading the reply…',
    revisa: 'No pude leer esa respuesta. Revisa los campos y complétalos.',
    unsure: 'Respuesta poco segura',
    check: 'Check these fields before sending.',
    attending: 'Are you coming?',
    yes: 'Yes, we will be there',
    maybe: 'We are not sure yet',
    no: 'We cannot make it',
    party: 'How many people?',
    kids: 'How many children?',
    meals: 'Food',
    allergy: 'Allergy (one word)',
    ride: 'Do you need a ride?',
    rideYes: 'Yes',
    rideNo: 'No',
    next: 'Continue',
    savingRsvp: 'Saving…',
    skip: 'Skip songs',
    send: 'Send reply',
    sent: 'Reply sent',
    thanks: 'Thank you for confirming',
    when: 'We will see you',
    attend: 'Attending',
    transport: 'Transport',
    calendar: 'Add to calendar',
    map: 'Directions',
    askTab: 'Ask',
    confirmTab: 'RSVP',
    detailsTab: 'Details',
    later: 'That part comes later.',
    labels: { vegetarian: 'Vegetarian', vegan: 'Vegan', gluten_free: 'Gluten free', kids_menu: 'Kids menu' },
    songsTitle: 'Songs for the DJ',
    songsHint: 'Add up to 3 songs you want to hear. You can leave them blank.',
    songsOfflineHint: 'Offline: your device reads the songs before saving.',
    songLabel: (n: number) => `Song ${n}`,
    songPlaceholder: 'Title or "the Marc Anthony song"',
    savingSongs: 'Saving songs…',
    songAmbiguous: 'Could not identify a clear song, but we noted it for review.',
    songError: 'Could not save that song.',
    songsSummary: 'Songs',
    songsSkipped: 'No songs',
    songReviewTag: 'Review',
  },
} as const;

function monthName(iso: string, lang: Lang): string {
  return new Intl.DateTimeFormat(lang === 'es' ? 'es' : 'en', { month: 'long' }).format(new Date(`${iso}T12:00:00`));
}

type Draft = Omit<RsvpExtraction, 'attending'> & { attending: RsvpExtraction['attending'] | '' };

function emptyDraft(): Draft {
  return {
    attending: '',
    party_size: null,
    meal_restrictions: [],
    kids_count: null,
    needs_ride: null,
    ambiguous: true,
    confidence: 0,
  };
}

function RsvpScreen() {
  const online = useOnline();
  const navigate = useNavigate();
  const publish = useToast();
  const [params] = useSearchParams();
  const [lang, setLang] = useState<Lang>('es');
  const [sheet, setSheet] = useState<WeddingInfo | null>(null);
  const [step, setStep] = useState<Step>('paste');
  const [message, setMessage] = useState('');
  const [code, setCode] = useState(params.get('code') ?? '');
  const [draft, setDraft] = useState<Draft | null>(null);
  const [baseline, setBaseline] = useState<Draft | null>(null);
  const [allergy, setAllergy] = useState('');
  const [busy, setBusy] = useState(false);
  const [savingRsvp, setSavingRsvp] = useState(false);
  const [note, setNote] = useState('');
  const [unsure, setUnsure] = useState(false);
  const [failed, setFailed] = useState(false);
  const [songTexts, setSongTexts] = useState<string[]>(['', '', '']);
  const [savingSongs, setSavingSongs] = useState(false);
  const [submittedSongs, setSubmittedSongs] = useState<SubmittedSong[]>([]);
  const copy = COPY[lang];

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    let alive = true;
    resolveWeddingInfo({ online: navigator.onLine })
      .then((info) => {
        if (alive) setSheet(info);
      })
      .catch(() => {
        if (alive) setSheet(null);
      });
    return () => {
      alive = false;
    };
  }, [online]);

  const review = Boolean(draft && (draft.ambiguous || draft.attending === 'maybe'));

  async function readReply() {
    if (!CODE_PATTERN.test(code.trim()) || message.trim().length < 2) return;
    setBusy(true);
    setNote('');
    setUnsure(false);
    setFailed(false);
    try {
      const attempt = await extractRsvp(message.trim(), lang);
      setUnsure(attempt.result.fallbackReason === 'offline_no_threshold');
      if (!attempt.extraction) {
        const blank = emptyDraft();
        setDraft(blank);
        setBaseline(blank);
        setNote(copy.revisa);
      } else {
        setDraft(attempt.extraction);
        setBaseline(attempt.extraction);
        const allergyTag = attempt.extraction.meal_restrictions.find((tag) => tag.startsWith('allergy:'));
        setAllergy(allergyTag ? allergyTag.slice('allergy:'.length) : '');
      }
      setStep('confirm');
    } catch (caught) {
      logGuestFailure(caught);
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!draft || !CODE_PATTERN.test(code.trim())) return;
    const allergyTag = allergy.trim().toLowerCase().replace(/[^a-z0-9_]/g, '');
    const meals = [
      ...draft.meal_restrictions.filter((tag) => !tag.startsWith('allergy:')),
      ...(allergyTag ? [`allergy:${allergyTag}`] : []),
    ];
    if (draft.attending !== 'yes' && draft.attending !== 'no' && draft.attending !== 'maybe') return;
    const next: RsvpExtraction = { ...draft, attending: draft.attending, meal_restrictions: meals };
    const edited =
      baseline?.attending === 'yes' || baseline?.attending === 'no' || baseline?.attending === 'maybe'
        ? !sameExtraction({ ...baseline, attending: baseline.attending }, next)
        : true;
    setSavingRsvp(true);
    setFailed(false);
    try {
      markLastPromptDetails({ edited_by_guest: edited, confidence: next.confidence });
      await saveRsvp(toSavedRsvp(code.trim(), next, edited));
      setDraft(next);
      setSubmittedSongs([]);
      if (next.attending === 'yes' || next.attending === 'maybe') {
        setStep('songs');
      } else {
        setStep('success');
      }
    } catch (caught) {
      logGuestFailure(caught);
      setFailed(true);
    } finally {
      setSavingRsvp(false);
    }
  }

  async function saveSongs() {
    const filled = songTexts
      .map((raw, index) => ({ slot: index + 1, text: raw.trim() }))
      .filter((item) => item.text.length > 0);
    if (filled.length === 0) {
      setSubmittedSongs([]);
      setStep('success');
      return;
    }

    setSavingSongs(true);
    const savedList: SubmittedSong[] = [];
    let anyAmbiguous = false;
    let anyError = false;

    for (const item of filled) {
      try {
        const attempt = await extractSong(item.text, lang);
        const extraction = attempt.extraction ?? {
          title: null,
          artist: null,
          energy: null,
          ambiguous: true,
          confidence: 0,
        };
        await saveSong(toSavedSong(code.trim(), item.slot, extraction, item.text));
        if (extraction.ambiguous || extraction.title === null) {
          anyAmbiguous = true;
        }
        savedList.push({
          slot: item.slot,
          title: extraction.ambiguous ? null : extraction.title,
          artist: extraction.artist,
          ambiguous: extraction.ambiguous || extraction.title === null,
          raw_text: item.text,
          route: attempt.result.route,
          unsure: attempt.result.fallbackReason === 'offline_no_threshold',
        });
      } catch {
        anyError = true;
      }
    }

    setSavingSongs(false);
    if (anyAmbiguous) {
      publish({ title: copy.songAmbiguous });
    }
    if (anyError) {
      publish({ title: copy.songError });
    }
    if (savedList.length === 0 && anyError) {
      return;
    }
    setSubmittedSongs(savedList);
    setStep('success');
  }

  function skipSongs() {
    setSubmittedSongs([]);
    setStep('success');
  }

  function toggleMeal(tag: (typeof MEALS)[number]) {
    setDraft((current) => {
      if (!current) return current;
      const has = current.meal_restrictions.includes(tag);
      return {
        ...current,
        meal_restrictions: has
          ? current.meal_restrictions.filter((item) => item !== tag)
          : [...current.meal_restrictions, tag],
      };
    });
  }

  function updateSong(index: number, value: string) {
    setSongTexts((prev) => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  }

  return (
    <div className="guest">
      <div className="weave" />
      <header className="appbar">
        <div className="mono">{sheet ? partnerInitials(sheet) : '··'}</div>
        <div className="seg" role="group" aria-label={lang === 'es' ? 'Idioma' : 'Language'}>
          <button type="button" aria-pressed={lang === 'es'} onClick={() => setLang('es')}>
            ES
          </button>
          <button type="button" aria-pressed={lang === 'en'} onClick={() => setLang('en')}>
            EN
          </button>
        </div>
      </header>
      <main className="screen">
        {failed ? (
          <div className="banner banner-danger" role="alert">
            <div>
              <b>{GUEST_FAILURE[lang].title}.</b> {GUEST_FAILURE[lang].body}
            </div>
          </div>
        ) : null}
        {step === 'paste' ? (
          <>
            <section className="r-head">
              <p className="eyebrow">{copy.eyebrow}</p>
              <h1>{copy.title}</h1>
              <p className="hint">{copy.hint}</p>
              {sheet ? (
                <p className="deadline">
                  <Icon name="clock" size={18} />
                  {copy.deadline(monthName(sheet.date, lang))}
                </p>
              ) : null}
            </section>
            <section className="r-sec card">
              <label htmlFor="invite-code">{copy.code}</label>
              <input
                id="invite-code"
                className="input"
                value={code}
                autoComplete="off"
                onChange={(event) => setCode(event.target.value)}
              />
              <label htmlFor="rsvp-message">{copy.message}</label>
              <textarea
                id="rsvp-message"
                className="input paste"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
              />
            </section>
            <div className="r-submit">
              <button type="button" className="btn btn-primary btn-block" disabled={busy} onClick={() => void readReply()}>
                {busy ? copy.reading : copy.read}
              </button>
            </div>
          </>
        ) : null}

        {step === 'confirm' && draft ? (
          <>
            <section className="r-head">
              <p className="eyebrow">{copy.eyebrow}</p>
              <h1>{copy.title}</h1>
              {unsure ? <p className="hint">{copy.unsure}</p> : null}
              {note ? <p role="status">{note}</p> : null}
              {review ? <p className="hint">{copy.check}</p> : null}
            </section>
            <section className={`r-sec card${review ? ' review' : ''}`}>
              <h2>{copy.attending}</h2>
              {(['yes', 'maybe', 'no'] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  className={`choice${draft.attending === value ? ' on' : ''}`}
                  aria-pressed={draft.attending === value}
                  onClick={() => setDraft({ ...draft, attending: value })}
                >
                  <span className="dot" />
                  <span>{copy[value]}</span>
                </button>
              ))}
            </section>
            <section className={`r-sec card${review ? ' review' : ''}`}>
              <label htmlFor="party-size">{copy.party}</label>
              <input
                id="party-size"
                className="input"
                inputMode="numeric"
                value={draft.party_size ?? ''}
                onChange={(event) =>
                  setDraft({ ...draft, party_size: event.target.value ? Number(event.target.value) : null })
                }
              />
              <label htmlFor="kids-count">{copy.kids}</label>
              <input
                id="kids-count"
                className="input"
                inputMode="numeric"
                value={draft.kids_count ?? ''}
                onChange={(event) =>
                  setDraft({ ...draft, kids_count: event.target.value ? Number(event.target.value) : null })
                }
              />
            </section>
            <section className="r-sec card">
              <h2>{copy.meals}</h2>
              <div className="chips">
                {MEALS.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className={`chip${draft.meal_restrictions.includes(tag) ? ' on' : ''}`}
                    aria-pressed={draft.meal_restrictions.includes(tag)}
                    onClick={() => toggleMeal(tag)}
                  >
                    {copy.labels[tag]}
                  </button>
                ))}
              </div>
              <label htmlFor="allergy">{copy.allergy}</label>
              <input
                id="allergy"
                className="input"
                value={allergy}
                onChange={(event) => setAllergy(event.target.value)}
              />
            </section>
            <section className="r-sec card">
              <button
                type="button"
                className="ride"
                role="switch"
                aria-checked={Boolean(draft.needs_ride)}
                onClick={() => setDraft({ ...draft, needs_ride: !draft.needs_ride })}
              >
                <span>{copy.ride}</span>
                <span className={`switch${draft.needs_ride ? ' on' : ''}`} />
              </button>
            </section>
            <div className="r-submit">
              <button
                type="button"
                className="btn btn-primary btn-block"
                disabled={draft.attending === '' || savingRsvp}
                onClick={() => void confirm()}
              >
                {savingRsvp ? copy.savingRsvp : draft.attending === 'no' ? copy.send : copy.next}
              </button>
            </div>
          </>
        ) : null}

        {step === 'songs' ? (
          <>
            <section className="r-head">
              <p className="eyebrow">{copy.eyebrow}</p>
              <h1 className="r-songs-title">
                <Icon name="music" size={28} />
                <span>{copy.songsTitle}</span>
              </h1>
              <p className="hint">{copy.songsHint}</p>
              {!online ? <p className="hint">{copy.songsOfflineHint}</p> : null}
            </section>
            <section className="r-sec card">
              {Array.from({ length: MAX_SONGS }, (_, i) => (
                <div key={i} className="song-field">
                  <label htmlFor={`song-${i}`}>{copy.songLabel(i + 1)}</label>
                  <input
                    id={`song-${i}`}
                    className="input"
                    value={songTexts[i]}
                    disabled={savingSongs}
                    placeholder={copy.songPlaceholder}
                    onChange={(event) => updateSong(i, event.target.value)}
                  />
                </div>
              ))}
            </section>
            <div className="r-submit r-songs-actions">
              <button
                type="button"
                className="btn btn-primary btn-block"
                disabled={savingSongs}
                onClick={() => void saveSongs()}
              >
                {savingSongs ? copy.savingSongs : copy.send}
              </button>
              <button
                type="button"
                className="btn btn-quiet btn-block"
                disabled={savingSongs}
                onClick={skipSongs}
              >
                {copy.skip}
              </button>
            </div>
          </>
        ) : null}

        {step === 'success' && draft && draft.attending && sheet ? (
          <section className="ok">
            <div className="ok-check">
              <Icon name="check" size={48} />
            </div>
            <p className="eyebrow">{copy.sent}</p>
            <h1>{copy.thanks}</h1>
            <p>
              {copy.when} {dateLine(sheet.date, lang)} · {sheet.venue.name}
            </p>
            <dl className="card r-sec">
              <div>
                <dt>{copy.attend}</dt>
                <dd>{draft.party_size ?? copy[draft.attending]}</dd>
              </div>
              <div>
                <dt>{copy.meals}</dt>
                <dd>
                  {draft.meal_restrictions
                    .map((tag) =>
                      tag in copy.labels
                        ? copy.labels[tag as keyof typeof copy.labels]
                        : tag.replace(/^allergy:/, ''),
                    )
                    .join(', ') || '—'}
                </dd>
              </div>
              <div>
                <dt>{copy.transport}</dt>
                <dd>{draft.needs_ride === true ? copy.rideYes : draft.needs_ride === false ? copy.rideNo : '—'}</dd>
              </div>
              {draft.attending !== 'no' ? (
                <div className="r-song-summary">
                  <dt>{copy.songsSummary}</dt>
                  <dd>
                    {submittedSongs.length === 0 ? (
                      copy.songsSkipped
                    ) : (
                      <ul className="r-song-list">
                        {submittedSongs.map((item) => (
                          <li key={item.slot} className="r-song-item">
                            <span>
                              {item.title
                                ? `${item.title}${item.artist ? ` · ${item.artist}` : ''}`
                                : `“${item.raw_text}” (${copy.songReviewTag})`}
                            </span>
                            <div className="r-song-meta">
                              <RouteBadge route={item.route} lang={lang} />
                              {item.unsure ? <span className="sm muted">{copy.unsure}</span> : null}
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </dd>
                </div>
              ) : null}
            </dl>
            <a className="btn btn-primary btn-block" href={calendarUrl(sheet)}>
              <Icon name="cal" size={20} />
              {copy.calendar}
            </a>
            <a className="btn btn-quiet btn-block" href={mapsUrl(sheet)}>
              <Icon name="pin" size={20} />
              {copy.map}
            </a>
          </section>
        ) : null}
      </main>
      <nav className="tabbar" aria-label="Secciones">
        <button type="button" onClick={() => navigate('/')}>
          <Icon name="question" size={24} />
          {copy.askTab}
        </button>
        <button type="button" className="on" aria-current="page">
          <Icon name="heart" size={24} />
          {copy.confirmTab}
        </button>
        <button type="button" onClick={() => publish({ title: copy.later })}>
          <Icon name="info" size={24} />
          {copy.detailsTab}
        </button>
      </nav>
    </div>
  );
}

export function RsvpPage() {
  return (
    <ToastProvider>
      <RsvpScreen />
    </ToastProvider>
  );
}

export const UNSURE_LABEL = COPY.es.unsure;
