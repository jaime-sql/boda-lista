import extractPrompt from '../../../evals/prompts/extract.json';

const rsvpTask = extractPrompt.tasks.rsvp;

export const RSVP_SYSTEM = [extractPrompt.system, rsvpTask.instruction, JSON.stringify(rsvpTask.output_schema)].join(
  '\n\n',
);

export function buildRsvpUserPrompt(text: string, lang: 'es' | 'en'): string {
  return extractPrompt.user_template
    .replace('{task}', 'rsvp')
    .replace('{lang}', lang)
    .replace('{text}', text);
}
