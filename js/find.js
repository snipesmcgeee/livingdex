// Where-to-find, This Game mode and route companion logic.

// Each game in the app -> PokeAPI version identifiers (DLC versions carry the DLC key that must be owned).
export const GAME_VERSIONS = {
  red: [['red'], ['red-japan'], ['green-japan']], blue: [['blue'], ['blue-japan']], yellow: [['yellow']],
  gold: [['gold']], silver: [['silver']], crystal: [['crystal']],
  ruby: [['ruby']], sapphire: [['sapphire']], emerald: [['emerald']], firered: [['firered']], leafgreen: [['leafgreen']],
  colosseum: [['colosseum']], xd: [['xd']],
  diamond: [['diamond']], pearl: [['pearl']], platinum: [['platinum']], heartgold: [['heartgold']], soulsilver: [['soulsilver']],
  black: [['black']], white: [['white']], black2: [['black-2']], white2: [['white-2']],
  x: [['x']], y: [['y']], omegaruby: [['omega-ruby']], alphasapphire: [['alpha-sapphire']],
  sun: [['sun']], moon: [['moon']], ultrasun: [['ultra-sun']], ultramoon: [['ultra-moon']],
  lgpikachu: [['lets-go-pikachu']], lgeevee: [['lets-go-eevee']],
  sword: [['sword'], ['the-isle-of-armor-sword', 'ioa'], ['the-crown-tundra-sword', 'ct']],
  shield: [['shield'], ['the-isle-of-armor-shield', 'ioa'], ['the-crown-tundra-shield', 'ct']],
  brilliantdiamond: [['brilliant-diamond']], shiningpearl: [['shining-pearl']], legendsarceus: [['legends-arceus']],
  scarlet: [['scarlet'], ['the-teal-mask-scarlet', 'tm'], ['the-indigo-disk-scarlet', 'id']],
  violet: [['violet'], ['the-teal-mask-violet', 'tm'], ['the-indigo-disk-violet', 'id']],
  legendsza: [['legends-za'], ['mega-dimension', 'md']], go: [['go']],
};
// Games whose wild data isn't in the dataset yet (built by hand later).
export const NO_DATA = new Set();
export const PARTIAL_DATA = new Set();
// Games that can't reach Home except through their 3DS Virtual Console release.
export const VC_ONLY = new Set(['red', 'blue', 'yellow', 'gold', 'silver', 'crystal']);
// Games with a Day Care / Nursery / picnic breeding.
const NO_BREEDING = new Set(['red', 'blue', 'yellow', 'colosseum', 'xd', 'lgpikachu', 'lgeevee', 'legendsarceus', 'legendsza', 'go']);

const METHOD_LABEL = {
  walk: 'Grass / cave', 'old-rod': 'Old Rod', 'good-rod': 'Good Rod', 'super-rod': 'Super Rod', surf: 'Surfing',
  'rock-smash': 'Rock Smash', headbutt: 'Headbutt', 'dark-grass': 'Dark grass', 'grass-spots': 'Rustling grass',
  'cave-spots': 'Dust cloud', 'bridge-spots': 'Bridge shadow', 'super-rod-spots': 'Fishing (ripples)', 'surf-spots': 'Surfing (ripples)',
  gift: 'Gift', 'gift-egg': 'Gift Egg', static: 'Static encounter', 'npc-trade': 'In-game trade', 'roaming-grass': 'Roaming',
  'roaming-water': 'Roaming (water)', sos: 'SOS call', 'island-scan': 'Island Scan', overworld: 'Overworld',
  'overworld-water': 'Overworld (water)', 'overworld-flying': 'Overworld (flying)', 'overworld-special': 'Overworld (special)',
  horde: 'Horde', 'hidden-grotto': 'Hidden Grotto', 'honey-tree': 'Honey Tree', wanderer: 'Wanderer', 'max-raid': 'Max Raid',
  'dynamax-adventure': 'Dynamax Adventure', 'berry-trees': 'Berry tree', snag: 'Snag (Shadow)', pokeflute: 'Poké Flute',
  'grand-underground': 'Grand Underground', 'space-time-distortion': 'Space-time distortion', landmark: 'Shaking tree / ore',
  'mass-outbreak': 'Mass outbreak', 'massive-mass-outbreak': 'Massive mass outbreak', 'tera-raid': 'Tera Raid',
  'wild-zone': 'Wild Zone', hyperspace: 'Hyperspace', 'go-wild': 'Wild', 'go-egg': 'Egg', 'go-raid': 'Raid',
  'go-research': 'Research', 'go-battle-league': 'GO Battle League', 'go-rocket': 'Team GO Rocket (Shadow)',
  'go-max-battle': 'Max Battle', 'go-other': 'Other events',
};
export const methodLabel = (m) => METHOD_LABEL[m] || m.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export function tier(method, rarity) {
  if (['gift', 'gift-egg', 'static', 'pokeflute'].includes(method)) return [1, 'Guaranteed'];
  if (['max-raid', 'dynamax-adventure', 'npc-trade', 'snag', 'snag-rematch', 'tera-raid', 'go-raid', 'go-max-battle'].includes(method)) return [4, method === 'npc-trade' ? 'Trade' : method.startsWith('snag') ? 'Snag' : 'Raid'];
  if (method.includes('outbreak')) return [2, 'Outbreak'];
  if (rarity >= 10) return [2, 'Common'];
  if (rarity > 0) return [3, 'Rare'];
  return [2, 'Listed'];
}

export function createFinder({ slots, games, settings, enc, canVia = () => true }) {
  const verToGame = {};
  for (const [g, vs] of Object.entries(GAME_VERSIONS)) for (const [v, dlc] of vs) verToGame[v] = [g, dlc];
  const bySid = new Map();
  for (const s of slots) { if (!bySid.has(s.sid)) bySid.set(s.sid, []); bySid.get(s.sid).push(s); }
  const suffixOf = (s) => (s.ident.match(/-(alola|galar|hisui|paldea)/) || [])[0] || '';

  function pidFor(sid, suffix) {
    const list = bySid.get(sid) || [];
    // A regional evolution can come from a plain pre-evolution (Pikachu -> Alolan Raichu), so fall back to the base form.
    if (suffix) { const r = list.find(x => x.ident.includes(suffix) && !x.gmax); if (r) return r.pid; }
    const b = list.find(x => x.formType === 'base') || list[0];
    return b ? b.pid : sid;
  }
  function ancestors(sid) { const out = []; let cur = (bySid.get(sid) || [])[0]; while (cur && cur.from) { out.push(cur.from); cur = (bySid.get(cur.from) || [])[0]; } return out; }
  const gameUsable = (g, dlc, showAll) => showAll || (settings().owned[g] && (!dlc || settings().dlc[g + ':' + dlc]));

  // All ways to get slot s. Returns {direct:[...], breed:[...], extra:[...], missingData:[...]}.
  function find(s, { showAll = false, onlyGame = null } = {}) {
    const suffix = suffixOf(s);
    const chain = [s.sid, ...ancestors(s.sid)];
    const direct = [];
    for (const sid of (s.gmax ? [s.sid] : chain)) {
      const pid = sid === s.sid && s.formType !== 'base' && !suffix && !s.gmax ? s.pid : pidFor(sid, suffix);
      const rowsFor = enc.enc[pid] || (pid !== sid ? [] : []);
      for (const [vi, area, mi, lo, hi, rar, conds] of rowsFor) {
        const v = enc.strings[vi]; const gm = verToGame[v]; if (!gm) continue;
        const [g, dlc] = gm;
        if (onlyGame && g !== onlyGame) continue;
        if (!gameUsable(g, dlc, showAll)) continue;
        const m = enc.strings[mi];
        if (s.gmax && !['max-raid', 'dynamax-adventure'].includes(m)) continue;
        direct.push({ game: g, dlc, area, place: enc.areas[area] || 'Unknown area', method: m, lo, hi, rar,
          conds: conds.map(c => enc.strings[c]), tier: tier(m, rar), via: sid === s.sid ? null : sid });
      }
    }
    direct.sort((a, b) => (a.tier[0] - b.tier[0]) || (games.findIndex(x => x.id === a.game) - games.findIndex(x => x.id === b.game)) || (b.rar - a.rar));

    const breed = [];
    const famBase = slots.filter(x => x.fam === s.fam && !x.from && x.formType === 'base');
    const fam = slots.filter(x => x.fam === s.fam);
    const canBreed = !s.gmax && fam.some(x => x.eggs.length && !x.eggs.includes('no-eggs') && !x.eggs.includes('ditto'));
    if (canBreed) {
      for (const g of games) {
        if (NO_BREEDING.has(g.id) || (onlyGame && g.id !== onlyGame) || !(showAll || settings().owned[g.id])) continue;
        if (g.gen && g.gen < 2) continue;
        breed.push(g.id);
      }
    }
    const extra = [];
    if (s.gmax) {
      if (s.sid === 809) extra.push({ text: 'Only from the Pokémon HOME gift (Gigantamax Melmetal), not from Max Soup.' });
      else for (const g of ['sword', 'shield']) if ((showAll || (settings().owned[g] && settings().dlc[g + ':ioa'])) && (!onlyGame || onlyGame === g))
        extra.push({ game: g, text: 'Feed Max Soup (Isle of Armor, Max Mushrooms) to a regular one to add the Gigantamax Factor.' });
    }
    if (s.formType === 'form' || s.formType === 'event') extra.push({ text: 'Form-specific: the locations show where the species appears; how this exact form is set (pattern, season, item, event) is noted per game in a later data pass.' });
    const missingData = games.filter(g => (NO_DATA.has(g.id) || PARTIAL_DATA.has(g.id)) && (showAll || settings().owned[g.id]) && (!onlyGame || onlyGame === g.id)).map(g => g.id);
    return { direct, breed, famBase, extra, missingData };
  }

  // Slots obtainable in one game (directly, via a pre-evolution, or Max Soup).
  const gameCache = new Map();
  function obtainableIn(game) {
    const k = game + JSON.stringify(settings().dlc);
    if (gameCache.has(k)) return gameCache.get(k);
    const set = new Set();
    for (const s of slots) {
      const r = find(s, { showAll: true, onlyGame: game });
      const ok = r.direct.some(e => (!e.dlc || settings().dlc[game + ':' + e.dlc]) && (!e.via || canVia(e.via, s, game))) || r.extra.some(e => e.game === game);
      if (ok) set.add(s.key);
    }
    gameCache.set(k, set);
    return set;
  }

  // Areas with encounters for a game, and what's there.
  function areasFor(game) {
    const vers = new Set((GAME_VERSIONS[game] || []).filter(([, dlc]) => !dlc || settings().dlc[game + ':' + dlc] || !settings().owned[game]).map(([v]) => v));
    const areas = new Map();
    for (const [pid, rowsFor] of Object.entries(enc.enc)) {
      for (const [vi, area, mi, lo, hi, rar, conds] of rowsFor) {
        if (!vers.has(enc.strings[vi])) continue;
        if (!areas.has(area)) areas.set(area, []);
        areas.get(area).push({ pid: Number(pid), method: enc.strings[mi], lo, hi, rar, conds: conds.map(c => enc.strings[c]), tier: tier(enc.strings[mi], rar) });
      }
    }
    return [...areas.entries()].map(([id, list]) => ({ id, name: enc.areas[id] || 'Area ' + id, list })).sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
  }
  const slotsForPid = (pid) => slots.filter(s => s.pid === pid && !s.gmax);
  return { find, obtainableIn, areasFor, slotsForPid, clear: () => gameCache.clear() };
}
