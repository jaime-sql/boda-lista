import extractPrompt from '../../../evals/prompts/extract.json';

const songTask = extractPrompt.tasks.song;

export const SONG_SYSTEM = [extractPrompt.system, songTask.instruction, JSON.stringify(songTask.output_schema)].join(
  '\n\n',
);

export function buildSongUserPrompt(text: string, lang: 'es' | 'en'): string {
  return extractPrompt.user_template
    .replace('{task}', 'song')
    .replace('{lang}', lang)
    .replace('{text}', text);
}
