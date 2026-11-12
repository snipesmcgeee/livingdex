"""Build livingdex/data/dex.json from PokeAPI CSVs + hand-maintained rules.

Run:  python3 -I build_data.py <raw_csv_dir> <home_sprite_list.txt> <out_dir>
"""
import csv, json, sys, os
from collections import defaultdict

RAW, SPRITE_LIST, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
EN = '9'

def rows(name):
    with open(os.path.join(RAW, name + '.csv'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

species = {r['id']: r for r in rows('pokemon_species')}
pokemon = {r['id']: r for r in rows('pokemon')}
forms = rows('pokemon_forms')
sprites = set(l.strip() for l in open(SPRITE_LIST) if l.strip())

sp_name = {r['pokemon_species_id']: r['name'] for r in rows('pokemon_species_names') if r['local_language_id'] == EN}
form_name = {}
for r in rows('pokemon_form_names'):
    if r['local_language_id'] == EN:
        form_name[r['pokemon_form_id']] = (r['form_name'], r['pokemon_name'])
type_id = {r['id']: r['identifier'] for r in rows('types')}
egg_id = {r['id']: r['identifier'] for r in rows('egg_groups')}
color_id = {r['id']: r['identifier'] for r in rows('pokemon_colors')}
shape_id = {r['id']: r['identifier'] for r in rows('pokemon_shapes')}
growth_id = {r['id']: r['identifier'] for r in rows('growth_rates')}
ability_name = {r['ability_id']: r['name'] for r in rows('ability_names') if r['local_language_id'] == EN}
trigger_id = {r['id']: r['identifier'] for r in rows('evolution_triggers')}
dex_id = {r['id']: r['identifier'] for r in rows('pokedexes')}

ptypes = defaultdict(list)
for r in sorted(rows('pokemon_types'), key=lambda r: int(r['slot'])):
    ptypes[r['pokemon_id']].append(type_id[r['type_id']])
STAT_ORDER = ['1', '2', '3', '4', '5', '6']  # hp atk def spa spd spe
pstats = defaultdict(dict)
for r in rows('pokemon_stats'):
    pstats[r['pokemon_id']][r['stat_id']] = int(r['base_stat'])
eggs = defaultdict(list)
for r in rows('pokemon_egg_groups'):
    eggs[r['species_id']].append(egg_id[r['egg_group_id']])
pabil = defaultdict(lambda: {'a': [], 'h': None})
for r in sorted(rows('pokemon_abilities'), key=lambda r: int(r['slot'])):
    n = ability_name.get(r['ability_id'], r['ability_id'])
    if r['is_hidden'] == '1':
        pabil[r['pokemon_id']]['h'] = n
    elif n not in pabil[r['pokemon_id']]['a']:
        pabil[r['pokemon_id']]['a'].append(n)
evo_method = {}
for r in rows('pokemon_evolution'):
    evo_method.setdefault(r['evolved_species_id'], trigger_id.get(r['evolution_trigger_id'], ''))
regional = defaultdict(dict)
for r in rows('pokemon_dex_numbers'):
    d = dex_id.get(r['pokedex_id'])
    if d and d != 'national':
        regional[r['species_id']][d] = int(r['pokedex_number'])

# ---------- families ----------
chain_members = defaultdict(list)
for sid, s in species.items():
    chain_members[s['evolution_chain_id']].append(int(sid))
# breeding links PokeAPI's evolution chains miss (see spec)
FAMILY_MERGES = [(29, 32), (313, 314), (489, 490)]
fam_of_chain = {c: min(m) for c, m in chain_members.items()}
family = {sid: fam_of_chain[s['evolution_chain_id']] for sid, s in species.items()}
for a, b in FAMILY_MERGES:
    fa, fb = family[str(a)], family[str(b)]
    lo = min(fa, fb)
    for sid in family:
        if family[sid] in (fa, fb):
            family[sid] = lo

def root(sid):
    s = species[sid]
    while s['evolves_from_species_id']:
        s = species[s['evolves_from_species_id']]
    return int(s['id'])

def stage(sid):
    n, s = 1, species[sid]
    while s['evolves_from_species_id']:
        n += 1
        s = species[s['evolves_from_species_id']]
    return n

# ---------- form rules ----------
ULTRA_BEASTS = {793, 794, 795, 796, 797, 798, 799, 803, 804, 805, 806}
PARADOX = set(range(984, 996)) | {1005, 1006, 1009, 1010, 1020, 1021, 1022, 1023}

# Forms that can never be in Home: official dex only.
NEVER_HOME = {'pichu-spiky-eared', 'pikachu-cosplay', 'pikachu-belle', 'pikachu-libre', 'pikachu-phd',
              'pikachu-pop-star', 'pikachu-rock-star', 'eternatus-eternamax'}
# Forms with no slot of their own (revert when deposited, ride/battle modes, or look identical to the base).
NO_SLOT_PREFIX = ('arceus-', 'silvally-', 'genesect-')
NO_SLOT = {'dialga-origin', 'palkia-origin', 'giratina-origin',
           'koraidon-limited-build', 'koraidon-sprinting-build', 'koraidon-swimming-build', 'koraidon-gliding-build',
           'miraidon-low-power-mode', 'miraidon-drive-mode', 'miraidon-aquatic-mode', 'miraidon-glide-mode',
           'pikachu-starter', 'eevee-starter',
           'ogerpon-wellspring-mask', 'ogerpon-hearthflame-mask', 'ogerpon-cornerstone-mask'}
# Calls that need checking against Home before Jack relies on them.
REVIEW = {}  # all eight open questions resolved against Serebii/Bulbapedia (Nov 2026)
# Look identical to the base; told apart only by ability (Jack wants these as slots).
ABILITY_FORMS = {'greninja-battle-bond': 'Battle Bond', 'rockruff-own-tempo': 'Own Tempo',
                 'zygarde-10-power-construct': '10% Forme · Power Construct', 'zygarde-50-power-construct': '50% Forme · Power Construct'}
# Scatterbug/Spewpa patterns look identical; only Vivillon's show.
IDENTICAL_PREFIX = ('scatterbug-', 'spewpa-', 'mothim-')

# Shiny unobtainable in every game (as of Nov 2026). Species ids, plus specific forms.
SHINY_LOCK_SPECIES = {789, 790, 891, 892, 896, 897, 898, 494, 720, 801, 802, 893, 1017, 1024,
                      1025, 1014, 1015, 1016, 1009, 1010, 1020, 1021, 1022, 1023}
SHINY_LOCK_FORMS = {'pikachu-original-cap', 'pikachu-hoenn-cap', 'pikachu-sinnoh-cap', 'pikachu-unova-cap',
                    'pikachu-kalos-cap', 'pikachu-alola-cap', 'pikachu-world-cap', 'vivillon-poke-ball',
                    'melmetal-gmax', 'ursaluna-bloodmoon', 'floette-eternal'}

# Species whose base form is the default but whose slots come only from alternate forms.
MINIOR = '774'

def sprite_file(f, p, shiny=False, female=False):
    pre = ('shiny/' if shiny else '') + ('female/' if female else '')
    cands = []
    if f['form_identifier'] == 'female':
        sh = 'shiny/' if shiny else ''
        if f"{sh}female/{p['species_id']}.png" in sprites:
            return f"{sh}female/{p['species_id']}.png", True
    if int(p['id']) > 10000:
        cands.append(f"{p['id']}.png")
    if f['form_identifier']:
        cands.append(f"{p['species_id']}-{f['form_identifier']}.png")
    cands.append(f"{p['id']}.png")
    cands.append(f"{p['species_id']}.png")
    for c in cands:
        if pre + c in sprites:
            return pre + c, True
    return None, False

slots, official_only, missing_art = [], [], []
has_female_form = {pokemon[f['pokemon_id']]['species_id'] for f in forms if f['identifier'].endswith('-female')}
seen_identical = set()

for f in sorted(forms, key=lambda f: (int(pokemon[f['pokemon_id']]['species_id']), int(f['order']))):
    ident = f['identifier']
    p = pokemon[f['pokemon_id']]
    sid = p['species_id']
    s = species[sid]
    is_gmax = ident.endswith('-gmax')
    if f['is_battle_only'] == '1' and not is_gmax:
        continue
    if ident.startswith(('-totem',)) or '-totem' in ident:
        continue
    if sid == MINIOR and ident.endswith('-meteor'):
        continue
    if ident.startswith(IDENTICAL_PREFIX) and f['is_default'] != '1':
        continue
    fid = f['id']
    fn, pn = form_name.get(fid, ('', ''))
    if ident.startswith(IDENTICAL_PREFIX):
        fn, pn = '', ''
    if ident in ABILITY_FORMS:
        fn = ABILITY_FORMS[ident]
    name = pn or sp_name.get(sid, s['identifier'].title())
    no_slot = ident in NO_SLOT or (ident.startswith(NO_SLOT_PREFIX) and f['is_default'] != '1')
    never_home = ident in NEVER_HOME

    st = pstats[p['id']]
    stats = [st.get(k, 0) for k in STAT_ORDER]
    sidn = int(sid)
    if is_gmax:
        ftype = 'gmax'
    elif f['is_default'] == '1' and p['is_default'] == '1':
        ftype = 'base'
    elif ident in NEVER_HOME or '-cap' in ident or ident in ('magearna-original', 'floette-eternal', 'zarude-dada'):
        ftype = 'event'
    elif any(r in ident for r in ('-alola', '-galar', '-hisui', '-paldea')):
        ftype = 'regional'
    else:
        ftype = 'form'
    cat = []
    if s['is_legendary'] == '1': cat.append('legendary')
    if s['is_mythical'] == '1': cat.append('mythical')
    if s['is_baby'] == '1': cat.append('baby')
    if sidn in ULTRA_BEASTS: cat.append('ultra-beast')
    if sidn in PARADOX: cat.append('paradox')

    base = {
        'sid': sidn, 'pid': int(p['id']), 'fid': int(fid), 'ident': ident,
        'name': name, 'species': sp_name.get(sid, ''), 'formName': fn,
        'gen': int(s['generation_id']), 'fam': family[sid], 'root': root(sid), 'from': int(s['evolves_from_species_id'] or 0), 'stage': stage(sid),
        'types': ptypes[p['id']], 'stats': stats, 'bst': sum(stats),
        'abilities': pabil[p['id']]['a'], 'hidden': pabil[p['id']]['h'],
        'eggs': eggs[sid], 'genderRate': int(s['gender_rate']),
        'height': int(p['height']) / 10, 'weight': int(p['weight']) / 10,
        'color': color_id.get(s['color_id'], ''), 'shape': shape_id.get(s['shape_id'], ''),
        'capture': int(s['capture_rate']), 'friendship': int(s['base_happiness'] or 0),
        'eggCycles': int(s['hatch_counter'] or 0), 'growth': growth_id.get(s['growth_rate_id'], ''),
        'evoMethod': evo_method.get(sid, ''), 'cat': cat, 'formType': ftype,
        'regional': regional.get(sid, {}),
        'shinyLock': sidn in SHINY_LOCK_SPECIES or ident in SHINY_LOCK_FORMS,
    }
    if ident in REVIEW:
        base['review'] = REVIEW[ident]

    if never_home:
        base['slot'] = False
        base['why'] = "Can't be transferred to Home"
        spr, _ = sprite_file(f, p)
        base['spr'] = spr
        official_only.append(base)
        continue
    if no_slot:
        base['slot'] = False
        base['why'] = 'Reverts or changes when stored, so no slot of its own'
        spr, _ = sprite_file(f, p)
        base['spr'] = spr
        official_only.append(base)
        continue

    gender_split = (f"female/{p['id']}.png" in sprites and ftype in ('base', 'regional')
                    and sid not in has_female_form)
    variants = [('m', False), ('f', True)] if gender_split else [(None, False)]
    for g, fem in variants:
        slot = dict(base)
        slot['slot'] = True
        slot['g'] = g or ('f' if ident.endswith('-female') else 'm' if ident.endswith('-male') else None)
        slot['gmax'] = is_gmax
        spr, exact = sprite_file(f, p, female=fem)
        sspr, _ = sprite_file(f, p, shiny=True, female=fem)
        slot['spr'], slot['sspr'] = spr, sspr
        if not spr or not sspr:
            missing_art.append(ident + ('-f' if fem else ''))
            slot['artMissing'] = True
        if gender_split:
            slot['key'] = f"{ident}-{g}"
        else:
            slot['key'] = ident
        slots.append(slot)

# Has-Mega tag on base slots
megas = {pokemon[f['pokemon_id']]['species_id'] for f in forms if f['is_mega'] == '1' or '-primal' in f['identifier']}
for sl in slots:
    sl['hasMega'] = str(sl['sid']) in megas and sl['formType'] in ('base', 'form')

# Order within species: base first, then forms in PokeAPI order (already sorted), G-Max last.
order_idx = {}
for i, sl in enumerate(slots):
    order_idx[sl['key']] = i
slots.sort(key=lambda sl: (sl['sid'], sl['gmax'], order_idx[sl['key']]))

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'dex.json'), 'w') as fh:
    json.dump({'built': '2026-11-11', 'spriteBase': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/',
               'slots': slots, 'officialOnly': official_only}, fh, separators=(',', ':'), ensure_ascii=False)

print('slots', len(slots), 'non-gmax', sum(1 for s in slots if not s['gmax']), 'gmax', sum(1 for s in slots if s['gmax']))
print('official-only', len(official_only))
print('shiny-locked slots', sum(1 for s in slots if s['shinyLock']))
print('missing/approx art', len(missing_art), missing_art[:40])
print('review', [s['ident'] for s in slots + official_only if s.get('review')])
