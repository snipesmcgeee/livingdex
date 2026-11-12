"""Build moves.json and encounters.json for the Living Dex from PokeAPI CSVs.

Run:  python3 -I build_extra.py <raw_csv_dir> <out_dir>
"""
import csv, json, os, re, sys
from collections import defaultdict

RAW, OUT = sys.argv[1], sys.argv[2]
EN = '9'

def rows(name):
    with open(os.path.join(RAW, name + '.csv'), newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)

# ---------- moves ----------
move_name = {r['move_id']: r['name'] for r in rows('move_names') if r['local_language_id'] == EN}
move_type = {}
for r in rows('moves'):
    move_type[r['id']] = r['type_id']
METHOD_BIT = {'1': 1, '2': 2, '3': 4, '4': 8}
vg_order = {r['id']: int(r['order']) for r in rows('version_groups')}
vg_name = {r['id']: r['identifier'] for r in rows('version_groups')}

learn = defaultdict(lambda: defaultdict(lambda: [0, 0, None]))  # pid -> move -> [mask, newestVG, levelInNewest]
for r in rows('pokemon_moves'):
    pid, mv, vg = r['pokemon_id'], r['move_id'], r['version_group_id']
    e = learn[pid][mv]
    e[0] |= METHOD_BIT.get(r['pokemon_move_method_id'], 16)
    if not e[1] or vg_order[vg] > vg_order[e[1]]:
        e[1] = vg

# level-up list from each Pokémon's newest game with level-up data
order_vg = {v: k for k, v in vg_order.items()}
levelup = defaultdict(list)
best = {}
for r in rows('pokemon_moves'):
    if r['pokemon_move_method_id'] != '1':
        continue
    o = vg_order[r['version_group_id']]
    if o > best.get(r['pokemon_id'], -1):
        best[r['pokemon_id']] = o
        levelup[r['pokemon_id']] = []
    if o == best[r['pokemon_id']]:
        levelup[r['pokemon_id']].append((int(r['level'] or 0), r['move_id']))

used = set()
out_learn = {}
for pid, mvs in learn.items():
    out_learn[pid] = {
        'm': [[int(mv), e[0], vg_order[e[1]]] for mv, e in sorted(mvs.items(), key=lambda kv: move_name.get(kv[0], ''))],
        'lv': sorted(set((lv, int(mv)) for lv, mv in levelup.get(pid, []))),
        'lvGame': vg_name.get(order_vg.get(best.get(pid)), ''),
    }
    used.update(mvs.keys())

with open(os.path.join(OUT, 'moves.json'), 'w') as fh:
    json.dump({'names': {int(k): move_name.get(k, k) for k in used},
               'vgNames': {vg_order[k]: v for k, v in vg_name.items()},
               'learn': out_learn}, fh, separators=(',', ':'), ensure_ascii=False)

# ---------- encounters ----------
ver = {r['id']: r['identifier'] for r in rows('versions')}
method = {r['id']: r['identifier'] for r in rows('encounter_methods')}
slot_info = {r['id']: (r['encounter_method_id'], int(r['rarity'] or 0)) for r in rows('encounter_slots')}
area_loc = {r['id']: r['location_id'] for r in rows('location_areas')}
area_name = {r['location_area_id']: r['name'] for r in rows('location_area_prose') if r['local_language_id'] == EN}
loc_name = {r['location_id']: r['name'] for r in rows('location_names') if r['local_language_id'] == EN}
loc_ident = {r['id']: r['identifier'] for r in rows('locations')}
cond_name = {r['encounter_condition_value_id']: r['name'] for r in rows('encounter_condition_value_prose') if r['local_language_id'] == EN}
cond = defaultdict(list)
for r in rows('encounter_condition_value_map'):
    cond[r['encounter_id']].append(r['encounter_condition_value_id'])

agg = {}
for r in rows('encounters'):
    mid, rar = slot_info.get(r['encounter_slot_id'], ('0', 0))
    conds = tuple(sorted(cond.get(r['id'], [])))
    key = (r['pokemon_id'], r['version_id'], r['location_area_id'], mid, conds)
    lo, hi = int(r['min_level']), int(r['max_level'])
    a = agg.get(key)
    if a:
        a[0] = min(a[0], lo); a[1] = max(a[1], hi); a[2] += rar
    else:
        agg[key] = [lo, hi, rar]

# string tables keep the file small
strings, sidx = [], {}
def S(x):
    if x not in sidx:
        sidx[x] = len(strings); strings.append(x)
    return sidx[x]

enc = defaultdict(list)
areas = {}
for (pid, vid, aid, mid, conds), (lo, hi, rar) in agg.items():
    loc = area_loc.get(aid)
    lname = loc_name.get(loc) or loc_ident.get(loc, '').replace('-', ' ').title()
    aname = area_name.get(aid, '')
    if re.match(r'^(Road|Route) \d+$', aname) or aname.lower() in ('area', 'main area'):
        aname = ''
    place = lname if not aname or aname == lname else (aname if lname in aname else f'{lname} – {aname}')
    areas[aid] = place
    enc[pid].append([ver[vid] and S(ver[vid]), int(aid), S(method.get(mid, 'unknown')), lo, hi, min(rar, 100),
                     [S(cond_name.get(c, c)) for c in conds]])

with open(os.path.join(OUT, 'encounters.json'), 'w') as fh:
    json.dump({'strings': strings, 'areas': {int(k): v for k, v in areas.items()}, 'enc': enc}, fh,
              separators=(',', ':'), ensure_ascii=False)

print('learnsets', len(out_learn), 'moves', len(used))
print('encounter pokemon', len(enc), 'rows', sum(len(v) for v in enc.values()), 'areas', len(areas))
