"""Build data/connections.json: which areas connect to which, per game.

Sources:
  - Gen 1-3 games: pret disassemblies (map connections + warps), exact.
  - Remakes with the same layout reuse those graphs (Let's Go -> Red/Blue/Yellow,
    HeartGold/SoulSilver -> Crystal, Omega Ruby/Alpha Sapphire -> Emerald).
  - Everything else: hand-built place graphs in tools/connections_manual.json.

Run:  python3 -I build_conn.py <pret_dir> <manual_json> <livingdex_data_dir>
"""
import json, os, re, sys, unicodedata
from collections import defaultdict

PRET, MANUAL, DATA = sys.argv[1], sys.argv[2], sys.argv[3]

STOP = {'kanto', 'johto', 'hoenn', 'sinnoh', 'unova', 'kalos', 'alola', 'galar', 'paldea', 'hisui', 'the', 'area'}
def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and ').replace('mount ', 'mt ').replace('mt. ', 'mt ').replace('pokemon', 'pkmn').replace("'", '')
    words = [w for w in re.split(r'[^a-z0-9]+', s) if w and w not in STOP]
    return ''.join(words)

def place_of(area_name):
    """The location part of an encounter-area name ("Mt. Moon – Mount Moon (1F)" -> "Mt. Moon")."""
    base = area_name.split(' – ')[0]
    base = re.sub(r'\s*\(.*?\)\s*', ' ', base).strip()
    return base

# ---------------- Gen 3 (pokefirered / pokeemerald) ----------------
def gen3(repo):
    root = os.path.join(PRET, repo, 'data/maps')
    sec_of, edges, names = {}, set(), {}
    maps = {}
    for d in os.listdir(root):
        p = os.path.join(root, d, 'map.json')
        if os.path.exists(p):
            m = json.load(open(p))
            maps[m['id']] = m
            sec_of[m['id']] = m.get('region_map_section', 'MAPSEC_NONE')
    for mid, m in maps.items():
        a = sec_of[mid]
        targets = [c['map'] for c in (m.get('connections') or [])] + [w['dest_map'] for w in (m.get('warp_events') or [])]
        for t in targets:
            b = sec_of.get(t)
            bad = ('NONE', 'DYNAMIC', 'SPECIAL_AREA')
            if b and a != b and not any(x in a or x in b for x in bad):
                edges.add(tuple(sorted((a, b))))
    for s in set(sec_of.values()):
        names[s] = s.replace('MAPSEC_', '').replace('_', ' ').title()
    return names, edges

# ---------------- Gen 1 (pokered) ----------------
def camel_to_const(n):
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', '_', n).upper()

def gen1(repo):
    root = os.path.join(PRET, repo, 'data/maps')
    names, edges = {}, set()
    towns = ['PALLET_TOWN', 'VIRIDIAN_CITY', 'PEWTER_CITY', 'CERULEAN_CITY', 'VERMILION_CITY', 'LAVENDER_TOWN',
             'CELADON_CITY', 'FUCHSIA_CITY', 'SAFFRON_CITY', 'CINNABAR_ISLAND', 'INDIGO_PLATEAU']
    keep = ['VIRIDIAN_FOREST', 'CERULEAN_CAVE', 'SAFARI_ZONE', 'SEAFOAM_ISLANDS', 'POKEMON_TOWER', 'POKEMON_MANSION',
            'ROCKET_HIDEOUT', 'SILPH_CO', 'MT_MOON', 'ROCK_TUNNEL', 'DIGLETTS_CAVE', 'VICTORY_ROAD', 'POWER_PLANT', 'SS_ANNE',
            'UNDERGROUND_PATH']
    special = {'REDS_HOUSE': 'PALLET_TOWN', 'BLUES_HOUSE': 'PALLET_TOWN', 'OAKS_LAB': 'PALLET_TOWN',
               'MUSEUM': 'PEWTER_CITY', 'BIKE_SHOP': 'CERULEAN_CITY', 'POKEMON_FAN_CLUB': 'VERMILION_CITY',
               'VERMILION_DOCK': 'VERMILION_CITY', 'GAME_CORNER': 'CELADON_CITY', 'FIGHTING_DOJO': 'SAFFRON_CITY',
               'COPYCATS_HOUSE': 'SAFFRON_CITY', 'MR_PSYCHICS_HOUSE': 'SAFFRON_CITY', 'DAYCARE': 'ROUTE_5',
               'BILLS_HOUSE': 'ROUTE_25', 'MT_MOON_POKECENTER': 'ROUTE_4', 'ROCK_TUNNEL_POKECENTER': 'ROUTE_10',
               'NAME_RATERS_HOUSE': 'LAVENDER_TOWN', 'MR_FUJIS_HOUSE': 'LAVENDER_TOWN', 'WARDENS_HOUSE': 'FUCHSIA_CITY',
               'LORELEIS_ROOM': 'INDIGO_PLATEAU', 'BRUNOS_ROOM': 'INDIGO_PLATEAU', 'AGATHAS_ROOM': 'INDIGO_PLATEAU',
               'LANCES_ROOM': 'INDIGO_PLATEAU', 'CHAMPIONS_ROOM': 'INDIGO_PLATEAU', 'HALL_OF_FAME': 'INDIGO_PLATEAU',
               'DIGLETTS_CAVE_ROUTE_2': 'DIGLETTS_CAVE', 'DIGLETTS_CAVE_ROUTE_11': 'DIGLETTS_CAVE'}
    def group(const):
        for k, v in special.items():
            if const.startswith(k):
                return v
        for k in keep:
            if const.startswith(k):
                return k
        m = re.match(r'(ROUTE_\d+)', const)
        if m:
            return m.group(1)
        for t in towns:
            if const.startswith(t.rsplit('_', 1)[0] + '_'):
                return t
        return const
    for f in os.listdir(os.path.join(root, 'headers')):
        src = open(os.path.join(root, 'headers', f)).read()
        m = re.search(r'map_header\s+(\w+),\s*(\w+)', src)
        if not m:
            continue
        a = group(m.group(2))
        for c in re.finditer(r'connection\s+\w+,\s*\w+,\s*(\w+)', src):
            edges.add(tuple(sorted((a, group(c.group(1))))))
        obj = os.path.join(root, 'objects', f)
        if os.path.exists(obj):
            for w in re.finditer(r'warp_event\s+\d+,\s*\d+,\s*(\w+)', open(obj).read()):
                if w.group(1) != 'LAST_MAP':
                    edges.add(tuple(sorted((a, group(w.group(1))))))
    edges = {e for e in edges if e[0] != e[1]}
    for e in edges:
        for n in e:
            names[n] = n.replace('_', ' ').title()
    return names, edges

# ---------------- Gen 2 (pokecrystal) ----------------
def gen2(repo):
    base = os.path.join(PRET, repo)
    lm = {}
    for m in re.finditer(r'map\s+(\w+),\s*\w+,\s*\w+,\s*LANDMARK_(\w+)', open(os.path.join(base, 'data/maps/maps.asm')).read()):
        lm[m.group(1).lower()] = m.group(2)
    key = lambda name: lm.get(name.replace('_', '').lower())
    edges = set()
    cur = None
    for line in open(os.path.join(base, 'data/maps/attributes.asm')).read().split('\n'):
        m = re.match(r'\s*map_attributes\s+(\w+),', line)
        if m:
            cur = key(m.group(1)); continue
        c = re.match(r'\s*connection\s+\w+,\s*(\w+),', line)
        if c and cur and key(c.group(1)):
            edges.add(tuple(sorted((cur, key(c.group(1))))))
    for f in os.listdir(os.path.join(base, 'maps')):
        if not f.endswith('.asm'):
            continue
        a = key(f[:-4])
        for w in re.finditer(r'warp_event\s+\d+,\s*\d+,\s*(\w+)', open(os.path.join(base, 'maps', f)).read()):
            b = key(w.group(1))
            if a and b:
                edges.add(tuple(sorted((a, b))))
    edges = {e for e in edges if e[0] != e[1] and 'SPECIAL' not in e[0] + e[1]}
    names = {n: n.replace('_', ' ').title() for e in edges for n in e}
    return names, edges

GRAPHS = {
    'frlg': gen3('pokefirered'),
    'rse': gen3('pokeemerald'),
    'rby': gen1('pokered'),
    'gsc': gen2('pokecrystal'),
}
manual = json.load(open(MANUAL)) if os.path.exists(MANUAL) else {'graphs': {}, 'games': {}}
for gid, g in manual.get('graphs', {}).items():
    names = {n: n for e in g['edges'] for n in e}
    GRAPHS[gid] = (names, {tuple(sorted(e)) for e in g['edges']})
    for alias, target in g.get('aliases', {}).items():
        GRAPHS[gid][0].setdefault(target, target)

GAME_GRAPH = {
    'red': 'rby', 'blue': 'rby', 'yellow': 'rby', 'lgpikachu': 'rby', 'lgeevee': 'rby',
    'gold': 'gsc', 'silver': 'gsc', 'crystal': 'gsc', 'heartgold': 'gsc', 'soulsilver': 'gsc',
    'ruby': 'rse', 'sapphire': 'rse', 'emerald': 'rse', 'omegaruby': 'rse', 'alphasapphire': 'rse',
    'firered': 'frlg', 'leafgreen': 'frlg',
}
GAME_GRAPH.update(manual.get('games', {}))
SOURCE = {'rby': 'exact', 'gsc': 'exact', 'rse': 'exact', 'frlg': 'exact'}
REMAKE = {'lgpikachu', 'lgeevee', 'heartgold', 'soulsilver', 'omegaruby', 'alphasapphire'}

# ---------------- match encounter areas to graph nodes ----------------
enc = json.load(open(os.path.join(DATA, 'encounters.json')))
S, A = enc['strings'], enc['areas']
GAME_VERSIONS = {
    'red': ['red', 'red-japan', 'green-japan'], 'blue': ['blue', 'blue-japan'], 'yellow': ['yellow'],
    'gold': ['gold'], 'silver': ['silver'], 'crystal': ['crystal'], 'ruby': ['ruby'], 'sapphire': ['sapphire'],
    'emerald': ['emerald'], 'firered': ['firered'], 'leafgreen': ['leafgreen'],
    'diamond': ['diamond'], 'pearl': ['pearl'], 'platinum': ['platinum'], 'heartgold': ['heartgold'], 'soulsilver': ['soulsilver'],
    'black': ['black'], 'white': ['white'], 'black2': ['black-2'], 'white2': ['white-2'], 'x': ['x'], 'y': ['y'],
    'omegaruby': ['omega-ruby'], 'alphasapphire': ['alpha-sapphire'], 'sun': ['sun'], 'moon': ['moon'],
    'ultrasun': ['ultra-sun'], 'ultramoon': ['ultra-moon'], 'lgpikachu': ['lets-go-pikachu'], 'lgeevee': ['lets-go-eevee'],
    'sword': ['sword', 'the-isle-of-armor-sword', 'the-crown-tundra-sword'], 'shield': ['shield', 'the-isle-of-armor-shield', 'the-crown-tundra-shield'],
    'brilliantdiamond': ['brilliant-diamond'], 'shiningpearl': ['shining-pearl'], 'legendsarceus': ['legends-arceus'],
    'scarlet': ['scarlet', 'the-teal-mask-scarlet', 'the-indigo-disk-scarlet'], 'violet': ['violet', 'the-teal-mask-violet', 'the-indigo-disk-violet'],
    'legendsza': ['legends-za', 'mega-dimension'],
}
game_areas = defaultdict(set)
ver_game = {v: g for g, vs in GAME_VERSIONS.items() for v in vs}
for rows in enc['enc'].values():
    for r in rows:
        g = ver_game.get(S[r[0]])
        if g:
            game_areas[g].add(r[1])

out = {'games': {}, 'graphs': {}}
report = {}
for game, gid in GAME_GRAPH.items():
    if gid not in GRAPHS:
        continue
    names, edges = GRAPHS[gid]
    extra = manual.get('extras', {}).get(game, {})
    if extra:
        names = dict(names); edges = set(edges)
        for a, b in extra.get('edges', []):
            edges.add(tuple(sorted((a, b))))
            for n in (a, b):
                names.setdefault(n, n.replace('MAPSEC_', '').replace('_', ' ').title() if n.isupper() else n)
        gid = gid + '+' + game
        GRAPHS[gid] = (names, edges)
    aliases = dict(manual.get('graphs', {}).get(gid.split('+')[0], {}).get('aliases', {}))
    aliases.update(manual.get('aliases', {}).get(gid.split('+')[0], {}))
    aliases.update(extra.get('aliases', {}))
    key_of = {}
    for n, nice in names.items():
        key_of.setdefault(norm(nice), n)
    for al, tgt in aliases.items():
        key_of[norm(al)] = tgt
    skip = {norm(x) for x in manual.get('skip', [])}
    area_node, unmatched = {}, []
    for aid in game_areas.get(game, ()):
        nm = A[str(aid)]
        cands = [nm.split(' – ')[-1], place_of(nm), nm.split(' – ')[0], re.sub(r'\s*\(.*', '', nm)]
        cands += [re.sub(r'^Sea ', '', c) for c in cands]
        hit = None
        for c in cands:
            k = norm(c)
            if k in key_of:
                hit = key_of[k]; break
        if not hit:
            # prefix match: "Mt Moon 1F" -> "Mt Moon"
            for c in cands:
                k = norm(c)
                best = max((kk for kk in key_of if k.startswith(kk) and len(kk) >= 4), key=len, default=None)
                if best:
                    hit = key_of[best]; break
        if hit:
            area_node[aid] = hit
        elif not any(norm(c) in skip or norm(c).startswith('unknown') or norm(c).startswith('all') for c in cands):
            unmatched.append(nm)
    out['games'][game] = {'graph': gid, 'areas': {str(k): v for k, v in area_node.items()},
                          'source': SOURCE.get(gid, 'manual'), 'remake': game in REMAKE,
                          'note': manual.get('sources', {}).get(gid.split('+')[0], '')}
    report[game] = (len(area_node), len(game_areas.get(game, ())), sorted(unmatched))
for gid, (names, edges) in GRAPHS.items():
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    out['graphs'][gid] = {'names': {n: nice for n, nice in names.items() if n in adj},
                          'adj': {k: sorted(v) for k, v in adj.items()}}

json.dump(out, open(os.path.join(DATA, 'connections.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
for g, (m, t, um) in sorted(report.items()):
    print(f'{g}: matched {m}/{t}', ('UNMATCHED: ' + '; '.join(um[:40])) if um else '')
