"""Adds hand-built place graphs for Unova, Kalos, Alola, Galar, Hisui, Paldea and Lumiose to connections_manual.json.
Each line is "Place: neighbour; neighbour; ..." (links go both ways)."""
import json, sys

def parse(text):
    edges = set()
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        a, rest = line.split(':', 1)
        for b in rest.split(';'):
            b = b.strip()
            if b:
                edges.add(tuple(sorted((a.strip(), b))))
    return [list(e) for e in sorted(edges)]

UNOVA_COMMON = """
Nuvema Town: Route 1
Route 1: Accumula Town; Route 17
Accumula Town: Route 2
Route 2: Striaton City
Striaton City: Route 3; Dreamyard
Route 3: Wellspring Cave; Nacrene City
Nacrene City: Pinwheel Forest
Pinwheel Forest: Skyarrow Bridge
Skyarrow Bridge: Castelia City
Castelia City: Route 4; Liberty Garden; Game Freak HQ
Route 4: Desert Resort; Nimbasa City
Desert Resort: Relic Castle
Nimbasa City: Route 5; Route 16
Route 16: Lostlorn Forest; Marvelous Bridge
Marvelous Bridge: Route 15
Route 15: Black City / White Forest
Black City / White Forest: Route 14
Route 14: Abundant Shrine; Undella Town
Undella Town: Undella Bay; Route 13
Route 13: Giant Chasm; Lacunosa Town
Lacunosa Town: Route 12
Route 12: Village Bridge
Village Bridge: Route 11
Route 11: Opelucid City
Opelucid City: Route 9
Route 9: Tubeline Bridge
Tubeline Bridge: Route 8
Route 8: Icirrus City; Moor of Icirrus
Icirrus City: Twist Mountain; Dragonspiral Tower
Twist Mountain: Route 7
Route 7: Mistralton City; Celestial Tower
Mistralton City: Chargestone Cave
Chargestone Cave: Route 6
Route 6: Driftveil City; Mistralton Cave
Mistralton Cave: Guidance Chamber
Driftveil City: Driftveil Drawbridge; Cold Storage
Driftveil Drawbridge: Route 5
Route 17: Route 18
Route 18: P2 Laboratory
Route 17: P2 Laboratory
"""
UNOVA_BW = UNOVA_COMMON + """
Route 9: Challenger's Cave
Opelucid City: Route 10
Route 10: Victory Road
Victory Road: Trial Chamber; Pokémon League
Pokémon League: N's Castle
"""
UNOVA_B2W2 = UNOVA_COMMON + """
Aspertia City: Route 19
Route 19: Floccesy Town
Floccesy Town: Route 20
Route 20: Floccesy Ranch; Virbank City
Virbank City: Virbank Complex; Castelia City
Castelia City: Castelia Sewers
Castelia Sewers: Relic Passage
Relic Passage: Driftveil City; Relic Castle
Driftveil City: Clay Tunnel
Clay Tunnel: Twist Mountain; Mistralton Cave; Underground Ruins
Underground Ruins: Rocky Mountain Room; Iron Room; Glacier Room
Twist Mountain: Glacier Room
Undella Town: Reversal Mountain; Marine Tube
Reversal Mountain: Lentimas Town; Strange House
Marine Tube: Humilau City
Humilau City: Route 21; Route 22
Route 21: Seaside Cave
Seaside Cave: Undella Bay
Route 22: Giant Chasm; Route 23
Route 23: Victory Road
Victory Road: Pokémon League
Mistralton City: Nature Sanctuary (by plane)
"""

KALOS = """
Vaniville Town: Route 1
Route 1: Aquacorde Town
Aquacorde Town: Route 2
Route 2: Santalune Forest
Santalune Forest: Route 3
Route 3: Santalune City
Santalune City: Route 4; Route 22
Route 22: Victory Road
Route 4: Lumiose City
Lumiose City: Route 5; Route 13; Route 14; Route 16; Team Flare Secret HQ; Kiloude City (by train)
Kiloude City (by train): Friend Safari
Route 5: Camphrier Town
Camphrier Town: Route 6; Route 7
Route 6: Parfum Palace
Route 7: Connecting Cave
Connecting Cave: Route 8; Cyllage City
Route 8: Ambrette Town; Cyllage City
Ambrette Town: Route 9
Route 9: Glittering Cave
Cyllage City: Route 10
Route 10: Geosenge Town
Geosenge Town: Route 11
Route 11: Reflection Cave
Reflection Cave: Shalour City
Shalour City: Tower of Mastery; Route 12
Route 12: Coumarine City; Azure Bay
Azure Bay: Sea Spirit's Den
Coumarine City: Route 13
Route 14: Laverre City
Laverre City: Route 15
Route 15: Route 16; Dendemille Town; Lost Hotel
Route 16: Lost Hotel
Dendemille Town: Frost Cavern; Route 17
Route 17: Anistar City
Anistar City: Route 18
Route 18: Couriway Town; Terminus Cave
Couriway Town: Route 19
Route 19: Snowbelle City
Snowbelle City: Route 20; Route 21
Route 20: Pokémon Village
Pokémon Village: Unknown Dungeon
Route 21: Victory Road
Victory Road: Pokémon League
"""

ALOLA = """
Iki Town: Route 1; Mahalo Trail
Mahalo Trail: Ruins of Conflict
Route 1: Hau'oli City; Ten Carat Hill; Trainers' School; Melemele Sea
Hau'oli City: Melemele Sea; Route 2; Heahea City (ferry)
Ten Carat Hill: Melemele Sea
Route 2: Hau'oli Cemetery; Verdant Cavern; Big Wave Beach
Big Wave Beach: Sandy Cave
Verdant Cavern: Route 3
Route 3: Melemele Meadow
Melemele Meadow: Seaward Cave
Seaward Cave: Kala'e Bay
Heahea City (ferry): Heahea City
Heahea City: Route 4; Heahea Beach; Diglett's Tunnel; Aether Paradise; Malie City (ferry)
Route 4: Paniola Town
Paniola Town: Route 5; Route 6
Route 5: Brooklet Hill; Lush Jungle; Route 8
Route 6: Paniola Ranch; Royal Avenue; Heahea City
Royal Avenue: Route 7
Route 7: Wela Volcano Park; Dividing Peak Tunnel
Dividing Peak Tunnel: Route 8
Route 8: Hano Beach
Diglett's Tunnel: Route 9
Route 9: Konikoni City; Memorial Hill
Memorial Hill: Akala Outskirts
Akala Outskirts: Ruins of Life
Malie City (ferry): Malie City
Malie City: Malie Garden; Route 10; Route 11; Seafolk Village (ferry)
Route 10: Mount Hokulani
Route 11: Route 12
Route 12: Blush Mountain; Secluded Shore; Ula'ula Beach; Route 13
Route 13: Haina Desert; Tapu Village
Haina Desert: Ruins of Abundance
Tapu Village: Route 14; Route 15; Mount Lanakila
Mount Lanakila: Mount Lanakila Crater
Route 15: Route 16
Route 16: Ula'ula Meadow
Ula'ula Meadow: Route 17
Route 17: Po Town
Po Town: Team Rocket's Castle
Seafolk Village (ferry): Seafolk Village
Seafolk Village: Poni Wilds; Exeggutor Island
Poni Wilds: Ancient Poni Path
Ancient Poni Path: Vast Poni Canyon; Poni Grove; Poni Breaker Coast
Poni Breaker Coast: Ruins of Hope
Poni Grove: Poni Plains
Poni Plains: Poni Coast; Poni Meadow
Poni Meadow: Resolution Cave
Poni Coast: Poni Gauntlet
Poni Gauntlet: Battle Tree
Vast Poni Canyon: Altar of the Sunne; Altar of the Moone
Ultra Space Wilds: Ultra Space Wilds Cave World; Ultra Space Wilds Cliff World; Ultra Space Wilds Rocky World; Ultra Space Wilds Water World; Ultra Space; Ultra Megalopolis
"""

GALAR = """
Postwick: Route 1; Slumbering Weald
Route 1: Wedgehurst
Wedgehurst: Route 2; Meetup Spot; Fields of Honor (train); Freezington (train)
Meetup Spot: Rolling Fields
Rolling Fields: Dappled Grove; West Lake Axewell; East Lake Axewell; South Lake Miloch
Dappled Grove: Watchtower Ruins
Watchtower Ruins: West Lake Axewell
West Lake Axewell: East Lake Axewell; Motostoke
East Lake Axewell: Axew's Eye; Giant's Seat; Motostoke
South Lake Miloch: North Lake Miloch; Giant's Seat
Giant's Seat: North Lake Miloch; Motostoke
Motostoke: Route 3; Motostoke Outskirts
Route 3: Galar Mine
Galar Mine: Route 4
Route 4: Turffield
Turffield: Route 5
Route 5: Hulbury
Hulbury: Galar Mine No. 2
Galar Mine No. 2: Motostoke Outskirts
Motostoke Outskirts: Motostoke Riverbank; Bridge Field
Motostoke Riverbank: Bridge Field
Bridge Field: Stony Wilderness; Dusty Bowl
Stony Wilderness: Giant's Cap; Dusty Bowl
Giant's Cap: Lake of Outrage; Dusty Bowl
Dusty Bowl: Giant's Mirror; Hammerlocke Hills
Giant's Mirror: Hammerlocke Hills
Hammerlocke Hills: Hammerlocke
Hammerlocke: Route 6; Route 7; Route 10; Energy Plant Tower Summit
Route 6: Stow-on-Side
Stow-on-Side: Glimwood Tangle
Glimwood Tangle: Ballonlea
Route 7: Route 8
Route 8: Circhester
Circhester: Route 9
Route 9: Spikemuth
Route 10: Wyndon
Wyndon: Battle Tower
# Isle of Armor (Bulbapedia location pages)
Fields of Honor (train): Fields of Honor
Fields of Honor: Workout Sea; Loop Lagoon; Courageous Cavern; Soothing Wetlands; Master Dojo
Courageous Cavern: Challenge Beach; Loop Lagoon
Loop Lagoon: Stepping-Stone Sea
Soothing Wetlands: Brawlers' Cave; Challenge Beach; Forest of Focus
Brawlers' Cave: Training Lowlands; Challenge Road; Workout Sea
Training Lowlands: Warm-Up Tunnel; Challenge Road; Forest of Focus; Honeycalm Sea
Warm-Up Tunnel: Potbottom Desert
Workout Sea: Stepping-Stone Sea
Stepping-Stone Sea: Challenge Beach; Honeycalm Sea; Insular Sea
Honeycalm Sea: Challenge Beach; Insular Sea; Honeycalm Island
Challenge Beach: Forest of Focus
# Crown Tundra (Bulbapedia location pages)
Freezington (train): Freezington
Freezington: Slippery Slope; Frostpoint Field
Slippery Slope: Max Lair
Frostpoint Field: Giant's Bed
Giant's Bed: Snowslide Slope; Giant's Foot; Ballimere Lake; Old Cemetery; Iron Ruins; Rock Peak Ruins
Snowslide Slope: Tunnel to the Top; Iceberg Ruins
Tunnel to the Top: Path to the Peak
Path to the Peak: Crown Shrine
Giant's Foot: Roaring-Sea Caves
Roaring-Sea Caves: Frigid Sea; Three-Point Pass
Frigid Sea: Three-Point Pass
Three-Point Pass: Split-Decision Ruins
Ballimere Lake: Lakeside Cave; Dyna Tree Hill
"""

HISUI_PARTS = {
    'Obsidian Fieldlands': 'Floaro Gardens; Horseshoe Plains; Grueling Grove; Lake Verity; Verity Cavern; Obsidian Falls; Nature\'s Pantry; Tidewater Dam; Ramanas Island; Grandtree Arena',
    'Crimson Mirelands': 'Diamond Settlement; Bolderoll Slope; Scarlet Bog; Gapejaw Bog; Sludge Mound; Shrouded Ruins; Valor Cavern',
    'Cobalt Coastlands': 'Spring Path; Lunker\'s Lair; Sand\'s Reach; Deadwood Haunt; Firespit Island; Seaside Hollow',
    'Coronet Highlands': 'Temple of Sinnoh; Moonview Arena; Celestica Ruins; Lonely Spring; Ancient Quarry; Fabled Spring; Wayward Cave',
    'Alabaster Icelands': 'Snowfall Hot Spring; Heart\'s Crag; Icepeak Arena; Avalugg\'s Legacy; Arena\'s Approach; Bonechill Wastes; Whiteout Valley; Icebound Falls; Snowpoint Temple; Ice Column Chamber; Acuity Cavern',
}
HISUI = '\n'.join(f'{k}: {v}' for k, v in HISUI_PARTS.items()) + """
Jubilife Village: Obsidian Fieldlands; Crimson Mirelands; Cobalt Coastlands; Coronet Highlands; Alabaster Icelands
Spring Path: Turnback Cave
Firespit Island: Lava Dome Sanctum
"""

PALDEA = """
Cabo Poco: Poco Path; South Province (Area One)
Poco Path: Inlet Grotto; South Province (Area One); South Province (Area Four); South Paldean Sea
South Province (Area One): Los Platos; Mesagoza; South Province (Area Four); South Province (Area Five)
Mesagoza: Naranja Academy; Uva Academy; South Province (Area Two); South Province (Area Three)
South Province (Area Two): Cortondo; Pokémon League; South Province (Area Four); South Province (Area Six); West Province (Area One)
South Province (Area Four): South Province (Area Six); West Province (Area One); South Paldean Sea
South Province (Area Six): Alfornada; Alfornada Cavern; West Province (Area One); South Paldean Sea
South Province (Area Three): South Province (Area Five); East Province (Area One); Artazon
South Province (Area Five): Artazon
West Province (Area One): Asado Desert; West Province (Area Three); Segin Squad's Base; West Paldean Sea
Asado Desert: Cascarrafa
Cascarrafa: West Province (Area Two)
West Province (Area Two): Porto Marinada; West Province (Area Three); Casseroya Lake
West Province (Area Three): Medali; Casseroya Lake
Casseroya Lake: Socarrat Trail; Glaseado Mountain; North Province (Area Three); North Paldean Sea
Glaseado Mountain: Montenevera; Dalizapa Passage; North Province (Area One); North Province (Area Three)
Dalizapa Passage: East Province (Area Three)
North Province (Area One): North Province (Area Two); East Province (Area Three); Tagtree Thicket; North Paldean Sea
North Province (Area Two): East Province (Area Three); Caph Squad's Base
North Province (Area Three): Ruchbah Squad's Base
East Province (Area One): Artazon; East Province (Area Two); East Province (Area Three); Schedar Squad's Base; Levincia
East Province (Area Two): East Province (Area Three); Levincia; East Paldean Sea
East Province (Area Three): Tagtree Thicket; Zapapico; East Paldean Sea
Tagtree Thicket: Navi Squad's Base
Great Crater of Paldea: Area Zero
Area Zero: Area Zero Underdepths
# Kitakami (The Teal Mask)
Kitakami Road: Mossui Town; Apple Hills; Mossfell Confluence
Reveler's Road: Mossui Town; Kitakami Hall; Loyalty Plaza
Loyalty Plaza: Kitakami Hall
Oni Mountain: Mossui Town; Dreaded Den; Crystal Pool; Oni's Maw; Chilling Waterhead; Infernal Pass; Fellhorn Gorge
Fellhorn Gorge: Mossfell Confluence
Kitakami Wilds: Mossui Town; Wistful Fields; Timeless Woods; Paradise Barrens; Apple Hills
# Terarium (The Indigo Disk)
Central Plaza: Savanna Biome; Coastal Biome; Canyon Biome; Polar Biome; Terarium
Savanna Biome: Savanna Plaza
Coastal Biome: Coastal Plaza; Torchlit Labyrinth
Canyon Biome: Canyon Plaza; Chargestone Cavern
Polar Biome: Polar Plaza; Chargestone Cavern
"""

ZA = ['Centrico Plaza: Lumiose City; North Boulevard; South Boulevard; Vernal Avenue; Estival Avenue; Autumnal Avenue; Hibernal Avenue; Saison Canal']
ZA.append('Saison Canal: Saison Canalside')
for c, n in [('Vert', 9), ('Bleu', 9), ('Magenta', 9), ('Rouge', 8), ('Jaune', 12)]:
    hub = f'{c} District (sectors)'
    ZA.append(f'{hub}: ' + '; '.join([f'{c} Sector {i}' for i in range(1, n + 1)] + [f'{c} Street', f'{c} Plaza']))
    ZA.append(f'{c} Plaza: Centrico Plaza')
ZA = '\n'.join(ZA)

m = json.load(open(sys.argv[1]))
src = 'Hand-built from Bulbapedia and Serebii location pages'
new = {
    'unova_bw': (UNOVA_BW, {'Black City': 'Black City / White Forest', 'White Forest': 'Black City / White Forest', 'Game Freak HQ 1F': 'Game Freak HQ'}, ['black', 'white'], src + '.'),
    'unova_b2w2': (UNOVA_B2W2, {'Black City': 'Black City / White Forest', 'White Forest': 'Black City / White Forest', 'Victory Road 2': 'Victory Road', 'Nature Sanctuary': 'Nature Sanctuary (by plane)'}, ['black2', 'white2'], src + '.'),
    'kalos': (KALOS, {"Sea Spirit’s Den": "Sea Spirit's Den"}, ['x', 'y'], src + '.'),
    'alola': (ALOLA, {'Diglett’s Tunnel': "Diglett's Tunnel", 'Hau’oli Cemetery': "Hau'oli Cemetery", 'Kala’e Bay': "Kala'e Bay", 'Ula’ula Meadow': "Ula'ula Meadow", 'Trainers’ School': "Trainers' School"},
              ['sun', 'moon', 'ultrasun', 'ultramoon'], src + '. Islands are linked by their ferry ports.'),
    'galar': (GALAR, {}, ['sword', 'shield'], src + '. Wild Area zones link to the zones they border; the DLC islands link to Wedgehurst by train.'),
    'hisui': (HISUI, {}, ['legendsarceus'], src + '. Each spot links to its area, and every area links to Jubilife Village.'),
    'paldea': (PALDEA, {}, ['scarlet', 'violet'], src + '. Provinces link to the areas they border. Kitakami’s open fields are grouped around Kitakami Wilds.'),
    'lumiose': (ZA, {f'{c} District': f'{c} District (sectors)' for c in ['Vert', 'Bleu', 'Magenta', 'Rouge', 'Jaune']}, ['legendsza'],
                src + '. Sectors are grouped by district; Wild Zones and buildings aren’t placed yet.'),
}
for gid, (text, aliases, games, note) in new.items():
    m['graphs'][gid] = {'edges': parse(text), 'aliases': aliases}
    for g in games:
        m['games'][g] = gid
    m['sources'][gid] = note
m['sources']['sinnoh'] = "Hand-built; cave and building links checked against Platinum's map data (pret/pokeplatinum)."
for s in ['Kalos Berry Fields', 'Alola Berry Fields', 'Poké Pelago', 'Kalos (Roaming)', 'Roaming Galar Wild Areas', 'Roaming the Crown Tundra',
          'Roaming the Isle of Armor', 'Random caves across the Isle of Armor', 'In-game trade', '——————', 'Tera Raid Battles', 'Hyperspace',
          'Team Flare Secret HQ (Unova)']:
    if s not in m['skip']:
        m['skip'].append(s)
json.dump(m, open(sys.argv[1], 'w'), indent=1, ensure_ascii=False)
print({k: len(v['edges']) for k, v in m['graphs'].items()})
