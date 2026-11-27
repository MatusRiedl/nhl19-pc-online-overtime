// Roster's League maker window (app/leaguemaker_ctl.py, docs/notes/league-maker.md). Slice leaguemaker; calls
// leaguemaker_*. A league of your own clubs (a KHL) takes one of NHL 19's club league slots: Python checks the clubs
// and makes them as one change (one Undo); Save keeps the league in My edits and Patch shows its name in the game.
// What was typed goes along with Make league too (a box's last text reaches Python on blur, maybe not before the click).
import { html, cls, useState, useEffect, useRef } from '../lib.js';
import { useSlice } from '../store.js';
import { call } from '../bridge.js';
import { Button, Modal, TextField, Select } from '../ui.js';

// the clubs box: one club a line; Python's text is shown unless the user is typing
function ClubsBox({ value, disabled, onChange, delay = 300 }) {
  const [text, setText] = useState(value || '');
  const typing = useRef(false);
  const timer = useRef(null);
  useEffect(() => { if (!typing.current) setText(value || ''); }, [value]);
  useEffect(() => () => clearTimeout(timer.current), []);
  return html`<textarea class="field ro-lg-clubs" value=${text} disabled=${disabled} spellcheck="false" rows="12"
    placeholder=${'CSKA Moscow | Moscow | CSKA | CSKA\nSKA Saint Petersburg | Saint Petersburg | SKA | SKA'}
    onFocus=${() => { typing.current = true; }}
    onBlur=${() => { typing.current = false; clearTimeout(timer.current); if (text !== (value || '')) onChange(text); }}
    onInput=${(e) => { const t = e.target.value; setText(t); clearTimeout(timer.current);
      timer.current = setTimeout(() => onChange(t), delay); }}/>`;
}

// Import... / Export...: Windows' picker; in a browser Python answers {type: true} and the path is typed
async function importFile() {
  const reply = await call('leaguemaker_import');
  if (!reply || !reply.type) return;
  const typed = window.prompt('The full path of the league file (.json):', '');
  if (typed && typed.trim()) call('leaguemaker_import_path', typed.trim());
}
async function exportFile() {
  const reply = await call('leaguemaker_export');
  if (!reply || !reply.type) return;
  const typed = window.prompt('The full path of a folder for the league file:', '');
  if (typed && typed.trim()) call('leaguemaker_export', typed.trim());
}

export function LeagueWindow() {
  const m = useSlice('leaguemaker');
  const typed = useRef({ key: null, values: {} });
  const w = m && m.window;
  if (!w) return null;
  if (typed.current.key !== w.key) typed.current = { key: w.key, values: {} };
  const off = m.busy;
  const v = w.values;
  const set = (k) => (x) => { typed.current.values[k] = x; call('leaguemaker_set', k, x); };
  const close = () => call('leaguemaker_close');
  const name = String(typed.current.values.name ?? v.name).trim();
  const clubs = String(typed.current.values.clubs ?? v.clubs).split('\n').filter((l) => l.trim()).length;
  const ready = w.can_make || (name !== '' && clubs > 0);
  const make = () => { if (!off) call('leaguemaker_make', typed.current.values); };
  const slots = w.slots.map((x) => ({ value: x.key, label: x.name ? `${x.label}: ${x.name}` : x.label }));
  const over = clubs > w.places;
  return html`<${Modal} className="ro-league" title="New league" onClose=${close} buttons=${html`
      <${Button} disabled=${off} onClick=${importFile}
        title="Read a league file a modder shared (it fills this window; nothing changes until Make league)">Import...<//>
      <${Button} disabled=${off} onClick=${exportFile}
        title="Write this slot's league as the roster has it now, to share">Export...<//>
      <${Button} disabled=${off} onClick=${() => call('leaguemaker_reset')}
        title="The slot's clubs as the game has them (the players stay)">Game's own clubs<//>
      <span class="ro-mnote">${w.problems.length ? '' : 'One Undo takes it back.'}</span>
      <${Button} kind="pick" disabled=${!ready || off} onClick=${make}>Make league<//>
      <${Button} onClick=${close}>Cancel<//>`}>
    <p class="small-note">Your own league (a KHL, say) in one of NHL 19's club leagues: its clubs take the slot's places
      one by one and keep their players and calendar. Save keeps the league in My edits, so every roster update keeps
      it, and Patch in Setup shows its name in the game. Crests, the league logo and the boards stay the slot's.</p>
    <p class="small-note ro-lg-warn">Seasons: have a roster made from Overtime default or your updated roster active in
      NHL 19. With a save of the Game roster (2018-19) active, NHL 19 crashes when a Season's team screen opens.</p>
    ${w.game_roster && html`<div class="note caution">This is the Game roster (2018-19): make the league on Overtime
      default or your updated roster instead, so its Seasons play.</div>`}
    <div class="ro-lg-grid">
      <label class="ro-lg-row"><span class="caps">Slot</span>
        <${Select} value=${v.slot} options=${slots} disabled=${off} onChange=${set('slot')}/></label>
      <label class="ro-lg-row"><span class="caps">League name</span>
        <${TextField} value=${v.name} placeholder=${w.slots.find((x) => x.key === v.slot)?.game_name || ''}
          disabled=${off} delay=${150} onChange=${set('name')}/></label>
    </div>
    <label class="ro-lg-row">
      <span class="ro-lg-head"><span class="caps">Clubs</span>
        <span class=${cls('ro-lg-count', over && 'bad')}>${clubs} of ${w.places} places</span>
        ${w.kept && html`<span class="ro-lg-kept" title="Save keeps what you make here instead">My edits keeps a league here</span>`}
      </span>
      <${ClubsBox} value=${v.clubs} disabled=${off} onChange=${set('clubs')}/>
      <span class="small-note">One club a line: name | city | nickname | ABBR (or name | ABBR). A place with no line
        keeps its club.</span>
    </label>
    ${w.problems.length > 0 && html`<div class="note caution">
      ${w.problems.map((p) => html`<div key=${p}>${p}</div>`)}</div>`}
    ${w.notes.length > 0 && html`<div class="small-note ro-lg-notes">
      ${w.notes.map((p) => html`<div key=${p}>${p}</div>`)}</div>`}
  <//>`;
}
