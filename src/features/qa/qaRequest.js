export const UNKNOWN_ANSWER = 'No tengo esa información, pregúntale a los novios';
export const UNKNOWN_ANSWER_EN = "I don't have that information, ask the couple";
export const GUEST_QUESTION_OUTPUT_SHAPE = '{answer, confidence}';

export const GUEST_QUESTION_RESPONSE_SCHEMA = {
  type: 'object',
  properties: {
    answer: { type: 'string' },
    confidence: { type: 'number' },
  },
  required: ['answer', 'confidence'],
};

const ES_STOP = new Set(
  'que qué cual cuál cuales cuáles como cómo donde dónde cuando cuándo quien quién hay esta está estan están son para por con una unos unas del puedo puede pueden tienen tiene sobre tambien también hora horas'.split(
    ' ',
  ),
);
const EN_STOP = new Set(
  'what where when who why how is are was were the there this that do does did can could should would please will have has any about time wedding parking'.split(
    ' ',
  ),
);

function fold(token) {
  return token.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function isCapitalized(token) {
  return /^[A-ZÁÉÍÓÚÜÑ]/.test(token);
}

export function detectQuestionLanguage(text, uiLocale) {
  const fallback = uiLocale === 'en' ? 'en' : 'es';
  const raw = String(text ?? '');
  let spanish = 0;
  let english = 0;
  if (/[¿¡]/.test(raw)) spanish += 2;
  const tokens = raw.match(/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+/g) ?? [];
  for (const token of tokens) {
    const folded = fold(token);
    const placeName = isCapitalized(token) && !ES_STOP.has(folded) && !EN_STOP.has(folded);
    if (ES_STOP.has(folded)) spanish += 1;
    if (EN_STOP.has(folded)) english += 1;
    if (!placeName && /[áéíóúüñ]/i.test(token)) spanish += 2;
  }
  if (spanish === english) return fallback;
  return spanish > english ? 'es' : 'en';
}

export function buildQaSystemPrompt(info) {
  return [
    'Eres el asistente de invitados de una boda.',
    'Responde únicamente con hechos que aparecen en la hoja de información proporcionada.',
    'Copia las horas, los lugares y los nombres textualmente, tal como están escritos en la hoja.',
    'No infieras ni añadas detalles que la hoja no dice.',
    'No uses conocimiento externo y no inventes datos.',
    'No infieras el idioma. Responde siempre en el idioma declarado en el turno del usuario.',
    'Ese turno trae una línea lang: es o lang: en, y una línea de idioma de respuesta. Obedece esas líneas.',
    'Si lang es en, answer va en inglés. Si lang es es, answer va en español.',
    `Si lang es es y el hecho no está en la hoja, answer es exactamente esta frase y nada más: ${UNKNOWN_ANSWER}`,
    `Si lang es en y el hecho no está en la hoja, answer es exactamente esta frase y nada más: ${UNKNOWN_ANSWER_EN}`,
    'La frase de rechazo va sola dentro de answer, sin traducción y sin una segunda oración.',
    `Devuelve únicamente un objeto JSON con la forma ${GUEST_QUESTION_OUTPUT_SHAPE} y ninguna clave extra.`,
    'answer es el texto de una o dos oraciones. confidence es un número entre 0 y 1.',
    'Hoja de información JSON:',
    JSON.stringify(info),
  ].join('\n');
}

export function buildQaUserTurn(input) {
  const lang = input.lang === 'en' ? 'en' : 'es';
  const languageLine = lang === 'en' ? 'Answer language: English' : 'Idioma de respuesta: español';
  return [`lang: ${lang}`, languageLine, 'Question:', String(input.question ?? '').trim(), 'Hoja de información JSON:', JSON.stringify(input.sheet)].join(
    '\n',
  );
}
