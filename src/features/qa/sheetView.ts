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

export function calendarUrl(info: WeddingInfo): string {
  const item = ceremonyItem(info);
  const compactDate = info.date.replaceAll('-', '');
  const compactTime = (item?.time ?? '16:00').replace(':', '') + '00';
  const start = `${compactDate}T${compactTime}`;
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: `${personName(info.couple.bride)} y ${personName(info.couple.groom)}`,
    dates: `${start}/${start}`,
    location: venueLine(info),
    details: info.venue.notes ?? info.disclaimer,
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
