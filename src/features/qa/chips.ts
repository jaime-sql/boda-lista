import type { InfoBlock, ScheduleItem, WeddingInfo } from '../../data/types';
import { UNKNOWN_ANSWER } from './prompt';
import type { UiLang } from './sheetView';

export const CHIP_TOPICS = ['schedule', 'venue', 'dress', 'parking', 'gifts', 'contacts'] as const;
export type ChipTopic = (typeof CHIP_TOPICS)[number];

function clean(value: string | undefined): string {
  return value?.trim() ?? '';
}

function sentence(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return '';
  return /[.!?]$/.test(trimmed) ? trimmed : `${trimmed}.`;
}

function blockText(block: InfoBlock | undefined, lang: UiLang): string | null {
  if (!block) return null;
  const summary = clean(block.summary);
  const details = clean(block.details);
  const notes = clean(block.notes);
  if (lang === 'en' && notes) return notes;
  const local = [summary, details].filter((part) => part.length > 0).join(' ');
  if (local) return local;
  return notes || null;
}

function formatBlock(block: InfoBlock | undefined, lang: UiLang, lead: Record<UiLang, string>): string {
  const text = blockText(block, lang);
  if (!text) return UNKNOWN_ANSWER;
  return `${lead[lang]} ${sentence(text)}`;
}

function formatScheduleItem(item: ScheduleItem): string {
  const head = [clean(item.time), clean(item.title)].filter((part) => part.length > 0).join(' ');
  const place = clean(item.place);
  const notes = clean(item.notes);
  const withPlace = place && head ? `${head}, ${place}` : head || place;
  if (!withPlace && !notes) return '';
  if (!withPlace) return sentence(notes);
  if (!notes) return sentence(withPlace);
  return `${sentence(withPlace)} ${sentence(notes)}`;
}

function formatSchedule(info: WeddingInfo, lang: UiLang): string {
  const items = (Array.isArray(info.schedule) ? info.schedule : [])
    .map(formatScheduleItem)
    .filter((line) => line.length > 0);
  if (items.length === 0) return UNKNOWN_ANSWER;
  const lead = lang === 'en' ? 'Schedule:' : 'Horario:';
  return `${lead} ${items.join(' ')}`;
}

function formatVenue(info: WeddingInfo, lang: UiLang): string {
  const venue = info.venue;
  const place = [venue?.name, venue?.address, venue?.city, venue?.country]
    .map((part) => clean(part))
    .filter((part) => part.length > 0);
  const ceremony = clean(venue?.ceremony_area);
  const reception = clean(venue?.reception_area);
  const notes = clean(venue?.notes);
  if (place.length === 0 && !ceremony && !reception && !notes) return UNKNOWN_ANSWER;
  const lines: string[] = [];
  if (place.length > 0) {
    lines.push(lang === 'en' ? `The wedding is at ${place.join(', ')}.` : `La boda es en ${place.join(', ')}.`);
  }
  if (ceremony) lines.push(lang === 'en' ? `Ceremony: ${ceremony}.` : `Ceremonia: ${ceremony}.`);
  if (reception) lines.push(lang === 'en' ? `Reception: ${reception}.` : `Recepción: ${reception}.`);
  if (notes) lines.push(sentence(notes));
  return lines.join(' ');
}

function formatContacts(info: WeddingInfo, lang: UiLang): string {
  const people = (Array.isArray(info.contacts) ? info.contacts : [])
    .map((contact) =>
      [contact.name, contact.role, contact.email, contact.phone]
        .map((part) => clean(part))
        .filter((part) => part.length > 0)
        .join(', '),
    )
    .filter((line) => line.length > 0);
  if (people.length === 0) return UNKNOWN_ANSWER;
  const lead = lang === 'en' ? 'Contacts:' : 'Contactos:';
  return `${lead} ${people.map(sentence).join(' ')}`;
}

export function formatChipAnswer(info: WeddingInfo, topic: ChipTopic, lang: UiLang): string {
  switch (topic) {
    case 'schedule':
      return formatSchedule(info, lang);
    case 'venue':
      return formatVenue(info, lang);
    case 'dress':
      return formatBlock(info.dress_code, lang, { es: 'Vestimenta:', en: 'Dress code:' });
    case 'parking':
      return formatBlock(info.parking, lang, { es: 'Parqueo:', en: 'Parking:' });
    case 'gifts':
      return formatBlock(info.gifts, lang, { es: 'Regalos:', en: 'Gifts:' });
    case 'contacts':
      return formatContacts(info, lang);
  }
}
