import * as store from './storage.js';
import { createFinder, methodLabel, NO_DATA, PARTIAL_DATA, VC_ONLY, GAME_VERSIONS } from './find.js';

// ---------- reference data ----------
const GAMES = [
  { id: 'red', name: 'Red / Green', gen: 1 }, { id: 'blue', name: 'Blue', gen: 1 }, { id: 'yellow', name: 'Yellow', gen: 1 },
  { id: 'gold', name: 'Gold', gen: 2 }, { id: 'silver', name: 'Silver', gen: 2 }, { id: 'crystal', name: 'Crystal', gen: 2 },
  { id: 'ruby', name: 'Ruby', gen: 3 }, { id: 'sapphire', name: 'Sapphire', gen: 3 }, { id: 'emerald', name: 'Emerald', gen: 3 },
  { id: 'firered', name: 'FireRed', gen: 3 }, { id: 'leafgreen', name: 'LeafGreen', gen: 3 },
  { id: 'colosseum', name: 'Colosseum', gen: 3 }, { id: 'xd', name: 'XD: Gale of Darkness', gen: 3 },
  { id: 'diamond', name: 'Diamond', gen: 4 }, { id: 'pearl', name: 'Pearl', gen: 4 }, { id: 'platinum', name: 'Platinum', gen: 4 },
  { id: 'heartgold', name: 'HeartGold', gen: 4 }, { id: 'soulsilver', name: 'SoulSilver', gen: 4 },
  { id: 'black', name: 'Black', gen: 5 }, { id: 'white', name: 'White', gen: 5 },
  { id: 'black2', name: 'Black 2', gen: 5, charm: true }, { id: 'white2', name: 'White 2', gen: 5, charm: true },
  { id: 'x', name: 'X', gen: 6, charm: true }, { id: 'y', name: 'Y', gen: 6, charm: true },
  { id: 'omegaruby', name: 'Omega Ruby', gen: 6, charm: true }, { id: 'alphasapphire', name: 'Alpha Sapphire', gen: 6, charm: true },
  { id: 'sun', name: 'Sun', gen: 7, charm: true }, { id: 'moon', name: 'Moon', gen: 7, charm: true },
  { id: 'ultrasun', name: 'Ultra Sun', gen: 7, charm: true }, { id: 'ultramoon', name: 'Ultra Moon', gen: 7, charm: true },
  { id: 'lgpikachu', name: "Let's Go Pikachu", gen: 7, charm: true }, { id: 'lgeevee', name: "Let's Go Eevee", gen: 7, charm: true },
  { id: 'sword', name: 'Sword', gen: 8, charm: true, dlc: [['ioa', 'Isle of Armor'], ['ct', 'Crown Tundra']] },
  { id: 'shield', name: 'Shield', gen: 8, charm: true, dlc: [['ioa', 'Isle of Armor'], ['ct', 'Crown Tundra']] },
  { id: 'brilliantdiamond', name: 'Brilliant Diamond', gen: 8, charm: true }, { id: 'shiningpearl', name: 'Shining Pearl', gen: 8, charm: true },
  { id: 'legendsarceus', name: 'Legends: Arceus', gen: 8, charm: true },
  { id: 'scarlet', name: 'Scarlet', gen: 9, charm: true, dlc: [['tm', 'The Teal Mask'], ['id', 'The Indigo Disk']] },
  { id: 'violet', name: 'Violet', gen: 9, charm: true, dlc: [['tm', 'The Teal Mask'], ['id', 'The Indigo Disk']] },
  { id: 'legendsza', name: 'Legends: Z-A', gen: 9, charm: true, dlc: [['md', 'Mega Dimension']] },
  { id: 'go', name: 'Pokémon GO', gen: 0 },
];
const GAME = Object.fromEntries(GAMES.map(g => [g.id, g]));
const DEFAULT_SETTINGS = {
  owned: Object.fromEntries(['firered', 'diamond', 'heartgold', 'white', 'x', 'omegaruby', 'sun', 'ultramoon', 'lgpikachu',
    'shield', 'shiningpearl', 'legendsarceus', 'violet', 'legendsza', 'go'].map(k => [k, true])),
  dlc: { 'shield:ioa': true, 'shield:ct': true, 'violet:tm': true, 'violet:id': true, 'legendsza:md': true },
  charm: {},
  gmax: true,
  buffer: 20,
};
const TYPE_COLORS = { normal: '#9a9a7b', fire: '#e8692d', water: '#4b8de0', electric: '#e5b622', grass: '#5fa840', ice: '#62c3c3',
  fighting: '#b8352c', poison: '#9443a0', ground: '#c9a24a', flying: '#8f87e6', psychic: '#e9527d', bug: '#97a524',
  rock: '#ad9635', ghost: '#6a5394', dragon: '#6436e8', dark: '#6b5547', steel: '#9a9ab8', fairy: '#d97fb0', stellar: '#40b5a5' };
const STAT_NAMES = ['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed'];
const PER_BOX = 30;

let DATA, SLOTS, OFFICIAL, BYKEY;
let view = 'living';
let sortKey = 'home', sortAsc = true;
let filters = {};
let layoutCache = {};
let boxIndex = 0;
let FINDER = null, ENC = null, MOVES = null, EVO = null, showAllGames = false;
let routeGame = '', routeArea = '';
let EVENTS = [];
const dataGames = () => GAMES.filter(g => !NO_DATA.has(g.id));

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const S = () => store.get().settings;
const P = () => store.get().progress;
const pad = (n) => String(n).padStart(4, '0');
const cap = (s) => String(s || '').replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

function toast(msg) { const t = $('toast'); t.textContent = msg; t.classList.remove('hidden'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.add('hidden'), 2200); }

function ensureSettings() {
  const st = store.get();
  st.settings = Object.assign(structuredClone(DEFAULT_SETTINGS), st.settings || {});
}

// ---------- slot helpers ----------
function displayName(s) {
  const g = s.g === 'm' ? ' ♂' : s.g === 'f' ? ' ♀' : '';
  return (s.species || s.name) + (s.formType === 'gmax' ? '' : g);
}
function formLabel(s) {
  if (s.formType === 'gmax') return 'Gigantamax';
  if (s.formName && !/♂|♀|^Male$|^Female$/.test(s.formName)) return s.formName;
  return '';
}
const spriteUrl = (s, shiny) => { const f = shiny ? (s.sspr || s.spr) : s.spr; return f ? DATA.spriteBase + f : ''; };
const prog = (dex, s) => P()[(dex === 'shiny' ? 'S:' : 'L:') + s.key] || {};
function setProg(dex, s, patch) {
  const k = (dex === 'shiny' ? 'S:' : 'L:') + s.key;
  const cur = Object.assign({}, P()[k] || {}, patch);
  if (!cur.c) { delete P()[k]; } else { P()[k] = cur; }
  store.save();
}
const activeSlots = (dex) => SLOTS.filter(s => (S().gmax || !s.gmax) && !(dex === 'shiny' && s.shinyLock));

// ---------- Home layout ----------
function layout(dex) {
  const key = dex + (S().gmax ? 'g' : '') + S().buffer;
  if (layoutCache[key]) return layoutCache[key];
  const pos = {};
  let start = 0;
  if (dex === 'shiny') start = (layout('living').boxes + Number(S().buffer || 0)) * PER_BOX;
  let i = start;
  const list = activeSlots(dex);
  const gens = [...new Set(list.map(s => s.gen))].sort((a, b) => a - b);
  gens.forEach((g, gi) => {
    for (const s of list) if (s.gen === g) {
      pos[s.key] = { box: Math.floor(i / PER_BOX) + 1, row: Math.floor((i % PER_BOX) / 6) + 1, col: (i % 6) + 1, idx: i };
      i++;
    }
    if (gi < gens.length - 1) i = Math.ceil(i / PER_BOX) * PER_BOX + PER_BOX; // finish the box, then one empty box
  });
  const res = { pos, firstBox: Math.floor(start / PER_BOX) + 1, boxes: Math.ceil(i / PER_BOX) - Math.floor(start / PER_BOX), lastBox: Math.ceil(i / PER_BOX) };
  layoutCache[key] = res;
  return res;
}
const posLabel = (p) => p ? `Box ${p.box} · R${p.row} C${p.col}` : '';

// ---------- filters & sorting ----------
const uniq = (arr) => [...new Set(arr.filter(Boolean))].sort();
function filterDefs() {
  const all = SLOTS;
  const isTracked = view !== 'official';
  const locs = [['home', 'Home'], ['bank', 'Pokémon Bank'], ...GAMES.filter(g => S().owned[g.id]).map(g => [g.id, g.name])];
  return [
    { id: 'gen', label: 'Generation', opts: [1, 2, 3, 4, 5, 6, 7, 8, 9].map(g => [g, 'Gen ' + g]) },
    { id: 'type', label: 'Type', opts: uniq(all.flatMap(s => s.types)).map(t => [t, cap(t)]) },
    isTracked && { id: 'status', label: 'Status', opts: [['caught', 'Caught'], ['missing', 'Missing'], ['transfer', 'Needs transfer']] },
    isTracked && { id: 'loc', label: 'Current location', opts: locs },
    FINDER && { id: 'game', label: 'Get it in (This Game mode)', opts: dataGames().filter(g => S().owned[g.id]).map(g => [g.id, g.name]) },
    MOVES && { id: 'move', label: 'Learns move', opts: Object.entries(MOVES.names).sort((a, b) => a[1].localeCompare(b[1])).map(([id, n]) => [id, n]) },
    { id: 'egg', label: 'Egg group', opts: uniq(all.flatMap(s => s.eggs)).map(e => [e, cap(e)]) },
    { id: 'cat', label: 'Category', opts: [['legendary', 'Legendary'], ['mythical', 'Mythical'], ['ultra-beast', 'Ultra Beast'], ['paradox', 'Paradox'], ['baby', 'Baby'], ['none', 'None of these']] },
    { id: 'formType', label: 'Form type', opts: [['base', 'Base'], ['regional', 'Regional'], ['form', 'Other form'], ['event', 'Event form'], ['gmax', 'Gigantamax']] },
    { id: 'gender', label: 'Gender', opts: [['diff', 'Has gender difference'], ['m', 'Male slot'], ['f', 'Female slot']] },
    { id: 'tag', label: 'Tags', opts: [['mega', 'Has Mega'], ['gmaxable', 'Can Gigantamax'], ['lock', 'Shiny-locked'], ['nolock', 'Not shiny-locked'], ['review', 'Needs Home check']] },
    { id: 'stage', label: 'Evolution stage', opts: [[1, 'Stage 1'], [2, 'Stage 2'], [3, 'Stage 3']] },
    { id: 'evo', label: 'Evolves by', opts: EVO ? [['base', "Doesn't evolve from anything"], ...uniq(Object.values(EVO.evo).flat().flatMap(r => r.tags)).map(t => [t, t])] : uniq(all.map(s => s.evoMethod)).map(e => [e, cap(e)]) },
    { id: 'color', label: 'Color', opts: uniq(all.map(s => s.color)).map(c => [c, cap(c)]) },
    { id: 'shape', label: 'Body shape', opts: uniq(all.map(s => s.shape)).map(c => [c, cap(c)]) },
    { id: 'growth', label: 'Growth rate', opts: uniq(all.map(s => s.growth)).map(c => [c, cap(c)]) },
    { id: 'genderRate', label: 'Gender ratio', opts: [['-1', 'Genderless'], ['0', 'Male only'], ['8', 'Female only'], ['mixed', 'Both']] },
  ].filter(Boolean);
}
const SORTS = [
  ['home', 'Home box order'], ['national', 'National Dex'], ['family', 'Family number'], ['name', 'Name'],
  ['bst', 'Base stat total'], ['s0', 'HP'], ['s1', 'Attack'], ['s2', 'Defense'], ['s3', 'Sp. Atk'], ['s4', 'Sp. Def'], ['s5', 'Speed'],
  ['height', 'Height'], ['weight', 'Weight'], ['capture', 'Catch rate'], ['eggCycles', 'Egg cycles'], ['friendship', 'Base friendship'],
];
const gmaxable = new Set();

function matches(s, dex) {
  const f = filters;
  const q = ($('search').value || '').trim().toLowerCase();
  if (q) {
    const hay = [s.name, s.species, s.formName, s.ident, ...s.types, ...(s.abilities || []), s.hidden, String(s.sid)].join(' ').toLowerCase();
    if (!q.split(/\s+/).every(w => hay.includes(w))) return false;
  }
  if (f.gen && s.gen !== Number(f.gen)) return false;
  if (f.type && !s.types.includes(f.type)) return false;
  if (f.egg && !s.eggs.includes(f.egg)) return false;
  if (f.cat) { if (f.cat === 'none' ? s.cat.length : !s.cat.includes(f.cat)) return false; }
  if (f.formType && s.formType !== f.formType) return false;
  if (f.gender === 'diff' && !s.g) return false;
  if ((f.gender === 'm' || f.gender === 'f') && s.g !== f.gender) return false;
  if (f.tag === 'mega' && !s.hasMega) return false;
  if (f.tag === 'gmaxable' && !gmaxable.has(s.sid)) return false;
  if (f.tag === 'lock' && !s.shinyLock) return false;
  if (f.tag === 'nolock' && s.shinyLock) return false;
  if (f.tag === 'review' && !s.review) return false;
  if (f.stage && s.stage !== Number(f.stage)) return false;
  if (f.evo) {
    if (!EVO) { if (s.evoMethod !== f.evo) return false; }
    else if (f.evo === 'base') { if (s.from) return false; }
    else if (!evoRowsFor(s).some(r => r.tags.includes(f.evo))) return false;
  }
  if (f.color && s.color !== f.color) return false;
  if (f.shape && s.shape !== f.shape) return false;
  if (f.growth && s.growth !== f.growth) return false;
  if (f.game && FINDER && !FINDER.obtainableIn(f.game).has(s.key)) return false;
  if (f.move && MOVES && !learnset(s).m.some(m => m[0] === Number(f.move))) return false;
  if (f.genderRate) {
    if (f.genderRate === 'mixed' ? !(s.genderRate > 0 && s.genderRate < 8) : s.genderRate !== Number(f.genderRate)) return false;
  }
  if (dex !== 'official' && s.slot !== false) {
    const p = prog(dex, s);
    if (f.status === 'caught' && !p.c) return false;
    if (f.status === 'missing' && p.c) return false;
    if (f.status === 'transfer' && !(p.c && p.loc && p.loc !== 'home')) return false;
    if (f.loc && !(p.c && (p.loc || 'home') === f.loc)) return false;
  }
  return true;
}

function sortList(list, dex) {
  const lay = dex === 'official' ? layout('living') : layout(dex);
  const idx = new Map(SLOTS.map((s, i) => [s.key, i]));
  const ord = (s) => idx.has(s.key) ? idx.get(s.key) : s.sid * 100 + 99;
  let fn;
  switch (sortKey) {
    case 'home': fn = (a, b) => ((lay.pos[a.key]?.idx ?? 1e9) - (lay.pos[b.key]?.idx ?? 1e9)) || (a.sid - b.sid) || (ord(a) - ord(b)); break;
    case 'national': fn = (a, b) => (a.sid - b.sid) || (ord(a) - ord(b)); break;
    case 'family': fn = (a, b) => (a.fam - b.fam) || (a.root - b.root) || (a.stage - b.stage) || (a.sid - b.sid) || (ord(a) - ord(b)); break;
    case 'name': fn = (a, b) => displayName(a).localeCompare(displayName(b)) || (ord(a) - ord(b)); break;
    default: {
      const v = sortKey.startsWith('s') && sortKey.length === 2 ? (s) => s.stats[Number(sortKey[1])] : (s) => s[sortKey];
      fn = (a, b) => (v(a) - v(b)) || (a.sid - b.sid) || (ord(a) - ord(b));
    }
  }
  list.sort(fn);
  if (!sortAsc) list.reverse();
  return list;
}

// ---------- rendering: list ----------
function locOptions(selected) {
  const opts = [['home', 'Home'], ['bank', 'Pokémon Bank'], ...GAMES.filter(g => S().owned[g.id] || g.id === selected).map(g => [g.id, g.name])];
  return opts.map(([v, l]) => `<option value="${v}"${v === (selected || 'home') ? ' selected' : ''}>${esc(l)}</option>`).join('');
}
function typePills(s) { return `<div class="types">${s.types.map(t => `<span class="type" style="background:${TYPE_COLORS[t] || '#888'}">${t}</span>`).join('')}</div>`; }

function renderList() {
  const dex = view;
  const base = dex === 'official' ? [...activeSlots('living'), ...OFFICIAL] : activeSlots(dex).slice();
  const list = dex === 'shiny' ? [...base, ...SLOTS.filter(s => s.shinyLock && (S().gmax || !s.gmax))] : base;
  const shown = sortList(list.filter(s => matches(s, dex)), dex);
  const lay = dex === 'official' ? null : layout(dex);
  $('resultCount').textContent = `${shown.length} of ${list.length}`;
  $('grid').innerHTML = shown.map(s => {
    const locked = dex === 'shiny' && s.shinyLock;
    const tracked = dex !== 'official' && s.slot !== false && !locked;
    const p = tracked ? prog(dex, s) : {};
    const needs = p.c && p.loc && p.loc !== 'home';
    let foot = '';
    if (tracked) {
      foot = `<div class="row"><button class="check${p.c ? ' on' : ''}" data-act="check" aria-label="Caught">✓</button>
        <select data-act="loc"${p.c ? '' : ' disabled'}>${locOptions(p.loc)}</select></div>`;
    } else if (locked) {
      foot = `<div class="pos">Shiny-locked</div>`;
    } else if (dex === 'official') {
      const l = s.slot !== false && prog('living', s).c, sh = s.slot !== false && prog('shiny', s).c;
      foot = s.slot === false ? `<div class="pos">No Home slot</div>` : `<div class="pos">${l ? '● Living' : '○ Living'} · ${sh ? '★ Shiny' : '☆ Shiny'}</div>`;
    }
    return `<div class="card${p.c ? ' caught' : ''}${locked ? ' locked' : ''}" data-key="${esc(s.key || s.ident)}">
      <span class="num">#${pad(s.sid)}</span>${needs ? '<span class="flag" title="Needs transfer to Home">⇪</span>' : ''}
      <img loading="lazy" src="${spriteUrl(s, dex === 'shiny')}" alt="">
      <div class="nm">${esc(displayName(s))}</div><div class="fm">${esc(formLabel(s))}</div>
      ${typePills(s)}
      ${lay && lay.pos[s.key] ? `<div class="pos">${posLabel(lay.pos[s.key])}</div>` : ''}
      ${foot}</div>`;
  }).join('');
}

function findAny(key) { return BYKEY.get(key); }

function onGridClick(e) {
  const card = e.target.closest('.card'); if (!card) return;
  const s = findAny(card.dataset.key); if (!s) return;
  const act = e.target.dataset.act;
  if (act === 'check') {
    const p = prog(view, s);
    setProg(view, s, { c: !p.c, loc: p.loc || 'home' });
    renderList();
    return;
  }
  if (act === 'loc') return;
  openDetail(s);
}
function onGridChange(e) {
  if (e.target.dataset.act !== 'loc') return;
  const s = findAny(e.target.closest('.card').dataset.key);
  setProg(view, s, { loc: e.target.value });
  renderList();
}

// ---------- detail panel ----------
function genderText(r) { if (r < 0) return 'Genderless'; if (r === 0) return '100% male'; if (r === 8) return '100% female'; return `${100 - r * 12.5}% male · ${r * 12.5}% female`; }
function trackerBlock(dex, s) {
  if (s.slot === false) return '';
  if (dex === 'shiny' && s.shinyLock) return `<tr><td>Shiny dex</td><td>Shiny-locked in every game</td></tr>`;
  const p = prog(dex, s), pos = layout(dex).pos[s.key];
  return `<tr><td>${dex === 'shiny' ? 'Shiny dex' : 'Living dex'}</td><td>
    <label><input type="checkbox" data-dex="${dex}" data-act="dcheck"${p.c ? ' checked' : ''}> Caught</label>
    <select data-dex="${dex}" data-act="dloc"${p.c ? '' : ' disabled'}>${locOptions(p.loc)}</select>
    <div class="muted small">${posLabel(pos)}</div></td></tr>`;
}
function openDetail(s) {
  const d = $('detail');
  const famMembers = SLOTS.filter(x => x.fam === s.fam && !x.gmax && x.formType === 'base').filter((x, i, a) => a.findIndex(y => y.sid === x.sid) === i);
  const regional = Object.entries(s.regional || {}).map(([k, v]) => `${cap(k)} #${v}`).join(', ');
  d.innerHTML = `<button class="close ghost" data-act="close">✕</button>
    <div class="muted">#${pad(s.sid)} · Gen ${s.gen} · Family ${s.fam}</div>
    <h2>${esc(displayName(s))}</h2><div class="muted">${esc(formLabel(s))}</div>
    <div class="sprites"><img src="${spriteUrl(s, false)}" alt="Regular"><img src="${spriteUrl(s, true)}" alt="Shiny"></div>
    ${typePills(s)}
    ${s.review ? `<div class="note">Needs a Home check: ${esc(s.review)}</div>` : ''}
    ${s.slot === false ? `<div class="note">${esc(s.why)}</div>` : ''}
    <table>${trackerBlock('living', s)}${trackerBlock('shiny', s)}</table>
    <h3>Base stats · ${s.bst}</h3>
    <table>${s.stats.map((v, i) => `<tr><td>${STAT_NAMES[i]}</td><td><div style="display:flex;gap:8px;align-items:center"><span style="width:28px">${v}</span><div class="bar" style="flex:1"><div style="width:${Math.min(100, v / 2.55)}%"></div></div></div></td></tr>`).join('')}</table>
    <h3>Details</h3>
    <table>
      <tr><td>Abilities</td><td>${esc(s.abilities.join(', '))}${s.hidden ? `<br><span class="muted">Hidden: ${esc(s.hidden)}</span>` : ''}</td></tr>
      <tr><td>Egg groups</td><td>${esc(s.eggs.map(cap).join(', '))}</td></tr>
      <tr><td>Gender ratio</td><td>${genderText(s.genderRate)}</td></tr>
      <tr><td>Height / weight</td><td>${s.height} m · ${s.weight} kg</td></tr>
      <tr><td>Catch rate</td><td>${s.capture}</td></tr>
      <tr><td>Base friendship</td><td>${s.friendship}</td></tr>
      <tr><td>Egg cycles</td><td>${s.eggCycles}</td></tr>
      <tr><td>Growth rate</td><td>${cap(s.growth)}</td></tr>
      <tr><td>Evolution stage</td><td>Stage ${s.stage}</td></tr>
      <tr><td>Color / shape</td><td>${cap(s.color)} · ${cap(s.shape)}</td></tr>
      <tr><td>Tags</td><td>${[...s.cat.map(cap), s.hasMega && 'Has Mega', gmaxable.has(s.sid) && 'Can Gigantamax', s.shinyLock && 'Shiny-locked'].filter(Boolean).join(', ') || '—'}</td></tr>
      ${regional ? `<tr><td>Regional dex</td><td>${esc(regional)}</td></tr>` : ''}
    </table>
    <h3>Evolution</h3>
    <div id="evoBox">${evoHtml(s)}</div>
    <h3>Where to find</h3>
    <label class="small"><input type="checkbox" data-act="showall"${showAllGames ? ' checked' : ''}> Include games I don't own</label>
    <div id="findBox">${s.slot === false ? '<p class="muted small">This form has no Home slot.</p>' : findHtml(s)}</div>
    <h3>Moves</h3>
    <div id="moveBox">${movesHtml(s)}</div>`;
  d.dataset.key = s.key || s.ident;
  d.classList.remove('hidden');
}
const gameName = (id) => (GAME[id] || {}).name || id;

// ---------- evolution ----------
const baseSlotOf = (sid) => SLOTS.find(x => x.sid === sid && !x.gmax && x.formType === 'base') || SLOTS.find(x => x.sid === sid && !x.gmax);
// Rows that lead to this slot's form (a form-specific row wins; otherwise the generic rows).
function evoRowsFor(slot) {
  const rows = (EVO && EVO.evo[slot.sid]) || [];
  const own = rows.filter(r => r.toForm === slot.fid);
  if (own.length) return own;
  return rows.filter(r => !r.toForm || r.toForm === (baseSlotOf(slot.sid) || {}).fid);
}
function gameVg(game) {
  if (!EVO) return null;
  const first = (GAME_VERSIONS[game] || [])[0];
  return first ? EVO.verVg[first[0]] ?? null : null;
}
// How to evolve into `slot` in `game`: {ok, txt}.
function evoInGame(slot, game) {
  if (game === 'go') return { ok: true, txt: 'Evolve with Candy' };
  const G = gameVg(game);
  if (G == null) return { ok: true, txt: evoRowsFor(slot).filter(r => r.cur).map(r => r.txt)[0] || 'Evolve' };
  if (EVO.vgWithData.includes(G) && !(EVO.present[slot.sid] || []).includes(G)) return { ok: false };
  const regions = EVO.vgRegions[G] || [];
  // In a region with its own evolution (Alola, Galar, Hisui), only the regional one happens there.
  const regionalHere = ((EVO.evo[slot.sid]) || []).some(r => r.region && r.vg <= G && regions.includes(r.region));
  const ok = evoRowsFor(slot).filter(r => r.vg <= G && (!r.locRegion || regions.includes(r.locRegion)) && (!r.region || regions.includes(r.region)) && (!regionalHere || r.region));
  if (!ok.length) return { ok: false };
  const top = Math.max(...ok.map(r => r.vg));
  return { ok: true, txt: [...new Set(ok.filter(r => r.vg === top).map(r => r.txt))].join(' or ') };
}
// "Catch X, then evolve: …" for an encounter of an earlier family member.
function viaText(viaSid, target, game) {
  const steps = [];
  let cur = target;
  while (cur && cur.sid !== viaSid) {
    steps.unshift(cur);
    cur = cur.from ? baseSlotOf(cur.from) : null;
  }
  const name = (baseSlotOf(viaSid) || {}).species || '#' + viaSid;
  const how = steps.map((st, i) => evoInGame(i === steps.length - 1 ? target : st, game));
  if (how.some(h => !h.ok)) return null;
  return `Catch ${esc(name)}, then evolve: ${how.map(h => esc(h.txt)).join(' → ')}`;
}
function methodLines(rows, slot) {
  const vgl = (o) => esc(EVO.vgLabel[o] || '');
  const byTarget = new Map();
  for (const r of rows) { const k = r.toLabel || ''; if (!byTarget.has(k)) byTarget.set(k, []); byTarget.get(k).push(r); }
  let h = '';
  const regional = [...new Set(rows.filter(r => r.region).map(r => EVO.regionName[r.region]))];
  for (const [label, list] of byTarget) {
    const mine = slot && list.some(r => r.toForm === slot.fid);
    const outside = regional.length && !list.some(r => r.region) ? ` <span class="muted">· not in ${esc(regional.join(' or '))}</span>` : '';
    h += `<div class="evo-method${mine ? ' mine' : ''}">${label ? `<b>${esc(label)}:</b> ` : ''}`;
    if (list.length === 1) h += `${esc(list[0].txt)} <span class="muted">· since ${vgl(list[0].vg)}</span>${outside}`;
    else h += list.map(r => `<div><span class="muted">${r.cur ? 'Now' : 'From ' + vgl(r.vg)}:</span> ${esc(r.txt)}${r.cur ? ` <span class="muted">(since ${vgl(r.vg)})</span>` : ''}</div>`).join('') + outside;
    h += '</div>';
  }
  return h;
}
function evoHtml(s) {
  if (!EVO) return '<p class="muted small">Loading evolution data…</p>';
  const fam = [...new Map(SLOTS.filter(x => x.fam === s.fam && !x.gmax).map(x => [x.sid, baseSlotOf(x.sid)])).values()];
  const inFam = new Set(fam.map(x => x.sid));
  const kids = (sid) => fam.filter(x => x.from === sid);
  const roots = fam.filter(x => !x.from || !inFam.has(x.from));
  if (fam.length === 1 && !s.from) return '<p class="muted small">Does not evolve.</p>';
  let top = '';
  const own = (EVO.evo[s.sid] || []).filter(r => r.toForm === s.fid);
  if (own.length && formLabel(s)) top = `<div class="note">This form: ${own.map(r => esc(r.txt)).join(' <b>or</b> ')}</div>`;
  const mon = (x, arrow) => `<span class="evo-mon${x.sid === s.sid ? ' here' : ''}" data-open="${esc(x.key)}">${arrow ? '<span class="evo-arrow">↳</span>' : ''}<img src="${spriteUrl(x, false)}" alt="">${esc(x.species)}</span>`;
  const steps = (x) => {
    const children = kids(x.sid);
    if (!children.length) return '';
    return `<ul>${children.map(c => {
      const rows = EVO.evo[c.sid] || [];
      const lines = methodLines(rows, c.sid === s.sid ? s : null);
      return `<li><div class="evo-card">${mon(c, true)}${rows.length > 9 ? `<details><summary>${rows.length} ways (one per form)</summary>${lines}</details>` : lines}</div>${steps(c)}</li>`;
    }).join('')}</ul>`;
  };
  const node = (x) => `<li>${mon(x, false)}${steps(x)}</li>`;
  return top + `<ul class="evo-tree">${roots.map(node).join('')}</ul>` + (roots.length > 1 ? '<p class="muted small">This family is joined by breeding, not evolution.</p>' : '');
}
function findHtml(s) {
  if (!FINDER) return '<p class="muted small">Loading location data…</p>';
  const r = FINDER.find(s, { showAll: showAllGames });
  const nameOf = (sid) => (SLOTS.find(x => x.sid === sid) || {}).species || '#' + sid;
  let h = '';
  if (s.g) h += `<p class="small">Needs a <b>${s.g === 'm' ? 'male' : 'female'}</b> one — catch or hatch one of that gender, then evolve if needed.</p>`;
  for (const e of r.extra) h += `<div class="note">${e.game ? '<b>' + esc(gameName(e.game)) + ':</b> ' : ''}${esc(e.text)}</div>`;
  if (s.gmax && r.direct.length) h += '<p class="small muted">Raid spots below list the species; only some dens or adventures give the Gigantamax version.</p>';
  const groups = new Map();
  for (const e of r.direct) { if (!groups.has(e.game)) groups.set(e.game, []); groups.get(e.game).push(e); }
  for (const [g, list] of groups) {
    const seen = new Set(), stuck = new Set();
    const usable = list.filter(e => { if (!e.via) return true; const v = viaText(e.via, s, g); if (!v) stuck.add(e.via); e.viaHtml = v; return !!v; });
    h += `<div class="panel" style="margin:6px 0;padding:8px"><b>${esc(gameName(g))}</b>${VC_ONLY.has(g) ? ' <span class="muted small">(Home only via 3DS Virtual Console)</span>' : ''}`;
    for (const e of usable.slice(0, 40)) {
      const k = e.place + e.method + e.via + e.conds.join();
      if (seen.has(k)) continue; seen.add(k);
      h += `<div class="small" style="padding:3px 0;border-top:1px solid var(--line)">
        <span class="tier t${e.tier[0]}">${e.tier[1]}</span> ${esc(e.place)} · ${esc(methodLabel(e.method))} · Lv ${e.lo}${e.hi !== e.lo ? '–' + e.hi : ''}${e.rar ? ' · ' + e.rar + '%' : ''}
        ${e.conds.length ? `<span class="muted"> · ${esc(e.conds.join(', '))}</span>` : ''}${e.via ? `<br><span class="muted">${e.viaHtml}</span>` : ''}</div>`;
    }
    if (stuck.size) h += `<div class="small muted" style="padding:3px 0;border-top:1px solid var(--line)">${esc([...stuck].map(v => (baseSlotOf(v) || {}).species).join(', '))} ${stuck.size > 1 ? 'are' : 'is'} here, but can't evolve into ${esc(s.species)}${formLabel(s) ? ' (' + esc(formLabel(s)) + ')' : ''} in this game. Catch here and evolve in another game.</div>`;
    h += '</div>';
  }
  // Only list games where the hatched baby can actually evolve into this slot.
  if (s.from) r.breed = r.breed.filter(g => r.famBase.some(b => viaText(b.sid, s, g)));
  if (r.breed.length) {
    const bases = r.famBase.map(x => x.species).join(' or ');
    h += `<p class="small"><b>Breed:</b> leave any member of the family with a Ditto (or a partner of the opposite gender) to hatch ${esc(bases)}${s.from ? ', then evolve' : ''}. Works in ${esc(r.breed.map(gameName).join(', '))}.</p>`;
  }
  if (!r.direct.length && !r.extra.length) h += `<p class="small muted">No wild or gift locations ${showAllGames ? 'in the data' : 'in your games'}${r.breed.length ? ' — breeding is your route' : ''}.</p>`;
  if (r.missingData.length) h += `<p class="small muted">No location data yet for: ${esc(r.missingData.map(g => gameName(g) + (PARTIAL_DATA.has(g) ? ' (partial)' : '')).join(', '))}.</p>`;
  return h;
}
function learnset(s) {
  const L = MOVES.learn;
  return L[s.pid] || L[(SLOTS.find(x => x.sid === s.sid && x.formType === 'base') || {}).pid] || L[s.sid] || { m: [], lv: [] };
}
function movesHtml(s) {
  if (!MOVES) return '<p class="muted small">Loading moves…</p>';
  const L = learnset(s), N = MOVES.names;
  if (!L.m.length) return '<p class="muted small">No move data for this form yet.</p>';
  const by = (bit) => L.m.filter(m => m[1] & bit).map(m => N[m[0]]).join(', ');
  return `<p class="small"><b>Level-up (${esc(cap(L.lvGame))}):</b> ${L.lv.map(([lv, id]) => `${lv || 'Evo'}: ${esc(N[id])}`).join(' · ')}</p>
    <details class="small"><summary>TM / HM moves (any game)</summary>${esc(by(8)) || '—'}</details>
    <details class="small"><summary>Egg moves (any game)</summary>${esc(by(2)) || '—'}</details>
    <details class="small"><summary>Tutor moves (any game)</summary>${esc(by(4)) || '—'}</details>`;
}
function onDetail(e) {
  const mon = e.target.closest('[data-open]');
  if (mon) { const t = BYKEY.get(mon.dataset.open); if (t) openDetail(t); return; }
  if (e.target.dataset.act === 'showall') { showAllGames = e.target.checked; openDetail(findAny($('detail').dataset.key)); return; }
  const act = e.target.dataset.act;
  if (act === 'close') { $('detail').classList.add('hidden'); return; }
  const s = findAny($('detail').dataset.key);
  if (act === 'dcheck') { setProg(e.target.dataset.dex, s, { c: e.target.checked, loc: prog(e.target.dataset.dex, s).loc || 'home' }); openDetail(s); refresh(); }
}
function onDetailChange(e) {
  if (e.target.dataset.act !== 'dloc') return;
  const s = findAny($('detail').dataset.key);
  setProg(e.target.dataset.dex, s, { loc: e.target.value }); refresh();
}

// ---------- boxes ----------
function renderBoxes() {
  const dex = $('boxDex').value;
  const lay = layout(dex);
  const byIdx = new Map(Object.entries(lay.pos).map(([k, p]) => [p.idx, k]));
  const first = lay.firstBox, last = lay.lastBox;
  const boxes = [];
  for (let b = first; b <= last; b++) {
    let label = `Box ${b}`;
    const keys = []; for (let i = 0; i < PER_BOX; i++) { const k = byIdx.get((b - 1) * PER_BOX + i); if (k) keys.push(k); }
    if (keys.length) { const a = BYKEY.get(keys[0]), z = BYKEY.get(keys[keys.length - 1]); label += ` · #${pad(a.sid)}–#${pad(z.sid)}`; } else label += ' · empty (gap)';
    boxes.push([b, label]);
  }
  boxIndex = Math.max(0, Math.min(boxIndex, boxes.length - 1));
  $('boxPick').innerHTML = boxes.map(([b, l], i) => `<option value="${i}"${i === boxIndex ? ' selected' : ''}>${esc(l)}</option>`).join('');
  const b = boxes[boxIndex][0];
  $('boxGrid').dataset.box = b;
  $('boxLoc').innerHTML = locOptions(boxLoc);
  let html = '';
  for (let i = 0; i < PER_BOX; i++) {
    const k = byIdx.get((b - 1) * PER_BOX + i);
    if (!k) { html += '<div class="box-cell empty"></div>'; continue; }
    const s = BYKEY.get(k), c = prog(dex, s).c;
    const away = c && prog(dex, s).loc && prog(dex, s).loc !== 'home';
    html += `<div class="box-cell${c ? ' caught' : ''}${away ? ' away' : ''}" data-key="${esc(k)}" title="${esc(displayName(s) + ' ' + formLabel(s))}"><img loading="lazy" src="${spriteUrl(s, dex === 'shiny')}" alt=""></div>`;
  }
  $('boxGrid').innerHTML = html;
  const inBox = boxKeys(), done = inBox.filter(k => prog(dex, BYKEY.get(k)).c).length;
  $('boxSummary').textContent = inBox.length ? `${done} of ${inBox.length} caught in this box` : 'Empty box, kept free for new forms';
  const total = lay.boxes, used = last;
  $('boxNote').textContent = `${dex === 'shiny' ? 'Shiny' : 'Living'} dex uses boxes ${first}–${last} (${total} boxes). Empty boxes between generations leave room for new forms. Overall, ${used} of Home's 200 boxes are planned.`;
}
let boxMode = 'mark', boxLoc = 'home';
function boxKeys() {
  const dex = $('boxDex').value, lay = layout(dex), b = Number($('boxGrid').dataset.box);
  return Object.entries(lay.pos).filter(([, p]) => p.box === b).map(([k]) => k);
}
function onBoxClick(e) {
  const c = e.target.closest('.box-cell'); if (!c || !c.dataset.key) return;
  const s = BYKEY.get(c.dataset.key), dex = $('boxDex').value;
  if (boxMode === 'info') { openDetail(s); return; }
  const p = prog(dex, s);
  setProg(dex, s, p.c ? { c: false } : { c: true, loc: boxLoc });
  renderBoxes();
}
function markBox(on) {
  const dex = $('boxDex').value;
  const keys = boxKeys();
  if (!on && !confirm(`Clear all ${keys.length} slots in this box?`)) return;
  for (const k of keys) { const s = BYKEY.get(k); if (on && prog(dex, s).c) continue; setProg(dex, s, on ? { c: true, loc: boxLoc } : { c: false }); }
  renderBoxes();
  toast(on ? 'Box marked caught' : 'Box cleared');
}

// ---------- dashboard ----------
function stats(dex) {
  const list = activeSlots(dex);
  let c = 0, h = 0; const gens = {};
  for (const s of list) {
    const p = prog(dex, s);
    const g = gens[s.gen] || (gens[s.gen] = { t: 0, c: 0, h: 0 });
    g.t++; if (p.c) { c++; g.c++; if (!p.loc || p.loc === 'home') { h++; g.h++; } }
  }
  return { t: list.length, c, h, gens };
}
const pct = (a, b) => b ? Math.round(a / b * 1000) / 10 : 0;
function thisGameHtml() {
  if (!FINDER) return '<p class="muted small">Loading location data…</p>';
  const opts = dataGames().filter(g => S().owned[g.id]);
  const g = filters.game || opts[0]?.id;
  if (!g) return '';
  const set = FINDER.obtainableIn(g);
  const row = (dex) => { const list = activeSlots(dex).filter(s => set.has(s.key)); const missing = list.filter(s => !prog(dex, s).c).length; return `<div>${dex === 'shiny' ? 'Shiny' : 'Living'}: <b>${missing}</b> still to get here (${pct(list.length - missing, list.length)}% of the ${list.length} available)</div>`; };
  return `<div class="panel" style="margin-top:10px"><h3>This game</h3>
    <select id="dashGame">${opts.map(o => `<option value="${o.id}"${o.id === g ? ' selected' : ''}>${esc(o.name)}</option>`).join('')}</select>
    <div class="small" style="margin-top:8px">${row('living')}${row('shiny')}</div>
    <p class="muted small">Games without location data yet (${esc([...NO_DATA].filter(x => S().owned[x]).map(gameName).join(', '))}) aren't listed.</p></div>`;
}
function renderDashboard() {
  const block = (title, dex) => {
    const st = stats(dex);
    return `<div class="panel"><h3>${title}</h3>
      <div class="big">${pct(st.h, st.t)}%</div><div class="muted small">in Home · ${st.h} of ${st.t}</div>
      <div class="progress home"><div style="width:${pct(st.h, st.t)}%"></div></div>
      <div class="muted small">Caught anywhere: ${pct(st.c, st.t)}% (${st.c}) · Needs transfer: ${st.c - st.h}</div>
      <div class="progress"><div style="width:${pct(st.c, st.t)}%"></div></div>
      ${Object.entries(st.gens).map(([g, v]) => `<div class="gen-row"><span>Gen ${g}</span><div class="progress home" style="margin:0"><div style="width:${pct(v.h, v.t)}%"></div></div><span>${pct(v.h, v.t)}%</span></div>`).join('')}
    </div>`;
  };
  $('dashboardView').innerHTML = `<div class="cards">${block('Living form dex', 'living')}${block('Shiny living form dex', 'shiny')}</div>
    ${thisGameHtml()}`;
}

// ---------- settings ----------
function renderSettings() {
  const st = S();
  const gameCard = (g) => `<div class="toggle"><span>${esc(g.name)}</span><input type="checkbox" data-set="owned" data-id="${g.id}"${st.owned[g.id] ? ' checked' : ''}></div>
    ${st.owned[g.id] ? (g.dlc || []).map(([id, n]) => `<div class="toggle sub"><span>${esc(n)}</span><input type="checkbox" data-set="dlc" data-id="${g.id}:${id}"${st.dlc[g.id + ':' + id] ? ' checked' : ''}></div>`).join('') +
      (g.charm ? `<div class="toggle sub"><span>Shiny Charm</span><input type="checkbox" data-set="charm" data-id="${g.id}"${st.charm[g.id] ? ' checked' : ''}></div>` : '') : ''}`;
  const gens = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0];
  const u = store.user();
  $('settingsView').innerHTML = `<div class="cards">
    <div class="panel"><h3>Home layout</h3>
      <div class="toggle"><span>Include Gigantamax slots</span><input type="checkbox" data-set="gmax"${st.gmax ? ' checked' : ''}></div>
      <div class="toggle"><span>Empty boxes before the shiny dex</span><input type="number" min="0" max="60" data-set="buffer" value="${st.buffer}" style="width:70px"></div>
      <p class="muted small">Each generation ends on its own box, followed by one empty box.</p></div>
    <div class="panel"><h3>Save &amp; backup</h3>
      <p class="small">${store.cloudEnabled() ? (u ? 'Syncing to your Google account (' + esc(u.email || '') + ').' : 'Sign in to sync across devices.') : 'Cloud sync isn\'t set up yet, so progress saves in this browser only. Export a backup regularly.'}</p>
      <div class="toolbar"><button id="exportBtn" class="primary">Export backup</button><button id="importBtn">Import backup</button><input id="importFile" type="file" accept="application/json" class="hidden"></div></div>
    ${gens.map(g => `<div class="panel"><h3>${g ? 'Generation ' + g : 'Other'}</h3>${GAMES.filter(x => x.gen === g).map(gameCard).join('')}</div>`).join('')}
  </div>`;
}
function onSettings(e) {
  const t = e.target, set = t.dataset.set;
  if (t.id === 'exportBtn') { store.exportJSON(); return; }
  if (t.id === 'importBtn') { $('importFile').click(); return; }
  if (!set || e.type === 'click') return;
  const st = S();
  if (set === 'gmax') st.gmax = t.checked;
  else if (set === 'buffer') st.buffer = Math.max(0, Math.min(60, Number(t.value) || 0));
  else st[set][t.dataset.id] = t.checked;
  if (FINDER) FINDER.clear();
  layoutCache = {};
  store.save();
  renderSettings();
}
async function onImport(e) {
  const file = e.target.files[0]; if (!file) return;
  try { store.importJSON(await file.text()); ensureSettings(); layoutCache = {}; toast('Backup restored'); refresh(); }
  catch (err) { toast(err.message); }
}

// ---------- shell ----------
function renderFilters() {
  const defs = filterDefs();
  $('filters').innerHTML = defs.map(d => `<label>${d.label}<select data-f="${d.id}"><option value="">Any</option>${d.opts.map(([v, l]) => `<option value="${esc(v)}"${String(filters[d.id] ?? '') === String(v) ? ' selected' : ''}>${esc(l)}</option>`).join('')}</select></label>`).join('')
    + '<div class="actions"><button id="clearFilters" class="ghost">Clear filters</button></div>';
  const n = Object.values(filters).filter(Boolean).length;
  $('filterCount').textContent = n ? `(${n})` : '';
}
function renderRoutes() {
  const v = $('routesView');
  if (!FINDER) { v.innerHTML = '<p class="muted">Loading location data…</p>'; return; }
  const opts = dataGames().filter(g => S().owned[g.id]);
  if (!routeGame || !GAME_VERSIONS_OK(routeGame)) routeGame = opts[0]?.id || 'red';
  const areas = FINDER.areasFor(routeGame);
  if (!areas.find(a => String(a.id) === String(routeArea))) routeArea = areas[0]?.id ?? '';
  const area = areas.find(a => String(a.id) === String(routeArea));
  const dex = v.dataset.dex || 'living';
  let rows = '';
  if (area) {
    const byPid = new Map();
    for (const e of area.list) { if (!byPid.has(e.pid)) byPid.set(e.pid, []); byPid.get(e.pid).push(e); }
    const items = [...byPid.entries()].map(([pid, list]) => ({ pid, list, slots: FINDER.slotsForPid(pid) })).filter(x => x.slots.length);
    items.sort((a, b) => Math.min(...a.list.map(e => e.tier[0])) - Math.min(...b.list.map(e => e.tier[0])) || a.slots[0].sid - b.slots[0].sid);
    rows = items.map(({ list, slots }) => {
      const missing = slots.filter(s => !(dex === 'shiny' && s.shinyLock) && !prog(dex, s).c);
      const s = slots[0];
      const methods = [...new Set(list.map(e => `<span class="tier t${e.tier[0]}">${e.tier[1]}</span> ${methodLabel(e.method)} Lv ${e.lo}${e.hi !== e.lo ? '–' + e.hi : ''}${e.rar ? ' · ' + e.rar + '%' : ''}${e.conds.length ? ' · ' + e.conds.join(', ') : ''}`))].join('<br>');
      return `<div class="card${missing.length ? '' : ' caught'}" data-key="${esc(s.key)}" style="flex-direction:row;align-items:flex-start;text-align:left">
        <img loading="lazy" src="${spriteUrl(s, dex === 'shiny')}" alt="" style="width:56px;height:56px">
        <div style="flex:1"><div class="nm" style="text-align:left">${esc(s.species)}${missing.length ? ` <span class="flag" style="position:static">${missing.length} missing</span>` : ' ✓'}</div>
        <div class="small muted">${methods}</div></div></div>`;
    }).join('');
  }
  v.innerHTML = `<div class="toolbar">
      <select id="routeGame">${opts.map(o => `<option value="${o.id}"${o.id === routeGame ? ' selected' : ''}>${esc(o.name)}</option>`).join('')}</select>
      <select id="routeArea">${areas.map(a => `<option value="${a.id}"${String(a.id) === String(routeArea) ? ' selected' : ''}>${esc(a.name)}</option>`).join('')}</select>
      <select id="routeDex"><option value="living"${dex === 'living' ? ' selected' : ''}>Living dex</option><option value="shiny"${dex === 'shiny' ? ' selected' : ''}>Shiny dex</option></select></div>
    <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(260px,1fr))">${rows || '<p class="muted">Nothing recorded here.</p>'}</div>
    <p class="muted small">Newer games (Shining Pearl, Legends: Arceus, Violet, Z-A) don't publish spawn rates, so their spots show as \u201cListed\u201d.</p>`;
}
const GAME_VERSIONS_OK = (g) => dataGames().some(x => x.id === g && S().owned[x.id]);
const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
function eventStatus(e) {
  const t = today();
  if (e.start && e.start > t) return 'upcoming';
  if (e.end && e.end < t) return 'ended';
  return 'active';
}
function eventMissing(e) {
  return (e.keys || []).map(k => BYKEY.get(k)).filter(Boolean).filter(s => s.slot !== false && !prog(e.shiny ? 'shiny' : 'living', s).c);
}
function renderBanner() {
  const b = $('banner');
  const hits = EVENTS.filter(e => eventStatus(e) === 'active' && eventMissing(e).length && (S().owned[e.game] || !e.game));
  if (!hits.length || sessionStorageGet('bannerHidden') === hits.map(e => e.id).join()) { b.classList.add('hidden'); return; }
  b.innerHTML = `<span>🎁 ${hits.length === 1 ? esc(hits[0].title) + ' is available now' : hits.length + ' events have Pokémon you\u2019re missing'} — <a href="#" data-act="toEvents">see events</a></span><button class="ghost" data-act="hideBanner">✕</button>`;
  b.classList.remove('hidden');
}
function sessionStorageGet(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
function renderEvents() {
  const groups = { active: [], upcoming: [], ended: [] };
  for (const e of EVENTS) groups[eventStatus(e)].push(e);
  const card = (e) => {
    const miss = eventMissing(e);
    const slots = (e.keys || []).map(k => BYKEY.get(k)).filter(Boolean);
    return `<div class="panel${miss.length && eventStatus(e) === 'active' ? ' event-hot' : ''}">
      <div style="display:flex;gap:8px;align-items:center">${slots.slice(0, 3).map(s => `<img src="${spriteUrl(s, e.shiny)}" alt="" style="width:56px;height:56px">`).join('')}
      <div><b>${esc(e.title)}</b>${e.shiny ? ' ★ shiny' : ''}<div class="small muted">${esc(gameName(e.game))}${S().owned[e.game] ? '' : ' (not owned)'}</div></div></div>
      <div class="small" style="margin-top:6px">${esc(e.how || '')}</div>
      <div class="small muted">${e.start ? 'From ' + e.start + ' · ' : ''}${e.end ? 'Ends ' + e.end : 'No end date announced'}</div>
      ${miss.length ? `<div class="small" style="color:var(--accent);margin-top:4px">You're missing ${miss.map(s => esc(displayName(s) + (formLabel(s) ? ' (' + formLabel(s) + ')' : ''))).join(', ')}</div>` : slots.length ? '<div class="small" style="color:var(--caught)">Already caught ✓</div>' : ''}
      ${e.source ? `<div class="small"><a href="${esc(e.source)}" target="_blank" rel="noopener">Source</a></div>` : ''}</div>`;
  };
  $('eventsView').innerHTML = `
    <h3>Available now</h3><div class="cards">${groups.active.map(card).join('') || '<p class="muted">Nothing running right now.</p>'}</div>
    ${groups.upcoming.length ? `<h3>Coming up</h3><div class="cards">${groups.upcoming.map(card).join('')}</div>` : ''}
    ${groups.ended.length ? `<details style="margin-top:12px"><summary>Recently ended</summary><div class="cards">${groups.ended.map(card).join('')}</div></details>` : ''}
    <p class="muted small">US distributions only. Last updated ${esc(EVENTS.updated || '')}.</p>`;
}
function refresh() {
  const isList = ['living', 'shiny', 'official'].includes(view);
  $('listView').classList.toggle('hidden', !isList);
  $('boxesView').classList.toggle('hidden', view !== 'boxes');
  $('dashboardView').classList.toggle('hidden', view !== 'dashboard');
  $('settingsView').classList.toggle('hidden', view !== 'settings');
  $('routesView').classList.toggle('hidden', view !== 'routes');
  $('eventsView').classList.toggle('hidden', view !== 'events');
  if (view === 'events') renderEvents();
  renderBanner();
  if (view === 'routes') renderRoutes();
  if (isList) { renderFilters(); renderList(); }
  if (view === 'boxes') renderBoxes();
  if (view === 'dashboard') renderDashboard();
  if (view === 'settings') renderSettings();
}
function renderAccount(u) {
  const a = $('account');
  if (!store.cloudEnabled()) { a.innerHTML = '<span class="muted">Saved on this device</span>'; return; }
  a.innerHTML = u ? `<span class="muted">${esc(u.displayName || u.email || 'Signed in')}</span><button id="signOut" class="ghost">Sign out</button>` : '<button id="signIn" class="primary">Sign in with Google</button>';
}

async function main() {
  store.load();
  ensureSettings();
  DATA = await (await fetch('data/dex.json')).json();
  SLOTS = DATA.slots;
  OFFICIAL = DATA.officialOnly;
  BYKEY = new Map([...SLOTS.map(s => [s.key, s]), ...OFFICIAL.map(s => [s.ident, Object.assign(s, { key: s.ident })])]);
  SLOTS.filter(s => s.gmax).forEach(s => gmaxable.add(s.sid));

  $('sort').innerHTML = SORTS.map(([v, l]) => `<option value="${v}">${l}</option>`).join('');
  $('tabs').addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b) return;
    view = b.dataset.view;
    [...$('tabs').children].forEach(x => x.classList.toggle('active', x === b));
    if (view === 'official' && sortKey === 'home') { sortKey = 'national'; $('sort').value = 'national'; }
    refresh();
  });
  $('search').addEventListener('input', () => renderList());
  $('sort').addEventListener('change', (e) => { sortKey = e.target.value; renderList(); });
  $('sortDir').addEventListener('click', () => { sortAsc = !sortAsc; $('sortDir').textContent = sortAsc ? '↑' : '↓'; renderList(); });
  $('filterToggle').addEventListener('click', () => $('filters').classList.toggle('hidden'));
  $('filters').addEventListener('change', (e) => { const f = e.target.dataset.f; if (!f) return; filters[f] = e.target.value; renderFilters(); renderList(); });
  $('filters').addEventListener('click', (e) => { if (e.target.id === 'clearFilters') { filters = {}; renderFilters(); renderList(); } });
  $('grid').addEventListener('click', onGridClick);
  $('grid').addEventListener('change', onGridChange);
  $('detail').addEventListener('click', onDetail);
  $('detail').addEventListener('change', onDetailChange);
  $('boxDex').addEventListener('change', () => { boxIndex = 0; renderBoxes(); });
  $('boxPick').addEventListener('change', (e) => { boxIndex = Number(e.target.value); renderBoxes(); });
  $('boxPrev').addEventListener('click', () => { boxIndex--; renderBoxes(); });
  $('boxNext').addEventListener('click', () => { boxIndex++; renderBoxes(); });
  $('boxGrid').addEventListener('click', onBoxClick);
  $('boxMode').addEventListener('click', (e) => { const m = e.target.dataset.mode; if (!m) return; boxMode = m; [...$('boxMode').children].forEach(x => x.classList.toggle('on', x.dataset.mode === m)); });
  $('boxLoc').addEventListener('change', (e) => { boxLoc = e.target.value; });
  $('boxAll').addEventListener('click', () => markBox(true));
  $('boxNone').addEventListener('click', () => markBox(false));
  $('settingsView').addEventListener('click', onSettings);
  $('settingsView').addEventListener('change', (e) => e.target.id === 'importFile' ? onImport(e) : onSettings(e));
  $('account').addEventListener('click', (e) => { if (e.target.id === 'signIn') store.signIn(); if (e.target.id === 'signOut') store.signOut(); });

  $('routesView').addEventListener('change', (e) => {
    if (e.target.id === 'routeGame') { routeGame = e.target.value; routeArea = ''; }
    if (e.target.id === 'routeArea') routeArea = e.target.value;
    if (e.target.id === 'routeDex') $('routesView').dataset.dex = e.target.value;
    renderRoutes();
  });
  $('routesView').addEventListener('click', (e) => { const c = e.target.closest('.card'); if (c) openDetail(BYKEY.get(c.dataset.key)); });
  $('dashboardView').addEventListener('change', (e) => { if (e.target.id === 'dashGame') { filters.game = e.target.value; renderDashboard(); } });
  $('banner').addEventListener('click', (e) => {
    if (e.target.dataset.act === 'toEvents') { e.preventDefault(); $('tabs').querySelector('[data-view=events]').click(); }
    if (e.target.dataset.act === 'hideBanner') { try { sessionStorage.setItem('bannerHidden', EVENTS.filter(x => eventStatus(x) === 'active' && eventMissing(x).length).map(x => x.id).join()); } catch (err) {} $('banner').classList.add('hidden'); }
  });
  fetch('data/events.json').then(r => r.json()).then(d => { EVENTS = d.events || []; EVENTS.updated = d.updated; refresh(); }).catch(() => {});
  renderAccount(null);
  refresh();
  Promise.all([fetch('data/encounters.json').then(r => r.json()), fetch('data/moves.json').then(r => r.json()), fetch('data/evolutions.json').then(r => r.json())]).then(([enc, moves, evo]) => {
    ENC = enc; MOVES = moves; EVO = evo;
    FINDER = createFinder({ slots: SLOTS, games: GAMES, settings: S, enc: ENC, canVia: (v, slot, g) => !!viaText(v, slot, g) });
    refresh();
    if (!$('detail').classList.contains('hidden')) openDetail(findAny($('detail').dataset.key));
  }).catch(err => console.error('Extra data failed to load', err));
  store.initCloud({
    onAuth: (u) => { renderAccount(u); if (view === 'settings') renderSettings(); },
    onRemote: () => { ensureSettings(); layoutCache = {}; refresh(); toast('Synced from the cloud'); },
  }).catch(err => console.error(err));
}
main();
