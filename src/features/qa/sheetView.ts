import type { WeddingInfo } from '../../data/types';

export type UiLang = 'es' | 'en';

export function personName(person: { first_name: string; last_name: string }): string {
  return `${person.first_name} ${person.last_name}`.trim();
}

export function partnerInitials(info: WeddingInfo): string {
  const bride = info.couple.bride.first_name.charAt(0);
  const groom = info.couple.groom.first_name.charAt(0);
  return `${bride}&${groom}`.toUpperCase();
}

export function ceremonyItem(info: WeddingInfo): { time: string; title: string } | null {
  return info.schedule.find((item) => /ceremonia/i.test(item.title)) ?? info.schedule[0] ?? null;
}

export function formatClock(time: string, lang: UiLang): string {
  const [hourText, minuteText] = time.split(':');
  const hour = Number(hourText);
  const minute = Number(minuteText);
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) return time;
  const hour12 = hour % 12 || 12;
  const minutes = String(minute).padStart(2, '0');
  const suffix = hour >= 12 ? (lang === 'es' ? 'p. m.' : 'p.m.') : lang === 'es' ? 'a. m.' : 'a.m.';
  return `${hour12}:${minutes} ${suffix}`;
}

export function dateLine(isoDate: string, lang: UiLang): string {
  const date = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  const locale = lang === 'es' ? 'es' : 'en';
  const weekday = new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(date).replace('.', '');
  const day = new Intl.DateTimeFormat(locale, { day: 'numeric' }).format(date);
  const month = new Intl.DateTimeFormat(locale, { month: 'short' }).format(date).replace('.', '');
  const year = new Intl.DateTimeFormat(locale, { year: 'numeric' }).format(date);
  return `${weekday} · ${day} · ${month} · ${year}`.toLocaleUpperCase(locale);
}

export function venueLine(info: WeddingInfo): string {
  return [info.venue.name, info.venue.address, info.venue.city]
    .filter((part) => part.trim().length > 0)
    .join(', ');
}

/** Length used when the wedding sheet does not set an end time or a duration. */
export const DEFAULT_CALENDAR_DURATION_HOURS = 5;

const CALENDAR_TIME_ZONE = 'America/El_Salvador';

const ENGLISH_VENUE_DETAILS =
  'The property is a 25-minute drive from central Santa Tecla. A covered backup hall is available if it rains.';

const SPANISH_VENUE_DETAILS =
  'La propiedad queda a 25 minutos en carro del centro de Santa Tecla. Hay un salón cubierto de respaldo si llueve.';

type Clock = { hours: number; minutes: number };

function pad2(value: number): string {
  return String(value).padStart(2, '0');
}

function calendarStamp(isoDate: string, clock: Clock): string {
  return `${isoDate.replaceAll('-', '')}T${pad2(clock.hours)}${pad2(clock.minutes)}00`;
}

function parseClock(value: string): Clock | null {
  const match = /^(\d{1,2}):(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (hours > 23 || minutes > 59) return null;
  return { hours, minutes };
}

function addMinutes(isoDate: string, clock: Clock, minutesToAdd: number): { date: string; clock: Clock } {
  const [year, month, day] = isoDate.split('-').map(Number);
  const utc = new Date(Date.UTC(year, (month ?? 1) - 1, day ?? 1, clock.hours, clock.minutes));
  utc.setUTCMinutes(utc.getUTCMinutes() + minutesToAdd);
  return {
    date: `${utc.getUTCFullYear()}-${pad2(utc.getUTCMonth() + 1)}-${pad2(utc.getUTCDate())}`,
    clock: { hours: utc.getUTCHours(), minutes: utc.getUTCMinutes() },
  };
}

function minutesFromDuration(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return Math.round(value * 60);
  }
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  const hours = /^(\d+(?:\.\d+)?)\s*h(?:ours?)?$/i.exec(trimmed);
  if (hours) return Math.round(Number(hours[1]) * 60);
  const asNumber = Number(trimmed);
  if (Number.isFinite(asNumber) && asNumber > 0) return Math.round(asNumber * 60);
  return null;
}

function configuredEnd(info: WeddingInfo, startDate: string, start: Clock): { date: string; clock: Clock } {
  const ceremony = ceremonyItem(info);
  const sources: object[] = ceremony ? [ceremony, info] : [info];
  for (const source of sources) {
    const record = source as Record<string, unknown>;
    const endValue = record.end ?? record.ends_at ?? record.end_time;
    if (typeof endValue === 'string') {
      const dated = /^(\d{4}-\d{2}-\d{2})[T ](\d{1,2}:\d{2})/.exec(endValue.trim());
      if (dated) {
        const clock = parseClock(dated[2]);
        if (clock) return { date: dated[1], clock };
      }
      const clock = parseClock(endValue);
      if (clock) {
        const later = clock.hours * 60 + clock.minutes > start.hours * 60 + start.minutes;
        return later ? { date: startDate, clock } : addMinutes(startDate, clock, 24 * 60);
      }
    }
    const duration = minutesFromDuration(record.duration_hours ?? record.durationHours ?? record.duration);
    if (duration !== null) return addMinutes(startDate, start, duration);
  }
  return addMinutes(startDate, start, DEFAULT_CALENDAR_DURATION_HOURS * 60);
}

function looksSpanish(text: string): boolean {
  return /[áéíóúüñ¿¡]/i.test(text) || /\b(el|la|los|las|del|hay|para|con|una|ceremonia|boda)\b/i.test(text);
}

function calendarDetails(info: WeddingInfo, lang: UiLang): string {
  const notes = (info.venue.notes ?? '').trim();
  if (lang === 'en') return notes || info.disclaimer.trim();
  if (notes === ENGLISH_VENUE_DETAILS) return SPANISH_VENUE_DETAILS;
  if (notes && looksSpanish(notes)) return notes;
  const place = [info.venue.name, info.venue.city].filter((part) => part.trim().length > 0).join(', ');
  return place ? `Ceremonia en ${place}.` : 'Ceremonia de la boda.';
}

export function calendarUrl(info: WeddingInfo, lang: UiLang = 'es'): string {
  const item = ceremonyItem(info);
  const start = parseClock(item?.time ?? '16:00') ?? { hours: 16, minutes: 0 };
  const end = configuredEnd(info, info.date, start);
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: `${personName(info.couple.bride)} y ${personName(info.couple.groom)}`,
    dates: `${calendarStamp(info.date, start)}/${calendarStamp(end.date, end.clock)}`,
    ctz: info.timezone.trim() || CALENDAR_TIME_ZONE,
    location: venueLine(info),
    details: calendarDetails(info, lang),
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function mapsUrl(info: WeddingInfo): string {
  const params = new URLSearchParams({ api: '1', query: venueLine(info) });
  return `https://www.google.com/maps/search/?${params.toString()}`;
}

export function whatsAppUrl(info: WeddingInfo, question: string): string | null {
  const phone = info.contacts.find((contact) => (contact.phone ?? '').trim().length > 0)?.phone ?? '';
  const digits = phone.replace(/\D/g, '');
  if (!digits) return null;
  const params = new URLSearchParams({ text: question });
  return `https://wa.me/${digits}?${params.toString()}`;
}
