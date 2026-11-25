const PATHS = {
  phone: '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
  cloud: '<path d="M7 18h10a4 4 0 0 0 .6-8A6 6 0 0 0 6 11a3.5 3.5 0 0 0 1 7z"/>',
  wifioff:
    '<path d="M2 8.5a15 15 0 0 1 20 0M5.5 12a10 10 0 0 1 13 0M9 15.5a5 5 0 0 1 6 0M12 19h.01M3 3l18 18"/>',
  cal: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
  pin: '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
  send: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  chat: '<path d="M4 18.5V6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v8a2.5 2.5 0 0 1-2.5 2.5H8z"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
  heart:
    '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10C19.5 15.4 12 20 12 20z"/>',
  question:
    '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .8-1 1.5v.7M12 17h.01"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  shirt:
    '<path d="M8 3.5l-4.5 3 2 4 2-1V20.5h9V9.5l2 1 2-4-4.5-3c-.5 1.5-2 2.5-4 2.5s-3.5-1-4-2.5z"/>',
  parking:
    '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M9.5 17V7h3.5a3 3 0 0 1 0 6H9.5"/>',
  gift: '<rect x="3.5" y="8" width="17" height="4" rx="1"/><path d="M5 12v8.5h14V12M12 8v12.5M12 8S10.5 3.5 8 4.5 9 8 12 8zm0 0s1.5-4.5 4-3.5S15 8 12 8z"/>',
  phonecall:
    '<path d="M5 4h3.5l1.5 4.5-2 1.5a11 11 0 0 0 6 6l1.5-2L20 15.5V19a1.5 1.5 0 0 1-1.6 1.5C10.5 20 4 13.5 3.5 5.6A1.5 1.5 0 0 1 5 4z"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  music: '<path d="M9 18V5.5l11-2V16"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
  download: '<path d="M12 4v11M7 10.5l5 5 5-5M5 20h14"/>',
  printer: '<path d="M7 9V3.5h10V9M7 17H4.5V9h15v8H17M7 14h10v6.5H7z"/>',
  flag: '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
} as const;

export type IconName = keyof typeof PATHS;

type IconProps = {
  name: IconName;
  size?: number;
  stroke?: number;
};

export function Icon({ name, size = 20, stroke = 2 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: PATHS[name] }}
    />
  );
}

export function Izote() {
  return (
    <svg
      width="50"
      height="66"
      viewBox="0 0 92 120"
      fill="none"
      stroke="var(--color-primary)"
      strokeWidth="1.4"
      aria-hidden="true"
    >
      <path d="M46 120V30" />
      <g fill="var(--color-bg)">
        <path d="M46 30c-7-4-9-13-4-20 3 6 5 9 4 20z" />
        <path d="M46 30c7-4 9-13 4-20-3 6-5 9-4 20z" />
        <path d="M46 48c-10-2-15-10-11-18 4 5 8 7 11 18z" />
        <path d="M46 48c10-2 15-10 11-18-4 5-8 7-11 18z" />
        <path d="M46 66c-11 0-18-8-16-17 5 4 10 6 16 17z" />
        <path d="M46 66c11 0 18-8 16-17-5 4-10 6-16 17z" />
      </g>
      <path d="M46 112c-10-6-26-6-38 0M46 112c10-6 26-6 38 0" stroke="var(--color-success-fg)" />
    </svg>
  );
}
