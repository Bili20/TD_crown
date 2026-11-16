"""Campanário: bases nv1–nv3 e a camada de cima com o sino e o sineiro.

O Campanário não mira: a camada de cima não vira com flipX. Ela continua separada da base para o
sino balançar no pulso e para toda torre usar a mesma estrutura de view (base + camada de cima).
"""
from dataclasses import dataclass
from PIL import Image
from pixel_canvas import Layer, stamp
from style_test import PLAYER, PLAYER_COLORS, PRESETS
from tower_parts import (BASE_WIDTH, BASE_HEIGHT, GROUND_Y, TURRET_WIDTH, TURRET_HEIGHT, WAIST_ROW,
                         WOOD, IRON, OPENING,
                         put, fill, draw_line, draw_pennant, draw_shield, draw_banner, erase_below,
                         layers_to_image, compose_tower, turret_origin)

WHITEWASH = PLAYER.ramp("WHITEWASH")
SLATE = PLAYER.ramp("SLATE")
BRONZE = PLAYER.ramp("BRONZE")

COLORS = {
    **PLAYER_COLORS,
    "1": BRONZE.dark, "2": BRONZE.base, "3": BRONZE.light, "4": BRONZE.shine,
    "n": WOOD.dark, "m": WOOD.base,
    "i": IRON.dark, "K": IRON.base, "M": IRON.light,
}

# Sineiros virados para o sino (direita), cortados na cintura pelo parapeito. Malho de madeira na mão.
RINGER_NOVICE = [
    "......MM.",
    "...bb.MK.",
    "..bbbc.m.",
    ".abbbbcm.",
    ".aotuuot.",
    ".asttss..",
    "..bbbbb..",
    ".abbbbb..",
    ".abbbba..",
]
RINGER_JOURNEYMAN = [
    "......MM.",
    "...c..MK.",
    "..cbb..m.",
    ".dbbbbdm.",
    "deeeeeedm",
    ".otuuto.t",
    "..stts.b.",
    ".abwbbbb.",
    ".abbbba..",
    ".deeeed..",
]
RINGER_MASTER = [
    "...cc..MM",
    "..cbbc.MK",
    ".dbbbbd.m",
    "deeeeeedm",
    ".otuuto.t",
    "..stts.fb",
    "fefbbefe.",
    ".ebwwbe..",
    ".ebwwbe..",
    ".deeeed..",
]

BELL_SMALL = [
    ".n1n.",
    ".212.",
    "12342",
    "12332",
    "12332",
    "11111",
    "..i..",
]
BELL_MEDIUM = [
    ".nnnnn.",
    "..121..",
    ".12342.",
    ".12332.",
    ".12332.",
    "1223322",
    "1111111",
    "...i...",
]
BELL_LARGE = [
    ".nnnnnnn.",
    "...121...",
    "..12342..",
    ".1233422.",
    ".1233322.",
    ".1233322.",
    "122333322",
    "111111111",
    "....i....",
]


@dataclass(frozen=True)
class CampanarioLevel:
    ringer: list[str]
    bell: list[str]
    bell_left: int
    bell_top: int
    rail_top_y: int
    turret_x: int
    frame_posts: bool      # nv1: a armação do sino vem na camada de cima


LEVELS = {
    1: CampanarioLevel(RINGER_NOVICE, BELL_SMALL, 12, 4, 32, 6, True),
    2: CampanarioLevel(RINGER_JOURNEYMAN, BELL_MEDIUM, 11, 3, 32, 6, False),
    3: CampanarioLevel(RINGER_MASTER, BELL_LARGE, 10, 2, 26, 6, False),
}


@dataclass(frozen=True)
class BellPose:
    ringer_y: int = 0
    mallet_raised: bool = True
    bell_swing: int = 0     # -1/0/+1: desloca a boca do sino
    wave: int = 0


def draw_turret(level_number: int, pose: BellPose) -> Image.Image:
    level = LEVELS[level_number]
    frame_layer = Layer()
    if level.frame_posts:
        post_left, post_right = level.bell_left - 2, level.bell_left + len(level.bell[0]) + 1
        fill(frame_layer, post_left, 1, post_right, 1, WOOD.light)
        fill(frame_layer, post_left, 2, post_right, 2, WOOD.dark)
        for post_x in (post_left, post_right):
            fill(frame_layer, post_x, 2, post_x, WAIST_ROW, WOOD.base)
    bell_layer = Layer()
    stamp(bell_layer, level.bell, level.bell_left, level.bell_top, COLORS)
    if pose.bell_swing:
        shifted = Layer()
        for (x, y), color in bell_layer.pixels.items():
            shift = pose.bell_swing if y >= level.bell_top + len(level.bell) // 2 else 0
            shifted.pixels[(x + shift, y)] = color
        bell_layer = shifted
    ringer_layer = Layer()
    ringer_top = WAIST_ROW + 1 - len(level.ringer) + pose.ringer_y
    stamp(ringer_layer, level.ringer, 1, ringer_top, COLORS)
    erase_below(ringer_layer, WAIST_ROW)
    return layers_to_image(TURRET_WIDTH, TURRET_HEIGHT, frame_layer, bell_layer, ringer_layer)


def whitewash_wall(layer: Layer, left: int, top: int, right: int, bottom: int):
    fill(layer, left, top, right, bottom, WHITEWASH.base)
    fill(layer, left, top, left, bottom, WHITEWASH.light)
    fill(layer, right - 2, top, right, bottom, WHITEWASH.dark)
    # Pedras aparecendo sob a cal, poucas e espaçadas para não virar textura.
    for x, y in [(left + 3, top + 4), (right - 4, top + 9), (left + 5, bottom - 3), (right - 3, bottom - 1)]:
        if top <= y <= bottom:
            put(layer, x, y, WHITEWASH.dark)
            put(layer, x + 1, y, WHITEWASH.dark)


def slate_roof(layer: Layer, left: int, right: int, bottom: int, peak_y: int):
    height = bottom - peak_y
    center = (left + right) / 2
    for row in range(peak_y, bottom + 1):
        half = (right - left) / 2 * (row - peak_y + 1) / (height + 1)
        row_left, row_right = round(center - half), round(center + half)
        for column in range(row_left, row_right + 1):
            color = SLATE.base
            if column <= center - 1:
                color = SLATE.light
            if (row - peak_y) % 2 == 1 and column % 3 == 0:
                color = SLATE.dark
            put(layer, column, row, color)
    fill(layer, left, bottom, right, bottom, SLATE.dark)


def belfry_parapet(layer: Layer, left: int, right: int, rail_top: int):
    fill(layer, left, rail_top, right, rail_top, SLATE.light)
    fill(layer, left, rail_top + 1, right, rail_top + 1, SLATE.base)
    fill(layer, left, rail_top + 2, right, rail_top + 2, SLATE.dark)


# --- nv1: armação de madeira com sino pequeno -----------------------------------------------------
def base_frame(wave: int) -> Layer:
    layer = Layer()
    level = LEVELS[1]
    rail = level.rail_top_y
    # Sapata de pedra caiada.
    whitewash_wall(layer, 6, 39, 25, GROUND_Y)
    fill(layer, 5, 38, 26, 38, SLATE.base)
    # Estrado de madeira com travessas em X.
    for leg_x in (8, 23):
        fill(layer, leg_x, rail + 3, leg_x, 37, WOOD.dark)
    draw_line(layer, (9, rail + 4), (22, 37), WOOD.dark)
    draw_line(layer, (22, rail + 4), (9, 37), WOOD.dark)
    fill(layer, 6, rail, 25, rail, WOOD.light)
    fill(layer, 6, rail + 1, 25, rail + 2, WOOD.base)
    fill(layer, 6, rail + 2, 25, rail + 2, WOOD.dark)
    draw_pennant(layer, 5, rail - 11, rail - 1, wave)
    return layer


def belfry_beam_row(level: CampanarioLevel) -> int:
    return turret_origin(level.turret_x, level.rail_top_y)[1] + level.bell_top - 1


# --- nv2: campanário caiado com telhado de ardósia -------------------------------------------------
def base_whitewashed(wave: int) -> Layer:
    layer = Layer()
    level = LEVELS[2]
    rail = level.rail_top_y
    beam = belfry_beam_row(level)
    whitewash_wall(layer, 8, rail + 3, 23, GROUND_Y)
    fill(layer, 14, 40, 17, GROUND_Y, OPENING)
    fill(layer, 15, 39, 16, 39, OPENING)
    draw_shield(layer, 13, rail + 3)
    belfry_parapet(layer, 7, 24, rail)
    # Pilares do campanário e o telhado acima do sino.
    for pillar_left in (6, 24):
        fill(layer, pillar_left, beam, pillar_left + 1, rail - 1, WHITEWASH.base)
        fill(layer, pillar_left + 1, beam, pillar_left + 1, rail - 1, WHITEWASH.dark)
    fill(layer, 6, beam, 25, beam, WOOD.dark)
    slate_roof(layer, 4, 27, beam - 1, beam - 7)
    put(layer, 15, beam - 8, BRONZE.light)
    put(layer, 16, beam - 8, BRONZE.base)
    draw_pennant(layer, 16, beam - 12, beam - 9, wave)
    return layer


# --- nv3: torre sineira alta com estandarte -------------------------------------------------------
def base_tall_tower(wave: int) -> Layer:
    layer = Layer()
    level = LEVELS[3]
    rail = level.rail_top_y
    beam = belfry_beam_row(level)
    whitewash_wall(layer, 7, rail + 3, 24, GROUND_Y)
    draw_banner(layer, 13, rail + 4, 10)
    for slit_x in (9, 21):
        fill(layer, slit_x, rail + 5, slit_x, rail + 8, OPENING)
    fill(layer, 7, rail + 14, 24, rail + 14, SLATE.base)
    fill(layer, 14, rail + 15, 17, GROUND_Y, OPENING)
    belfry_parapet(layer, 6, 25, rail)
    for pillar_left in (5, 25):
        fill(layer, pillar_left, beam, pillar_left + 1, rail - 1, WHITEWASH.base)
        fill(layer, pillar_left + 1, beam, pillar_left + 1, rail - 1, WHITEWASH.dark)
    fill(layer, 5, beam, 26, beam, WOOD.dark)
    slate_roof(layer, 3, 28, beam - 1, beam - 8)
    fill(layer, 2, beam - 1, 29, beam - 1, SLATE.dark)
    put(layer, 15, beam - 9, BRONZE.shine)
    put(layer, 16, beam - 9, BRONZE.base)
    draw_pennant(layer, 16, beam - 13, beam - 10, wave)
    return layer


BASES = {1: base_frame, 2: base_whitewashed, 3: base_tall_tower}


def draw_base(level_number: int, wave: int) -> Image.Image:
    return layers_to_image(BASE_WIDTH, BASE_HEIGHT, BASES[level_number](wave))


def compose(level_number: int, pose: BellPose, preset=None) -> Image.Image:
    level = LEVELS[level_number]
    return compose_tower(draw_base(level_number, pose.wave), draw_turret(level_number, pose),
                         turret_origin(level.turret_x, level.rail_top_y), preset)


if __name__ == "__main__":
    from balista import row_of
    frames = [compose(level, BellPose(), PRESETS["real"]) for level in (1, 2, 3)]
    frames += [compose(level, BellPose(), PRESETS["rubi"]) for level in (1, 2, 3)]
    row_of(frames, gap=4, scale=6).save("campanario_preview.png")
