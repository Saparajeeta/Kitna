"""CSS and the small scripts the page needs. System fonts only: no third-party requests."""
CSS = """
:root, .gradio-container {
  --k-high-bg:#e3f4e8; --k-high-fg:#0b4a22; --k-med-bg:#fff3cd; --k-med-fg:#5c4300;
  --k-low-bg:#fde2e1; --k-low-fg:#7a1512; --k-amb-bg:#ffe8cc; --k-amb-fg:#6b3500;
  --k-chosen-bg:#e0e7ff; --k-chosen-fg:#1e2a78; --k-line:#c9ced6; --k-soft:#f6f7f9; --k-fg:#16181d;
  --k-muted:#4a5160; --k-warn-bg:#fff4e5; --k-warn-fg:#5c3a00; --k-link:#0b57d0;
}
.dark, .dark .gradio-container {
  --k-high-bg:#123d22; --k-high-fg:#c9f2d6; --k-med-bg:#4a3a00; --k-med-fg:#ffe9a8;
  --k-low-bg:#5a1513; --k-low-fg:#ffd3d1; --k-amb-bg:#5a3200; --k-amb-fg:#ffd9a8;
  --k-chosen-bg:#232d6b; --k-chosen-fg:#d5dcff; --k-line:#4a5160; --k-soft:#1d2027; --k-fg:#f1f3f6;
  --k-muted:#c3c8d2; --k-warn-bg:#3d2c0a; --k-warn-fg:#ffe2b0; --k-link:#9cc2ff;
}
.gradio-container { max-width: 880px !important; margin: 0 auto !important; }
.k-story { font-size: 1.35rem; line-height: 1.35; font-weight: 700; color: var(--k-fg); margin: 4px 0 8px; }
.k-banner { background: var(--k-warn-bg); color: var(--k-warn-fg); border: 1px solid var(--k-line);
  border-radius: 10px; padding: 10px 12px; font-size: .95rem; }
.k-banner a, .k-fb a, .k-about a { color: var(--k-link); text-decoration: underline; }
.k-empty { border: 1px dashed var(--k-line); border-radius: 10px; padding: 16px; color: var(--k-muted);
  background: var(--k-soft); }
.k-error { border: 1px solid var(--k-low-fg); background: var(--k-low-bg); color: var(--k-low-fg);
  border-radius: 10px; padding: 12px; }
.k-msg { font-size: 1.15rem; line-height: 2.3; color: var(--k-fg); background: var(--k-soft);
  border: 1px solid var(--k-line); border-radius: 10px; padding: 10px 14px; overflow-wrap: anywhere; }
.k-hl { border-radius: 6px; padding: 3px 6px; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.k-eq { font-weight: 700; }
.k-hl.k-high, .k-chip-high { background: var(--k-high-bg); color: var(--k-high-fg); }
.k-hl.k-med, .k-chip-med { background: var(--k-med-bg); color: var(--k-med-fg); }
.k-hl.k-low, .k-chip-low { background: var(--k-low-bg); color: var(--k-low-fg); }
.k-hl.k-amb, .k-chip-amb { background: var(--k-amb-bg); color: var(--k-amb-fg); }
.k-hl.k-amb { border-bottom: 2px dashed var(--k-amb-fg); }
.k-hl.k-chosen, .k-chip-chosen { background: var(--k-chosen-bg); color: var(--k-chosen-fg); }
.k-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }
.k-card, .k-rcard, .k-act, .k-cmp { border: 1px solid var(--k-line); border-radius: 12px; padding: 12px 14px;
  background: var(--k-soft); color: var(--k-fg); }
.k-card.k-amb { border-color: var(--k-amb-fg); border-style: dashed; }
.k-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
.k-kind { font-size: .8rem; letter-spacing: .04em; text-transform: uppercase; color: var(--k-muted); }
.k-chip { font-size: .8rem; font-weight: 700; border-radius: 999px; padding: 2px 10px; white-space: nowrap; }
.k-said { color: var(--k-muted); margin-top: 6px; overflow-wrap: anywhere; }
.k-read { font-size: 1.3rem; font-weight: 700; margin: 2px 0 6px; overflow-wrap: anywhere; color: var(--k-fg); }
.k-ask, .k-block { color: var(--k-amb-fg); background: var(--k-amb-bg); border-radius: 8px; padding: 6px 8px; }
.k-why { font-size: .93rem; color: var(--k-fg); }
.k-whyh { font-weight: 700; }
.k-why ul { margin: 2px 0 6px 18px; padding: 0; list-style: disc; }
.k-rule { display: block; font-size: .82rem; color: var(--k-muted); }
.k-det summary { cursor: pointer; color: var(--k-link); font-size: .9rem; padding: 6px 0; }
.k-det table, .k-cmp table { width: 100%; border-collapse: collapse; font-size: .88rem; table-layout: fixed; }
.k-det th, .k-det td, .k-cmp th, .k-cmp td { text-align: left; vertical-align: top; padding: 4px 6px;
  border-top: 1px solid var(--k-line); overflow-wrap: anywhere; color: var(--k-fg); }
.k-det th { width: 45%; font-weight: 600; color: var(--k-muted); }
.k-acth { font-size: .8rem; letter-spacing: .04em; text-transform: uppercase; color: var(--k-muted); }
.k-sentence { font-size: 1.35rem; font-weight: 700; margin: 4px 0 8px; overflow-wrap: anywhere; }
.k-ready { color: var(--k-high-fg); background: var(--k-high-bg); border-radius: 8px; padding: 6px 8px; }
.k-preview { font-weight: 600; margin: 6px 0 2px; }
.k-how, .k-cmp-note, .k-progt, .k-rhelp, .k-rnote { font-size: .88rem; color: var(--k-muted); }
.k-done { border: 1px solid var(--k-high-fg); background: var(--k-high-bg); color: var(--k-high-fg);
  border-radius: 10px; padding: 10px 12px; }
.k-cmp { margin-bottom: 10px; }
.k-cmp h4 { margin: 0 0 6px; font-size: 1.05rem; }
.k-ver { font-size: .8rem; font-weight: 600; color: var(--k-muted); margin-left: 6px; }
.k-cmp td:first-child { width: 52%; }
.k-fb { border: 1px solid var(--k-line); border-radius: 10px; padding: 10px 12px; background: var(--k-soft);
  color: var(--k-fg); }
.k-fb ul { margin: 4px 0 0 18px; list-style: disc; }
.k-prog { height: 12px; background: var(--k-soft); border: 1px solid var(--k-line); border-radius: 999px;
  overflow: hidden; }
.k-bar { height: 100%; background: var(--k-high-fg); }
.k-rtext { font-size: 1.6rem; font-weight: 700; margin: 2px 0 8px; overflow-wrap: anywhere; }
.k-rlabel { font-size: .8rem; letter-spacing: .04em; text-transform: uppercase; color: var(--k-muted);
  margin: 8px 0 0; }
.k-dl { display: inline-block; font-weight: 700; padding: 10px 14px; border-radius: 10px;
  background: var(--k-high-bg); color: var(--k-high-fg) !important; }
.k-gallery button { min-width: 0 !important; flex: 1 1 140px !important; }
.k-verdicts button { min-height: 56px; font-size: 1.05rem; }
footer { display: none !important; }
@media (max-width: 480px) {
  .k-story { font-size: 1.12rem; }
  .k-msg { font-size: 1.02rem; line-height: 2.1; }
  .k-sentence, .k-read { font-size: 1.15rem; }
  .k-rtext { font-size: 1.35rem; }
  .k-det th { width: 50%; }
  .k-cmp td:first-child { width: 45%; }
}
"""

#: Ctrl+Enter / Cmd+Enter anywhere on the page reads the message
HEAD = """
<meta name="description" content="Kitna reads amounts, dates and times in Hinglish and Hindi messages.">
<script>
document.addEventListener('keydown', function (e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    var b = document.querySelector('#k-read-btn button') || document.querySelector('button#k-read-btn');
    if (b) { e.preventDefault(); b.click(); }
  }
});
</script>
"""

#: fills 'now' from the visitor's own clock when the fields are empty
JS_LOCAL_NOW = """
(d, t) => {
  const n = new Date(), p = (x) => String(x).padStart(2, '0');
  return [d || `${n.getFullYear()}-${p(n.getMonth() + 1)}-${p(n.getDate())}`,
          t || `${p(n.getHours())}:${p(n.getMinutes())}`];
}
"""
JS_SHARE = """
(text, d, t) => {
  const u = new URL(window.location.href);
  u.search = '';
  if (text) u.searchParams.set('text', text);
  if (d) u.searchParams.set('d', d);
  if (t) u.searchParams.set('t', t);
  const link = u.toString();
  try { navigator.clipboard.writeText(link).catch(() => {}); } catch (e) {}
  return link;
}
"""
JS_THEME = """
() => {
  const dark = !document.body.classList.contains('dark');
  document.body.classList.toggle('dark', dark);
  document.documentElement.classList.toggle('dark', dark);
  try { const u = new URL(window.location.href); u.searchParams.set('__theme', dark ? 'dark' : 'light');
        window.history.replaceState({}, '', u); } catch (e) {}
}
"""
