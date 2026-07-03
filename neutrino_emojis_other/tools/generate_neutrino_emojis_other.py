#!/usr/bin/env python3
"""
Generate the neutrino_emojis_other asset package.
Original deterministic SVG/PNG emoji-style icons. No third-party artwork.
SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import math
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

try:
    import pycountry
except Exception:
    pycountry = None

PKG = "neutrino_emojis_other"
CANVAS = 128
SIZES = [16, 32, 64, 128]

THEMES: Dict[str, Dict[str, str]] = {
    "classic_yellow": {
        "primary": "#FFD85A", "secondary": "#F4B94A", "accent": "#E94B66", "accent2": "#FFFFFF",
        "outline": "#3A2C20", "feature": "#2D2118", "skin": "#F2C6A0", "skin2": "#DFA06E",
        "green": "#65B95A", "blue": "#56A8E8", "red": "#E85B4B", "purple": "#9C70E8", "orange": "#F27B35",
        "metal": "#8E9BAA", "brown": "#8B5A2B", "white": "#FFF8E7", "dark": "#1A1613", "bg": "#FFFFFF",
    },
    "neutrino_blue": {
        "primary": "#83D7FF", "secondary": "#43A6E8", "accent": "#00E0FF", "accent2": "#F4FEFF",
        "outline": "#13314A", "feature": "#0B2032", "skin": "#95DAFF", "skin2": "#56B5E8",
        "green": "#62DFA3", "blue": "#317CFF", "red": "#FF6B7D", "purple": "#8D81FF", "orange": "#FFAF55",
        "metal": "#6D8FAA", "brown": "#557A9A", "white": "#F6FBFF", "dark": "#092033", "bg": "#F6FBFF",
    },
    "graphite_dark": {
        "primary": "#515E6B", "secondary": "#303943", "accent": "#9FD6FF", "accent2": "#0D1218",
        "outline": "#E8EDF2", "feature": "#F5F7FA", "skin": "#8B949E", "skin2": "#5F6B76",
        "green": "#89D18B", "blue": "#8DC7FF", "red": "#FF8B8B", "purple": "#C0A8FF", "orange": "#FFBD7B",
        "metal": "#B8C2CC", "brown": "#A68A73", "white": "#F7F7F7", "dark": "#151A20", "bg": "#151A20",
    },
    "forest_mint": {
        "primary": "#A8F0BF", "secondary": "#58C983", "accent": "#1FCE7A", "accent2": "#F7FFF8",
        "outline": "#163B24", "feature": "#0F2A19", "skin": "#C7E8BA", "skin2": "#8ABF7D",
        "green": "#2EA85F", "blue": "#66B8D9", "red": "#E96B5D", "purple": "#9B7DE0", "orange": "#F0A64A",
        "metal": "#6C9C7C", "brown": "#725A32", "white": "#FAFFFB", "dark": "#0F2417", "bg": "#FAFFFB",
    },
    "royal_purple": {
        "primary": "#C7A8FF", "secondary": "#8B68D8", "accent": "#FF72D2", "accent2": "#FFF8FE",
        "outline": "#2C1E4A", "feature": "#211536", "skin": "#D1B2F0", "skin2": "#A075D8",
        "green": "#65D980", "blue": "#7DB2FF", "red": "#FF7B8F", "purple": "#A15CFF", "orange": "#FFB55F",
        "metal": "#A89DBB", "brown": "#8E6A55", "white": "#FCFAFF", "dark": "#1A102B", "bg": "#FCFAFF",
    },
    "solar_gold": {
        "primary": "#FFC647", "secondary": "#E88A24", "accent": "#FF6A00", "accent2": "#FFF8E7",
        "outline": "#4B2A08", "feature": "#2C1703", "skin": "#F4BC73", "skin2": "#D9913E",
        "green": "#7FC14D", "blue": "#54A8E8", "red": "#E75B42", "purple": "#A06AE9", "orange": "#F38A1E",
        "metal": "#AA8860", "brown": "#8A531F", "white": "#FFFDF5", "dark": "#2C1703", "bg": "#FFFDF5",
    },
    "candy_pink": {
        "primary": "#FFB7D5", "secondary": "#F079B1", "accent": "#FF2E9E", "accent2": "#FFF7FB",
        "outline": "#5A1B37", "feature": "#341020", "skin": "#FFC2CC", "skin2": "#E48B9D",
        "green": "#73D97A", "blue": "#62C2FF", "red": "#F04E70", "purple": "#B574FF", "orange": "#FFA160",
        "metal": "#BB8AA4", "brown": "#945C67", "white": "#FFF8FC", "dark": "#341020", "bg": "#FFF8FC",
    },
    "aqua_cyan": {
        "primary": "#6FF2E5", "secondary": "#27BFB6", "accent": "#009DFF", "accent2": "#F4FFFF",
        "outline": "#063E3D", "feature": "#052928", "skin": "#8CE9DE", "skin2": "#48C7BD",
        "green": "#33D47A", "blue": "#287DFF", "red": "#FF6F91", "purple": "#8678FF", "orange": "#FFB45C",
        "metal": "#5B9BA0", "brown": "#5A827E", "white": "#F5FFFF", "dark": "#052928", "bg": "#F5FFFF",
    },
    "lava_orange": {
        "primary": "#FF8759", "secondary": "#D94B2E", "accent": "#FFD34D", "accent2": "#FFF5ED",
        "outline": "#4A140A", "feature": "#2D0B05", "skin": "#E8A26C", "skin2": "#C96E42",
        "green": "#81CA55", "blue": "#50A6E8", "red": "#E43B32", "purple": "#A06AE9", "orange": "#FF6B2E",
        "metal": "#A47C6A", "brown": "#874722", "white": "#FFF8F3", "dark": "#2D0B05", "bg": "#FFF8F3",
    },
    "mono_ink": {
        "primary": "#F2F2F2", "secondary": "#C7C7C7", "accent": "#444444", "accent2": "#FFFFFF",
        "outline": "#161616", "feature": "#111111", "skin": "#E0E0E0", "skin2": "#B8B8B8",
        "green": "#BEBEBE", "blue": "#A8A8A8", "red": "#777777", "purple": "#9A9A9A", "orange": "#D0D0D0",
        "metal": "#888888", "brown": "#9A9A9A", "white": "#FFFFFF", "dark": "#111111", "bg": "#FFFFFF",
    },
}

CSS_VARS = {k: f"var(--nt-{k})" for k in next(iter(THEMES.values())).keys()}

CATEGORY_COUNTS: Dict[str, int] = {
    "things_tools": 650,
    "tech_office": 500,
    "vehicles_land": 500,
    "vehicles_air_space": 400,
    "vehicles_water_rail": 300,
    "country_flags": 550,
    "toys_games": 600,
    "fruits": 300,
    "vegetables": 300,
    "food_drink": 300,
    "animals_mammals": 650,
    "birds": 400,
    "aquatic_animals": 400,
    "reptiles_amphibians_bugs": 450,
    "hands_gestures": 600,
    "body_parts": 300,
    "people_family_gender": 500,
    "activities": 500,
    "sports_games": 600,
    "military_defense_symbolic": 300,
    "nature_weather_space": 500,
    "symbols_status": 400,
}

assert sum(CATEGORY_COUNTS.values()) == 10000

STYLE_NAMES = [
    "plain", "sparkle", "badge", "stripe", "dot", "ring", "shadow", "orbit", "leaf", "star", "heart", "bolt",
    "check", "plus", "minus", "alert", "music", "motion", "sleep", "glow", "double", "tiny", "round", "square",
]

ITEMS: Dict[str, List[str]] = {
    "things_tools": "backpack suitcase key lock unlock bell hourglass clock watch lamp candle flashlight book notebook scroll map compass magnet hammer wrench screwdriver pliers saw axe shovel pickaxe broom brush umbrella glasses sunglasses crown ring gem coin wallet ticket tag gift balloon mail envelope package calendar pin pushpin paperclip scissors ruler pencil pen paintbrush palette microphone speaker headphone radio camera telescope microscope test_tube beaker thread yarn needle button zipper rope chain anchor gear cog battery plug switch bulb fan thermometer bucket basket soap sponge toothbrush mirror comb perfume vase pot toolbox ladder door window bed chair table sofa toilet shower sink bathtub towel".split(),
    "tech_office": "desktop laptop tablet phone smartphone keyboard mouse trackpad monitor server printer scanner router satellite dish usb chip memory card sim card database cloud floppy disk hard_drive cd dvd joystick calculator cash_register projector folder file document clipboard chart graph newspaper inbox outbox paper stack paper plane stapler tape dispenser binder briefcase safe lockbox pen_tablet webcam vr_headset smartwatch console terminal code brackets bug shield firewall wifi bluetooth antenna robot drone controller".split(),
    "vehicles_land": "car taxi bus minibus truck pickup van ambulance fire_engine police_car tractor bicycle motorcycle scooter skateboard roller_skate wheelchair stroller rickshaw tuk_tuk camper caravan jeep suv race_car formula_car bulldozer excavator crane forklift roadster limousine snowmobile sled horse_cart delivery_van tram_train metro_train streetcar monorail cable_car mountain_railway".split(),
    "vehicles_air_space": "airplane airplane_takeoff airplane_landing jet propeller_plane helicopter gyrocopter hot_air_balloon parachute glider hang_glider drone quadcopter rocket capsule satellite ufo shuttle space_station comet meteor airship blimp paper_airplane kite airport_tower radar dish orbit module rover lander probe".split(),
    "vehicles_water_rail": "ship boat sailboat speedboat ferry canoe kayak raft submarine anchor buoy lighthouse train locomotive metro tram monorail bullet_train station rail_bridge cable_car gondola tram_stop container_ship cargo_ship tugboat fishing_boat lifeboat yacht harbor crane rail_signal ticket_gate".split(),
    "toys_games": "teddy_bear doll robot_toy yo_yo kite spinning_top jack_in_box rocking_horse toy_car toy_train toy_plane toy_boat blocks puzzle_piece jigsaw dice domino card chess_pawn chess_rook chess_knight chess_bishop chess_queen chess_king checker go_stone mahjong_tile game_controller joystick arcade_pinball bowling_pin marble ball balloon bubble_wand frisbee hula_hoop jump_rope slinky pinwheel toy_drum toy_trumpet toy_guitar stuffed_cat stuffed_dog action_figure building_block cube pyramid hoop ring toss sand_bucket shovel beach_ball water_gun toy_blaster".split(),
    "fruits": "apple green_apple pear peach orange tangerine lemon lime banana mango pineapple coconut kiwi strawberry blueberry cherry grapes melon watermelon papaya guava fig pomegranate avocado plum apricot passionfruit lychee rambutan dragonfruit starfruit cranberry raspberry blackberry currant date olive tomato cacao pod durian jackfruit breadfruit plantain persimmon nectarine kumquat grapefruit pomelo ugli_fruit quince gooseberry".split(),
    "vegetables": "carrot broccoli cucumber lettuce cabbage cauliflower corn potato sweet_potato onion garlic pepper chili eggplant mushroom pumpkin squash zucchini pea_pod beans celery asparagus spinach kale radish beet turnip leek artichoke okra ginger turmeric yam water_chestnut lotus_root bamboo_shoot sprout herb basil parsley mint rosemary thyme seaweed pepper_green pepper_red tomato_veg olive_veg bok_choy fennel chard endive".split(),
    "food_drink": "bread baguette croissant pretzel bagel pancake waffle cheese egg fried_egg bacon meat fish_cake sushi ramen noodles rice curry dumpling taco burrito sandwich pizza burger fries hotdog salad soup stew bento cake cupcake pie cookie donut chocolate candy lollipop icecream popsicle honey tea coffee milk juice smoothie soda water bottle glass mug cup teapot kettle wine_glass mocktail bowl plate spoon fork knife chopsticks salt pepper pot pan jar can soup_can cereal".split(),
    "animals_mammals": "cat dog mouse hamster rabbit fox bear panda koala tiger lion cow pig boar frog monkey gorilla orangutan horse zebra deer moose bison camel llama giraffe elephant rhino hippo kangaroo sloth otter skunk badger raccoon squirrel chipmunk hedgehog bat wolf goat sheep ram donkey ox buffalo leopard cheetah panther yak seal dolphin_whale polar_bear red_panda anteater armadillo beaver mole meerkat lemur baboon alpaca pony puppy kitten cub".split(),
    "birds": "bird chick baby_chick hatching_chick rooster chicken turkey duck goose swan peacock parrot dove eagle owl penguin flamingo crane stork heron sparrow finch robin bluebird crow raven magpie seagull pelican toucan kiwi ostrich emu hummingbird woodpecker falcon hawk canary cardinal pheasant quail pigeon condor albatross kingfisher hornbill puffin lyrebird".split(),
    "aquatic_animals": "fish tropical_fish blowfish shark whale dolphin seal otter crab lobster shrimp squid octopus jellyfish starfish coral shell clam oyster snail sea_turtle manta_ray stingray eel seahorse sea_lion walrus narwhal swordfish tuna salmon carp koi angelfish pufferfish goldfish anchovy sardine sea_slug sea_urchin anemone sponge plankton krill barnacle horseshoe_crab".split(),
    "reptiles_amphibians_bugs": "snake lizard gecko iguana crocodile alligator turtle tortoise frog toad salamander newt chameleon dinosaur sauropod trex dragon worm butterfly moth bee bumblebee beetle ladybug ant cricket grasshopper spider scorpion mosquito fly cockroach centipede millipede caterpillar firefly dragonfly damselfly mantis stick_insect snail_slug tick flea aphid cicada locust termite".split(),
    "hands_gestures": "wave raised_hand palm_stop open_hands praying_hands clapping handshake thumbs_up thumbs_down ok_hand victory_hand crossed_fingers love_you sign_of_horns fist_oncoming raised_fist left_fist right_fist point_left point_right point_up point_down index_up writing_hand pinch_hand pinched_fingers heart_hands palms_up together_hands salute snap_fingers counting_one counting_two counting_three counting_four high_five hand_with_pen hand_with_wrench hand_with_star hand_with_heart hand_wave_motion".split(),
    "body_parts": "eye eyes ear nose mouth lips tooth tongue brain heart lungs bone arm biceps elbow hand finger leg knee foot footprints torso head hair beard moustache face_profile neck shoulder spine stomach liver kidney muscle skin blood_drop nerve voice ear_listening eye_wink mouth_smile mouth_frown nose_scent hand_touch body_stretch body_twist".split(),
    "people_family_gender": "person man woman child baby adult older_person grandfather grandmother boy girl parent family couple friends worker artist scientist teacher doctor nurse chef farmer mechanic pilot astronaut firefighter police officer guard judge student singer dancer runner cyclist swimmer skier gamer coder manager builder sailor explorer wizard fairy superhero male_symbol female_symbol nonbinary_symbol trans_symbol gender_symbols family_two family_three family_four".split(),
    "activities": "running walking dancing yoga meditation climbing hiking camping cooking reading writing painting drawing singing music_playing drumming guitar_playing piano_playing camera_photo filming flying_kite gardening fishing sailing surfing diving swimming skating skiing snowboarding cycling lifting archery bowling juggling shopping traveling typing coding repairing building cleaning sleeping bathing cheering waving presenting teaching debating volunteering picnic party celebrating birthday wedding graduation voting recycling exploring stargazing".split(),
    "sports_games": "soccer_ball basketball football baseball softball tennis_ball volleyball rugby_ball cricket_ball hockey_puck golf_ball bowling_ball ping_pong billiards dart target archery_bow fishing_pole cricket_bat baseball_bat tennis_racket badminton_racket hockey_stick lacrosse_stick ski snowboard skateboard surfboard boxing_glove martial_arts_uniform medal trophy goal_net scoreboard whistle stopwatch finish_flag chess_board chess_pawn card_spade card_heart card_diamond card_club dice domino puzzle_esport controller joystick horseshoe frisbee curling_stone running_shoe bicycle_wheel kayak_paddle".split(),
    "military_defense_symbolic": "shield helmet service_star medal ribbon badge target radar radio compass binoculars map_coded boot glove generic_blaster toy_blaster signal_flag bunker_tent field_pack canteen sandbag barrier watchtower fort wall gate safety_cone first_aid_kit rescue_rope flare_symbol nonfunctional_rounds ammo_crate training_target drone_symbol armored_vehicle_symbol patrol_boat_symbol aircraft_symbol naval_anchor peace_shield dove_shield warning_shield tactical_grid decoy_marker whistle checkpoint badge_rank chevron_rank star_rank unit_patch".split(),
    "nature_weather_space": "sun moon crescent moon_star cloud rain_cloud thunder_cloud snow_cloud fog tornado cyclone umbrella_rain snowflake droplet wave fire volcano mountain hill island desert cactus tree evergreen palm_tree deciduous_tree leaf maple_leaf flower rose tulip sunflower blossom seedling herb mushroom planet saturn earth globe comet star constellation galaxy nebula meteor rainbow wind thermometer hot cold sunrise sunset night_sky river lake waterfall rock crystal shell sand dune cave valley meadow forest".split(),
    "symbols_status": "check cross plus minus info question exclamation warning stop play pause record rewind fast_forward up down left right arrow_up arrow_down arrow_left arrow_right refresh repeat shuffle lock unlock key heart star sparkle music note bell clock hourglass calendar map_pin location wifi battery power search home settings menu more upload download cloud_sync link unlink bookmark flag tag filter sort code terminal database fire water leaf recycle peace atom orbit neutrino eye_visibility hidden mail chat call video microphone muted loud quiet".split(),
}

COUNTRY_FALLBACK = [
    ("US", "United States"), ("IN", "India"), ("GB", "United Kingdom"), ("CA", "Canada"), ("AU", "Australia"),
    ("DE", "Germany"), ("FR", "France"), ("JP", "Japan"), ("CN", "China"), ("BR", "Brazil"), ("ZA", "South Africa"),
]

@dataclass(frozen=True)
class Spec:
    index: int
    uid: str
    name: str
    display_name: str
    category: str
    subcategory: str
    kind: str
    item: str
    variant: int
    style: str
    label: str
    description: str
    tags: Tuple[str, ...]


def slugify(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch.isalnum(): out.append(ch)
        elif ch in " _-.+/": out.append("_")
    slug = "".join(out).strip("_")
    while "__" in slug: slug = slug.replace("__", "_")
    return slug or "icon"


def abbrev(item: str, maxlen: int = 3) -> str:
    words = [w for w in item.replace("-", "_").split("_") if w]
    if not words: return "?"
    if len(words) == 1:
        w = words[0]
        return (w[:maxlen]).upper()
    return "".join(w[0] for w in words[:maxlen]).upper()


def hnum(*parts: object) -> int:
    h = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def pick(seq: Sequence[str], seed: int) -> str:
    return seq[seed % len(seq)]


def build_specs(limit: Optional[int] = None) -> List[Spec]:
    specs: List[Spec] = []
    idx = 0
    for category, count in CATEGORY_COUNTS.items():
        if category == "country_flags":
            if pycountry:
                countries = sorted([(c.alpha_2, c.name) for c in pycountry.countries], key=lambda x: x[0])
            else:
                countries = COUNTRY_FALLBACK
            styles = ["waving", "roundel", "pennant", "badge"]
            for j in range(count):
                code, country = countries[j % len(countries)]
                var = j // len(countries)
                style = styles[(j // len(countries)) % len(styles)]
                idx += 1
                name = f"flag_{code.lower()}_{style}_{var:02d}"
                display = f"{country} flag {style} {var}"
                specs.append(Spec(idx, f"NEO{idx:05d}", name, display, category, "country_code_flags", "flag", code.lower(), var, style, code.upper(), f"Original stylized country-code flag icon for {country}; not imported from official flag artwork.", ("flag", "country", code.upper(), country)))
                if limit and len(specs) >= limit: return specs
            continue
        items = ITEMS[category]
        for j in range(count):
            item = items[j % len(items)]
            variant = j // len(items)
            style = STYLE_NAMES[(j + len(category)) % len(STYLE_NAMES)]
            idx += 1
            name = f"{category}_{slugify(item)}_{style}_{variant:02d}"
            label = abbrev(item, 3)
            display = f"{item.replace('_', ' ')} {style} {variant}"
            description = f"Original Neutrino {category.replace('_', ' ')} emoji icon: {item.replace('_', ' ')} with {style} styling."
            specs.append(Spec(idx, f"NEO{idx:05d}", name, display, category, category, category, item, variant, style, label, description, tuple(dict.fromkeys((category, item, style, "neutrino", "emoji")))))
            if limit and len(specs) >= limit: return specs
    return specs


# Geometry helpers
Point = Tuple[float, float]
Color = str

@dataclass
class Op:
    kind: str
    args: Tuple
    fill: Optional[Color] = None
    stroke: Optional[Color] = None
    width: float = 1.0
    opacity: float = 1.0
    radius: float = 0.0
    text: str = ""
    font_size: float = 12.0

class Icon:
    def __init__(self, title: str = "", desc: str = ""):
        self.title = title
        self.desc = desc
        self.ops: List[Op] = []
    def ellipse(self, box, fill, stroke=None, width=1, opacity=1): self.ops.append(Op("ellipse", tuple(box), fill, stroke, width, opacity))
    def rect(self, box, fill, stroke=None, width=1, radius=0, opacity=1): self.ops.append(Op("rect", tuple(box), fill, stroke, width, opacity, radius))
    def polygon(self, points, fill, stroke=None, width=1, opacity=1): self.ops.append(Op("polygon", tuple(tuple(p) for p in points), fill, stroke, width, opacity))
    def line(self, points, stroke, width=4, opacity=1): self.ops.append(Op("line", tuple(tuple(p) for p in points), None, stroke, width, opacity))
    def qcurve(self, p0, pc, p1, stroke, width=4, fill=None, opacity=1): self.ops.append(Op("qcurve", (tuple(p0), tuple(pc), tuple(p1)), fill, stroke, width, opacity))
    def text(self, text, x, y, size, fill, opacity=1): self.ops.append(Op("text", (x, y), fill, None, 1, opacity, 0, str(text), size))


def color_key(c: Optional[str], theme: Dict[str, str]) -> Optional[Tuple[int, int, int, int]]:
    if c is None: return None
    h = theme.get(c, c)
    if h == "none": return None
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def svg_color(c: Optional[str], theme: Optional[Dict[str, str]] = None) -> str:
    if c is None: return "none"
    if c in CSS_VARS:
        return theme[c] if theme else CSS_VARS[c]
    return c


def bezier_points(p0: Point, pc: Point, p1: Point, n: int = 20) -> List[Point]:
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * pc[0] + t ** 2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * pc[1] + t ** 2 * p1[1]
        pts.append((x, y))
    return pts


def scale_box(box, scale: float) -> Tuple[int, int, int, int]: return tuple(int(round(v * scale)) for v in box)
def scale_pts(points, scale: float) -> List[Tuple[int, int]]: return [(int(round(x * scale)), int(round(y * scale))) for x, y in points]

_FONT_CACHE: Dict[int, ImageFont.FreeTypeFont] = {}

def get_font(px: int):
    px = max(5, int(px))
    if px in _FONT_CACHE: return _FONT_CACHE[px]
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            _FONT_CACHE[px] = ImageFont.truetype(p, px)
            return _FONT_CACHE[px]
    _FONT_CACHE[px] = ImageFont.load_default()
    return _FONT_CACHE[px]


def render_icon(icon: Icon, theme: Dict[str, str], size: int) -> Image.Image:
    # Render at 128 for compact crisp icons, then resample to target.
    base = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    for op in icon.ops:
        fill = color_key(op.fill, theme)
        stroke = color_key(op.stroke, theme)
        if op.opacity < 1:
            if fill: fill = (*fill[:3], int(255 * op.opacity))
            if stroke: stroke = (*stroke[:3], int(255 * op.opacity))
        if op.kind == "ellipse":
            d.ellipse(op.args, fill=fill, outline=stroke, width=max(1, int(round(op.width))))
        elif op.kind == "rect":
            if op.radius:
                d.rounded_rectangle(op.args, radius=int(round(op.radius)), fill=fill, outline=stroke, width=max(1, int(round(op.width))))
            else:
                d.rectangle(op.args, fill=fill, outline=stroke, width=max(1, int(round(op.width))))
        elif op.kind == "polygon":
            pts = list(op.args)
            d.polygon(pts, fill=fill)
            if stroke:
                d.line(pts + [pts[0]], fill=stroke, width=max(1, int(round(op.width))), joint="curve")
        elif op.kind == "line":
            d.line(list(op.args), fill=stroke, width=max(1, int(round(op.width))), joint="curve")
        elif op.kind == "qcurve":
            p0, pc, p1 = op.args
            pts = bezier_points(p0, pc, p1, 24)
            if op.fill:
                d.polygon(pts, fill=fill)
            if stroke:
                d.line(pts, fill=stroke, width=max(1, int(round(op.width))), joint="curve")
        elif op.kind == "text":
            x, y = op.args
            text = op.text
            font = get_font(int(round(op.font_size)))
            bb = d.textbbox((0, 0), text, font=font)
            tx = int(round(x - (bb[2] - bb[0]) / 2))
            ty = int(round(y - (bb[3] - bb[1]) / 2 - 1))
            d.text((tx, ty), text, fill=fill, font=font)
    if size != CANVAS:
        base = base.resize((size, size), Image.Resampling.LANCZOS)
    return base


def svg_icon(icon: Icon, theme: Optional[Dict[str, str]] = None) -> str:
    parts: List[str] = []
    if theme is None:
        default = THEMES["classic_yellow"]
        vars_css = ";".join(f"--nt-{k}:{v}" for k, v in default.items())
        parts.append(f"<style>:root{{{vars_css}}} text{{font-family:Arial,DejaVu Sans,sans-serif;font-weight:700}}</style>")
    else:
        parts.append("<style>text{font-family:Arial,DejaVu Sans,sans-serif;font-weight:700}</style>")
    for op in icon.ops:
        fill = svg_color(op.fill, theme)
        stroke = svg_color(op.stroke, theme)
        opacity = f' opacity="{op.opacity:.3g}"' if op.opacity < 1 else ""
        if op.kind == "ellipse":
            x0, y0, x1, y1 = op.args; cx = (x0 + x1) / 2; cy = (y0 + y1) / 2; rx = (x1 - x0) / 2; ry = (y1 - y0) / 2
            parts.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{op.width:.2f}"' if op.stroke else "") + opacity + "/>")
        elif op.kind == "rect":
            x0, y0, x1, y1 = op.args; rx = f' rx="{op.radius:.2f}" ry="{op.radius:.2f}"' if op.radius else ""
            parts.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}"{rx} fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{op.width:.2f}"' if op.stroke else "") + opacity + "/>")
        elif op.kind == "polygon":
            pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in op.args)
            parts.append(f'<polygon points="{pts}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{op.width:.2f}" stroke-linejoin="round"' if op.stroke else "") + opacity + "/>")
        elif op.kind == "line":
            pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in op.args)
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{op.width:.2f}" stroke-linecap="round" stroke-linejoin="round"' + opacity + "/>")
        elif op.kind == "qcurve":
            p0, pc, p1 = op.args
            parts.append(f'<path d="M {p0[0]:.2f} {p0[1]:.2f} Q {pc[0]:.2f} {pc[1]:.2f} {p1[0]:.2f} {p1[1]:.2f}" fill="{fill if op.fill else "none"}" stroke="{stroke}" stroke-width="{op.width:.2f}" stroke-linecap="round" stroke-linejoin="round"' + opacity + "/>")
        elif op.kind == "text":
            x, y = op.args
            parts.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{op.font_size:.2f}" text-anchor="middle" dominant-baseline="central" fill="{fill}"' + opacity + f'>{html.escape(op.text)}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128" role="img" aria-labelledby="title desc">\n<title id="title">{html.escape(icon.title)}</title>\n<desc id="desc">{html.escape(icon.desc)}</desc>\n' + "\n".join(parts) + "\n</svg>\n"

# Shape helpers

def regular(cx, cy, r, n, rot=-90) -> List[Point]:
    return [(cx + r * math.cos(math.radians(rot + 360 * i / n)), cy + r * math.sin(math.radians(rot + 360 * i / n))) for i in range(n)]


def star(cx, cy, r1, r2, n=5, rot=-90) -> List[Point]:
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def heart(cx, cy, s) -> List[Point]:
    pts = []
    for i in range(36):
        t = 2 * math.pi * i / 36
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 32, cy + y * s / 32))
    return pts


def drop(cx, cy, s) -> List[Point]:
    return [(cx, cy - s), (cx + .70 * s, cy - .05 * s), (cx + .45 * s, cy + .75 * s), (cx, cy + s), (cx - .45 * s, cy + .75 * s), (cx - .70 * s, cy - .05 * s)]


def add_badge(icon: Icon, spec: Spec, symbol: Optional[str] = None, color: str = "accent") -> None:
    style = spec.style
    if style in {"plain", "shadow"}: return
    if symbol is None:
        m = {
            "sparkle": "✦", "badge": spec.label[:2], "stripe": "≋", "dot": "•", "ring": "○", "orbit": "⟲", "leaf": "⌁",
            "star": "★", "heart": "♥", "bolt": "⚡", "check": "✓", "plus": "+", "minus": "−", "alert": "!", "music": "♪",
            "motion": "›", "sleep": "Z", "glow": "✧", "double": "2", "tiny": "·", "round": "●", "square": "■",
        }
        symbol = m.get(style, "•")
    icon.ellipse((91, 90, 124, 123), "accent2", "outline", 3)
    icon.ellipse((96, 95, 119, 118), color, None)
    icon.text(symbol, 107.5, 106.5, 16 if len(symbol) <= 2 else 12, "accent2")


def add_shadow(icon: Icon):
    icon.ellipse((19, 92, 109, 120), "dark", None, opacity=0.12)


def base_disc(icon: Icon, fill="primary"):
    icon.ellipse((16, 14, 112, 110), fill, "outline", 5)
    icon.ellipse((29, 24, 74, 44), "white", None, opacity=0.26)

# Category drawing functions

def draw_thing(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 8
    if mode == 0:  # bag/package
        icon.rect((30, 37, 98, 104), "primary", "outline", 5, 12)
        icon.qcurve((45, 40), (64, 15), (83, 40), "outline", 5)
        icon.rect((40, 55, 88, 81), "secondary", None, radius=8)
        icon.text(spec.label[:3], 64, 68, 18, "feature")
    elif mode == 1:  # key/tool
        icon.ellipse((23, 45, 55, 77), "secondary", "outline", 5)
        icon.ellipse((33, 55, 45, 67), "white", "outline", 2)
        icon.line([(53, 61), (102, 61)], "outline", 9)
        icon.line([(79, 61), (79, 76), (91, 76)], "outline", 6)
        icon.ellipse((88, 90, 114, 116), "accent", "outline", 4)
        icon.text(spec.label[:2], 101, 102, 12, "accent2")
    elif mode == 2:  # book/document
        icon.rect((26, 22, 94, 104), "primary", "outline", 5, 8)
        icon.rect((36, 29, 104, 110), "white", "outline", 5, 8)
        icon.line([(47, 48), (91, 48)], "secondary", 4)
        icon.line([(47, 62), (91, 62)], "secondary", 4)
        icon.line([(47, 76), (82, 76)], "secondary", 4)
        icon.text(spec.label[:2], 70, 94, 16, "accent")
    elif mode == 3:  # lamp/bulb
        icon.ellipse((43, 22, 86, 65), "primary", "outline", 5)
        icon.rect((51, 63, 78, 78), "secondary", "outline", 4, 5)
        icon.line([(64, 78), (64, 103)], "outline", 6)
        icon.rect((39, 99, 89, 112), "metal", "outline", 4, 6)
        icon.text(spec.label[:2], 64, 50, 14, "feature")
    elif mode == 4:  # gift/box
        icon.rect((27, 44, 101, 105), "primary", "outline", 5, 10)
        icon.rect((57, 44, 71, 105), "accent", None)
        icon.rect((27, 62, 101, 76), "accent", None)
        icon.qcurve((47, 42), (42, 22), (63, 44), "outline", 4, fill=None)
        icon.qcurve((65, 44), (86, 22), (81, 42), "outline", 4, fill=None)
        icon.text(spec.label[:2], 64, 91, 14, "feature")
    elif mode == 5:  # clock/watch
        icon.ellipse((25, 25, 103, 103), "white", "outline", 5)
        icon.line([(64, 64), (64, 39)], "feature", 5)
        icon.line([(64, 64), (83, 76)], "feature", 5)
        icon.text(spec.label[:2], 64, 89, 12, "accent")
    elif mode == 6:  # gear-like
        for a in range(0, 360, 45):
            x = 64 + 36 * math.cos(math.radians(a)); y = 64 + 36 * math.sin(math.radians(a))
            icon.rect((x - 8, y - 8, x + 8, y + 8), "secondary", "outline", 2, 3)
        icon.ellipse((30, 30, 98, 98), "primary", "outline", 5)
        icon.ellipse((51, 51, 77, 77), "white", "outline", 4)
        icon.text(spec.label[:2], 64, 64, 12, "feature")
    else:  # simple object badge
        base_disc(icon)
        icon.rect((42, 55, 86, 92), "white", "outline", 4, 8)
        icon.text(spec.label[:3], 64, 73, 16, "feature")
    add_badge(icon, spec)
    return icon


def draw_tech(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 7
    if mode == 0:  # phone/tablet
        icon.rect((39, 17, 89, 111), "dark", "outline", 5, 10)
        icon.rect((45, 27, 83, 93), "blue", None, radius=5)
        icon.ellipse((58, 97, 70, 109), "metal", None)
        icon.text(spec.label[:2], 64, 60, 15, "white")
    elif mode == 1:  # laptop
        icon.rect((28, 31, 100, 82), "dark", "outline", 5, 7)
        icon.rect((35, 39, 93, 75), "blue", None, radius=3)
        icon.rect((18, 82, 110, 103), "metal", "outline", 4, 6)
        icon.text(spec.label[:3], 64, 60, 15, "white")
    elif mode == 2:  # camera
        icon.rect((25, 41, 103, 94), "primary", "outline", 5, 10)
        icon.rect((36, 31, 62, 45), "secondary", "outline", 4, 5)
        icon.ellipse((49, 49, 88, 88), "dark", "outline", 3)
        icon.ellipse((58, 58, 79, 79), "blue", None)
        icon.ellipse((87, 49, 97, 59), "red", None)
    elif mode == 3:  # chip
        icon.rect((33, 33, 95, 95), "green", "outline", 5, 8)
        for x in [24, 104]:
            for y in range(42, 91, 12): icon.line([(x, y), (33 if x < 64 else 95, y)], "outline", 3)
        for y in [24, 104]:
            for x in range(42, 91, 12): icon.line([(x, y), (x, 33 if y < 64 else 95)], "outline", 3)
        icon.rect((48, 48, 80, 80), "dark", None, radius=5)
        icon.text(spec.label[:2], 64, 64, 13, "white")
    elif mode == 4:  # cloud/database
        icon.ellipse((25, 55, 60, 91), "blue", "outline", 4)
        icon.ellipse((48, 39, 83, 91), "blue", "outline", 4)
        icon.ellipse((73, 53, 105, 91), "blue", "outline", 4)
        icon.rect((32, 67, 100, 94), "blue", None)
        icon.line([(35, 94), (96, 94)], "outline", 4)
        icon.text(spec.label[:2], 65, 73, 16, "white")
    elif mode == 5:  # printer/router
        icon.rect((35, 25, 93, 55), "white", "outline", 4, 5)
        icon.rect((24, 52, 104, 89), "metal", "outline", 5, 8)
        icon.rect((38, 78, 90, 108), "white", "outline", 4, 3)
        icon.line([(47, 89), (81, 89)], "secondary", 3)
        icon.text(spec.label[:2], 64, 101, 10, "feature")
    else:  # terminal code
        icon.rect((24, 29, 104, 99), "dark", "outline", 5, 8)
        icon.text(">_", 52, 60, 23, "green")
        icon.text(spec.label[:2], 79, 82, 13, "accent")
    add_badge(icon, spec)
    return icon


def draw_vehicle_land(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 6
    if mode in (0, 1, 2):
        # car/truck/bus body
        if mode == 0:
            icon.qcurve((29, 72), (42, 39), (65, 41), "outline", 5)
            icon.qcurve((65, 41), (91, 43), (101, 72), "outline", 5)
            icon.rect((22, 62, 106, 91), "primary", "outline", 5, 11)
            icon.rect((43, 48, 62, 63), "blue", None, radius=3); icon.rect((68, 48, 88, 63), "blue", None, radius=3)
        elif mode == 1:
            icon.rect((20, 48, 83, 91), "primary", "outline", 5, 8)
            icon.rect((83, 60, 108, 91), "secondary", "outline", 5, 5)
            icon.rect((31, 57, 52, 72), "blue", None, radius=3); icon.rect((57, 57, 77, 72), "blue", None, radius=3)
        else:
            icon.rect((18, 45, 111, 91), "primary", "outline", 5, 9)
            for x in [29, 51, 73]: icon.rect((x, 55, x+16, 70), "blue", None, radius=2)
        icon.ellipse((30, 81, 52, 103), "dark", "outline", 3)
        icon.ellipse((78, 81, 100, 103), "dark", "outline", 3)
        icon.ellipse((37, 88, 45, 96), "metal"); icon.ellipse((85, 88, 93, 96), "metal")
        icon.text(spec.label[:2], 64, 77, 12, "feature")
    elif mode == 3:  # bicycle/motorbike
        icon.ellipse((21, 68, 55, 102), None, "outline", 5)
        icon.ellipse((75, 68, 109, 102), None, "outline", 5)
        icon.line([(38, 85), (62, 55), (84, 85), (53, 85), (38, 85)], "primary", 5)
        icon.line([(62, 55), (74, 48), (82, 50)], "outline", 4)
        icon.line([(53, 85), (47, 53), (57, 53)], "outline", 4)
    elif mode == 4:  # tractor/construction
        icon.rect((28, 45, 79, 85), "orange", "outline", 5, 6)
        icon.rect((72, 29, 101, 84), "primary", "outline", 5, 7)
        icon.rect((80, 38, 94, 58), "blue")
        icon.ellipse((21, 74, 61, 114), "dark", "outline", 4); icon.ellipse((78, 79, 108, 109), "dark", "outline", 4)
        icon.ellipse((34, 87, 48, 101), "metal"); icon.ellipse((88, 89, 98, 99), "metal")
    else:  # rail/road badge
        icon.rect((33, 22, 95, 91), "primary", "outline", 5, 10)
        icon.rect((43, 34, 85, 56), "blue", None, radius=4)
        icon.line([(41, 100), (25, 116)], "outline", 4); icon.line([(87, 100), (103, 116)], "outline", 4)
        icon.ellipse((40, 75, 54, 89), "dark"); icon.ellipse((74, 75, 88, 89), "dark")
        icon.text(spec.label[:2], 64, 68, 12, "feature")
    add_badge(icon, spec)
    return icon


def draw_air_space(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 6
    if mode == 0:  # airplane
        icon.polygon([(18, 61), (113, 36), (78, 68), (113, 92)], "primary", "outline", 5)
        icon.polygon([(55, 58), (37, 31), (72, 53)], "secondary", "outline", 3)
        icon.polygon([(57, 69), (37, 100), (78, 73)], "secondary", "outline", 3)
        icon.text(spec.label[:2], 76, 63, 12, "feature")
    elif mode == 1:  # rocket
        icon.polygon([(64, 15), (86, 50), (77, 96), (51, 96), (42, 50)], "primary", "outline", 5)
        icon.ellipse((54, 39, 74, 59), "blue", "outline", 3)
        icon.polygon([(51, 83), (33, 105), (55, 98)], "secondary", "outline", 4)
        icon.polygon([(77, 83), (95, 105), (73, 98)], "secondary", "outline", 4)
        icon.polygon([(55, 98), (64, 121), (73, 98)], "orange", "outline", 3)
    elif mode == 2:  # helicopter/drone
        icon.line([(32, 26), (96, 26)], "outline", 5)
        icon.line([(64, 26), (64, 47)], "outline", 4)
        icon.rect((33, 49, 97, 83), "primary", "outline", 5, 16)
        icon.rect((45, 54, 65, 71), "blue", None, radius=5)
        icon.line([(42, 88), (86, 88)], "outline", 4)
        icon.line([(92, 56), (115, 46)], "outline", 4)
    elif mode == 3:  # balloon
        icon.ellipse((38, 18, 90, 75), "primary", "outline", 5)
        icon.line([(52, 71), (46, 95)], "outline", 3); icon.line([(76, 71), (82, 95)], "outline", 3)
        icon.rect((44, 92, 84, 109), "brown", "outline", 4, 4)
        icon.line([(64, 22), (64, 73)], "secondary", 3)
    elif mode == 4:  # satellite/orbit
        icon.rect((48, 48, 80, 80), "metal", "outline", 4, 5)
        icon.rect((18, 42, 44, 86), "blue", "outline", 3, 3)
        icon.rect((84, 42, 110, 86), "blue", "outline", 3, 3)
        icon.line([(44, 64), (48, 64)], "outline", 4); icon.line([(80, 64), (84, 64)], "outline", 4)
        icon.qcurve((20, 100), (64, 18), (110, 100), "accent", 3)
    else:  # planet/ufo
        icon.ellipse((36, 34, 92, 90), "primary", "outline", 5)
        icon.qcurve((19, 69), (64, 93), (109, 60), "outline", 5)
        icon.qcurve((19, 69), (64, 47), (109, 60), "accent", 4)
        icon.text(spec.label[:2], 64, 61, 13, "feature")
    add_badge(icon, spec)
    return icon


def draw_water_rail(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 5
    if mode == 0:  # boat
        icon.polygon([(19, 71), (109, 71), (94, 101), (34, 101)], "primary", "outline", 5)
        icon.rect((42, 44, 86, 72), "white", "outline", 4, 5)
        icon.rect((53, 52, 65, 63), "blue"); icon.rect((69, 52, 81, 63), "blue")
        icon.line([(21, 108), (42, 104), (64, 109), (86, 104), (107, 108)], "blue", 4)
    elif mode == 1:  # sailboat
        icon.polygon([(28, 76), (101, 76), (88, 102), (42, 102)], "secondary", "outline", 5)
        icon.line([(64, 25), (64, 79)], "outline", 5)
        icon.polygon([(66, 29), (97, 73), (66, 73)], "primary", "outline", 4)
        icon.polygon([(62, 39), (33, 73), (62, 73)], "white", "outline", 4)
        icon.line([(22, 110), (105, 110)], "blue", 4)
    elif mode == 2:  # submarine
        icon.ellipse((22, 51, 106, 91), "primary", "outline", 5)
        icon.rect((58, 34, 78, 54), "primary", "outline", 4, 4)
        icon.line([(68, 34), (68, 21), (83, 21)], "outline", 4)
        for x in [42, 64, 86]: icon.ellipse((x-6, 65, x+6, 77), "blue", "outline", 2)
        icon.polygon([(22, 71), (10, 58), (10, 84)], "secondary", "outline", 4)
    elif mode == 3:  # train/rail
        icon.rect((30, 21, 98, 91), "primary", "outline", 5, 9)
        icon.rect((42, 34, 86, 58), "blue", None, radius=4)
        icon.rect((38, 65, 90, 77), "white", None, radius=4)
        icon.ellipse((41, 80, 55, 94), "dark"); icon.ellipse((73, 80, 87, 94), "dark")
        icon.line([(39, 101), (27, 115)], "outline", 4); icon.line([(89, 101), (101, 115)], "outline", 4)
    else:  # lighthouse/harbor
        icon.polygon([(48, 108), (80, 108), (75, 42), (53, 42)], "white", "outline", 5)
        icon.rect((46, 31, 82, 45), "accent", "outline", 4, 4)
        icon.polygon([(42, 31), (64, 16), (86, 31)], "primary", "outline", 4)
        icon.line([(54, 62), (74, 62)], "red", 5); icon.line([(52, 82), (76, 82)], "red", 5)
        icon.qcurve((16, 111), (64, 98), (112, 111), "blue", 4)
    add_badge(icon, spec)
    return icon


def draw_flag(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    colors = ["primary", "secondary", "accent", "green", "blue", "red", "purple", "orange", "white"]
    c1, c2, c3 = colors[seed % len(colors)], colors[(seed // 7) % len(colors)], colors[(seed // 13) % len(colors)]
    if spec.style == "roundel":
        icon.ellipse((21, 21, 107, 107), c1, "outline", 5)
        icon.ellipse((34, 34, 94, 94), c2, None)
        icon.ellipse((48, 48, 80, 80), c3, None)
        icon.text(spec.label[:2], 64, 65, 24, "feature")
    elif spec.style == "pennant":
        icon.line([(31, 21), (31, 109)], "outline", 6)
        icon.polygon([(31, 25), (105, 40), (31, 56)], c1, "outline", 4)
        icon.polygon([(31, 56), (95, 72), (31, 87)], c2, "outline", 4)
        icon.text(spec.label[:2], 59, 51, 16, "feature")
    elif spec.style == "badge":
        icon.rect((22, 30, 106, 98), "white", "outline", 5, 14)
        icon.rect((29, 37, 99, 56), c1, None, radius=4)
        icon.rect((29, 56, 99, 75), c2, None, radius=0)
        icon.rect((29, 75, 99, 91), c3, None, radius=4)
        icon.text(spec.label[:2], 64, 66, 24, "feature")
    else:
        icon.line([(27, 19), (27, 111)], "outline", 6)
        icon.polygon([(30, 23), (103, 29), (92, 54), (105, 80), (30, 74)], c1, "outline", 4)
        icon.polygon([(31, 42), (98, 47), (92, 54), (99, 64), (31, 59)], c2, None)
        icon.text(spec.label[:2], 62, 52, 18, "feature")
    return icon


def draw_toy_game(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 7
    if mode == 0:  # teddy/animal toy
        icon.ellipse((25, 34, 103, 104), "brown", "outline", 5)
        icon.ellipse((17, 23, 48, 55), "brown", "outline", 4); icon.ellipse((80, 23, 111, 55), "brown", "outline", 4)
        icon.ellipse((44, 57, 84, 90), "skin", "outline", 3)
        icon.ellipse((48, 50, 56, 58), "feature"); icon.ellipse((72, 50, 80, 58), "feature")
        icon.ellipse((60, 65, 68, 73), "feature"); icon.qcurve((64, 73), (56, 83), (48, 76), "feature", 3); icon.qcurve((64, 73), (72, 83), (80, 76), "feature", 3)
    elif mode == 1:  # dice
        icon.rect((32, 34, 96, 98), "white", "outline", 5, 12)
        for x, y in [(49, 51), (79, 51), (64, 66), (49, 81), (79, 81)]: icon.ellipse((x-5, y-5, x+5, y+5), "feature")
        icon.text(spec.label[:2], 64, 111, 10, "accent")
    elif mode == 2:  # blocks
        icon.rect((22, 57, 57, 94), "primary", "outline", 4, 5)
        icon.rect((56, 35, 91, 72), "secondary", "outline", 4, 5)
        icon.rect((77, 68, 112, 105), "accent", "outline", 4, 5)
        icon.text(spec.label[:1], 40, 75, 16, "feature"); icon.text(spec.label[-1:], 74, 53, 16, "feature")
    elif mode == 3:  # kite
        icon.polygon([(64, 16), (98, 52), (64, 91), (30, 52)], "primary", "outline", 5)
        icon.line([(64, 16), (64, 91)], "secondary", 3); icon.line([(30, 52), (98, 52)], "secondary", 3)
        icon.qcurve((64, 91), (52, 110), (77, 116), "outline", 3)
        icon.polygon(star(87, 108, 7, 3), "accent")
    elif mode == 4:  # controller
        icon.rect((23, 52, 105, 92), "dark", "outline", 5, 18)
        icon.ellipse((34, 62, 58, 86), "metal"); icon.line([(42, 74), (50, 74)], "feature", 3); icon.line([(46, 70), (46, 78)], "feature", 3)
        icon.ellipse((77, 67, 87, 77), "red"); icon.ellipse((91, 61, 101, 71), "green")
        icon.text(spec.label[:2], 64, 62, 10, "white")
    elif mode == 5:  # card/chess
        icon.rect((39, 22, 90, 106), "white", "outline", 5, 9)
        icon.polygon(heart(64, 63, 34), "red")
        icon.text(spec.label[:1], 54, 39, 14, "feature")
    else:  # ball/marble
        icon.ellipse((27, 27, 101, 101), "primary", "outline", 5)
        icon.qcurve((28, 64), (64, 45), (100, 64), "white", 5)
        icon.qcurve((64, 28), (46, 64), (64, 100), "white", 5)
        icon.text(spec.label[:2], 64, 66, 14, "feature")
    add_badge(icon, spec)
    return icon


def draw_fruit(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 6
    fill = ["primary", "green", "red", "orange", "purple", "blue"][seed % 6]
    if mode == 0:  # apple/round fruit
        icon.ellipse((30, 36, 75, 101), fill, "outline", 5)
        icon.ellipse((55, 36, 100, 101), fill, "outline", 5)
        icon.line([(64, 39), (68, 23)], "brown", 5)
        icon.ellipse((69, 18, 93, 38), "green", "outline", 3)
    elif mode == 1:  # banana/curved
        icon.qcurve((31, 84), (68, 108), (101, 47), "outline", 14)
        icon.qcurve((31, 84), (68, 108), (101, 47), "primary", 9)
        icon.qcurve((38, 79), (67, 92), (91, 43), "white", 3)
    elif mode == 2:  # citrus
        icon.ellipse((28, 28, 100, 100), fill, "outline", 5)
        for a in range(0, 360, 45):
            icon.line([(64, 64), (64 + 30 * math.cos(math.radians(a)), 64 + 30 * math.sin(math.radians(a)))], "white", 2)
        icon.ellipse((58, 58, 70, 70), "white")
    elif mode == 3:  # berry cluster
        for x, y in [(47, 46), (67, 43), (84, 56), (39, 68), (60, 70), (80, 78), (56, 91)]:
            icon.ellipse((x-14, y-14, x+14, y+14), fill, "outline", 2)
        icon.polygon([(61, 27), (75, 15), (73, 35)], "green", "outline", 3)
    elif mode == 4:  # pear/pineapple
        icon.ellipse((39, 29, 89, 70), fill, "outline", 5)
        icon.ellipse((30, 55, 98, 110), fill, "outline", 5)
        icon.line([(64, 29), (68, 16)], "brown", 4)
        icon.polygon([(59, 26), (48, 12), (68, 20), (81, 12), (72, 28)], "green", "outline", 2)
    else:  # slice
        icon.polygon([(26, 92), (64, 25), (102, 92)], fill, "outline", 5)
        icon.polygon([(37, 86), (64, 39), (91, 86)], "white", None)
        for x in [54, 64, 74]: icon.ellipse((x-3, 66, x+3, 72), "feature")
    add_badge(icon, spec)
    return icon


def draw_vegetable(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 6
    if mode == 0:  # carrot/root
        icon.polygon([(52, 41), (86, 38), (68, 108)], "orange", "outline", 5)
        icon.polygon([(54, 42), (45, 17), (64, 32), (75, 15), (75, 39), (91, 22), (85, 43)], "green", "outline", 3)
        icon.line([(61, 62), (77, 59)], "outline", 2); icon.line([(58, 78), (72, 75)], "outline", 2)
    elif mode == 1:  # broccoli/cauliflower
        for x, y in [(43, 48), (60, 35), (78, 44), (52, 60), (76, 61)]: icon.ellipse((x-18, y-18, x+18, y+18), "green", "outline", 3)
        icon.rect((54, 62, 75, 107), "secondary", "outline", 4, 8)
    elif mode == 2:  # corn
        icon.ellipse((43, 25, 86, 103), "primary", "outline", 5)
        for y in range(38, 89, 12):
            for x in range(51, 80, 12): icon.ellipse((x-3, y-3, x+3, y+3), "secondary")
        icon.polygon([(43, 60), (26, 96), (54, 91)], "green", "outline", 3)
        icon.polygon([(86, 60), (103, 96), (74, 91)], "green", "outline", 3)
    elif mode == 3:  # pepper/chili
        icon.qcurve((39, 70), (71, 13), (101, 49), "outline", 16)
        icon.qcurve((39, 70), (71, 13), (101, 49), "red", 11)
        icon.line([(84, 34), (96, 20)], "green", 5)
    elif mode == 4:  # mushroom/onion
        icon.ellipse((31, 31, 97, 79), "red", "outline", 5)
        icon.rect((52, 66, 77, 106), "white", "outline", 4, 10)
        icon.ellipse((45, 48, 53, 56), "white"); icon.ellipse((70, 40, 80, 50), "white")
    else:  # leaf/bean pod
        icon.ellipse((33, 42, 98, 87), "green", "outline", 5)
        icon.qcurve((36, 65), (65, 83), (96, 61), "white", 3)
        for x in [51, 64, 77]: icon.ellipse((x-5, 59, x+5, 69), "secondary")
    add_badge(icon, spec)
    return icon


def draw_food_drink(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 7
    if mode == 0:  # plate
        icon.ellipse((25, 35, 103, 101), "white", "outline", 5)
        icon.ellipse((42, 51, 86, 85), "primary", None)
        icon.text(spec.label[:2], 64, 68, 15, "feature")
    elif mode == 1:  # cup
        icon.rect((36, 38, 86, 99), "primary", "outline", 5, 8)
        icon.qcurve((86, 52), (113, 64), (88, 78), "outline", 5)
        icon.ellipse((42, 31, 80, 45), "white", "outline", 3)
        icon.qcurve((47, 26), (48, 12), (56, 25), "accent", 3); icon.qcurve((65, 26), (66, 12), (74, 25), "accent", 3)
    elif mode == 2:  # burger/sandwich
        icon.ellipse((26, 34, 102, 67), "orange", "outline", 5)
        icon.rect((24, 61, 104, 76), "green", "outline", 2, 4)
        icon.rect((27, 75, 101, 91), "brown", "outline", 2, 4)
        icon.ellipse((28, 82, 100, 106), "primary", "outline", 5)
    elif mode == 3:  # pizza/slice
        icon.polygon([(29, 101), (62, 28), (101, 101)], "orange", "outline", 5)
        icon.polygon([(41, 93), (63, 43), (88, 93)], "primary", None)
        for x, y in [(61, 73), (73, 83), (53, 88)]: icon.ellipse((x-5, y-5, x+5, y+5), "red")
    elif mode == 4:  # bowl/noodles
        icon.ellipse((26, 62, 102, 105), "white", "outline", 5)
        icon.rect((31, 62, 97, 83), "primary", None, radius=4)
        for x in [43, 57, 71, 85]: icon.qcurve((x, 55), (x-8, 42), (x+5, 34), "secondary", 3)
        icon.line([(25, 51), (103, 35)], "outline", 4)
    elif mode == 5:  # bottle
        icon.rect((49, 20, 79, 43), "metal", "outline", 4, 5)
        icon.rect((40, 39, 88, 108), "blue", "outline", 5, 13)
        icon.rect((47, 64, 81, 85), "white", None, radius=5)
        icon.text(spec.label[:2], 64, 75, 11, "feature")
    else:  # sweet/cake
        icon.rect((33, 53, 95, 101), "primary", "outline", 5, 8)
        icon.ellipse((33, 39, 95, 66), "white", "outline", 4)
        icon.line([(43, 78), (85, 78)], "secondary", 4)
        icon.ellipse((59, 24, 69, 39), "red")
    add_badge(icon, spec)
    return icon


def draw_animal(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 6
    fill = ["brown", "primary", "secondary", "orange", "metal", "white"][seed % 6]
    # head-first mammal style
    if mode in [0, 1, 2, 3]:
        if mode == 0:
            icon.ellipse((20, 30, 50, 62), fill, "outline", 4); icon.ellipse((78, 30, 108, 62), fill, "outline", 4)
        elif mode == 1:
            icon.polygon([(31, 56), (27, 22), (54, 43)], fill, "outline", 4); icon.polygon([(97, 56), (101, 22), (74, 43)], fill, "outline", 4)
        elif mode == 2:
            icon.line([(44, 33), (38, 18)], "outline", 4); icon.line([(84, 33), (90, 18)], "outline", 4)
        else:
            icon.ellipse((16, 40, 45, 74), "white", "outline", 4); icon.ellipse((83, 40, 112, 74), "white", "outline", 4)
        icon.ellipse((25, 34, 103, 106), fill, "outline", 5)
        icon.ellipse((44, 67, 84, 96), "skin", "outline", 3)
        icon.ellipse((45, 55, 55, 65), "feature"); icon.ellipse((73, 55, 83, 65), "feature")
        icon.ellipse((60, 71, 68, 79), "feature")
        icon.qcurve((64, 79), (55, 88), (48, 82), "feature", 3); icon.qcurve((64, 79), (73, 88), (80, 82), "feature", 3)
        if spec.style in {"stripe", "double", "motion"}:
            icon.line([(35, 47), (51, 53)], "dark", 2, opacity=0.5); icon.line([(93, 47), (77, 53)], "dark", 2, opacity=0.5)
    elif mode == 4:  # long body
        icon.ellipse((22, 57, 85, 96), fill, "outline", 5)
        icon.ellipse((73, 43, 108, 78), fill, "outline", 5)
        icon.ellipse((83, 54, 91, 62), "feature")
        icon.qcurve((23, 67), (4, 48), (23, 42), "outline", 5)
        icon.line([(37, 92), (33, 111)], "outline", 4); icon.line([(70, 92), (75, 111)], "outline", 4)
    else:  # hoofed animal
        icon.ellipse((20, 50, 91, 91), fill, "outline", 5)
        icon.rect((76, 36, 108, 67), fill, "outline", 4, 12)
        icon.line([(83, 36), (76, 22)], "outline", 4); icon.line([(99, 36), (106, 22)], "outline", 4)
        icon.ellipse((91, 48, 99, 56), "feature")
        for x in [35, 72]: icon.line([(x, 88), (x-4, 111)], "outline", 4)
    add_badge(icon, spec)
    return icon


def draw_bird(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    fill = ["primary", "blue", "green", "purple", "white", "orange"][seed % 6]
    mode = seed % 5
    if mode == 0:  # perched bird
        icon.ellipse((34, 38, 88, 94), fill, "outline", 5)
        icon.ellipse((58, 28, 101, 69), fill, "outline", 5)
        icon.polygon([(98, 47), (119, 55), (98, 64)], "orange", "outline", 3)
        icon.ellipse((78, 42, 87, 51), "feature")
        icon.polygon([(49, 54), (24, 42), (41, 75)], "secondary", "outline", 3)
        icon.line([(56, 92), (51, 110)], "outline", 3); icon.line([(70, 92), (75, 110)], "outline", 3)
    elif mode == 1:  # flying bird
        icon.ellipse((45, 44, 86, 81), fill, "outline", 5)
        icon.polygon([(50, 53), (14, 25), (38, 77)], "secondary", "outline", 4)
        icon.polygon([(81, 53), (116, 25), (93, 77)], "secondary", "outline", 4)
        icon.polygon([(86, 59), (105, 64), (86, 70)], "orange", "outline", 3)
        icon.ellipse((70, 52, 78, 60), "feature")
    elif mode == 2:  # owl
        icon.ellipse((27, 26, 101, 101), fill, "outline", 5)
        icon.polygon([(38, 35), (50, 17), (61, 39)], fill, "outline", 4); icon.polygon([(67, 39), (78, 17), (90, 35)], fill, "outline", 4)
        icon.ellipse((39, 46, 61, 68), "white", "outline", 2); icon.ellipse((67, 46, 89, 68), "white", "outline", 2)
        icon.ellipse((48, 55, 54, 61), "feature"); icon.ellipse((76, 55, 82, 61), "feature")
        icon.polygon([(64, 68), (55, 80), (73, 80)], "orange", "outline", 2)
    elif mode == 3:  # penguin/chick
        icon.ellipse((31, 20, 97, 106), "dark", "outline", 5)
        icon.ellipse((43, 44, 85, 102), "white", None)
        icon.ellipse((48, 44, 57, 53), "feature"); icon.ellipse((71, 44, 80, 53), "feature")
        icon.polygon([(64, 55), (54, 66), (74, 66)], "orange")
        icon.line([(52, 105), (43, 116)], "orange", 4); icon.line([(76, 105), (85, 116)], "orange", 4)
    else:  # peacock/flamingo generic
        for a in range(210, 331, 30):
            icon.line([(64, 68), (64 + 45 * math.cos(math.radians(a)), 68 + 45 * math.sin(math.radians(a)))], "green", 8)
        icon.ellipse((45, 42, 83, 95), fill, "outline", 5)
        icon.qcurve((70, 44), (96, 20), (95, 59), "outline", 6)
        icon.ellipse((89, 48, 108, 67), fill, "outline", 4)
        icon.polygon([(106, 55), (119, 61), (106, 65)], "orange")
    add_badge(icon, spec)
    return icon


def draw_aquatic(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 6
    if mode == 0:  # fish
        icon.ellipse((32, 44, 96, 86), "blue", "outline", 5)
        icon.polygon([(32, 65), (13, 48), (13, 82)], "secondary", "outline", 4)
        icon.polygon([(64, 45), (77, 24), (83, 50)], "secondary", "outline", 3)
        icon.ellipse((78, 57, 86, 65), "feature")
        icon.qcurve((88, 68), (98, 73), (105, 66), "feature", 3)
    elif mode == 1:  # whale/dolphin
        icon.ellipse((20, 45, 102, 91), "blue", "outline", 5)
        icon.polygon([(99, 62), (119, 48), (116, 75)], "secondary", "outline", 4)
        icon.polygon([(56, 49), (45, 27), (72, 48)], "secondary", "outline", 3)
        icon.ellipse((78, 57, 86, 65), "feature")
        icon.qcurve((35, 42), (28, 22), (49, 23), "blue", 5)
    elif mode == 2:  # octopus/jellyfish
        icon.ellipse((35, 22, 93, 77), "purple", "outline", 5)
        icon.rect((35, 58, 93, 82), "purple", None)
        for x in [41, 53, 65, 77, 89]: icon.qcurve((x, 78), (x-11, 101), (x+2, 112), "outline", 4)
        icon.ellipse((51, 47, 59, 55), "feature"); icon.ellipse((70, 47, 78, 55), "feature")
    elif mode == 3:  # crab
        icon.ellipse((36, 54, 92, 92), "red", "outline", 5)
        for x in [45, 83]: icon.ellipse((x-5, 43, x+5, 53), "feature")
        icon.line([(38, 66), (18, 54), (13, 42)], "outline", 4); icon.line([(90, 66), (110, 54), (115, 42)], "outline", 4)
        icon.ellipse((7, 32, 27, 52), "red", "outline", 3); icon.ellipse((101, 32, 121, 52), "red", "outline", 3)
        for x in [45, 55, 73, 83]: icon.line([(x, 89), (x-8 if x < 64 else x+8, 106)], "outline", 3)
    elif mode == 4:  # shell/starfish
        icon.polygon(star(64, 66, 47, 22, 5), "orange", "outline", 5)
        icon.ellipse((56, 58, 63, 65), "feature"); icon.ellipse((70, 58, 77, 65), "feature")
        icon.qcurve((55, 78), (64, 86), (73, 78), "feature", 3)
    else:  # turtle/sea creature
        icon.ellipse((29, 42, 91, 92), "green", "outline", 5)
        icon.ellipse((86, 56, 111, 78), "green", "outline", 4)
        icon.ellipse((96, 62, 103, 69), "feature")
        for p in [(31,50),(21,37),(42,43),(35,88),(22,103),(48,93),(85,50),(101,37),(92,60),(83,89),(99,104),(75,93)]:
            pass
        icon.polygon([(35, 50), (20, 36), (46, 43)], "green", "outline", 3)
        icon.polygon([(36, 86), (20, 103), (50, 95)], "green", "outline", 3)
        icon.line([(45, 65), (79, 65)], "secondary", 3); icon.line([(64, 44), (64, 90)], "secondary", 3)
    add_badge(icon, spec)
    return icon


def draw_reptile_bug(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 6
    if mode == 0:  # snake
        icon.qcurve((23, 84), (50, 31), (80, 58), "outline", 14)
        icon.qcurve((23, 84), (50, 31), (80, 58), "green", 9)
        icon.qcurve((80, 58), (111, 86), (79, 100), "outline", 14)
        icon.qcurve((80, 58), (111, 86), (79, 100), "green", 9)
        icon.ellipse((76, 50, 97, 70), "green", "outline", 3)
        icon.ellipse((88, 56, 93, 61), "feature")
        icon.line([(96, 61), (112, 61)], "red", 2)
    elif mode == 1:  # turtle
        icon.ellipse((29, 38, 95, 94), "green", "outline", 5)
        icon.ellipse((86, 55, 111, 76), "green", "outline", 4)
        icon.line([(48, 47), (76, 87)], "secondary", 3); icon.line([(77, 47), (49, 87)], "secondary", 3)
        icon.ellipse((96, 61, 103, 68), "feature")
        for x,y in [(31,49),(31,83),(90,49),(90,83)]: icon.ellipse((x-8,y-8,x+8,y+8),"green","outline",2)
    elif mode == 2:  # frog/toad
        icon.ellipse((28, 39, 100, 100), "green", "outline", 5)
        icon.ellipse((36, 25, 58, 50), "green", "outline", 4); icon.ellipse((70, 25, 92, 50), "green", "outline", 4)
        icon.ellipse((44, 34, 52, 42), "feature"); icon.ellipse((76, 34, 84, 42), "feature")
        icon.qcurve((48, 74), (64, 91), (80, 74), "feature", 4)
    elif mode == 3:  # lizard/croc
        icon.ellipse((24, 54, 94, 86), "green", "outline", 5)
        icon.polygon([(90, 57), (119, 65), (90, 78)], "green", "outline", 4)
        icon.qcurve((25, 69), (5, 45), (23, 40), "outline", 5)
        icon.ellipse((95, 62, 102, 69), "feature")
        icon.line([(42, 83), (37, 103)], "outline", 3); icon.line([(72, 83), (77, 103)], "outline", 3)
    elif mode == 4:  # beetle/bug
        icon.ellipse((40, 26, 88, 98), "primary", "outline", 5)
        icon.line([(64, 31), (64, 95)], "outline", 3)
        icon.ellipse((48, 39, 58, 49), "feature"); icon.ellipse((70, 39, 80, 49), "feature")
        for y in [53, 66, 79]:
            icon.line([(41, y), (18, y-10)], "outline", 3); icon.line([(87, y), (110, y-10)], "outline", 3)
        icon.line([(53, 28), (41, 14)], "outline", 3); icon.line([(75, 28), (87, 14)], "outline", 3)
    else:  # butterfly
        icon.ellipse((57, 33, 71, 93), "dark", "outline", 3)
        icon.ellipse((22, 29, 60, 70), "purple", "outline", 4)
        icon.ellipse((68, 29, 106, 70), "purple", "outline", 4)
        icon.ellipse((26, 68, 59, 104), "accent", "outline", 4)
        icon.ellipse((69, 68, 102, 104), "accent", "outline", 4)
        icon.line([(60, 34), (48, 18)], "outline", 3); icon.line([(68, 34), (80, 18)], "outline", 3)
    add_badge(icon, spec)
    return icon


def draw_hand(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 8
    # Palm with simple fingers; modes indicate gestures.
    if mode == 0:  # wave/open hand
        for x,h in [(39,50),(50,42),(61,39),(72,43),(83,51)]: icon.rect((x, 24, x+12, h+34), "skin", "outline", 3, 7)
        icon.ellipse((36, 54, 94, 104), "skin", "outline", 5)
        icon.line([(24, 27), (32, 38)], "accent", 3); icon.line([(101, 25), (93, 38)], "accent", 3)
    elif mode == 1:  # thumbs up
        icon.rect((44, 51, 91, 99), "skin", "outline", 5, 12)
        icon.rect((29, 65, 51, 103), "skin2", "outline", 4, 8)
        icon.polygon([(52, 51), (62, 20), (78, 25), (74, 53)], "skin", "outline", 4)
        for y in [58, 70, 82]: icon.line([(78, y), (98, y)], "outline", 3)
    elif mode == 2:  # pointing
        icon.rect((30, 62, 79, 98), "skin", "outline", 5, 12)
        icon.rect((68, 45, 111, 62), "skin", "outline", 4, 8)
        icon.rect((38, 48, 57, 67), "skin2", "outline", 4, 8)
        icon.text("→", 97, 38, 18, "accent")
    elif mode == 3:  # peace
        icon.rect((46, 54, 88, 103), "skin", "outline", 5, 12)
        icon.rect((46, 20, 60, 66), "skin", "outline", 4, 7)
        icon.rect((68, 19, 82, 66), "skin", "outline", 4, 7)
        icon.rect((84, 56, 100, 86), "skin2", "outline", 4, 7)
        icon.text("V", 64, 79, 18, "feature")
    elif mode == 4:  # ok hand
        icon.ellipse((39, 47, 75, 83), None, "skin", 9)
        icon.rect((68, 35, 102, 50), "skin", "outline", 4, 7)
        icon.rect((74, 54, 106, 69), "skin", "outline", 4, 7)
        icon.rect((72, 73, 99, 88), "skin", "outline", 4, 7)
        icon.ellipse((34, 42, 81, 89), None, "outline", 4)
    elif mode == 5:  # fist
        icon.rect((31, 42, 98, 96), "skin", "outline", 5, 13)
        for x in [38, 52, 66, 80]: icon.rect((x, 28, x+15, 56), "skin", "outline", 3, 7)
        icon.line([(38, 66), (91, 66)], "skin2", 3)
    elif mode == 6:  # handshake
        icon.polygon([(17, 71), (48, 51), (72, 79), (43, 99)], "skin", "outline", 4)
        icon.polygon([(111, 70), (80, 50), (56, 78), (85, 99)], "skin2", "outline", 4)
        icon.rect((45, 68, 83, 90), "skin", "outline", 3, 10)
    else:  # heart hands
        icon.polygon(heart(64, 59, 42), "red", "outline", 4)
        icon.rect((24, 70, 54, 107), "skin", "outline", 4, 10)
        icon.rect((74, 70, 104, 107), "skin2", "outline", 4, 10)
    add_badge(icon, spec)
    return icon


def draw_body(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 8
    if mode == 0:  # eye
        icon.polygon([(18, 64), (38, 38), (64, 31), (90, 38), (110, 64), (90, 90), (64, 97), (38, 90)], "white", "outline", 5)
        icon.ellipse((47, 47, 81, 81), "blue", "outline", 3); icon.ellipse((58, 58, 70, 70), "feature")
    elif mode == 1:  # ear
        icon.ellipse((42, 24, 92, 102), "skin", "outline", 5)
        icon.qcurve((63, 47), (86, 50), (70, 73), "skin2", 5)
        icon.qcurve((68, 73), (57, 88), (80, 89), "skin2", 4)
    elif mode == 2:  # mouth/tooth
        icon.qcurve((30, 64), (64, 91), (98, 64), "red", 12)
        icon.qcurve((30, 64), (64, 48), (98, 64), "red", 12)
        icon.rect((44, 59, 58, 80), "white", "outline", 2, 2); icon.rect((70, 59, 84, 80), "white", "outline", 2, 2)
    elif mode == 3:  # brain
        for x,y in [(47,43),(63,34),(81,43),(40,62),(64,60),(88,62),(54,82),(76,82)]: icon.ellipse((x-17,y-16,x+17,y+16), "purple", "outline", 3)
        icon.qcurve((64, 32), (64, 98), (64, 99), "outline", 3)
    elif mode == 4:  # heart/lung
        icon.polygon(heart(64, 61, 56), "red", "outline", 5)
        icon.text(spec.label[:1], 64, 66, 16, "white")
    elif mode == 5:  # arm/leg
        icon.qcurve((34, 45), (54, 85), (84, 69), "outline", 19)
        icon.qcurve((34, 45), (54, 85), (84, 69), "skin", 14)
        icon.ellipse((76, 59, 103, 86), "skin", "outline", 4)
    elif mode == 6:  # profile head
        icon.ellipse((35, 22, 88, 77), "skin", "outline", 5)
        icon.polygon([(78, 49), (102, 59), (78, 66)], "skin", "outline", 4)
        icon.rect((50, 74, 83, 108), "skin2", "outline", 4, 8)
        icon.ellipse((65, 42, 73, 50), "feature")
    else:  # foot/footprints
        icon.ellipse((32, 53, 76, 103), "skin", "outline", 5)
        for x,y in [(30,36),(42,31),(55,32),(67,38),(77,48)]: icon.ellipse((x-5,y-5,x+5,y+5), "skin", "outline", 2)
        icon.ellipse((79, 54, 105, 88), "skin2", "outline", 4)
    add_badge(icon, spec)
    return icon


def draw_person(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 7
    if mode in [0, 1, 2, 3]:
        icon.ellipse((42, 18, 86, 62), "skin", "outline", 5)
        hair = ["brown", "dark", "orange", "purple"][seed % 4]
        if mode == 1: icon.qcurve((41, 38), (64, 8), (88, 38), hair, 10)
        elif mode == 2: icon.rect((38, 20, 90, 41), hair, "outline", 3, 8)
        elif mode == 3: icon.ellipse((31, 20, 97, 58), hair, "outline", 3)
        icon.ellipse((53, 38, 59, 45), "feature"); icon.ellipse((69, 38, 75, 45), "feature")
        icon.qcurve((55, 50), (64, 57), (73, 50), "feature", 3)
        icon.rect((31, 65, 97, 111), "primary", "outline", 5, 16)
        sym = pick(["♂", "♀", "⚧", "★", "+", "∞", "✓"], seed // 5)
        icon.text(sym, 64, 88, 22, "accent2")
    elif mode == 4:  # family/group
        for cx, sz, col in [(44, 21, "skin"), (68, 25, "skin2"), (88, 19, "skin")]:
            icon.ellipse((cx-sz/2, 25, cx+sz/2, 25+sz), col, "outline", 3)
            icon.rect((cx-sz/1.2, 52, cx+sz/1.2, 104), "primary", "outline", 3, 12)
        icon.text(spec.label[:2], 66, 83, 11, "accent2")
    elif mode == 5:  # worker role
        icon.ellipse((42, 25, 86, 66), "skin", "outline", 5)
        icon.rect((36, 20, 92, 38), "orange", "outline", 3, 8)
        icon.rect((30, 68, 98, 111), "blue", "outline", 5, 12)
        icon.line([(46, 74), (46, 110)], "white", 3); icon.line([(82, 74), (82, 110)], "white", 3)
        icon.text(spec.label[:2], 64, 91, 12, "white")
    else:  # superhero/role badge
        icon.polygon([(20, 102), (42, 38), (64, 102)], "accent", "outline", 4)
        icon.polygon([(108, 102), (86, 38), (64, 102)], "accent", "outline", 4)
        icon.ellipse((42, 16, 86, 60), "skin", "outline", 5)
        icon.rect((48, 35, 80, 48), "dark", None, radius=5)
        icon.rect((38, 62, 90, 111), "primary", "outline", 5, 14)
        icon.text("★", 64, 87, 22, "accent2")
    add_badge(icon, spec)
    return icon


def draw_activity(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 8
    # stick-avatar with props
    icon.ellipse((54, 18, 74, 38), "skin", "outline", 3)
    icon.line([(64, 39), (64, 73)], "primary", 8)
    if mode == 0:  # running
        icon.line([(64, 52), (37, 67)], "primary", 6); icon.line([(64, 53), (91, 47)], "primary", 6)
        icon.line([(64, 73), (44, 104)], "primary", 6); icon.line([(64, 73), (92, 97)], "primary", 6)
        icon.line([(98, 96), (111, 93)], "accent", 3)
    elif mode == 1:  # yoga/meditation
        icon.line([(64, 52), (36, 46)], "primary", 6); icon.line([(64, 52), (92, 46)], "primary", 6)
        icon.qcurve((48, 88), (64, 70), (80, 88), "primary", 7)
        icon.qcurve((47, 89), (28, 104), (55, 104), "primary", 6); icon.qcurve((81, 89), (100, 104), (73, 104), "primary", 6)
    elif mode == 2:  # music
        icon.line([(64, 51), (42, 72)], "primary", 6); icon.line([(64, 52), (87, 70)], "primary", 6)
        icon.line([(64, 73), (52, 105)], "primary", 6); icon.line([(64, 73), (77, 105)], "primary", 6)
        icon.text("♪", 96, 38, 26, "accent")
    elif mode == 3:  # painting/writing
        icon.line([(64, 52), (36, 62)], "primary", 6); icon.line([(64, 52), (89, 64)], "primary", 6)
        icon.line([(88, 63), (113, 41)], "brown", 5); icon.ellipse((108, 36, 119, 47), "accent")
        icon.line([(64, 73), (50, 104)], "primary", 6); icon.line([(64, 73), (82, 104)], "primary", 6)
    elif mode == 4:  # swimming/surfing
        icon.line([(64, 53), (36, 59)], "primary", 6); icon.line([(64, 53), (91, 58)], "primary", 6)
        icon.qcurve((20, 98), (64, 76), (108, 98), "blue", 6)
        icon.ellipse((23, 82, 102, 108), "blue", None, opacity=0.3)
    elif mode == 5:  # cooking/gardening
        icon.line([(64, 52), (37, 71)], "primary", 6); icon.line([(64, 52), (90, 70)], "primary", 6)
        icon.rect((82, 64, 114, 92), "metal", "outline", 3, 8)
        icon.line([(64, 73), (50, 105)], "primary", 6); icon.line([(64, 73), (82, 105)], "primary", 6)
    elif mode == 6:  # climbing/hiking
        icon.line([(64, 50), (39, 35)], "primary", 6); icon.line([(64, 51), (88, 33)], "primary", 6)
        icon.line([(64, 73), (45, 95)], "primary", 6); icon.line([(64, 73), (92, 82)], "primary", 6)
        icon.polygon([(89, 19), (115, 111), (78, 111)], "metal", "outline", 3)
    else:  # celebration
        icon.line([(64, 50), (38, 28)], "primary", 6); icon.line([(64, 50), (91, 28)], "primary", 6)
        icon.line([(64, 73), (48, 106)], "primary", 6); icon.line([(64, 73), (83, 106)], "primary", 6)
        icon.polygon(star(31, 24, 9, 4), "accent"); icon.polygon(star(99, 23, 9, 4), "green")
    icon.text(spec.label[:2], 64, 120, 8, "feature")
    add_badge(icon, spec)
    return icon


def draw_sport(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 8
    if mode == 0:  # ball
        icon.ellipse((28, 28, 100, 100), "white", "outline", 5)
        icon.polygon(regular(64, 64, 16, 5), "feature")
        for a in range(0, 360, 72): icon.line([(64,64),(64+34*math.cos(math.radians(a)),64+34*math.sin(math.radians(a)))],"feature",3)
    elif mode == 1:  # basketball/volleyball
        icon.ellipse((27, 27, 101, 101), "orange", "outline", 5)
        icon.line([(64, 29), (64, 99)], "feature", 3); icon.line([(29, 64), (99, 64)], "feature", 3)
        icon.qcurve((34, 38), (64, 63), (34, 90), "feature", 3); icon.qcurve((94, 38), (64, 63), (94, 90), "feature", 3)
    elif mode == 2:  # racket/bat
        icon.ellipse((28, 20, 78, 70), None, "outline", 5)
        icon.line([(64, 64), (100, 105)], "brown", 8)
        icon.line([(41, 33), (70, 62)], "metal", 2); icon.line([(69, 33), (40, 62)], "metal", 2)
        icon.ellipse((91, 20, 111, 40), "primary", "outline", 3)
    elif mode == 3:  # trophy/medal
        icon.rect((42, 25, 86, 76), "primary", "outline", 5, 6)
        icon.qcurve((42, 39), (20, 37), (33, 61), "outline", 4); icon.qcurve((86, 39), (108, 37), (95, 61), "outline", 4)
        icon.line([(64, 76), (64, 98)], "outline", 5); icon.rect((43, 98, 85, 111), "secondary", "outline", 4, 5)
        icon.text("★", 64, 52, 20, "feature")
    elif mode == 4:  # target/dart
        for r, col in [(42,"red"),(30,"white"),(18,"red"),(7,"feature")]: icon.ellipse((64-r,64-r,64+r,64+r), col, "outline" if r==42 else None, 4)
        icon.line([(90, 36), (111, 15)], "feature", 4); icon.polygon([(111,15),(108,32),(94,29)],"accent","outline",2)
    elif mode == 5:  # chess/card
        icon.rect((36, 26, 92, 104), "white", "outline", 5, 7)
        icon.polygon(star(64, 62, 23, 10), "feature")
        icon.text(spec.label[:1], 50, 43, 14, "red")
    elif mode == 6:  # goal/field
        icon.rect((25, 41, 103, 94), None, "outline", 5, 4)
        for x in [40, 55, 70, 85]: icon.line([(x, 42), (x, 93)], "metal", 2)
        icon.ellipse((53, 60, 75, 82), "white", "outline", 3)
    else:  # board/game piece
        icon.rect((28, 28, 100, 100), "white", "outline", 5, 6)
        for i in range(4):
            for j in range(4):
                icon.rect((34+i*15, 34+j*15, 49+i*15, 49+j*15), "dark" if (i+j)%2 else "primary")
        icon.text(spec.label[:2], 64, 112, 9, "feature")
    add_badge(icon, spec)
    return icon


def draw_defense(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 8
    if mode == 0:  # shield
        icon.polygon([(64, 17), (101, 31), (94, 83), (64, 111), (34, 83), (27, 31)], "primary", "outline", 5)
        icon.polygon([(64, 29), (87, 39), (82, 76), (64, 94), (46, 76), (41, 39)], "accent2", None)
        icon.text("✓", 64, 64, 28, "feature")
    elif mode == 1:  # helmet
        icon.ellipse((28, 34, 100, 88), "primary", "outline", 5)
        icon.rect((24, 73, 104, 92), "primary", "outline", 4, 6)
        icon.rect((43, 52, 85, 67), "blue", None, radius=4)
        icon.text(spec.label[:2], 64, 86, 10, "feature")
    elif mode == 2:  # target/radar
        for r, col in [(43,"accent2"),(31,"primary"),(19,"accent2"),(8,"red")]: icon.ellipse((64-r,64-r,64+r,64+r), col, "outline" if r==43 else None, 4)
        icon.line([(64, 64), (97, 32)], "feature", 3)
    elif mode == 3:  # radio/compass
        icon.rect((31, 37, 97, 102), "metal", "outline", 5, 9)
        icon.line([(45, 37), (31, 16)], "outline", 4)
        icon.ellipse((47, 57, 81, 91), "dark", None)
        icon.text(spec.label[:2], 64, 74, 13, "accent")
        for x in [83, 91]: icon.ellipse((x, 45, x+7, 52), "feature")
    elif mode == 4:  # generic nonfunctional blaster silhouette
        icon.rect((24, 52, 95, 72), "metal", "outline", 5, 6)
        icon.rect((50, 69, 73, 99), "metal", "outline", 4, 6)
        icon.rect((86, 47, 110, 62), "accent", "outline", 3, 4)
        icon.line([(25, 62), (14, 62)], "outline", 5)
        icon.text("SIM", 60, 62, 9, "feature")
    elif mode == 5:  # nonfunctional rounds/crate dots
        icon.rect((28, 39, 100, 96), "brown", "outline", 5, 8)
        for x in [45, 64, 83]: icon.ellipse((x-7, 57, x+7, 71), "primary", "outline", 2)
        icon.line([(36, 83), (92, 83)], "outline", 3)
    elif mode == 6:  # vehicle symbol
        icon.rect((25, 59, 102, 86), "green", "outline", 5, 8)
        icon.ellipse((30, 76, 51, 97), "dark"); icon.ellipse((76, 76, 97, 97), "dark")
        icon.rect((50, 38, 81, 62), "green", "outline", 4, 4)
        icon.line([(81, 49), (109, 42)], "outline", 5)
    else:  # peace/defense emblem
        icon.ellipse((24, 24, 104, 104), "accent2", "outline", 5)
        icon.line([(64, 35), (64, 93)], "green", 5)
        icon.line([(64, 70), (43, 91)], "green", 5); icon.line([(64, 70), (85, 91)], "green", 5)
        icon.text(spec.label[:2], 64, 22, 9, "feature")
    add_badge(icon, spec)
    return icon


def draw_nature(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    mode = seed % 9
    if mode == 0:  # sun
        for a in range(0, 360, 30): icon.line([(64 + 35*math.cos(math.radians(a)),64 + 35*math.sin(math.radians(a))), (64 + 50*math.cos(math.radians(a)),64 + 50*math.sin(math.radians(a)))], "orange", 4)
        icon.ellipse((29, 29, 99, 99), "primary", "outline", 5)
        icon.ellipse((49, 53, 57, 61), "feature"); icon.ellipse((71, 53, 79, 61), "feature"); icon.qcurve((51, 73), (64, 84), (77, 73), "feature", 3)
    elif mode == 1:  # moon/star
        icon.ellipse((33, 22, 97, 98), "primary", "outline", 5)
        icon.ellipse((57, 18, 111, 92), "bg", None)
        icon.polygon(star(92, 34, 10, 4), "accent", "outline", 2)
    elif mode == 2:  # cloud/rain
        icon.ellipse((24, 56, 58, 90), "white", "outline", 4); icon.ellipse((45, 38, 82, 91), "white", "outline", 4); icon.ellipse((73, 55, 106, 90), "white", "outline", 4)
        icon.rect((31, 66, 100, 92), "white", None)
        for x in [42, 64, 86]: icon.polygon(drop(x, 109, 8), "blue")
    elif mode == 3:  # mountain
        icon.polygon([(17, 104), (52, 38), (78, 104)], "metal", "outline", 5)
        icon.polygon([(51, 38), (61, 58), (43, 58)], "white", None)
        icon.polygon([(52, 104), (89, 30), (116, 104)], "primary", "outline", 5)
        icon.polygon([(89, 30), (99, 52), (78, 52)], "white", None)
    elif mode == 4:  # tree
        icon.rect((56, 69, 72, 109), "brown", "outline", 4, 5)
        icon.ellipse((31, 33, 68, 76), "green", "outline", 4); icon.ellipse((59, 25, 96, 75), "green", "outline", 4); icon.ellipse((42, 54, 88, 94), "green", "outline", 4)
    elif mode == 5:  # flower
        for a in range(0, 360, 45):
            x=64+24*math.cos(math.radians(a)); y=58+24*math.sin(math.radians(a)); icon.ellipse((x-13,y-13,x+13,y+13), "accent", "outline", 2)
        icon.ellipse((51, 45, 77, 71), "primary", "outline", 3)
        icon.line([(64, 72), (64, 111)], "green", 5); icon.ellipse((42, 82, 63, 99), "green", "outline", 2)
    elif mode == 6:  # planet
        icon.ellipse((36, 32, 92, 88), "blue", "outline", 5)
        icon.qcurve((17, 67), (64, 101), (111, 55), "accent", 5)
        icon.qcurve((18, 67), (64, 37), (110, 55), "white", 3)
        icon.text(spec.label[:2], 64, 62, 12, "white")
    elif mode == 7:  # fire/water/weather
        icon.polygon([(64, 18), (83, 51), (75, 45), (91, 80), (64, 112), (37, 80), (52, 47)], "orange", "outline", 5)
        icon.polygon([(64, 52), (77, 79), (64, 101), (51, 79)], "primary")
    else:  # leaf/wave
        icon.ellipse((28, 32, 101, 85), "green", "outline", 5)
        icon.qcurve((30, 60), (65, 82), (99, 43), "white", 3)
        icon.qcurve((22, 106), (64, 84), (106, 106), "blue", 4)
    add_badge(icon, spec)
    return icon


def draw_symbol(spec: Spec) -> Icon:
    icon = Icon(spec.display_name, spec.description)
    seed = hnum(spec.name)
    add_shadow(icon)
    shape = seed % 4
    if shape == 0: icon.ellipse((21, 21, 107, 107), "primary", "outline", 5)
    elif shape == 1: icon.rect((25, 25, 103, 103), "primary", "outline", 5, 14)
    elif shape == 2: icon.polygon(regular(64,64,48,6), "primary", "outline", 5)
    else: icon.polygon(star(64,64,48,23), "primary", "outline", 5)
    symbols = ["✓","×","+","−","i","?","!","▶","Ⅱ","●","↻","⇄","↑","↓","←","→","⌂","⚙","☰","…","⇧","⇩","☁","🔗","★","♥","♪","⚑","⌕","#"]
    sym = symbols[seed % len(symbols)]
    # Avoid multicolor emoji font fallback; use common monochrome symbols as much as possible.
    if sym == "🔗": sym = "∞"
    icon.text(sym, 64, 62, 34 if len(sym)==1 else 25, "accent2")
    icon.text(spec.label[:2], 64, 94, 10, "feature")
    return icon


def make_icon(spec: Spec) -> Icon:
    if spec.category == "things_tools": return draw_thing(spec)
    if spec.category == "tech_office": return draw_tech(spec)
    if spec.category == "vehicles_land": return draw_vehicle_land(spec)
    if spec.category == "vehicles_air_space": return draw_air_space(spec)
    if spec.category == "vehicles_water_rail": return draw_water_rail(spec)
    if spec.category == "country_flags": return draw_flag(spec)
    if spec.category == "toys_games": return draw_toy_game(spec)
    if spec.category == "fruits": return draw_fruit(spec)
    if spec.category == "vegetables": return draw_vegetable(spec)
    if spec.category == "food_drink": return draw_food_drink(spec)
    if spec.category == "animals_mammals": return draw_animal(spec)
    if spec.category == "birds": return draw_bird(spec)
    if spec.category == "aquatic_animals": return draw_aquatic(spec)
    if spec.category == "reptiles_amphibians_bugs": return draw_reptile_bug(spec)
    if spec.category == "hands_gestures": return draw_hand(spec)
    if spec.category == "body_parts": return draw_body(spec)
    if spec.category == "people_family_gender": return draw_person(spec)
    if spec.category == "activities": return draw_activity(spec)
    if spec.category == "sports_games": return draw_sport(spec)
    if spec.category == "military_defense_symbolic": return draw_defense(spec)
    if spec.category == "nature_weather_space": return draw_nature(spec)
    if spec.category == "symbols_status": return draw_symbol(spec)
    return draw_symbol(spec)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def save_pngs_for_icon(icon: Icon, spec: Spec, out: Path) -> None:
    for theme_name, theme in THEMES.items():
        img128 = render_icon(icon, theme, 128)
        for sz in SIZES:
            d = out / "png" / theme_name / str(sz)
            d.mkdir(parents=True, exist_ok=True)
            img = img128 if sz == 128 else img128.resize((sz, sz), Image.Resampling.LANCZOS)
            # Default zlib compression keeps assets compact without optimize's high CPU cost.
            img.save(d / f"{spec.name}.png")


def create_preview(specs: List[Spec], out: Path, max_icons: int = 576) -> None:
    preview_dir = out / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    # Deterministic cross-category sample: take first N from each category until full.
    bycat: Dict[str, List[Spec]] = {}
    for sp in specs:
        bycat.setdefault(sp.category, []).append(sp)
    sample: List[Spec] = []
    per_cat = max(8, max_icons // len(CATEGORY_COUNTS))
    for cat in CATEGORY_COUNTS:
        sample.extend(bycat.get(cat, [])[:per_cat])
    if len(sample) < max_icons:
        seen = {sp.name for sp in sample}
        for sp in specs:
            if sp.name not in seen:
                sample.append(sp)
                if len(sample) >= max_icons: break
    sample = sample[:max_icons]
    cell = 40
    cols = 24
    rows = math.ceil(len(sample) / cols)
    font = get_font(7)
    icons_cache = {sp.name: make_icon(sp) for sp in sample}
    for theme_name, theme in THEMES.items():
        sheet = Image.new("RGBA", (cols * cell, rows * cell), color_key("bg", theme))
        d = ImageDraw.Draw(sheet)
        for i, sp in enumerate(sample):
            x = (i % cols) * cell
            y = (i // cols) * cell
            im = render_icon(icons_cache[sp.name], theme, 32)
            sheet.alpha_composite(im, (x + 4, y + 1))
            label = sp.label[:3]
            bb = d.textbbox((0, 0), label, font=font)
            d.text((x + (cell - (bb[2] - bb[0])) // 2, y + 32), label, fill=color_key("feature", theme), font=font)
        sheet.save(preview_dir / f"contact_sheet_{theme_name}.png")
    cards = []
    for theme in THEMES:
        cards.append(f'<div class="card"><h2>{html.escape(theme)}</h2><img src="contact_sheet_{theme}.png" alt="{html.escape(theme)} contact sheet"></div>')
    write_text(preview_dir / "index.html", f"""<!doctype html>
<html><head><meta charset='utf-8'><title>neutrino_emojis_other preview</title>
<style>body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;background:#f7f7f7;color:#222}}.card{{background:white;border:1px solid #ddd;border-radius:12px;padding:16px;margin:16px 0;box-shadow:0 2px 8px #0001}}img{{image-rendering:auto;max-width:100%;height:auto;border:1px solid #eee}}</style>
</head><body><h1>neutrino_emojis_other preview</h1><p>Deterministic sample contact sheets. Full package contains 10,000 icons, 10 themes and 4 PNG sizes.</p>{''.join(cards)}</body></html>""")


def create_docs(out: Path, specs: List[Spec], started_at: float) -> None:
    category_counts = {cat: 0 for cat in CATEGORY_COUNTS}
    for sp in specs: category_counts[sp.category] += 1
    write_text(out / "LICENSE.md", """CC0 1.0 Universal-style Public Domain Dedication

The generated neutrino_emojis_other icon artwork, metadata produced by the generator, and package-specific integration files are dedicated to the public domain to the fullest extent possible.

Where public-domain dedication is not legally available, the package author grants everyone a worldwide, royalty-free, non-exclusive, irrevocable license to copy, modify, distribute, perform, display, and use the generated artwork and package files for any purpose, without attribution or additional permission.

This file is a practical CC0-style dedication for the generated package. For the canonical CC0 1.0 Universal legal text, see Creative Commons.
""")
    write_text(out / "NOTICE.md", """neutrino_emojis_other provenance notice

This package was generated as original deterministic geometric artwork for the Neutrino Project.

No third-party emoji artwork, icon files, font files, or flag image files are bundled in this package.

The country-flag entries are stylized country-code flag badges generated from ISO-style country codes. They are not imported reproductions of government flag artwork and should be reviewed before use anywhere exact official national flag rendering is required.

The defense/military category uses simplified non-operational symbolic icons such as shields, helmets, targets, generic training markers and nonfunctional toy-blaster silhouettes. It does not include technical weapon diagrams or instructions.
""")
    readme = f"""# neutrino_emojis_other

`neutrino_emojis_other` is an original, normalized emoji-style icon package generated for the Neutrino Project.

## Contents

- 10,000 original emoji-style icons
- 10 color themes: {', '.join(THEMES.keys())}
- PNG sizes: {', '.join(str(s)+'x'+str(s) for s in SIZES)}
- 400,000 themed PNG files
- 10,000 master SVG files with CSS color variables
- Full `manifest.json` and `manifest.csv`
- C/C++ integration header: `include/neutrino_emojis_other.h`
- Preview contact sheets under `preview/`
- Regeneration/customization script under `tools/`

## Normalized visual style

The icons are built on a 128x128 coordinate grid with transparent backgrounds, rounded outlines, simplified emoji geometry, consistent margins, and small bottom-right badges for variants such as sparkle, alert, check, heart, music, motion and status.

## Categories

```json
{json.dumps(category_counts, indent=2)}
```

## Usage paths

Example PNG path:

```text
png/classic_yellow/128/things_tools_backpack_shadow_00.png
```

Example master SVG path:

```text
svg/master/things_tools_backpack_shadow_00.svg
```

## Theming

PNG files are pre-rendered for all themes. Master SVG files use CSS variables with defaults based on `classic_yellow`:

```css
--nt-primary, --nt-secondary, --nt-accent, --nt-accent2,
--nt-outline, --nt-feature, --nt-skin, --nt-skin2,
--nt-green, --nt-blue, --nt-red, --nt-purple, --nt-orange,
--nt-metal, --nt-brown, --nt-white, --nt-dark, --nt-bg
```

## License/provenance

The artwork in this package is original generated geometry with a CC0-style public-domain dedication. See `LICENSE.md` and `NOTICE.md`.
"""
    write_text(out / "README.md", readme)
    write_text(out / "themes.json", json.dumps(THEMES, indent=2))
    write_text(out / "category_summary.json", json.dumps(category_counts, indent=2))
    report = {
        "package": PKG,
        "generated_at_epoch": int(time.time()),
        "elapsed_seconds": round(time.time() - started_at, 2),
        "icon_count": len(specs),
        "theme_count": len(THEMES),
        "png_sizes": SIZES,
        "expected_png_files": len(specs) * len(THEMES) * len(SIZES),
        "expected_master_svg_files": len(specs),
        "category_counts": category_counts,
        "provenance": "Original deterministic geometric artwork; no third-party icon artwork bundled.",
    }
    write_text(out / "generation_report.json", json.dumps(report, indent=2))
    header_lines = [
        "#ifndef NEUTRINO_EMOJIS_OTHER_H",
        "#define NEUTRINO_EMOJIS_OTHER_H",
        "",
        "/* Generated metadata constants for the neutrino_emojis_other icon package. */",
        f"#define NEUTRINO_EMOJIS_OTHER_ICON_COUNT {len(specs)}",
        f"#define NEUTRINO_EMOJIS_OTHER_THEME_COUNT {len(THEMES)}",
        "#define NEUTRINO_EMOJIS_OTHER_SIZE_COUNT 4",
        "",
        "static const int NEUTRINO_EMOJIS_OTHER_SIZES[4] = {16, 32, 64, 128};",
        "static const char* const NEUTRINO_EMOJIS_OTHER_THEMES[10] = {",
    ]
    for t in THEMES: header_lines.append(f'    "{t}",')
    header_lines += ["};", "", "/* Full icon metadata is available in manifest.csv and manifest.json. */", "", "#endif /* NEUTRINO_EMOJIS_OTHER_H */", ""]
    write_text(out / "include" / "neutrino_emojis_other.h", "\n".join(header_lines))


def create_manifest(out: Path, specs: List[Spec]) -> None:
    manifest = []
    for sp in specs:
        row = asdict(sp)
        row["tags"] = list(sp.tags)
        row["svg_master"] = f"svg/master/{sp.name}.svg"
        row["png_paths"] = {theme: {str(sz): f"png/{theme}/{sz}/{sp.name}.png" for sz in SIZES} for theme in THEMES}
        manifest.append(row)
    write_text(out / "manifest.json", json.dumps({"package": PKG, "icons": manifest}, indent=2))
    with (out / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["uid", "name", "display_name", "category", "subcategory", "kind", "item", "variant", "style", "label", "description", "tags", "svg_master"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for sp in specs:
            w.writerow({
                "uid": sp.uid,
                "name": sp.name,
                "display_name": sp.display_name,
                "category": sp.category,
                "subcategory": sp.subcategory,
                "kind": sp.kind,
                "item": sp.item,
                "variant": sp.variant,
                "style": sp.style,
                "label": sp.label,
                "description": sp.description,
                "tags": ";".join(sp.tags),
                "svg_master": f"svg/master/{sp.name}.svg",
            })


def generate_package(root: Path, limit: Optional[int] = None, skip_png: bool = False) -> Path:
    started = time.time()
    out = root / PKG
    if out.exists(): shutil.rmtree(out)
    (out / "svg" / "master").mkdir(parents=True, exist_ok=True)
    specs = build_specs(limit)
    print(f"Generating {len(specs)} icons into {out}", flush=True)
    create_manifest(out, specs)
    create_docs(out, specs, started)
    # Copy generator into package tools.
    tools_dir = out / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    shutil.copy2(src, tools_dir / src.name)
    # Pre-create PNG directories for fewer mkdir calls.
    if not skip_png:
        for theme in THEMES:
            for sz in SIZES:
                (out / "png" / theme / str(sz)).mkdir(parents=True, exist_ok=True)
    # Generate assets.
    svg_master_dir = out / "svg" / "master"
    svg_master_dir.mkdir(parents=True, exist_ok=True)
    for n, sp in enumerate(specs, 1):
        icon = make_icon(sp)
        if not svg_master_dir.exists():
            svg_master_dir.mkdir(parents=True, exist_ok=True)
        (svg_master_dir / f"{sp.name}.svg").write_text(svg_icon(icon), encoding="utf-8")
        if not skip_png:
            for theme_name, theme in THEMES.items():
                img128 = render_icon(icon, theme, 128)
                for sz in SIZES:
                    img = img128 if sz == 128 else img128.resize((sz, sz), Image.Resampling.LANCZOS)
                    img.save(out / "png" / theme_name / str(sz) / f"{sp.name}.png")
        if n % 250 == 0 or n == len(specs):
            print(f"  assets {n}/{len(specs)}", flush=True)
    create_preview(specs, out)
    # Refresh report after generation/preview.
    create_docs(out, specs, started)
    print(f"Done package tree: {out}", flush=True)
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_files(out: Path) -> Dict[str, int]:
    png = sum(1 for _ in (out / "png").rglob("*.png")) if (out / "png").exists() else 0
    svg = sum(1 for _ in (out / "svg").rglob("*.svg")) if (out / "svg").exists() else 0
    total = sum(1 for _ in out.rglob("*"))
    return {"png_files": png, "svg_files": svg, "total_paths": total}


def make_archives(root: Path, out: Path) -> Tuple[Path, Path, Path]:
    zip_path = root / f"{PKG}.zip"
    tar_path = root / f"{PKG}.tar.gz"
    checksums = root / f"{PKG}_archive_checksums.txt"
    for p in [zip_path, tar_path, checksums]:
        if p.exists(): p.unlink()
    print("Creating zip archive...", flush=True)
    subprocess.run(["zip", "-qr", "-6", str(zip_path), PKG], cwd=str(root), check=True)
    print("Creating tar.gz archive...", flush=True)
    subprocess.run(["tar", "-czf", str(tar_path), PKG], cwd=str(root), check=True)
    lines = [
        f"{sha256(zip_path)}  {zip_path.name}",
        f"{sha256(tar_path)}  {tar_path.name}",
    ]
    checksums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Archives created.", flush=True)
    return zip_path, tar_path, checksums


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate neutrino_emojis_other")
    ap.add_argument("--root", default="/mnt/data", help="Output parent directory")
    ap.add_argument("--limit", type=int, default=None, help="Generate only first N specs for testing")
    ap.add_argument("--skip-png", action="store_true", help="Only generate SVG/docs")
    ap.add_argument("--archive", action="store_true", help="Create zip and tar.gz archives")
    args = ap.parse_args(argv)
    root = Path(args.root)
    out = generate_package(root, limit=args.limit, skip_png=args.skip_png)
    counts = count_files(out)
    (out / "file_counts.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
    print(json.dumps(counts, indent=2), flush=True)
    if args.archive:
        make_archives(root, out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
