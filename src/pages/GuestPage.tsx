import * as Form from '@radix-ui/react-form';
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { ask } from '../ai/hybrid';
import type { AskContext, AskResult, Route } from '../ai/types';
import { probeDeviceModel, type DeviceAvailability } from '../ai/device';
import { Icon, Izote } from '../components/Icon';
import { RouteBadge } from '../components/RouteBadge';
import { useToast } from '../components/ToastProvider';
import { resolveWeddingInfo } from '../data/loadWeddingInfo';
import type { WeddingInfo } from '../data/types';
import { getFirebaseProblem } from '../firebase/client';
import { missingEnv } from '../firebase/config';
import { UNKNOWN_ANSWER, buildQaSystemPrompt } from '../features/qa/prompt';
import {
  calendarUrl,
  ceremonyItem,
  dateLine,
  formatClock,
  mapsUrl,
  partnerInitials,
  personName,
  venueLine,
  whatsAppUrl,
  type UiLang,
} from '../features/qa/sheetView';
import { useOnline } from '../lib/useOnline';

const TOPICS = ['schedule', 'venue', 'dress', 'parking', 'gifts', 'contacts'] as const;
type Topic = (typeof TOPICS)[number];

const TOPIC_ICON = {
  schedule: 'clock',
  venue: 'pin',
  dress: 'shirt',
  parking: 'parking',
  gifts: 'gift',
  contacts: 'phonecall',
} as const;

const COPY = {
  es: {
    eyebrow: 'Nos casamos',
    calendar: 'Al calendario',
    directions: 'Cómo llegar',
    quick: 'Preguntas rápidas',
    topics: {
      schedule: 'Horario',
      venue: 'Lugar',
      dress: 'Vestimenta',
      parking: 'Parqueo',
      gifts: 'Regalos',
      contacts: 'Contactos',
    },
    questions: {
      schedule: '¿Cuál es el horario?',
      venue: '¿Dónde es la boda?',
      dress: '¿Cuál es el código de vestimenta?',
      parking: '¿Hay parqueo?',
      gifts: '¿Qué podemos regalar?',
      contacts: '¿A quién contacto?',
    },
    placeholder: 'Escribe tu pregunta…',
    label: 'Tu pregunta',
    send: 'Enviar',
    emptyField: 'Escribe una pregunta.',
    searching: 'Buscando en la información de la boda…',
    cloudBanner: 'Este teléfono no tiene el asistente integrado, así que respondemos desde la nube.',
    offlineLead: 'Sin señal.',
    offlineRest: 'Igual te respondemos desde tu teléfono con la información guardada.',
    idkBody: 'No está en la información de la boda y no queremos inventarte una respuesta.',
    askCouple: 'Pregúntale a los novios',
    another: 'Hacer otra pregunta',
    noSource: 'Sin fuente',
    source: 'Fuente',
    askTab: 'Preguntar',
    confirmTab: 'Confirmar',
    detailsTab: 'Detalles',
    later: 'Esa parte llega después.',
    errorTitle: 'No pudimos responder',
    errorBody: 'Inténtalo de nuevo en un momento.',
    missing: 'Falta la configuración de Firebase. Revisa las variables de entorno.',
    sheetError: 'No se pudo abrir la hoja de la boda.',
    ready: 'Respuesta lista',
  },
  en: {
    eyebrow: 'We are getting married',
    calendar: 'Add to calendar',
    directions: 'Get directions',
    quick: 'Quick questions',
    topics: {
      schedule: 'Schedule',
      venue: 'Venue',
      dress: 'Dress code',
      parking: 'Parking',
      gifts: 'Gifts',
      contacts: 'Contacts',
    },
    questions: {
      schedule: 'What is the schedule?',
      venue: 'Where is the wedding?',
      dress: 'What is the dress code?',
      parking: 'Is there parking?',
      gifts: 'What can we give as a gift?',
      contacts: 'Who can I contact?',
    },
    placeholder: 'Write your question…',
    label: 'Your question',
    send: 'Send',
    emptyField: 'Write a question.',
    searching: 'Looking through the wedding details…',
    cloudBanner: 'This phone does not have the built-in assistant, so we answer from the cloud.',
    offlineLead: 'No signal.',
    offlineRest: 'We can still answer from your phone with the saved details.',
    idkBody: 'It is not in the wedding details, and we will not invent an answer.',
    askCouple: 'Pregúntale a los novios',
    another: 'Ask another question',
    noSource: 'No source',
    source: 'Source',
    askTab: 'Ask',
    confirmTab: 'RSVP',
    detailsTab: 'Details',
    later: 'That part comes later.',
    errorTitle: 'We could not answer',
    errorBody: 'Try again in a moment.',
    missing: 'Firebase is not configured. Check the environment variables.',
    sheetError: 'The wedding sheet could not be opened.',
    ready: 'Answer ready',
  },
} as const;

type ChatTurn = {
  question: string;
  topic: Topic | null;
  answer: string;
  route: Route;
  unknown: boolean;
};

type GuestPageProps = {
  requestAnswer?: (prompt: string, context: AskContext) => Promise<AskResult>;
};

function isUnknownAnswer(text: string): boolean {
  return text.trim().replace(/\s+/g, ' ') === UNKNOWN_ANSWER;
}

export function GuestPage({ requestAnswer = ask }: GuestPageProps) {
  const online = useOnline();
  const publish = useToast();
  const [lang, setLang] = useState<UiLang>('es');
  const copy = COPY[lang];
  const [sheet, setSheet] = useState<WeddingInfo | null>(null);
  const [sheetStatus, setSheetStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [question, setQuestion] = useState('');
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [activeTopic, setActiveTopic] = useState<Topic | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [device, setDevice] = useState<DeviceAvailability | null>(null);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    let alive = true;
    setSheetStatus('loading');
    resolveWeddingInfo({ online: navigator.onLine })
      .then((info) => {
        if (!alive) return;
        setSheet(info);
        setSheetStatus('ready');
      })
      .catch(() => {
        if (alive) setSheetStatus('error');
      });
    return () => {
      alive = false;
    };
  }, [online]);

  useEffect(() => {
    let alive = true;
    probeDeviceModel()
      .then((status) => {
        if (alive) setDevice(status);
      })
      .catch(() => {
        if (alive) setDevice('unavailable');
      });
    return () => {
      alive = false;
    };
  }, []);

  async function submit(text: string, topic: Topic | null) {
    const trimmed = text.trim();
    if (!trimmed || !sheet) return;
    setError(null);
    setPendingQuestion(trimmed);
    setActiveTopic(topic);
    try {
      const result = await requestAnswer(trimmed, {
        feature: 'guest_question',
        system: buildQaSystemPrompt(sheet),
      });
      const answer = result.text.trim();
      setTurns((current) => [
        ...current,
        {
          question: trimmed,
          topic,
          answer,
          route: result.route,
          unknown: answer.length === 0 || isUnknownAnswer(answer),
        },
      ]);
      setQuestion('');
      publish({ title: copy.ready });
    } catch (caught) {
      const missing =
        (caught instanceof Error && caught.message === 'firebase-config-missing') ||
        missingEnv().length > 0 ||
        getFirebaseProblem() === 'missing';
      setError(missing ? copy.missing : copy.errorBody);
      publish({ title: copy.errorTitle, description: missing ? copy.missing : copy.errorBody });
    } finally {
      setPendingQuestion(null);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit(question, null);
  }

  const ceremony = sheet ? ceremonyItem(sheet) : null;
  const showCloudBanner = !online ? false : device !== null && device !== 'available';

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
      {sheetStatus === 'error' ? (
        <div className="g-main">
          <div className="banner banner-danger" role="alert">
            {copy.sheetError}
          </div>
        </div>
      ) : null}
      {sheet ? (
        <section className="g-hero">
          <div className="g-hero-art">
            <Izote />
          </div>
          <p className="eyebrow">{copy.eyebrow}</p>
          <h1 className="display g-names">
            {personName(sheet.couple.bride)} <i>&amp;</i> {personName(sheet.couple.groom)}
          </h1>
          <p className="date-spaced g-date">{dateLine(sheet.date, lang)}</p>
          <p>
            {ceremony ? formatClock(ceremony.time, lang) : null}
            {ceremony ? <br /> : null}
            {venueLine(sheet)}
          </p>
          <div className="row gap-2 g-hero-actions">
            <a className="btn btn-secondary" href={calendarUrl(sheet)} target="_blank" rel="noreferrer">
              <Icon name="cal" />
              {copy.calendar}
            </a>
            <a className="btn btn-secondary" href={mapsUrl(sheet)} target="_blank" rel="noreferrer">
              <Icon name="pin" />
              {copy.directions}
            </a>
          </div>
        </section>
      ) : null}
      <main id="contenido" className="g-main" aria-live="polite">
        {!online ? (
          <div className="banner banner-offline" role="status">
            <Icon name="wifioff" size={22} />
            <div>
              <b>{copy.offlineLead}</b> {copy.offlineRest}
            </div>
          </div>
        ) : null}
        {showCloudBanner ? (
          <div className="banner banner-info" role="status">
            <Icon name="info" size={22} />
            <div>{copy.cloudBanner}</div>
          </div>
        ) : null}
        {turns.map((turn, index) => {
          const source = turn.topic ? copy.topics[turn.topic] : null;
          const coupleLink = sheet ? whatsAppUrl(sheet, turn.question) : null;
          return (
            <div className="stack gap-3" key={`${turn.question}-${index}`}>
              <div className="bubble-q">{turn.question}</div>
              {turn.unknown ? (
                <div className="bubble-a bubble-idk">
                  <h2 className="display">{UNKNOWN_ANSWER}</h2>
                  <p>{copy.idkBody}</p>
                  <div className="stack gap-2 idk-actions">
                    {coupleLink ? (
                      <a className="btn btn-primary btn-block" href={coupleLink} target="_blank" rel="noreferrer">
                        <Icon name="chat" />
                        {copy.askCouple}
                      </a>
                    ) : (
                      <button type="button" className="btn btn-primary btn-block" disabled>
                        <Icon name="chat" />
                        {copy.askCouple}
                      </button>
                    )}
                    <button
                      type="button"
                      className="btn btn-quiet btn-block"
                      onClick={() => {
                        setTurns((current) => current.filter((_, item) => item !== index));
                      }}
                    >
                      {copy.another}
                    </button>
                  </div>
                  <div className="foot">
                    <RouteBadge route={turn.route} />
                    <span className="sm muted">{copy.noSource}</span>
                  </div>
                </div>
              ) : (
                <div className="bubble-a">
                  <p>{turn.answer}</p>
                  <div className="foot">
                    <RouteBadge route={turn.route} />
                    <span className="sm muted">
                      {source ? `${copy.source}: ${source}` : copy.noSource}
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
        {pendingQuestion ? (
          <div className="stack gap-3">
            <div className="bubble-q">{pendingQuestion}</div>
            <div className="bubble-a" aria-busy="true">
              <div className="row gap-3">
                <span className="typing">
                  <b />
                  <b />
                  <b />
                </span>
                <span className="muted">{copy.searching}</span>
              </div>
            </div>
          </div>
        ) : null}
        {error ? (
          <div className="banner banner-danger" role="alert">
            <div>
              <b>{copy.errorTitle}.</b> {error}
            </div>
          </div>
        ) : null}
      </main>
      <section className="g-quick">
        <h2>{copy.quick}</h2>
        <div className="row wrap gap-2">
          {TOPICS.map((topic) => (
            <button
              key={topic}
              type="button"
              className="chip"
              aria-pressed={activeTopic === topic}
              onClick={() => void submit(copy.questions[topic], topic)}
            >
              <Icon name={TOPIC_ICON[topic]} size={18} />
              {copy.topics[topic]}
            </button>
          ))}
        </div>
      </section>
      <Form.Root className="g-composer" onSubmit={onSubmit}>
        <Form.Field name="question" className="field">
          <Form.Label className="sr-only">{copy.label}</Form.Label>
          <Form.Control asChild>
            <input
              className="input"
              required
              value={question}
              placeholder={copy.placeholder}
              disabled={pendingQuestion !== null || !sheet}
              onChange={(event) => setQuestion(event.target.value)}
            />
          </Form.Control>
          <Form.Message className="hint" match="valueMissing">
            {copy.emptyField}
          </Form.Message>
        </Form.Field>
        <Form.Submit asChild>
          <button className="btn btn-icon" aria-label={copy.send} disabled={pendingQuestion !== null || !sheet}>
            <Icon name="send" size={24} stroke={2.4} />
          </button>
        </Form.Submit>
      </Form.Root>
      <nav className="tabbar" aria-label={copy.askTab}>
        <button type="button" className="on">
          <Icon name="question" size={24} />
          {copy.askTab}
        </button>
        <button type="button" onClick={() => publish({ title: copy.later })}>
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
