// The Jerseys & gear tab: the team's gear colours (shades of one colour change together, so every jersey's gear does),
// what each jersey wears (a preview of a skater and a goalie), the team colours (editable; the gear follows), another
// team's gear to copy, the sticks. Python keeps a draft per team; Apply hands it to My edits. Slice `jerseys`, calls in
// docs/ui/jerseys.md. One page scroll: the card body is the only scroller; the action bar stays at the foot.
import { html, cls, Fragment, useState, useEffect, useRef } from '../lib.js';
import { useSlice } from '../store.js';
import { call } from '../bridge.js';
import { Select, Why as UiWhy } from '../ui.js';
import { Code } from '../rail.js';

export const tip = 'Click a colour to change it on every jersey, or change a team colour, then Apply.';

const bg = (h) => ({ background: `#${h}` });
const poss = (name) => (name.endsWith('s') ? `${name}'` : `${name}'s`);
const recolour = (from, to) => call('gear_recolour', { [from]: to });
const teamColour = (slot, to) => call('gear_team_colour', slot, to);
const WHERE = "In NHL 19 the Primary colour is the team's colour in the menus: the glow behind it on team select and game setup, the header band of Edit Player and Edit Lines, and its bars on the pause screen.";
const UNSEEN = 'Not seen in game: a place where NHL 19 shows the Secondary or Third colour, besides the gear that wears it. The scoreboard keeps its own look.';
const OFF_TIP = "NHL 19 keeps more helmets, gloves and goalie gear than these jerseys wear: the retro jerseys' sets. "
  + 'This colour changes there too, but the preview cannot show it.';
const FALLBACK = '6B717A';
const PIECE_ORDER = ['Helmet', 'Gloves', 'Goalie pads', 'Blocker', 'Trapper', 'Goalie stick'];

// a colour box: the swatch is the label, the browser's colour picker opens on click
function Pick({ hex, label, onPick, className, tipText }) {
  return html`<label class=${cls('jg-sw jg-pick', className)} style=${bg(hex)} data-tip=${tipText}
      data-tip-h=${tipText ? label : undefined}>
    <input type="color" value=${`#${hex.toLowerCase()}`} aria-label=${label}
      onChange=${(e) => onPick(e.target.value.slice(1).toUpperCase())}/></label>`;
}

// a team the tab cannot show, or its gear still being read (Legacy's Why)
function Why({ s }) {
  return html`<${UiWhy} className="jg-why" mark=${s.view && html`<${Code} team=${s.view}/>`} text=${s.why} busy=${s.loading}/>`;
}

const Arrow = () => html`<svg viewBox="0 0 12 10" class="jg-arrow" aria-hidden="true"><path d="M0 4h8V1l4 4-4 4V6H0z" fill="currentColor"/></svg>`;

// the hover explanations of this tab: one box that follows the pointer (and the keyboard focus). It reads the element's
// data-tip (text), data-tip-h (a heading) and data-tip-u (the amber "not yet seen in game" line). Text only, no HTML.
function Tips() {
  const ref = useRef(null);
  useEffect(() => {
    const tip = ref.current;
    const root = tip.closest('.jg-tab') || document.body;
    let cur = null;
    const place = (x, y) => {
      tip.style.left = `${Math.max(8, Math.min(x + 14, window.innerWidth - tip.offsetWidth - 8))}px`;
      tip.style.top = `${Math.max(8, Math.min(y + 16, window.innerHeight - tip.offsetHeight - 8))}px`;
    };
    const fill = (el) => {
      tip.replaceChildren();
      const add = (tag, text, name) => {
        if (!text) return;
        const n = document.createElement(tag);
        if (name) n.className = name;
        n.textContent = text;
        tip.append(n);
      };
      add('b', el.dataset.tipH);
      add('span', el.dataset.tip);
      add('span', el.dataset.tipU, 'u');
    };
    const over = (e) => {
      const el = e.target instanceof Element ? e.target.closest('[data-tip],[data-tip-h]') : null;
      if (el === cur) return;
      cur = el;
      if (!el || !root.contains(el) || !(el.dataset.tip || el.dataset.tipH)) { tip.style.display = 'none'; return; }
      fill(el);
      tip.style.display = 'block';
      if (e.type === 'mouseover') place(e.clientX, e.clientY);
      else { const r = el.getBoundingClientRect(); place(r.left, r.bottom - 16); }
    };
    const move = (e) => { if (cur && tip.style.display === 'block') place(e.clientX, e.clientY); };
    const gone = () => { cur = null; tip.style.display = 'none'; };
    document.addEventListener('mouseover', over);
    document.addEventListener('mousemove', move);
    document.addEventListener('focusin', over);
    document.addEventListener('focusout', gone);
    return () => {
      document.removeEventListener('mouseover', over);
      document.removeEventListener('mousemove', move);
      document.removeEventListener('focusin', over);
      document.removeEventListener('focusout', gone);
    };
  }, []);
  return html`<div class="jg-tip" ref=${ref} role="tooltip" style=${{ display: 'none' }}></div>`;
}

// --- the figures: a skater and a goalie. Their helmet, gloves and goalie gear take the colours of their gear rows (Now:
// the roster's, After Apply: the draft's); the jersey is a sketch from the team colours.
// slot 0 the piece's main colour, 1 its trim (the main one when it has one colour), 2 a detail, drawn only when the
// piece has a third colour (Anaheim's goalie gear: one orange zone of 15)
function Gear({ fig, part, slot = 0, d }) {
  const keys = fig.jersey ? fig.jersey.parts[part] || [] : [];
  if (slot === 2 && keys.length < 3) return null;
  const key = keys.length > slot ? keys[slot] : keys[0];
  const row = key && fig.palette.find((r) => r.from === key);
  const fill = row ? `#${fig.mode === 'now' ? row.from : row.to}` : `#${FALLBACK}`;
  return html`<path d=${d} class=${cls('jg-edge', fig.lit && key === fig.lit && 'lit')} fill=${fill}
    data-part=${part} data-key=${key || ''}/>`;
}

function Skater({ fig }) {
  const sk = (k) => `#${fig.sketch[k]}`;
  return html`<svg viewBox="0 0 160 300" class="jg-fig" role="img" aria-label="Skater">
    <ellipse cx="80" cy="292" rx="52" ry="6" fill="rgba(0,0,0,.35)"/>
    <path class="jg-edge" d="M46 264 L74 264 L75 278 L40 279 Q38 272 46 264Z" fill="#26292e"/>
    <path class="jg-edge" d="M86 264 L114 264 Q122 272 120 279 L85 278Z" fill="#26292e"/>
    <rect x="38" y="281" width="40" height="3" fill="#c8d0d8"/><rect x="82" y="281" width="40" height="3" fill="#c8d0d8"/>
    <path class="jg-edge" d="M50 212 L74 212 L73 266 L48 266Z M86 212 L110 212 L112 266 L87 266Z" fill=${sk('body')}/>
    <path d="M49 236 L73 236 L73 243 L49 243Z M87 236 L111 236 L111 243 L87 243Z" fill=${sk('trim')}/>
    <path class="jg-edge" d="M44 170 L116 170 L118 214 L86 214 L80 196 L74 214 L42 214Z" fill="#1a1a1a"/>
    <path d="M30 278 L146 152" stroke="#c9a46a" stroke-width="5" stroke-linecap="round"/>
    <path d="M30 278 L8 282" stroke="#c9a46a" stroke-width="7" stroke-linecap="round"/>
    <path class="jg-edge" d="M46 84 Q80 72 114 84 L140 122 L130 150 L118 138 L116 174 L44 174 L42 138 L30 150 L20 122Z" fill=${sk('body')}/>
    <path d="M22 128 L38 146 L34 151 L20 134Z M138 128 L122 146 L126 151 L140 134Z M44 158 L116 158 L116 165 L44 165Z" fill=${sk('trim')}/>
    <path d="M64 80 Q80 90 96 80 L96 84 Q80 95 64 84Z" fill=${sk('trim')}/>
    <text x="80" y="132" text-anchor="middle" font-family="Titillium Web, Segoe UI" font-weight="700" font-size="30" fill=${sk('num')}>17</text>
    <${Gear} fig=${fig} part="gloves" d="M14 142 L34 150 L30 172 L10 166Z M146 142 L126 150 L130 172 L150 166Z"/>
    <${Gear} fig=${fig} part="gloves" slot=${1} d="M18 136 L38 144 L35 152 L15 145Z M142 136 L122 144 L125 152 L145 145Z"/>
    <${Gear} fig=${fig} part="gloves" slot=${2} d="M13 156 L33 163 L32 167 L12 161Z M147 156 L127 163 L128 167 L148 161Z"/>
    <ellipse cx="80" cy="64" rx="16" ry="15" fill="#d9a882"/>
    <${Gear} fig=${fig} part="helmet" d="M52 52 C50 20 110 20 108 52 L104 60 L99 52 L61 52 L56 60Z"/>
    <${Gear} fig=${fig} part="helmet" slot=${1} d="M52 46 L108 46 L108 52 L52 52Z M76 29 Q80 28 84 29 L84 46 L76 46Z"/>
    <${Gear} fig=${fig} part="helmet" slot=${2} d="M58 36 L68 34 L68 42 L57 43Z M102 36 L92 34 L92 42 L103 43Z"/>
    <rect x="61" y="52" width="38" height="8" rx="2" fill="rgba(170,215,255,.35)" stroke="rgba(255,255,255,.4)"/>
  </svg>`;
}

function Goalie({ fig }) {
  const sk = (k) => `#${fig.sketch[k]}`;
  return html`<svg viewBox="0 0 170 300" class="jg-fig" role="img" aria-label="Goalie">
    <ellipse cx="85" cy="292" rx="66" ry="6" fill="rgba(0,0,0,.35)"/>
    <${Gear} fig=${fig} part="gstick" d="M140 150 L146 150 L146 238 L140 238Z M120 238 L148 238 L150 288 L104 290 L104 280 L122 276Z"/>
    <${Gear} fig=${fig} part="gstick" slot=${2} d="M140 200 L146 200 L146 210 L140 210Z M104 282 L149 278 L149 283 L104 286Z"/>
    <path class="jg-edge" d="M48 168 L122 168 L124 206 L46 206Z" fill="#1a1a1a"/>
    <${Gear} fig=${fig} part="pads" d="M40 200 L82 200 L82 284 L38 284Z M88 200 L130 200 L132 284 L88 284Z"/>
    <${Gear} fig=${fig} part="pads" slot=${1} d="M40 214 L82 214 L82 224 L40 224Z M88 214 L130 214 L130 224 L88 224Z M40 250 L82 250 L82 258 L40 258Z M88 250 L130 250 L130 258 L88 258Z"/>
    <${Gear} fig=${fig} part="pads" slot=${2} d="M40 234 L82 234 L82 239 L40 239Z M88 234 L130 234 L130 239 L88 239Z M40 272 L82 272 L82 276 L39 276Z M88 272 L131 272 L131 276 L88 276Z"/>
    <path class="jg-edge" d="M44 82 Q85 68 126 82 L156 126 L144 158 L128 142 L126 176 L44 176 L42 142 L26 158 L14 126Z" fill=${sk('body')}/>
    <path d="M16 132 L32 150 L28 155 L14 138Z M154 132 L138 150 L142 155 L156 138Z M44 160 L126 160 L126 167 L44 167Z" fill=${sk('trim')}/>
    <text x="85" y="130" text-anchor="middle" font-family="Titillium Web, Segoe UI" font-weight="700" font-size="28" fill=${sk('num')}>31</text>
    <${Gear} fig=${fig} part="trapper" d="M2 140 Q-2 118 22 118 Q42 120 38 146 L34 170 L8 168Z"/>
    <${Gear} fig=${fig} part="trapper" slot=${1} d="M8 150 L36 152 L34 170 L8 168Z"/>
    <${Gear} fig=${fig} part="trapper" slot=${2} d="M9 146 L37 148 L36 152 L8 150Z"/>
    <${Gear} fig=${fig} part="blocker" d="M134 130 L164 128 L166 178 L136 180Z"/>
    <${Gear} fig=${fig} part="blocker" slot=${1} d="M134 130 L164 128 L165 140 L135 142Z"/>
    <${Gear} fig=${fig} part="blocker" slot=${2} d="M135 160 L165 158 L165 164 L135 166Z"/>
    <${Gear} fig=${fig} part="helmet" d="M60 60 C56 26 114 26 110 60 L108 78 L62 78Z"/>
    <${Gear} fig=${fig} part="helmet" slot=${1} d="M60 50 L110 50 L110 56 L60 56Z"/>
    <${Gear} fig=${fig} part="helmet" slot=${2} d="M64 38 L74 34 L74 44 L63 46Z M106 38 L96 34 L96 44 L107 46Z"/>
    <path d="M68 58 L102 58 L100 76 L70 76Z" fill="#cfd5db" opacity=".9"/>
    <path d="M72 58 L72 76 M79 58 L79 76 M86 58 L86 76 M93 58 L93 76 M98 58 L98 76 M68 64 L102 64 M69 70 L101 70" stroke="#5c646c" stroke-width="1.4"/>
  </svg>`;
}

// the gear colours a figure part wears, by name, for the legend
function Legend({ fig, jersey }) {
  const rows = [['Helmet', 'helmet'], ['Gloves', 'gloves'], ['Goalie pads', 'pads'], ['Blocker', 'blocker']];
  return html`<div class="jg-legend">${rows.map(([name, part]) => {
    const keys = (jersey && jersey.parts[part]) || [];
    const got = keys.map((k) => fig.palette.find((r) => r.from === k)).filter(Boolean);
    return html`<${Fragment} key=${part}><span class="jg-lk">${name}</span><span class="jg-lv">${got.length
      ? got.map((r, i) => html`<span key=${i} class="jg-lsw"><i class="jg-sw small" style=${bg(fig.mode === 'now' ? r.from : r.to)}></i>${r.name}${i < got.length - 1 ? ' · ' : ''}</span>`)
      : html`<span class="faint">none</span>`}</span><//>`;
  })}</div>`;
}

// --- gear colours: one row per colour of the team's gear: now, new, the team colour picks, where it is, Back -----------
function GearRow({ r, s, nJerseys, lit, setLit, backOne }) {
  const team = s.colours.new || s.colours.now;
  const worn = Object.entries(r.worn || {});
  const off = r.pieces.filter((p) => !(r.worn && p in r.worn));    // in gear rows no jersey here wears
  const shades = r.shades.length > 1 ? `${r.shades.length} shades` : '';
  return html`<div class=${cls('jg-row', r.changed && 'changed', lit === r.from && 'lit')}
      onMouseEnter=${() => setLit(r.from)} onMouseLeave=${() => setLit('')}>
    <div class="jg-name">
      <span class="jg-sw big" style=${bg(r.from)} data-tip=${`${r.name} now: #${r.from}.`}></span>
      <span class="jg-cn"><b>${r.name}</b>${shades && html`<small class="jg-shades" data-tip-h=${`${r.shades.length} shades of ${r.name.toLowerCase()}`}
        data-tip=${`${r.shades.map((h) => `#${h}`).join(', ')}. They change together: a change here moves every shade, so the gear keeps its look.`}>${shades}</small>`}</span>
    </div>
    <${Arrow}/>
    <span class="jg-sw big jg-newsw" style=${bg(r.to)}
      data-tip=${r.changed ? `${r.name} becomes #${r.to} after Apply.` : `${r.name} stays as it is. Pick a colour on the right.`}></span>
    <div class="jg-picks">
      <span class="jg-lbl">Team colours</span>
      ${team.map((c, k) => html`<button type="button" key=${k} class=${cls('jg-qsw', r.to === c && 'on')}
          style=${bg(c)} data-tip-h=${`${(s.colours.slots[k] || '')} team colour`}
          data-tip=${`#${c}. One click: ${r.name.toLowerCase()} becomes this colour.`}
          onClick=${() => recolour(r.from, c)}></button>`)}
      <label class="jg-any" data-tip="The full colour picker: any colour for this row.">Any colour...
        <input type="color" value=${`#${r.to.toLowerCase()}`} aria-label=${`Any colour for ${r.name}`}
          onChange=${(e) => recolour(r.from, e.target.value.slice(1).toUpperCase())}/></label>
    </div>
    <span class="jg-tags">${r.changed
      ? html`<span class="jg-tag good" data-tip=${`${r.name} is changed in the draft. Apply keeps it.`}>changed</span>`
      : r.slot ? html`<span class="jg-tag blue" data-tip=${`This colour is the team's ${r.slot.toLowerCase()} colour. It follows when you change that team colour.`}>= ${r.slot} team colour</span>` : ''}</span>
    <button type="button" class="btn small jg-back" disabled=${!r.changed} onClick=${() => backOne(r)}
      data-tip=${`Back to ${r.name.toLowerCase()} #${r.from}, the roster's colour.`}>Back</button>
    <div class="jg-worn-line"><span class="jg-lbl">Worn on</span>
      ${worn.length ? worn.map(([piece, labels]) => html`<span key=${piece} class="jg-chip"
          data-tip-h=${piece} data-tip=${`${piece} in ${r.name}: ${labels.length === nJerseys ? 'every jersey' : labels.join(', ')}.`}>${piece}</span>`)
        : html`<span class="jg-off" data-tip-h="Not on these jerseys" data-tip=${OFF_TIP}>none of these jerseys</span>`}
      ${off.length ? html`<span class="jg-off" data-tip-h="Gear these jerseys don't wear" data-tip=${OFF_TIP}>${worn.length ? 'also on other gear' : 'only on other gear'}: ${off.join(', ').toLowerCase()}</span>` : ''}</div>
  </div>`;
}

// --- worn with each jersey: the helmet and gloves of each jersey, the picked one marked --------------------------------
function Worn({ s, pick, jersey, mode }) {
  if (!s.jerseys || !s.jerseys.length) return null;
  const sw = (j, part) => (j.parts[part] || []).map((k, i) => {
    const row = s.palette.find((r) => r.from === k);
    return html`<i key=${i} class="jg-sw small" style=${bg(row ? (mode === 'now' ? row.from : row.to) : FALLBACK)}></i>`;
  });
  return html`<div class="jg-wj">${s.jerseys.map((j, i) => html`<button type="button" key=${j.label}
      class=${cls('jg-wcard', i === jersey && 'on')} onClick=${() => pick(i)}
      data-tip-h=${j.label} data-tip=${`Show the ${j.label} jersey's gear on the figures.`}>
    <span class="jg-jname">${j.label}</span>
    <span class="jg-wline"><span class="jg-lbl">Helmet</span><span class="jg-wsw">${sw(j, 'helmet')}</span></span>
    <span class="jg-wline"><span class="jg-lbl">Gloves</span><span class="jg-wsw">${sw(j, 'gloves')}</span></span>
  </button>`)}</div>`;
}

function Colours({ s }) {
  const c = s.colours;
  const chips = (list) => list.map((h, k) => html`<span key=${k} class="jg-chip" data-tip-h="NHL 19's own colour" data-tip=${`#${h}`}><i class="jg-sw small" style=${bg(h)}></i>#${h}</span>`);
  return html`<${Fragment}><div class="jg-tc-row">${c.now.map((h, k) => {
      const to = c.new[k];
      const changed = c.changed[k];
      return html`<div key=${k} class=${cls('jg-tc', changed && 'changed')}
          data-tip-h=${`${c.slots[k]} team colour`}
          data-tip=${(changed ? `Now #${h}, after Apply #${to}. The gear rows in this colour follow it.` : `Now #${h}. Pick a colour to change it. The gear rows in this colour follow it.`) + (k === 0 ? ` ${WHERE}` : '')}
          data-tip-u=${k === 0 ? undefined : UNSEEN}>
        <span class="jg-tc-name">${c.slots[k]}</span>
        <${Pick} hex=${to} className="big" label=${`New ${c.slots[k].toLowerCase()} team colour`} onPick=${(v) => teamColour(k, v)}/>
        <span class="jg-tc-hex">${changed ? html`<s>#${h}</s> ` : ''}#${to}</span>
        ${changed ? html`<span class="jg-tags"><span class="jg-tag good">changed</span></span>
          <button type="button" class="btn small jg-back" onClick=${() => teamColour(k, h)}>Back</button>` : ''}
      </div>`;
    })}</div>
    <div class="jg-crow"><span class="jg-lbl">NHL 19's own</span>${c.game ? chips(c.game) : html`<span class="faint">None</span>`}</div>
    <div class="jg-actions">
      <span data-tip="Gear colours that wear NHL 19's old team colours change to the colours now. You check them, then Apply."><button type="button"
        class="btn" disabled=${!c.can_propose} onClick=${() => call('gear_propose')}>Gear to the team colours</button></span>
      <span class="small-note faint">${c.note}</span>
    </div><//>`;
}

function Copy({ s }) {
  const c = s.copy;
  const options = [{ value: '', label: "This team's own gear" }, ...c.options];
  return html`<div class="jg-actions">
    <span data-tip="Gives this team another team's helmets, gloves and goalie gear. One Apply, one Undo.">
      <${Select} className="jg-select" value=${c.from ?? ''} options=${options} title="Copy the gear of"
        disabled=${c.from == null && !c.options.some((o) => !o.disabled)}
        onChange=${(v) => call('gear_copy', v === '' ? null : v)}/></span>
    ${c.error ? html`<span class="note bad jg-error">${c.error}</span>`
      : html`<span class="small-note faint jg-cnote">${c.note}</span>`}
  </div>`;
}

function Sticks({ s }) {
  const k = s.sticks;
  return html`<${Fragment}>${k.count ? html`<div class="jg-sticks">${k.rows.map((r) => html`<div key=${r.name}
        class=${cls('jg-stick', k.fitted && 'fitted')} data-tip-h=${r.name} data-tip=${`Now ${r.old}. ${k.fitted ? `After Apply ${r.new}.` : `Fitted: ${r.new}.`}`}>
        <b>${r.name}</b><span class="jg-old">${r.old}</span><${Arrow}/><span class="jg-new">${r.new}</span>
      </div>`)}</div>`
      : html`<p class="jg-none">Every stick matches the team colours.</p>`}
    <div class="jg-actions">
      <span data-tip="Each stick changes to a stick of the same brand in the team colours.">
        <button type="button" class="btn" disabled=${!k.count} onClick=${() => call('gear_sticks', false)}>${k.fitted ? 'Keep these sticks' : "Fit this team's sticks"}</button></span>
      <span data-tip=${`${k.nhl_count} sticks on ${k.nhl_teams} NHL teams. You are asked first.`}>
        <button type="button" class="btn" disabled=${!k.nhl_count} onClick=${() => call('gear_sticks', true)}>Every NHL team...</button></span>
      <span class="small-note faint">${k.fitted ? `${k.count} ${k.count === 1 ? 'stick changes' : 'sticks change'} when you press Apply.`
        : k.count ? 'Each becomes a stick of its brand in the team colours.'
          : k.nhl_count ? `${k.nhl_count} sticks on ${k.nhl_teams} NHL teams do not match their team colours.` : ''}</span>
    </div><//>`;
}

export default function Jerseys() {
  const s = useSlice('jerseys');
  const [jersey, setJersey] = useState(0);
  const [mode, setMode] = useState('new');
  const [lit, setLit] = useState('');
  if (!s) return null;
  if (s.why) return html`<${Why} s=${s}/>`;
  const list = s.jerseys || [];
  const at = list.length ? Math.min(jersey, list.length - 1) : 0;
  const cur = list.length ? list[at] : null;
  const sketch = cur ? cur.sketch[mode === 'now' ? 'now' : 'new'] : { body: '303640', trim: 'E6E6E6', num: 'FFFFFF' };
  const fig = { jersey: cur, palette: s.palette, mode, lit, sketch };
  const rowsChanged = s.palette.filter((r) => r.changed).length;
  const teamChanged = s.colours.changed.filter(Boolean).length;
  const waiting = rowsChanged + teamChanged + (s.copy.from != null ? 1 : 0) + (s.sticks.fitted ? 1 : 0);
  const backOne = (r) => recolour(r.from, r.from);
  const backAll = async () => {
    for (let k = 0; k < s.colours.changed.length; k += 1) if (s.colours.changed[k]) await teamColour(k, s.colours.now[k]);
    for (const r of s.palette) if (r.changed) await recolour(r.from, r.from);
  };
  const helmet = (s.pieces.find((p) => p.name === 'Helmet') || { colours: [] }).colours.map((c) => c.hex);
  return html`<section class="card grow jg-tab">
    <header class="card-head jg-head">
      ${s.view && html`<${Code} team=${s.view} small/>`}
      <span class="title">${s.title}</span>
      ${s.touched && html`<span class="aside"><span class="pill">Not applied</span></span>`}
    </header>
    <div class="card-body scroll jg-body">
      <${Tips}/>
      <p class=${cls('small-note jg-note', s.note_tone)}>${s.note}</p>
      <div class="jg-how">
        <div><b>1</b>Each row under <i>Gear colours</i> is one colour this team's gear wears today.</div>
        <div><b>2</b>Give a row a new colour: every helmet, glove and pad in that colour changes, on every jersey.</div>
        <div><b>3</b><i>Apply</i> keeps it in My edits. <i>Patch</i> on the Patch tab puts it in NHL 19.</div>
      </div>
      <div class="jg-grid">
        <aside class="jg-preview">
          <div class="jg-sec-head"><span class="jg-h caps">Preview</span>
            <span class="jg-info" tabindex="0" data-tip="What a skater and a goalie of this team wear with the jersey you pick. Helmet, gloves and the goalie's gear come from the gear colour rows. The jersey itself is a sketch in the team colours.">i</span></div>
          <div class="jg-jtabs">${list.map((j, i) => html`<button type="button" key=${j.label}
              class=${cls('jg-jt', i === at && 'on')} onClick=${() => setJersey(i)}
              data-tip-h=${j.label} data-tip=${`See the gear worn with the ${j.label} jersey.`}>${j.label}</button>`)}</div>
          <div class="jg-figures">
            <div><${Skater} fig=${fig}/><span class="jg-fig-label">Skater</span></div>
            <div><${Goalie} fig=${fig}/><span class="jg-fig-label">Goalie</span></div>
          </div>
          <div class="jg-seg" data-tip-h="Now and After Apply" data-tip="Now shows the gear as the roster has it. After Apply shows it with your picks.">
            <button type="button" class=${cls(mode === 'now' && 'on')} aria-pressed=${mode === 'now'} onClick=${() => setMode('now')}>Now</button>
            <button type="button" class=${cls(mode === 'new' && 'on')} aria-pressed=${mode === 'new'} onClick=${() => setMode('new')}>After Apply</button>
          </div>
          <${Legend} fig=${fig} jersey=${cur}/>
          <p class="jg-sketch">The jersey is a sketch from the team colours. Helmet, gloves and goalie gear are true to the roster.</p>
        </aside>
        <div class="jg-main">
          <section class="jg-sec">
            <div class="jg-sec-head"><span class="jg-h caps">Team colours</span><span class="faint jg-aside">the club's three colours</span>
              <span class="jg-info" tabindex="0" data-tip=${`Team colours: the club's Primary, Secondary and Third colour. The gear rows offer them as one-click picks. Change one and the gear rows in that colour follow it. ${WHERE}`} data-tip-u=${UNSEEN}>i</span></div>
            <${Colours} s=${s}/>
          </section>

          <section class="jg-sec">
            <div class="jg-sec-head"><span class="jg-h caps">Gear colours</span>
              <span class="faint jg-aside">${s.palette.length} ${s.palette.length === 1 ? 'colour' : 'colours'} on every jersey</span>
              <span class="jg-info" tabindex="0" data-tip="The colours on this team's helmets, gloves and goalie gear, across all its jerseys, most used first. Change a row and every piece in that colour changes together, so the gear keeps its design in new colours.">i</span></div>
            <p class="jg-lead">Pick a team colour, or <i>Any colour...</i> for the full picker. <i>Back</i> undoes a row. Hover a row and its pieces light up on the figures.</p>
            <div class="jg-rows">${s.palette.map((r) => html`<${GearRow} key=${r.from} r=${r} s=${s} nJerseys=${list.length}
                lit=${lit} setLit=${setLit} backOne=${backOne}/>`)}</div>
          </section>

          <section class="jg-sec">
            <div class="jg-sec-head"><span class="jg-h caps">Worn with each jersey</span><span class="faint jg-aside">click one to see it on the figures</span>
              <span class="jg-info" tabindex="0" data-tip="The helmet and gloves a skater wears with each jersey, in the colours above, as NHL 19 dresses them.">i</span></div>
            <${Worn} s=${s} pick=${setJersey} jersey=${at} mode=${mode}/>
          </section>

          <div class="jg-more">
            <section class="jg-sec">
              <div class="jg-sec-head"><span class="jg-h caps">Copy gear</span></div>
              <${Copy} s=${s}/>
            </section>
            <section class="jg-sec">
              <div class="jg-sec-head"><span class="jg-h caps">Sticks</span>
                <span class="faint jg-aside">${s.sticks.count ? `${s.sticks.count} not in the team colours` : 'the stick brands'}</span></div>
              <${Sticks} s=${s}/>
            </section>
          </div>
        </div>
      </div>
    </div>
    <div class="card-foot jg-foot">
      <span class="jg-count">${waiting
        ? html`<b>${waiting}</b> ${waiting === 1 ? 'change' : 'changes'} waiting for Apply`
        : (s.mine ? 'This team wears your gear. Save the roster to keep it.' : 'No changes yet')}</span>
      <button type="button" class="btn" disabled=${!(rowsChanged + teamChanged)} onClick=${backAll}
        data-tip="Every colour and team colour back to what the roster has. Copied gear and fitted sticks stay.">Back all</button>
      <button type="button" class="btn" disabled=${!s.can_undo} onClick=${() => call('jerseys_undo')}
        data-tip="Drop your changes and put back the gear the roster had.">Take back my gear</button>
      <button type="button" class="btn primary" disabled=${!s.can_apply} onClick=${() => call('jerseys_apply')}
        data-tip="Apply writes the gear and team colours as one change in My edits (one Undo takes it back). Press Patch afterwards and NHL 19 shows it.">Apply</button>
    </div>
  </section>`;
}
