"""Build data/evolutions.json: every evolution method, in plain words, per game.

Run:  python3 -I build_evo.py <raw_csv_dir> <out_dir>
"""
import csv, json, os, sys
from collections import defaultdict

RAW, OUT = sys.argv[1], sys.argv[2]
EN = '9'

def rows(name):
    with open(os.path.join(RAW, name + '.csv'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def names(table, key, field='name'):
    return {r[key]: r[field] for r in rows(table) if r.get('local_language_id') == EN}

sp_name = names('pokemon_species_names', 'pokemon_species_id')
item_name = names('item_names', 'item_id')
move_name = names('move_names', 'move_id')
type_name = names('type_names', 'type_id')
loc_name = names('location_names', 'location_id')
region_name = names('region_names', 'region_id')
loc_region = {r['id']: r['region_id'] for r in rows('locations')}
nature_by_index = {}
nat_names = names('nature_names', 'nature_id')
for r in rows('natures'):
    nature_by_index[int(r['id']) - 1] = nat_names.get(r['id'], r['identifier'].title())  # mask bit = nature id - 1

# version groups: order + display name ("Red / Blue")
vg_order = {r['id']: int(r['order']) for r in rows('version_groups')}
ver_name = names('version_names', 'version_id')
vg_versions = defaultdict(list)
ver_vg = {}
for r in rows('versions'):
    vg_versions[r['version_group_id']].append(ver_name.get(r['id'], r['identifier']))
    ver_vg[r['identifier']] = vg_order[r['version_group_id']]
vg_label = {vg_order[k]: ' / '.join(v) for k, v in vg_versions.items()}
vg_regions = defaultdict(set)
for r in rows('version_group_regions'):
    vg_regions[vg_order[r['version_group_id']]].add(int(r['region_id']))

# forms: id -> (is_default, display name)
form_name = {r['pokemon_form_id']: r['form_name'] for r in rows('pokemon_form_names') if r['local_language_id'] == EN}
pokemon_species = {r['id']: r['species_id'] for r in rows('pokemon')}
forms = {}
for r in rows('pokemon_forms'):
    sid = pokemon_species.get(r['pokemon_id'])
    forms[r['id']] = (r['is_default'] == '1', sid, form_name.get(r['id'], ''))
def form_label(fid, include_default=False):
    if not fid or fid not in forms:
        return ''
    is_def, sid, fn = forms[fid]
    if (is_def and not include_default) or not fn:
        return ''
    return f"{fn} {sp_name.get(sid, '')}".strip() if sp_name.get(sid, '') not in fn else fn

# species present per version group (from learnset data)
present = defaultdict(set)
vg_with_data = set()
for r in rows('pokemon_moves'):
    sid = pokemon_species.get(r['pokemon_id'])
    o = vg_order[r['version_group_id']]
    vg_with_data.add(o)
    if sid:
        present[sid].add(o)

TIME = {'day': 'during the day', 'night': 'at night', 'dusk': 'at dusk', 'full-moon': 'under a full moon'}
SPIN_DIR = {'0': 'clockwise', '1': 'counterclockwise'}

def spin_text(expr, time):
    parts = expr.split()
    d = parts[parts.index('SPIN_DIR') + 1] if 'SPIN_DIR' in parts else None
    i = parts.index('SPIN_SEC')
    secs, op = parts[i + 1], parts[i + 2]
    dur = f"for {'under' if op == '<' else 'at least'} {secs} seconds"
    t = {'day': 'during the day', 'night': 'at night', 'dusk': 'at dusk'}.get(time, '')
    return 'spin ' + ' '.join(x for x in [SPIN_DIR.get(d, ''), dur, t] if x)

def describe(r):
    """Plain-words method text and filter tags for one evolution row."""
    t = r['evolution_trigger_id']
    tags, bits = set(), []
    item = item_name.get(r['trigger_item_id'], '')
    held = item_name.get(r['held_item_id'], '')
    loc = loc_name.get(r['location_id'], '')
    if t == '1':
        lvl = r['minimum_level']
        head = f"Level {lvl}" if lvl else 'Level up'
        tags.add('Level' if lvl else 'Level up (condition)')
        if r['minimum_happiness']: bits.append('with high friendship'); tags.add('Friendship')
        if r['minimum_affection']: bits.append('with high affection'); tags.add('Affection')
        if r['minimum_beauty']: bits.append('with high Beauty'); tags.add('Special condition')
        if held: bits.append(f'holding {held}'); tags.add('Level up holding item')
        if r['known_move_id']: bits.append(f"knowing {move_name.get(r['known_move_id'], '')}"); tags.add('Knows a move')
        if r['known_move_type_id']: bits.append(f"knowing a {type_name.get(r['known_move_type_id'], '')}-type move"); tags.add('Knows a move')
        if r['near_special_rock'] == '1':
            bits.append(f'near the special rock at {loc}' if loc else 'near the special rock'); tags.add('Location')
        elif loc:
            bits.append(f'at {loc}'); tags.add('Location')
        if r['party_species_id']: bits.append(f"with {sp_name.get(r['party_species_id'], '')} in the party"); tags.add('Party condition')
        if r['party_type_id']: bits.append(f"with a {type_name.get(r['party_type_id'], '')}-type in the party"); tags.add('Party condition')
        if r['relative_physical_stats']:
            bits.append({'1': 'with Attack higher than Defense', '-1': 'with Defense higher than Attack', '0': 'with Attack equal to Defense'}[r['relative_physical_stats']]); tags.add('Special condition')
        if r['needs_overworld_rain'] == '1': bits.append('while it is raining'); tags.add('Weather')
        if r['turn_upside_down'] == '1': bits.append('with the console held upside down'); tags.add('Special condition')
        if r['needs_multiplayer'] == '1': bits.append('while in a Union Circle'); tags.add('Special condition')
        if r['minimum_steps']: bits.append(f"after walking {int(r['minimum_steps']):,} steps with it following you (Let's Go mode)"); tags.add('Special condition')
        if r['nature_bitmask']:
            m = int(r['nature_bitmask'])
            nats = sorted(nature_by_index[i] for i in range(25) if m >> i & 1)
            bits.append('with nature ' + ', '.join(nats)); tags.add('Nature')
        text = head
    elif t == '2':
        text = 'Trade'
        tags.add('Trade')
        if held: bits.append(f'holding {held}'); tags.add('Trade holding item')
        if r['trade_species_id']: bits.append(f"for a {sp_name.get(r['trade_species_id'], '')}"); tags.add('Trade for a specific Pokémon')
    elif t == '3':
        text = f'Use {item}'
        tags.add('Item: ' + item)
    elif t == '4':
        text = 'Appears in an empty party slot when Nincada evolves (needs a spare Poké Ball)'; tags.add('Special condition')
    elif t == '5':
        text = f"Hold {held}, then " + spin_text(r['condition_expression'], r['time_of_day']); tags.add('Special condition')
    elif t == '6':
        text = 'Train in the Tower of Darkness (Isle of Armor)'; tags.add('Special condition')
    elif t == '7':
        text = 'Train in the Tower of Waters (Isle of Armor)'; tags.add('Special condition')
    elif t == '8':
        text = 'Land 3 critical hits in one battle'; tags.add('Special condition')
    elif t == '9':
        text = f"Take at least {r['minimum_damage_taken']} damage without fainting, then walk under the stone arch in Dusty Bowl"; tags.add('Special condition')
    elif t == '10':
        text = f"Level {r['minimum_level']} (evolves after a battle)" if r['minimum_level'] else 'Level up after a battle'; tags.add('Level')
    elif t == '11':
        text = f"Use {move_name.get(r['used_move_id'], '')} in Agile Style 20 times"; tags.add('Use a move')
    elif t == '12':
        text = f"Use {move_name.get(r['used_move_id'], '')} in Strong Style 20 times"; tags.add('Use a move')
    elif t == '13':
        text = f"Lose at least {r['minimum_damage_taken']} HP from recoil without fainting"; tags.add('Special condition')
    elif t == '14':
        text = f"Use {move_name.get(r['used_move_id'], '')} 20 times"; tags.add('Use a move')
    elif t == '15':
        text = 'Defeat 3 Bisharp that lead packs, holding a Leader\'s Crest'; tags.add('Special condition')
    elif t == '16':
        text = 'Level up with 999 Gimmighoul Coins'; tags.add('Special condition')
    elif t == '17':
        text = 'Feed 400 Meltan Candy in Pokémon GO'; tags.add('Special condition')
    else:
        text = 'Special method'; tags.add('Special condition')

    if t not in ('5',) and r['time_of_day']:
        bits.append(TIME.get(r['time_of_day'], r['time_of_day'])); tags.add('Time of day')
    if t in ('3', '2') and r['gender_id'] or t == '1' and r['gender_id']:
        bits.append('(female only)' if r['gender_id'] == '1' else '(male only)'); tags.add('Gender-specific')
    if r['region_id']:
        bits.append(f"in {region_name.get(r['region_id'], '')}"); tags.add('Regional')
    if r['percentage_chance']:
        bits.append(f"({r['percentage_chance']}% chance)")
    elif r['condition_expression'] and t != '5':
        bits.append('(50/50, decided when caught)')
    full = text + (' ' + ' '.join(bits) if bits else '')
    return full.replace('  ', ' ').strip(), sorted(tags)

evo = defaultdict(list)
for r in rows('pokemon_evolution'):
    to = r['evolved_species_id']
    text, tags = describe(r)
    lr = loc_region.get(r['location_id'])
    entry = {
        'vg': vg_order[r['version_group_id']], 'txt': text, 'tags': tags,
        'cur': r['is_default'] == '1',
    }
    if r['evolved_pokemon_form_id'] and r['evolved_pokemon_form_id'] in forms:
        entry['toForm'] = int(r['evolved_pokemon_form_id'])
        lbl = form_label(r['evolved_pokemon_form_id'], include_default=True)
        if lbl: entry['toLabel'] = lbl
    if r['required_pokemon_form_id'] and r['required_pokemon_form_id'] in forms and not forms[r['required_pokemon_form_id']][0]:
        entry['fromLabel'] = form_label(r['required_pokemon_form_id'])
    if lr:
        entry['locRegion'] = int(lr)
    if r['region_id']:
        entry['region'] = int(r['region_id'])
    evo[to].append(entry)

for v in evo.values():
    v.sort(key=lambda e: (e['vg'], e['txt']))

out = {
    'vgLabel': vg_label,
    'vgRegions': {k: sorted(v) for k, v in vg_regions.items()},
    'verVg': ver_vg,
    'vgWithData': sorted(vg_with_data),
    'present': {int(k): sorted(v) for k, v in present.items()},
    'evo': {int(k): v for k, v in evo.items()},
}
with open(os.path.join(OUT, 'evolutions.json'), 'w') as fh:
    json.dump(out, fh, separators=(',', ':'), ensure_ascii=False)
print('species with methods', len(evo), 'rows', sum(len(v) for v in evo.values()))
