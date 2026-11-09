// Inline icons, 24px grid, stroked with currentColor.
const svg = (body: string, size = 20) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${body}</svg>`;

export const icons = {
  chat: svg(
    '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.8A8 8 0 1 1 21 12Z"/><path d="M8.5 12h.01M12 12h.01M15.5 12h.01" stroke-width="2.6"/>',
    26,
  ),
  close: svg('<path d="M18 6 6 18M6 6l12 12"/>'),
  closeSmall: svg('<path d="M18 6 6 18M6 6l12 12"/>', 14),
  send: svg('<path d="M12 19V5M5 12l7-7 7 7"/>', 18),
  stop: svg('<rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor" stroke="none"/>', 18),
  restart: svg('<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/>', 18),
  doc: svg(
    '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    14,
  ),
  person: svg('<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>', 16),
  check: svg('<path d="m5 12.5 4.5 4.5L19 7.5"/>', 16),
  chevron: svg('<path d="m6 9 6 6 6-6"/>', 14),
};
