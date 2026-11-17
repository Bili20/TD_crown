"""Campanário: bases nv1–nv3 e a camada de cima com o sino e o sineiro.

O Campanário não mira: a camada de cima não vira com flipX. Ela continua separada da base para o
sino balançar no pulso e para toda torre usar a mesma estrutura de view (base + camada de cima).
"""
import random
from dataclasses import dataclass
from PIL import Image
from pixel_canvas import Layer, stamp
from style_test import PLAYER, PLAYER_COLORS, PRESETS
from material_map import (Sprite, DEEP, DARK, BASE, LIGHT, SHINE, shade_volume, cast_shadow,
                          ambient_occlusion, recess, tile_roof, planks, pyramid_roof, plaster_wear,
                          team_pennant, team_shield, team_banner)
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


# --- Bases no pipeline em 5 etapas (material_map) --------------------------------------------------
def belfry_beam_row(level: CampanarioLevel) -> int:
    return turret_origin(level.turret_x, level.rail_top_y)[1] + level.bell_top - 1


def parapet(sprite: Sprite, left, right, rail):
    sprite.fill(left, rail, right, rail, "slate", "top")
    sprite.fill(left, rail + 1, right, rail + 2, "slate")


def frame_shape(wave: int):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    rail = LEVELS[1].rail_top_y
    sprite.fill(6, 39, 25, GROUND_Y, "whitewash")
    sprite.fill(5, 38, 26, 38, "slate", "top")
    for leg_x in (8, 23):
        sprite.fill(leg_x, rail + 3, leg_x, 37, "wood", tone=DARK)
    for x, y in zip(range(9, 23), range(rail + 3, 38)):
        sprite.set(x, y if y <= 37 else 37, "wood", tone=DARK)
    sprite.fill(6, rail, 25, rail, "wood", "top")
    sprite.fill(6, rail + 1, 25, rail + 2, "wood")
    team_pennant(sprite, 5, rail - 11, rail - 1, wave)
    return sprite


def frame_shading(sprite: Sprite):
    shade_volume(sprite, 6, 39, 25, GROUND_Y, ("whitewash",), shadow_columns=3)
    cast_shadow(sprite, 6, 25, 39, depth=1, materials=("whitewash",))
    sprite.fill(6, LEVELS[1].rail_top_y + 2, 25, LEVELS[1].rail_top_y + 2, "wood", tone=DARK)
    ambient_occlusion(sprite, 6, 25, GROUND_Y)


def frame_details(sprite: Sprite, rng):
    plaster_wear(sprite, 6, 39, 25, GROUND_Y, rng)
    planks(sprite, 6, LEVELS[1].rail_top_y + 1, 25, LEVELS[1].rail_top_y + 1, rng, vertical=False, nails=False)


def whitewashed_shape(wave: int):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    level = LEVELS[2]
    rail, beam = level.rail_top_y, belfry_beam_row(level)
    sprite.fill(8, rail + 3, 23, GROUND_Y, "whitewash")
    sprite.fill(14, 40, 17, GROUND_Y, "wood")
    sprite.fill(15, 39, 16, 39, "wood")
    parapet(sprite, 7, 24, rail)
    for pillar_left in (6, 24):
        sprite.fill(pillar_left, beam, pillar_left + 1, rail - 1, "whitewash")
    sprite.fill(6, beam, 25, beam, "wood", tone=DARK)
    pyramid_roof(sprite, 4, 27, beam - 1, beam - 7)
    sprite.set(15, beam - 8, "bronze", tone=LIGHT)
    sprite.set(16, beam - 8, "bronze")
    team_shield(sprite, 13, rail + 3)
    team_pennant(sprite, 16, beam - 12, beam - 9, wave)
    return sprite


def whitewashed_shading(sprite: Sprite):
    level = LEVELS[2]
    rail, beam = level.rail_top_y, belfry_beam_row(level)
    shade_volume(sprite, 8, rail + 3, 23, GROUND_Y, ("whitewash",), shadow_columns=3)
    cast_shadow(sprite, 8, 23, rail + 3, depth=2, materials=("whitewash",))
    for pillar_left in (6, 24):
        for y in range(beam, rail):
            sprite.shift(pillar_left + 1, y, -1, ("whitewash",))
    recess(sprite, 14, 39, 17, GROUND_Y, ("wood",))
    ambient_occlusion(sprite, 8, 23, GROUND_Y, ("whitewash",))


def whitewashed_details(sprite: Sprite, rng):
    level = LEVELS[2]
    rail, beam = level.rail_top_y, belfry_beam_row(level)
    plaster_wear(sprite, 8, rail + 8, 23, GROUND_Y, rng)
    tile_roof(sprite, range(beam - 7, beam), 15.5, "slate", lit_tone=LIGHT, shadow_tone=BASE)
    sprite.fill(4, beam - 1, 27, beam - 1, "slate", tone=DEEP)
    planks(sprite, 14, 40, 17, GROUND_Y, rng, plank_width=2, nails=False)


def tall_tower_shape(wave: int):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    level = LEVELS[3]
    rail, beam = level.rail_top_y, belfry_beam_row(level)
    sprite.fill(7, rail + 3, 24, GROUND_Y, "whitewash")
    for slit_x in (9, 21):
        sprite.fill(slit_x, rail + 5, slit_x, rail + 8, "opening")
    sprite.fill(7, rail + 14, 24, rail + 14, "slate")
    sprite.fill(14, rail + 15, 17, GROUND_Y, "wood")
    parapet(sprite, 6, 25, rail)
    for pillar_left in (5, 25):
        sprite.fill(pillar_left, beam, pillar_left + 1, rail - 1, "whitewash")
    sprite.fill(5, beam, 26, beam, "wood", tone=DARK)
    pyramid_roof(sprite, 3, 28, beam - 1, beam - 8)
    sprite.fill(2, beam - 1, 29, beam - 1, "slate")
    sprite.set(15, beam - 9, "bronze", tone=SHINE)
    sprite.set(16, beam - 9, "bronze")
    team_banner(sprite, 13, rail + 4, 10)
    team_pennant(sprite, 16, beam - 12, beam - 10, wave)
    return sprite


def tall_tower_shading(sprite: Sprite):
    level = LEVELS[3]
    rail, beam = level.rail_top_y, belfry_beam_row(level)
    shade_volume(sprite, 7, rail + 3, 24, GROUND_Y, ("whitewash",), shadow_columns=3)
    cast_shadow(sprite, 7, 24, rail + 3, depth=2, materials=("whitewash",))
    cast_shadow(sprite, 7, 24, rail + 15, depth=1, materials=("whitewash",))
    for pillar_left in (5, 25):
        for y in range(beam, rail):
            sprite.shift(pillar_left + 1, y, -1, ("whitewash",))
    recess(sprite, 14, rail + 15, 17, GROUND_Y, ("wood",))
    ambient_occlusion(sprite, 7, 24, GROUND_Y, ("whitewash",))


def tall_tower_details(sprite: Sprite, rng):
    level = LEVELS[3]
    rail, beam = level.rail_top_y, belfry_beam_row(level)
    for left, right in ((8, 12), (19, 23)):
        plaster_wear(sprite, left, rail + 5, right, rail + 13, rng)
    plaster_wear(sprite, 8, rail + 16, 23, GROUND_Y, rng)
    tile_roof(sprite, range(beam - 8, beam - 1), 15.5, "slate", lit_tone=LIGHT, shadow_tone=BASE)
    sprite.fill(2, beam - 1, 29, beam - 1, "slate", tone=DEEP)
    planks(sprite, 14, rail + 15, 17, GROUND_Y, rng, plank_width=2, nails=False)


SHAPES = {1: frame_shape, 2: whitewashed_shape, 3: tall_tower_shape}
SHADERS = {1: frame_shading, 2: whitewashed_shading, 3: tall_tower_shading}
DETAILS = {1: frame_details, 2: whitewashed_details, 3: tall_tower_details}


def build_base(level_number: int, wave: int = 0, stage: int = 5) -> Image.Image:
    sprite = SHAPES[level_number](wave)
    if stage == 1:
        return sprite.render(silhouette=True)
    sprite.reset_tones()
    if stage >= 3:
        SHADERS[level_number](sprite)
    if stage >= 4:
        DETAILS[level_number](sprite, random.Random(level_number * 17))
    return sprite.render()


def draw_base(level_number: int, wave: int) -> Image.Image:
    return build_base(level_number, wave)


def compose(level_number: int, pose: BellPose, preset=None) -> Image.Image:
    level = LEVELS[level_number]
    return compose_tower(draw_base(level_number, pose.wave), draw_turret(level_number, pose),
                         turret_origin(level.turret_x, level.rail_top_y), preset)


if __name__ == "__main__":
    from balista import row_of
    frames = [compose(level, BellPose(), PRESETS["real"]) for level in (1, 2, 3)]
    frames += [compose(level, BellPose(), PRESETS["rubi"]) for level in (1, 2, 3)]
    row_of(frames, gap=4, scale=6).save("campanario_preview.png")
