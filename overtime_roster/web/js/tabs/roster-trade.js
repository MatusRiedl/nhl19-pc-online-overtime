// Roster's Move / trade window, its Bring in game moves window and the next-step note (app/trade_ctl.py,
// docs/notes/trades.md). Slice trade; calls trade_*. Python decides everything: numbers, places in the lines, what the
// roster refuses and what to press next; the page draws it.
import { html, cls, Fragment } from '../lib.js';
import { useSlice } from '../store.js';
import { call } from '../bridge.js';
import { Button, Modal, TextField, Select, Checkbox, Empty } from '../ui.js';

const PICK = '';

// where one player goes: the league, then the club (the free agents are a league of one)
function Where({ r, leagues, off }) {
  const league = leagues.find((l) => l.value === r.league);
  const leagueOptions = [...(r.league == null ? [{ value: PICK, label: 'Pick a league' }] : []),
    ...leagues.map((l) => ({ value: l.value, label: l.label }))];
  const teamOptions = league ? [...(r.to == null ? [{ value: PICK, label: 'Pick a club' }] : []),
    ...league.teams.map((t) => ({ value: t.value, label: t.label }))] : [];
  const pickLeague = (v) => {
    const l = leagues.find((x) => x.value === v);
    call('trade_to', r.gid, l && l.teams.length === 1 ? l.teams[0].value : (l ? `league:${l.value}` : PICK));
  };
  return html`<span class="ro-tr-where">
    <${Select} className="ro-tr-league" value=${r.league ?? PICK} options=${leagueOptions} disabled=${off} onChange=${pickLeague}/>
    ${league && league.teams.length > 1 && html`<${Select} className="ro-tr-team" value=${r.to ?? PICK} options=${teamOptions}
      disabled=${off} onChange=${(v) => call('trade_to', r.gid, v)}/>`}
  </span>`;
}

function TradeRow({ r, leagues, off }) {
  return html`<div class=${cls('ro-tr-row', r.to == null && 'open')}>
    <div class="ro-tr-who"><b>${r.name}</b><span class="faint">${[r.pos, r.ovr && `${r.ovr} OVR`].filter(Boolean).join(' · ')}</span></div>
    <div class="ro-tr-move">
      <span class="ro-tr-from" title="Where he plays now">${r.from}</span>
      <span class="ro-tr-arrow" aria-hidden="true">→</span>
      <${Where} r=${r} leagues=${leagues} off=${off}/>
      <button type="button" class="ro-tr-drop" title="Take him out of the trade" disabled=${off}
        onClick=${() => call('trade_drop', r.gid)}>×</button>
    </div>
    ${r.line && html`<div class="small-note ro-tr-line">${r.line}</div>`}
  </div>`;
}

export function TradeWindow() {
  const t = useSlice('trade');
  const w = t && t.window;
  if (!w) return null;
  const off = t.busy;
  const close = () => call('trade_close');
  return html`<${Modal} wide className="ro-trade" title="Move / trade" onClose=${close} buttons=${html`
      <span class="ro-mnote">${w.problems.length ? '' : 'One Undo takes the whole trade back.'}</span>
      <${Button} kind="pick" className="ro-tr-apply" disabled=${!w.can_apply || off} onClick=${() => call('trade_apply')}>${w.button}<//>
      <${Button} onClick=${close}>Cancel<//>`}>
    <p class="small-note">Pick where each player goes: another club, any league, or the free agents. Add players for a
      trade. Numbers, places in the lines and contracts follow the game's own rules; nothing changes until you
      press <b>${w.button}</b>.</p>
    <div class="ro-tr-rows">
      ${w.rows.length ? w.rows.map((r) => html`<${TradeRow} key=${r.gid} r=${r} leagues=${w.leagues} off=${off}/>`)
        : html`<${Empty}>Find a player below to start.<//>`}
    </div>
    <div class="ro-tr-add">
      <${TextField} className="ro-tr-search" value=${w.query} placeholder="Add a player to the trade (name)" delay=${220}
        disabled=${off} onChange=${(v) => call('trade_find', v)}/>
      ${w.found.length > 0 && html`<div class="ro-tr-found">${w.found.map((f) => html`<button type="button" key=${f.id}
          class="ro-tr-hit" disabled=${off} onClick=${() => call('trade_add', f.id)}>
          <b>${f.name}</b><span class="faint">${f.pos} · ${f.ovr} · ${f.team}</span></button>`)}</div>`}
      ${w.query && !w.found.length && html`<span class="small-note">Nobody by that name.</span>`}
    </div>
    ${w.problems.length > 0 && html`<div class="note caution ro-tr-problems">${w.problems.map((p) => html`<div key=${p}>${p}</div>`)}</div>`}
  <//>`;
}

export function ImportWindow() {
  const t = useSlice('trade');
  const m = t && t.importing;
  if (!m) return null;
  const off = t.busy;
  const close = () => call('trade_import_close');
  const ticked = m.moves.filter((x) => x.on).length;
  return html`<${Modal} wide className="ro-import" title="Bring in game moves" onClose=${close} buttons=${html`
      <span class="ro-mnote">${m.can_apply ? `${ticked} move${ticked === 1 ? '' : 's'} come over as one change (one Undo).` : ''}</span>
      <${Button} kind="pick" className="ro-im-apply" disabled=${!m.can_apply || off} onClick=${() => call('trade_import_apply')}>Bring them in<//>
      <${Button} onClick=${close}>Close<//>`}>
    <p class="small-note">Moved players in NHL 19 (Edit Rosters, trades, signings) and saved the roster there? Pick that
      save: the app reads it, never writes it, and lists who plays somewhere else in it. Only clubs come over; your
      edits here stay.</p>
    <label class="ro-im-pick"><span class="caps">Save from the game</span>
      <${Select} value=${m.folder} options=${m.saves} disabled=${off} onChange=${(v) => call('trade_import_pick', v)}/></label>
    ${m.error && html`<div class="note bad">${m.error}</div>`}
    ${m.different && html`<div class="note caution">This save is a different roster, not the open one changed in the game.
      Open it in Setup instead.</div>`}
    ${!m.error && !m.different && (m.moves.length ? html`<div class="ro-im-rows">${m.moves.map((x) => html`
      <div key=${x.gid} class=${cls('ro-im-row', x.mine && 'mine')}>
        <${Checkbox} on=${x.on} disabled=${off} onChange=${(on) => call('trade_import_tick', x.gid, on)}>
          <b>${x.name}</b><span class="faint">${x.pos}</span><span>${x.from} → ${x.to}</span><//>
        ${x.mine && html`<div class="small-note">${x.mine}</div>`}
      </div>`)}</div>` : m.saves.length && html`<${Empty}>No moves: every player plays for the same club in both.<//>`)}
    ${m.skipped.map((x) => html`<div key=${x.why} class="small-note">${`Not brought in: ${x.names.join(', ')}${x.more ? ` and ${x.more} more` : ''}. ${x.why}`}</div>`)}
    ${m.unknown > 0 && html`<div class="small-note">${`${m.unknown} player${m.unknown === 1 ? '' : 's'} made in the game ${m.unknown === 1 ? 'is' : 'are'} not in this roster: they stay out.`}</div>`}
    ${m.problems.length > 0 && html`<div class="note caution">${m.problems.map((p) => html`<div key=${p}>${p}</div>`)}</div>`}
  <//>`;
}

// after a trade or game moves: what to press next, until it is played or closed
export function NextNote({ note }) {
  if (!note) return null;
  return html`<div class=${cls('ro-next', note.unsaved && 'unsaved')} role="note">
    <div class="ro-next-head"><b>${note.title}</b>
      <button type="button" class="ro-next-x" title="Close this note" onClick=${() => call('trade_note_close')}>×</button></div>
    <ol>${note.steps.map((s) => html`<li key=${s}>${s}</li>`)}</ol>
    ${note.caution && html`<div class="note caution">${note.caution}</div>`}
  </div>`;
}

export function TradeModals() {
  return html`<${Fragment}><${TradeWindow}/><${ImportWindow}/><//>`;
}
