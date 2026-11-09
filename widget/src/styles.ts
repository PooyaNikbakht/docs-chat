// All sizes are in px, not rem, so the host page's root font size can't change the widget.
export const css = `
:host {
  all: initial !important;
  display: block !important;
  position: fixed !important;
  inset: auto !important;
  width: 0 !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  transform: none !important;
  filter: none !important;
  opacity: 1 !important;
  visibility: visible !important;
  z-index: 2147483000 !important;
  contain: none !important;
}
* , *::before, *::after { box-sizing: border-box; }
[hidden] { display: none !important; }

.dc {
  --accent: #0F766E;
  --on-accent: #FFFFFF;
  --bg: #FFFFFF;
  --surface: #F4F3F1;
  --ink: #1C1917;
  --muted: #625D58;
  --border: #E4E0DA;
  --mark: #FBEAB0;
  --danger: #B42318;
  --radius: 14px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 14.5px;
  line-height: 1.5;
  font-weight: 400;
  letter-spacing: normal;
  text-transform: none;
  text-align: left;
  text-indent: 0;
  word-spacing: normal;
  white-space: normal;
  font-style: normal;
  cursor: auto;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
}
.dc button, .dc textarea, .dc a { font: inherit; color: inherit; }
.dc button { cursor: pointer; background: none; border: 0; margin: 0; padding: 0; }
.dc :focus { outline: none; }
.dc :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Launcher */
.launcher {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--accent) !important;
  color: var(--on-accent) !important;
  border: 2px solid var(--bg) !important;
  transition: transform 160ms ease;
}
.dc.left .launcher { right: auto; left: 20px; }
.launcher:hover { transform: scale(1.05); }
.launcher:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.launcher .icon-close { display: none; }
.dc.open .launcher .icon-chat { display: none; }
.dc.open .launcher .icon-close { display: block; }

/* One-time greeting tooltip */
.tooltip {
  position: fixed;
  bottom: 92px;
  right: 20px;
  max-width: 260px;
  padding: 12px 36px 12px 14px;
  border-radius: 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--ink);
  font-size: 14px;
  line-height: 1.4;
  animation: rise 220ms ease both;
}
.dc.left .tooltip { right: auto; left: 20px; }
.tooltip-open { all: unset; cursor: pointer; display: block; }
.tooltip-open:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; border-radius: 4px; }
.tooltip-close {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  color: var(--muted) !important;
}
.tooltip-close:hover { background: var(--surface) !important; }

/* Panel */
.panel {
  position: fixed;
  bottom: 92px;
  right: 20px;
  width: 384px;
  height: min(640px, calc(100vh - 116px));
  display: flex;
  flex-direction: column;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transform-origin: bottom right;
  animation: pop 180ms ease both;
}
.dc.left .panel { right: auto; left: 20px; transform-origin: bottom left; }

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 10px 14px 16px;
  background: var(--accent);
  color: var(--on-accent);
}
.avatar {
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--on-accent);
  color: var(--accent);
  font-weight: 700;
  font-size: 15px;
}
.titles { flex: 1; min-width: 0; }
.title { margin: 0; font-size: 15.5px; font-weight: 650; line-height: 1.3; }
.subline { margin: 1px 0 0; font-size: 12.5px; line-height: 1.35; opacity: 0.86; }
.head-btn {
  flex: none;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: var(--on-accent) !important;
}
.head-btn:hover { background: rgba(255, 255, 255, 0.14) !important; }
.head-btn:focus-visible { outline: 2px solid var(--on-accent); outline-offset: -2px; }

.log {
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 18px 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  scroll-behavior: smooth;
}
.msg { display: flex; flex-direction: column; max-width: 100%; }
.msg.user { align-items: flex-end; }
.bubble {
  max-width: 88%;
  padding: 10px 13px;
  border-radius: 14px;
  overflow-wrap: anywhere;
}
.msg.assistant .bubble { background: var(--surface); border-bottom-left-radius: 4px; }
.msg.user .bubble { background: var(--accent); color: var(--on-accent); border-bottom-right-radius: 4px; }
.bubble p { margin: 0; }
.bubble p + p, .bubble p + ul, .bubble p + ol, .bubble ul + p, .bubble ol + p { margin-top: 8px; }
.bubble ul, .bubble ol { margin: 4px 0 0; padding-left: 20px; }
.bubble li + li { margin-top: 2px; }
.msg.error .bubble { background: #FEF3F2; color: var(--danger); }
.stopped { margin: 4px 2px 0; font-size: 12px; color: var(--muted); }
.notice { margin: 6px 2px 0; font-size: 12px; color: var(--muted); max-width: 88%; }

.typing { display: inline-flex; gap: 4px; padding: 4px 2px; }
.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--muted);
  opacity: 0.35;
  animation: blink 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: 0.15s; }
.typing span:nth-child(3) { animation-delay: 0.3s; }

/* Suggestions */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 2px; }
.dc .chip {
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid var(--border) !important;
  background: var(--bg) !important;
  font-size: 13.5px;
  line-height: 1.35;
  text-align: left;
  color: var(--ink) !important;
  transition: border-color 120ms ease, background-color 120ms ease;
}
.chip:hover { border-color: var(--accent) !important; }

/* Sources */
.source-block { max-width: 88%; margin-top: 8px; }
.sources { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px; }
.dc .chip-source {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 28px;
  padding: 3px 8px 3px 9px;
  border-radius: 8px;
  border: 1px solid var(--border) !important;
  background: var(--bg) !important;
  font-size: 12.5px;
  color: var(--muted) !important;
}
.dc .chip-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--accent) !important;
  background: var(--bg) !important;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent) !important;
  text-decoration: none !important;
}
.chip-link:hover { background: var(--accent) !important; color: var(--on-accent) !important; }
.chip-source:hover, .chip-source[aria-expanded="true"] { color: var(--ink) !important; border-color: var(--accent) !important; }
.chip-source .chev { display: inline-flex; transition: transform 140ms ease; }
.chip-source[aria-expanded="true"] .chev { transform: rotate(180deg); }
.passage {
  margin: 8px 0 0;
  padding: 10px 12px;
  border-left: 3px solid var(--accent);
  background: var(--bg);
  border-radius: 0 8px 8px 0;
  border-top: 1px solid var(--border);
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  line-height: 1.5;
}
.passage-label { margin: 0 0 4px; font-size: 11.5px; font-weight: 650; letter-spacing: 0.02em; color: var(--muted); }
.passage-text { margin: 0; color: var(--ink); }
.passage mark { background: var(--mark); color: inherit; padding: 0 1px; border-radius: 2px; }

/* Booking: choices and the confirm card */
.choices { max-width: 92%; margin-top: 8px; }
.choices-label { margin: 0 0 6px; font-size: 12px; font-weight: 600; color: var(--muted); }
.choice-list { display: flex; flex-wrap: wrap; gap: 8px; }
.dc .choice {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  min-height: 40px;
  min-width: 84px;
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid var(--accent) !important;
  background: var(--bg) !important;
  color: var(--accent) !important;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.25;
  text-align: left;
  transition: background-color 120ms ease, color 120ms ease;
}
.choice:hover { background: var(--accent) !important; color: var(--on-accent) !important; }
.choice-detail { font-size: 12px; font-weight: 400; opacity: 0.8; }
.booking {
  max-width: 92%;
  margin-top: 8px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}
.booking.confirmed { border-color: var(--accent); }
.booking-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 8px;
  font-size: 13.5px;
  font-weight: 650;
  color: var(--ink);
}
.booking.confirmed .booking-head { color: var(--accent); }
.booking-list { margin: 0; display: grid; gap: 4px; }
.booking-row { display: grid; grid-template-columns: 76px 1fr; gap: 8px; font-size: 13.5px; }
.booking-row dt { color: var(--muted); }
.booking-row dd { margin: 0; color: var(--ink); overflow-wrap: anywhere; }
.booking-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.dc .confirm, .dc .change {
  min-height: 40px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
}
.confirm { background: var(--accent) !important; color: var(--on-accent) !important; border: 1px solid var(--accent) !important; }
.change { background: var(--bg) !important; color: var(--ink) !important; border: 1px solid var(--border) !important; }
.change:hover { border-color: var(--accent) !important; }

/* Handoff and retry */
.actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.dc .handoff, .dc .retry {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid var(--accent) !important;
  color: var(--accent) !important;
  background: var(--bg) !important;
}
.handoff:hover, .retry:hover { background: var(--accent) !important; color: var(--on-accent) !important; }

/* Composer */
.composer { border-top: 1px solid var(--border); padding: 10px 12px 8px; background: var(--bg); }
.row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 4px 4px 4px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}
.row:focus-within { border-color: var(--accent); }
.input {
  flex: 1;
  min-width: 0;
  min-height: 36px;
  max-height: 120px;
  padding: 7px 0;
  border: 0 !important;
  background: transparent !important;
  resize: none;
  font-size: 15px !important;
  line-height: 1.45;
  color: var(--ink) !important;
  outline: none !important;
}
.input::placeholder { color: var(--muted); opacity: 1; }
.send {
  flex: none;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  background: var(--accent) !important;
  color: var(--on-accent) !important;
}
.send:disabled { opacity: 0.4; cursor: default; }
.foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 6px;
  padding: 0 2px;
  font-size: 12px;
  color: var(--muted);
}
.foot a { display: inline-flex; align-items: center; gap: 4px; color: var(--muted) !important; text-decoration: underline; text-underline-offset: 2px; }
.foot a:hover { color: var(--ink) !important; }
.tag {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 999px;
  border: 1px solid var(--border);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--muted);
  white-space: nowrap;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 480px) {
  .panel {
    inset: 0;
    width: 100%;
    height: 100%;
    height: 100dvh;
    border: 0;
    border-radius: 0;
    animation-name: slide;
  }
  .dc.open .launcher, .dc.open .tooltip { display: none; }
  .launcher { bottom: 16px; right: 16px; }
  .dc.left .launcher { left: 16px; }
  .tooltip { right: 16px; bottom: 88px; max-width: calc(100vw - 32px); }
  .bubble, .source-block, .notice { max-width: 92%; }
  .input { font-size: 16px !important; }
}

@keyframes pop { from { opacity: 0; transform: translateY(8px) scale(0.98); } to { opacity: 1; transform: none; } }
@keyframes slide { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
@keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
@keyframes blink { 0%, 80%, 100% { opacity: 0.25; } 40% { opacity: 0.9; } }

@media (prefers-reduced-motion: reduce) {
  .panel, .tooltip { animation: none; }
  .typing span { animation: none; opacity: 0.6; }
  .launcher, .chip-source .chev, .chip, .choice { transition: none; }
  .launcher:hover { transform: none; }
  .log { scroll-behavior: auto; }
}
`;
