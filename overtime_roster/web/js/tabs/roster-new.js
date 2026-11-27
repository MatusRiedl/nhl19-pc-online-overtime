// Roster's New player window (app/newplayer_ctl.py, docs/notes/new-player.md). Slice newplayer; calls newplayer_*.
// Python checks every value and makes him (one change, one Undo); then his card opens for the rest. What was typed
// goes along with Make him too (a field's last text reaches Python on blur, which may not be in before the click).
import { html, cls, useRef } from '../lib.js';
import { useSlice } from '../store.js';
import { call } from '../bridge.js';
import { Button, Modal, TextField, Select, Segmented } from '../ui.js';

const PICK = '';

function Row({ label, k, problems, children }) {
  const problem = problems.find((p) => p.key === k);
  return html`<label class=${cls('ro-np-row', problem && 'bad')}>
    <span class="caps">${label}</span>
    <span class="ro-np-ctl">${children}</span>
    ${problem && html`<span class="ro-problem">${problem.text}</span>`}
  </label>`;
}

export function NewPlayerWindow() {
  const n = useSlice('newplayer');
  const typed = useRef({ key: null, values: {} });
  const w = n && n.window;
  if (!w) return null;
  if (typed.current.key !== w.key) typed.current = { key: w.key, values: {} };
  const off = n.busy;
  const v = w.values;
  const set = (k) => (x) => { typed.current.values[k] = x; call('newplayer_set', k, x); };
  const close = () => call('newplayer_close');
  const ready = w.can_make || (v.team !== PICK
    && ['last', 'born'].every((k) => String(typed.current.values[k] ?? v[k]).trim() !== ''));
  const make = () => { if (!off) call('newplayer_make', typed.current.values); };
  const league = w.leagues.find((l) => l.value === v.league);
  const leagueOptions = [...(v.league === PICK ? [{ value: PICK, label: 'Pick a league' }] : []),
    ...w.leagues.map((l) => ({ value: l.value, label: l.label }))];
  const teamOptions = league ? [...(v.team === PICK ? [{ value: PICK, label: 'Pick a club' }] : []),
    ...league.teams.map((t) => ({ value: t.value, label: t.label }))] : [];
  const general = w.problems.filter((p) => !p.key);
  return html`<${Modal} className="ro-newplayer" title="New player" onClose=${close} buttons=${html`
      <span class="ro-mnote">${w.problems.length ? '' : 'One Undo takes him back.'}</span>
      <${Button} kind="pick" className="ro-np-make" disabled=${!ready || off} onClick=${make}>Make him<//>
      <${Button} onClick=${close}>Cancel<//>`}>
    <p class="small-note">A new player for any club, or the free agents. He starts with a stand-in face and a fringe
      player's ratings: set his number, ratings, face and equipment on his card next. Save keeps him in My edits, so
      every roster update leaves him where you put him.</p>
    <div class="ro-np-grid">
      <${Row} label="First name" k="first" problems=${w.problems}>
        <${TextField} value=${v.first} disabled=${off} delay=${150} onChange=${set('first')}/><//>
      <${Row} label="Last name" k="last" problems=${w.problems}>
        <${TextField} value=${v.last} disabled=${off} delay=${150} onChange=${set('last')}/><//>
      <${Row} label="Position" k="pos" problems=${w.problems}>
        <${Select} value=${v.pos} disabled=${off} options=${w.positions.map((p) => ({ value: p, label: p }))}
          onChange=${set('pos')}/><//>
      <${Row} label="Shoots" k="shoots" problems=${w.problems}>
        <${Segmented} className="ro-seg" value=${v.shoots} disabled=${off}
          options=${w.hands.map((h) => ({ value: h, label: h }))} onChange=${set('shoots')}/><//>
      <${Row} label="Born" k="born" problems=${w.problems}>
        <${TextField} value=${v.born} placeholder="YYYY-MM-DD" disabled=${off} delay=${150}
          onChange=${set('born')}/><//>
      <${Row} label="Club" k="team" problems=${w.problems}>
        <span class="ro-np-where">
          <${Select} className="ro-np-league" value=${v.league} options=${leagueOptions} disabled=${off}
            onChange=${set('league')}/>
          ${league && league.teams.length > 1 && html`<${Select} className="ro-np-team" value=${v.team}
            options=${teamOptions} disabled=${off} onChange=${set('team')}/>`}
        </span><//>
    </div>
    ${general.length > 0 && html`<div class="note caution">
      ${general.map((p) => html`<div key=${p.text}>${p.text}</div>`)}</div>`}
  <//>`;
}
