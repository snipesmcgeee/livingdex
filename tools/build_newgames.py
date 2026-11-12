"""Add BDSP, Legends: Arceus, Scarlet/Violet, Legends: Z-A and Pokémon GO encounters to encounters.json.

Source: PKHeX's legality encounter tables (datamined) + its English location names.
Run:  python3 -I build_newgames.py <pkhex_core_dir> <raw_csv_dir> <out_dir>
"""
import csv, json, os, re, struct, sys
from collections import defaultdict

PK, RAW, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
WILD = os.path.join(PK, 'Resources/legality/wild')
TXT = os.path.join(PK, 'Resources/text/locations')
DATA = os.path.join(PK, 'Legality/Encounters/Data')

# ---------- (species, form) -> PokeAPI pokemon id ----------
with open(os.path.join(RAW, 'pokemon_forms.csv'), newline='') as f:
    forms = list(csv.DictReader(f))
with open(os.path.join(RAW, 'pokemon.csv'), newline='') as f:
    pk_species = {r['id']: int(r['species_id']) for r in csv.DictReader(f)}
by_species = defaultdict(list)
for r in forms:
    by_species[pk_species[r['pokemon_id']]].append(r)
form_pid = {}
for sp, lst in by_species.items():
    lst.sort(key=lambda r: (int(r['form_order']), int(r['id'])))
    for r in lst:
        idx = int(r['form_order']) - 1
        form_pid.setdefault((sp, idx), int(r['pokemon_id']))
def pid(species, form):
    return form_pid.get((species, form)) or form_pid.get((species, 0)) or species

# ---------- helpers ----------
def linker32(d):
    n = struct.unpack_from('<H', d, 2)[0]
    return [d[struct.unpack_from('<I', d, 4 + i * 4)[0]:struct.unpack_from('<I', d, 8 + i * 4)[0]] for i in range(n)]
def linker16(d):
    n = struct.unpack_from('<H', d, 2)[0]
    return [d[struct.unpack_from('<H', d, 4 + i * 2)[0]:struct.unpack_from('<H', d, 6 + i * 2)[0]] for i in range(n)]
def rd(path):
    return open(path, 'rb').read()
def loc_names(folder, prefix):
    out = {}
    for base in (0, 30000, 40000, 60000):
        p = os.path.join(TXT, folder, f'text_{prefix}_{base:05d}_en.txt')
        if os.path.exists(p):
            for i, line in enumerate(open(p, encoding='utf-8').read().split('\n')):
                out[base + i] = line.strip()
    return out

rows = []  # (pid, version, area_key, area_name, method, lo, hi, conds)
def add(p, ver, area_key, area_name, method, lo, hi, conds=()):
    rows.append((p, ver, area_key, area_name or 'Unknown area', method, lo, hi, tuple(conds)))

# ---------- BDSP ----------
L8b = loc_names('gen8b', 'bdsp')
T8b = {1: 'walk', 2: 'surf', 3: 'old-rod', 4: 'good-rod', 5: 'super-rod', 6: 'rock-smash', 7: 'headbutt', 8: 'honey-tree', 0: 'walk'}
for fn, ver, ug in (('bd', 'brilliant-diamond', False), ('sp', 'shining-pearl', False), ('bd_underground', 'brilliant-diamond', True), ('sp_underground', 'shining-pearl', True)):
    for a in linker32(rd(f'{WILD}/Gen8/encounter_{fn}.pkl')):
        loc, typ = struct.unpack_from('<H', a, 0)[0], a[2]
        for j in range((len(a) - 4) // 4):
            sp, lo, hi = struct.unpack_from('<HBB', a, 4 + j * 4)
            form, sp = sp >> 11, sp & 0x3FF
            add(pid(sp, form), ver, ('8b', loc), L8b.get(loc), 'grand-underground' if ug else T8b.get(typ, 'walk'), lo, hi)

# ---------- Omega Ruby / Alpha Sapphire (PokeAPI's data is partial) ----------
L6 = loc_names('gen6', 'xy')
T6 = {0: 'walk', 1: 'walk', 2: 'surf', 3: 'old-rod', 4: 'good-rod', 5: 'super-rod', 6: 'rock-smash', 7: 'horde', 8: 'walk'}
for fn, ver in (('or', 'omega-ruby'), ('as', 'alpha-sapphire')):
    for a in linker32(rd(f'{WILD}/Gen6/encounter_{fn}.pkl')):
        loc, typ = struct.unpack_from('<H', a, 0)[0], a[2]
        for j in range((len(a) - 4) // 4):
            sp, lo, hi = struct.unpack_from('<HBB', a, 4 + j * 4)
            form, sp = sp >> 11, sp & 0x3FF
            add(pid(sp, form), ver, ('6', loc), L6.get(loc), T6.get(typ, 'walk'), lo, hi)
ORAS_V = {'OR': ['omega-ruby'], 'AS': ['alpha-sapphire'], 'ORAS': ['omega-ruby', 'alpha-sapphire'], None: ['omega-ruby', 'alpha-sapphire']}

# ---------- Legends: Arceus ----------
L8a = loc_names('gen8a', 'la')
T8a = {0: 'overworld', 1: 'space-time-distortion', 2: 'landmark', 3: 'mass-outbreak', 4: 'massive-mass-outbreak'}
for a in linker32(rd(f'{WILD}/Gen8/encounter_la.pkl')):
    n = a[0]; locs = list(a[1:1 + n]); align = n + 1; align += align & 1
    b = a[align:]; typ, count = b[0], b[1]
    for j in range(count):
        sp, form, alpha, lo, hi, gender, flaw = struct.unpack_from('<HBBBBBB', b, 2 + j * 8)
        for loc in locs[:1]:
            add(pid(sp, form), 'legends-arceus', ('8a', loc), L8a.get(loc), T8a.get(typ, 'overworld'), lo, hi, ['Alpha'] if alpha == 1 else [])

# ---------- Scarlet / Violet ----------
L9 = loc_names('gen9', 'sv')
def sv_dlc(loc):
    return 'tm' if 132 <= loc <= 172 else 'id' if 174 <= loc <= 210 else None
SV_TIME = ['afternoon', 'night', 'evening', 'morning']
W9 = {1: 'Normal', 2: 'Overcast', 4: 'Rain', 8: 'Thunderstorm', 16: 'Fog', 32: 'Snow', 64: 'Snowstorm', 128: 'Sandstorm'}
STANDARD_W = {1 | 2 | 4 | 8, 1 | 2 | 4 | 128, 1 | 2 | 32 | 64, 1 | 2, 0, 255}
def sv_versions(dlc, scarlet=True, violet=True):
    out = []
    if scarlet: out.append({'tm': 'the-teal-mask-scarlet', 'id': 'the-indigo-disk-scarlet'}.get(dlc, 'scarlet'))
    if violet: out.append({'tm': 'the-teal-mask-violet', 'id': 'the-indigo-disk-violet'}.get(dlc, 'violet'))
    return out

# version exclusives (wild spawns), from dittobase's list; forms as (species, form)
SCARLET_ONLY = {(128, 2), (246, 0), (247, 0), (248, 0), (425, 0), (426, 0), (434, 0), (435, 0), (633, 0), (634, 0), (635, 0),
                (690, 0), (691, 0), (765, 0), (874, 0), (936, 0), (984, 0), (985, 0), (986, 0), (987, 0), (988, 0), (989, 0),
                (1005, 0), (207, 0), (472, 0), (845, 0), (37, 1), (38, 1), (408, 0), (409, 0)}
VIOLET_ONLY = {(128, 3), (200, 0), (316, 0), (317, 0), (371, 0), (372, 0), (373, 0), (429, 0), (692, 0), (693, 0), (766, 0),
               (875, 0), (885, 0), (886, 0), (887, 0), (937, 0), (990, 0), (991, 0), (992, 0), (993, 0), (994, 0), (995, 0),
               (1006, 0), (190, 0), (424, 0), (877, 0), (27, 1), (28, 1), (410, 0), (411, 0)}
def sv_add(sp, form, loc, method, lo, hi, conds, scarlet=True, violet=True):
    if (sp, form) in SCARLET_ONLY: violet = False
    if (sp, form) in VIOLET_ONLY: scarlet = False
    for v in sv_versions(sv_dlc(loc), scarlet, violet):
        add(pid(sp, form), v, ('9', loc), L9.get(loc), method, lo, hi, conds)

for a in linker32(rd(f'{WILD}/Gen9/encounter_wild_paldea.pkl')):
    loc = a[0]
    for j in range((len(a) - 4) // 8):
        sp, form, gender, lo, hi, time, weather = struct.unpack_from('<HBBBBBB', a, 4 + j * 8)
        conds = []
        if time:
            conds.append('Not in the ' + ', '.join(SV_TIME[b] for b in range(4) if time & (1 << b)))
        if weather and not weather & 1:
            conds.append('Weather: ' + ', '.join(n for b, n in W9.items() if weather & b))
        sv_add(sp, form, loc, 'overworld', lo, hi, conds)

d = rd(f'{WILD}/Gen9/encounter_fixed_paldea.pkl')
for i in range(len(d) // 0x14):
    sp, form, lvl = struct.unpack_from('<HBB', d, i * 0x14)
    locs = [x for x in d[i * 0x14 + 0x10:i * 0x14 + 0x14] if x]
    for loc in locs[:1]:
        sv_add(sp, form, loc, 'static', lvl, lvl, [])

for fn, map_dlc, place in (('gem_paldea', None, 'Tera Raid Battles (Paldea)'), ('gem_kitakami', 'tm', 'Tera Raid Battles (Kitakami)'), ('gem_blueberry', 'id', 'Tera Raid Battles (Blueberry Academy)')):
    d = rd(f'{WILD}/Gen9/encounter_{fn}.pkl')
    seen = set()
    for i in range(len(d) // 0x18):
        e = d[i * 0x18:(i + 1) * 0x18]
        sp, form = struct.unpack_from('<HB', e, 0)
        shiny, lvl, stars = e[6], e[7], e[0x12]
        rs, rv = struct.unpack_from('<hh', e, 0x14)
        key = (sp, form, stars, rs >= 0, rv >= 0)
        if key in seen: continue
        seen.add(key)
        conds = [f'{stars}★ raid'] + (['Shiny-locked'] if shiny == 1 else [])
        for v in sv_versions(map_dlc, rs >= 0, rv >= 0):
            add(pid(sp, form), v, ('9raid', fn), place, 'tera-raid', lvl, lvl, conds)

d = rd(f'{WILD}/Gen9/encounter_outbreak_paldea.pkl')
SIZE = 0xC + 16
for i in range(len(d) // SIZE):
    e = d[i * SIZE:(i + 1) * SIZE]
    sp, form, gender, lo, hi = struct.unpack_from('<HBBBB', e, 0)
    met = e[0x0C]
    flags = int.from_bytes(e[0x0C:0x1C], 'little') >> 8
    locs = [met + b for b in range(120) if flags >> b & 1]
    for loc in locs:
        sv_add(sp, form, loc, 'mass-outbreak', lo, hi, ['Mass outbreak'])

# ---------- Legends: Z-A ----------
L9a = loc_names('gen9a', 'za')
for fn, dlc in (('za', None), ('hyperspace_za', 'md')):
    for a in linker16(rd(f'{WILD}/Gen9/encounter_{fn}.pkl')):
        loc = struct.unpack_from('<H', a, 0)[0]
        for j in range((len(a) - 4) // 8):
            sp, form, gender, lo, hi, alpha, shiny = struct.unpack_from('<HBBBBBB', a, 4 + j * 8)
            conds = (['Alpha'] if alpha == 1 else []) + (['Shiny-locked'] if shiny == 1 else [])
            add(pid(sp, form), 'mega-dimension' if dlc else 'legends-za', ('9a', loc), L9a.get(loc),
                'hyperspace' if dlc else 'wild-zone' if 'Wild Zone' in L9a.get(loc, '') else 'overworld', lo, hi, conds)

# ---------- gifts / statics / trades from PKHeX's C# tables ----------
def parse_cs(path, game, locs, version_map):
    src = open(path, encoding='utf-8').read()
    out = []
    for block in re.finditer(r'readonly (Encounter(?:Static|Gift|Trade)\w*)\[\] (\w+)\s*=\s*\[(.*?)\n\s*\];', src, re.S):
        cls, name, body = block.groups()
        kind = 'npc-trade' if 'Trade' in cls else 'gift' if ('Gift' in cls or 'Gift' in name) else 'static'
        for line in body.split('\n'):
            line = line.strip()
            if not line.startswith('new('): continue
            m = re.match(r'new\(([^)]*)\)', line)
            args = [x.strip() for x in m.group(1).split(',')] if m else []
            sp = re.search(r'Species = (\d+)', line)
            lv = re.search(r'Level = (\d+)', line)
            fm = re.search(r'\bForm = (\d+)', line)
            loc = re.search(r'Location = (\d+)', line)
            ver = next((a for a in args if a in version_map), None)
            nums = [a for a in args if a.isdigit()]
            if sp:
                species, level, form = int(sp.group(1)), int(lv.group(1)) if lv else 0, int(fm.group(1)) if fm else 0
            elif cls.startswith('EncounterTrade') and len(nums) >= 3:
                # (names, index, [ver,] species, [form,] level)
                rest = nums[1:]
                if len(rest) == 2: species, form, level = int(rest[0]), 0, int(rest[1])
                else: species, form, level = int(rest[0]), int(rest[1]), int(rest[2])
            elif len(nums) >= 3:
                species, form, level = int(nums[0]), int(nums[1]), int(nums[2])
            else:
                continue
            l = int(loc.group(1)) if loc else None
            if fm and not sp is None: form = int(fm.group(1))
            shiny = 'Shiny = Never' in line or 'Shiny = Shiny.Never' in line
            out.append((species, form, level, l, kind, version_map.get(ver, version_map.get(None)), shiny))
    return out

BDSP_V = {'BD': ['brilliant-diamond'], 'SP': ['shining-pearl'], 'BDSP': ['brilliant-diamond', 'shining-pearl'], None: ['brilliant-diamond', 'shining-pearl']}
for sp, form, lvl, loc, kind, vers, shiny in parse_cs(f'{DATA}/Gen8/Encounters8b.cs', '8b', L8b, BDSP_V):
    for v in vers:
        add(pid(sp, form), v, ('8b', loc) if loc is not None else ('8b-trade', 0), L8b.get(loc, 'In-game trade'), kind, lvl, lvl, ['Shiny-locked'] if shiny else [])
for sp, form, lvl, loc, kind, vers, shiny in parse_cs(f'{DATA}/Gen8/Encounters8a.cs', '8a', L8a, {None: ['legends-arceus']}):
    add(pid(sp, form), 'legends-arceus', ('8a', loc) if loc is not None else ('8a-trade', 0), L8a.get(loc, 'In-game trade'), kind, lvl, lvl, [])
for sp, form, lvl, loc, kind, vers, shiny in parse_cs(f'{DATA}/Gen6/Encounters6AO.cs', '6', L6, ORAS_V):
    for v in vers:
        add(pid(sp, form), v, ('6', loc) if loc is not None else ('6-trade', 0), L6.get(loc, 'In-game trade'), kind, lvl, lvl, ['Shiny-locked'] if shiny else [])
SV_V = {'SL': (True, False), 'VL': (False, True), 'SV': (True, True), None: (True, True)}
for sp, form, lvl, loc, kind, sv, shiny in parse_cs(f'{DATA}/Gen9/Encounters9.cs', '9', L9, SV_V):
    for v in sv_versions(sv_dlc(loc or 0), *sv):
        add(pid(sp, form), v, ('9', loc) if loc is not None else ('9-trade', 0), L9.get(loc, 'In-game trade'), kind, lvl, lvl, ['Shiny-locked'] if shiny else [])
for sp, form, lvl, loc, kind, _, shiny in parse_cs(f'{DATA}/Gen9/Encounters9a.cs', '9a', L9a, {None: None}):
    add(pid(sp, form), 'legends-za', ('9a', loc) if loc is not None else ('9a-trade', 0), L9a.get(loc, 'In-game trade'), kind, lvl, lvl, [])

# ---------- Pokémon GO ----------
GO_KIND = lambda t: 'go-wild' if t == 1 else 'go-egg' if t in (2, 3) else 'go-raid' if 10 <= t < 20 else 'go-research' if 20 <= t < 40 else 'go-battle-league' if 40 <= t < 50 else 'go-rocket' if 50 <= t < 60 else 'go-max-battle' if 60 <= t < 70 else 'go-other'
for a in linker32(rd(f'{WILD}/encounter_go_home.pkl')):
    sp, form = struct.unpack_from('<HB', a, 0)
    kinds = {}
    for j in range((len(a) - 4) // 12):
        e = a[4 + j * 12:16 + j * 12]
        t, lvl = e[6], e[9]
        k = GO_KIND(t)
        kinds[k] = min(kinds.get(k, 99), lvl or 1)
    for k, lvl in kinds.items():
        add(pid(sp, form), 'go', ('go', 0), 'Pokémon GO', k, lvl, lvl, ['Availability rotates with events'])

# ---------- merge into encounters.json ----------
path = os.path.join(OUT, 'encounters.json')
enc = json.load(open(path))
for k in list(enc['enc']):
    enc['enc'][k] = [r for r in enc['enc'][k] if enc['strings'][r[0]] not in ('omega-ruby', 'alpha-sapphire')]
strings = enc['strings']; sidx = {s: i for i, s in enumerate(strings)}
def S(x):
    if x not in sidx:
        sidx[x] = len(strings); strings.append(x)
    return sidx[x]
area_ids = {}
next_id = 200000
agg = {}
for p, ver, akey, aname, method, lo, hi, conds in rows:
    if akey not in area_ids:
        area_ids[akey] = next_id; enc['areas'][str(next_id)] = aname; next_id += 1
    k = (p, ver, area_ids[akey], method, conds)
    if k in agg: agg[k] = (min(agg[k][0], lo), max(agg[k][1], hi))
    else: agg[k] = (lo, hi)
for (p, ver, aid, method, conds), (lo, hi) in agg.items():
    enc['enc'].setdefault(str(p), []).append([S(ver), aid, S(method), lo, hi, 0, [S(c) for c in conds]])
added = len(agg)
json.dump(enc, open(path, 'w'), separators=(',', ':'), ensure_ascii=False)
from collections import Counter
print('added rows', added, Counter(r[1] for r in rows))
