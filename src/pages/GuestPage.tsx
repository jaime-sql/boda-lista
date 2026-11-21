import * as Form from '@radix-ui/react-form';
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { ask } from '../ai/hybrid';
import type { AskContext, AskResult, Route } from '../ai/types';
import { InfoDialog } from '../components/InfoDialog';
import { RouteBadge } from '../components/RouteBadge';
import { EmptyState, ErrorState, LoadingSkeleton, OfflineState, THINKING_LABEL } from '../components/ScreenState';
import { useToast } from '../components/ToastProvider';
import { resolveWeddingInfo } from '../data/loadWeddingInfo';
import type { WeddingInfo } from '../data/types';
import { getFirebaseProblem } from '../firebase/client';
import { missingEnv } from '../firebase/config';
import { UNKNOWN_ANSWER, buildQaSystemPrompt } from '../features/qa/prompt';
import { useOnline } from '../lib/useOnline';

type GuestPageProps = {
  requestAnswer?: (prompt: string, context: AskContext) => Promise<AskResult>;
};

export function GuestPage({ requestAnswer = ask }: GuestPageProps) {
  const online = useOnline();
  const publish = useToast();
  const [sheet, setSheet] = useState<WeddingInfo | null>(null);
  const [sheetStatus, setSheetStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [question, setQuestion] = useState('');
  const [pending, setPending] = useState(false);
  const [answer, setAnswer] = useState<{ text: string; route: Route } | null>(null);
  const [error, setError] = useState<'missing' | 'failed' | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);

  const loadSheet = useCallback(() => {
    setSheetStatus('loading');
    resolveWeddingInfo({ online: navigator.onLine })
      .then((info) => {
        setSheet(info);
        setSheetStatus('ready');
      })
      .catch(() => setSheetStatus('error'));
  }, []);

  useEffect(() => {
    loadSheet();
  }, [loadSheet, loadAttempt, online]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || !sheet) return;
    setPending(true);
    setError(null);
    try {
      const result = await requestAnswer(trimmed, {
        feature: 'qa',
        system: buildQaSystemPrompt(sheet),
      });
      const text = result.text.trim() || UNKNOWN_ANSWER;
      setAnswer({ text, route: result.route });
      publish({
        title: 'Respuesta lista',
        description: 'Revisa el texto y si salió del teléfono o de la nube.',
      });
    } catch (caught) {
      const missing =
        (caught instanceof Error && caught.message === 'firebase-config-missing') ||
        missingEnv().length > 0 ||
        getFirebaseProblem() === 'missing';
      setError(missing ? 'missing' : 'failed');
      publish({
        title: 'No pudimos responder',
        description: 'Inténtalo de nuevo en un momento.',
      });
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="stack">
      <h1 className="title">Preguntas de la boda</h1>
      <p>
        Pregunta por el horario, el lugar, la vestimenta, el estacionamiento, los regalos o los contactos.
        Si la hoja no lo dice, te lo diremos.
      </p>
      <p className="muted">Puedes preguntar en español o en inglés. Esta demostración usa una boda de ejemplo.</p>
      <InfoDialog trigger="Qué cubre la hoja" title="Hoja de la boda de ejemplo">
        <p>Horario, vestimenta, lugar, estacionamiento, regalos y contactos. Los datos son ficticios.</p>
      </InfoDialog>
      {!online ? (
        <OfflineState detail="Sin red, la nube no responde. Si este teléfono ya tiene el modelo, la pregunta puede resolverse aquí." />
      ) : null}
      {sheetStatus === 'loading' ? <LoadingSkeleton label="Cargando la hoja de la boda…" /> : null}
      {sheetStatus === 'error' ? (
        <ErrorState
          title="No se pudo abrir la hoja"
          detail="No encontramos la información de la boda en este navegador."
          onRetry={() => setLoadAttempt((value) => value + 1)}
        />
      ) : null}
      {sheetStatus === 'ready' ? (
        <Form.Root onSubmit={(event) => void onSubmit(event)}>
          <Form.Field name="question" className="field">
            <Form.Label className="label">Tu pregunta</Form.Label>
            <Form.Control asChild>
              <textarea
                className="textarea"
                required
                value={question}
                placeholder="Por ejemplo, ¿a qué hora es la ceremonia?"
                disabled={pending}
                onChange={(event) => setQuestion(event.target.value)}
              />
            </Form.Control>
            <Form.Message className="state-error" match="valueMissing">
              Escribe una pregunta.
            </Form.Message>
          </Form.Field>
          <Form.Submit asChild>
            <button className="button" disabled={pending}>
              Preguntar
            </button>
          </Form.Submit>
        </Form.Root>
      ) : null}
      {pending ? <LoadingSkeleton label={THINKING_LABEL} /> : null}
      {error ? (
        <ErrorState
          title="No pudimos responder"
          detail={
            error === 'missing'
              ? 'Falta la configuración de Firebase. Revisa las variables de entorno.'
              : 'Inténtalo de nuevo en un momento.'
          }
          onRetry={() => setError(null)}
        />
      ) : null}
      {answer ? (
        <article className="answer" aria-live="polite">
          <h2 className="heading">Respuesta</h2>
          <RouteBadge route={answer.route} />
          <p>{answer.text}</p>
        </article>
      ) : null}
      {sheetStatus === 'ready' && !pending && !answer && !error ? (
        <EmptyState
          title="Todavía no hay una respuesta"
          detail="Cuando preguntes, la respuesta aparecerá aquí."
        />
      ) : null}
    </div>
  );
}
