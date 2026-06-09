/* ============================================================
   matrixos-icons.jsx — Matrix OS icon set
   ============================================================ */
function OI({ d, size = 18, sw = 1.7, style }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style} aria-hidden="true">{d}</svg>;
}
const O = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="1.6" /><rect x="14" y="3" width="7" height="7" rx="1.6" /><rect x="3" y="14" width="7" height="7" rx="1.6" /><rect x="14" y="14" width="7" height="7" rx="1.6" /></>,
  spark: <><path d="M12 3v4M12 17v4M3 12h4M17 12h4" /><path d="m6.3 6.3 2.4 2.4M15.3 15.3l2.4 2.4M17.7 6.3l-2.4 2.4M8.7 15.3l-2.4 2.4" /></>,
  bot: <><rect x="4" y="8" width="16" height="11" rx="3" /><path d="M12 8V4M9 4h6" /><circle cx="9" cy="13.5" r="1.1" fill="currentColor" stroke="none" /><circle cx="15" cy="13.5" r="1.1" fill="currentColor" stroke="none" /></>,
  flow: <><rect x="3" y="3" width="6" height="6" rx="1.5" /><rect x="15" y="15" width="6" height="6" rx="1.5" /><path d="M9 6h4a2 2 0 0 1 2 2v7" /></>,
  brain: <><path d="M12 5a3 3 0 1 0-5.99.1 4 4 0 0 0-1.5 6.97A3.5 3.5 0 0 0 6 19a3 3 0 0 0 6 .5z" /><path d="M12 5a3 3 0 1 1 5.99.1 4 4 0 0 1 1.5 6.97A3.5 3.5 0 0 1 18 19a3 3 0 0 1-6 .5z" /></>,
  shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" /><path d="m9 12 2 2 4-4" /></>,
  wrench: <><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z" /></>,
  play: <path d="M7 4l13 8-13 8z" />,
  db: <><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v14c0 1.6 3.6 3 8 3s8-1.4 8-3V5" /><path d="M4 12c0 1.6 3.6 3 8 3s8-1.4 8-3" /></>,
  gauge: <><path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" /><path d="M13.4 12.6 19 7" /><path d="M6.3 19a9 9 0 1 1 11.4 0" /></>,
  scroll: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M9 13h6M9 17h4" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></>,
  chevr: <path d="m9 18 6-6-6-6" />,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" /></>,
  rocket: <><path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2 0-2.8a2 2 0 0 0-3 0z" /><path d="M12 15l-3-3a16 16 0 0 1 8-8c2 0 3 1 3 3a16 16 0 0 1-8 8z" /><circle cx="14.5" cy="9.5" r="1.2" /></>,
  user: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
  x: <><path d="M18 6 6 18M6 6l12 12" /></>,
  activity: <path d="M22 12h-4l-3 9L9 3l-3 9H2" />,
  cpu: <><rect x="6" y="6" width="12" height="12" rx="2" /><path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2" /></>,
  layers: <><path d="m12 2 9 5-9 5-9-5z" /><path d="m3 12 9 5 9-5" /><path d="m3 17 9 5 9-5" /></>,
  check: <path d="M20 6 9 17l-5-5" />,
  globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18" /><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18" /></>,
  upgrade: <><path d="M12 3l2.5 5.5L20 9l-4 4 1 6-5-2.8L7 19l1-6-4-4 5.5-.5z" /></>,
  sliders: <><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6" /></>,
  badge: <><circle cx="12" cy="12" r="9" /><path d="M12 8v4l2.5 1.5" /></>,
  help: <><circle cx="12" cy="12" r="9" /><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3" /><path d="M12 17h.01" /></>,
  logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5" /><path d="M21 12H9" /></>,
  eye: <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" /><circle cx="12" cy="12" r="3" /></>,
};
/* Brand mark — the hub-and-spoke logo (matches assets/logo-mark.svg / README). */
/* Brand mark — the plus-configuration network logo (matches assets/logo-mark.svg). */
function Logo({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      {/* orthogonal connectors */}
      <g stroke="#00ff8c" strokeWidth="1.4" strokeLinecap="round" opacity="0.9">
        <line x1="12" y1="8.4" x2="12" y2="5.6" />
        <line x1="15.6" y1="12" x2="18.4" y2="12" />
        <line x1="12" y1="15.6" x2="12" y2="18.4" />
        <line x1="8.4" y1="12" x2="5.6" y2="12" />
      </g>
      {/* center hub: ring + green core + white pip */}
      <circle cx="12" cy="12" r="3.4" fill="#050807" stroke="#00ff8c" strokeWidth="1.5" />
      <circle cx="12" cy="12" r="1.7" fill="#00ff8c" />
      <circle cx="12" cy="12" r="0.7" fill="#ffffff" />
      {/* satellite nodes (N/E/S/W) */}
      <g fill="#050807" stroke="#00ff8c" strokeWidth="1.5">
        <circle cx="12" cy="3.6" r="1.8" />
        <circle cx="20.4" cy="12" r="1.8" />
        <circle cx="12" cy="20.4" r="1.8" />
        <circle cx="3.6" cy="12" r="1.8" />
      </g>
    </svg>
  );
}

window.MOS = { OI, O, Logo };
