"""Alquimista: bases nv1–nv3, operador que arremessa o frasco, o frasco e a poça ácida.

O operador mira e vira com flipX, como a besta da Balista. A poça é uma zona no chão (raio de 1 tile)
em ACID, que contrasta com a terra do caminho e não se confunde com o HELLFIRE dos demônios.
"""
import math
import random
from dataclasses import dataclass
from PIL import Image
from pixel_canvas import Layer, stamp, ellipse_pixels
from style_test import PLAYER, PLAYER_COLORS, PRESETS
from material_map import (Sprite, DEEP, DARK, BASE, LIGHT, SHINE, shade_volume, cast_shadow,
                          ambient_occlusion, brick_courses, tile_roof, planks, plaster_wear,
                          team_pennant, team_shield, team_banner)
from tower_parts import (BASE_WIDTH, BASE_HEIGHT, GROUND_Y, TURRET_WIDTH, TURRET_HEIGHT, WAIST_ROW,
                         WOOD, IRON, STONE, OPENING, PRIMARY_DARK, PRIMARY_LIGHT,
                         put, fill, draw_pennant, draw_shield, draw_banner, erase_below,
                         layers_to_image, compose_tower, turret_origin)

BRICK = PLAYER.ramp("BRICK")
COPPER = PLAYER.ramp("COPPER")
GLASS = PLAYER.ramp("GLASS")
ACID = PLAYER.ramp("ACID")

COLORS = {
    **PLAYER_COLORS,
    "n": WOOD.dark, "m": WOOD.base, "M": WOOD.light,
    "i": IRON.dark, "j": IRON.base, "k": IRON.light,
    "r": BRICK.dark, "R": BRICK.base, "q": BRICK.light,
    "1": COPPER.dark, "2": COPPER.base, "3": COPPER.light, "4": COPPER.shine,
    "g": GLASS.dark, "G": GLASS.base, "H": GLASS.light, "J": GLASS.shine,
    "x": ACID.dark, "y": ACID.base, "Y": ACID.light, "Z": ACID.shine,
}

# Operadores virados para a direita, com o frasco erguido na mão de trás, pronto para o arremesso.
ALCHEMIST_APPRENTICE = [
    "....bb......",
    "...bbbc..m..",
    "..abbbbc.Hy.",
    ".abbbbbbcyx.",
    ".aotuutobt..",
    ".aasttsabb..",
    ".abbbbbbb...",
    ".abbbbbba...",
    ".abbbbbba...",
]
ALCHEMIST_ADEPT = [
    "............",
    "...bbbc..m..",
    "..bbbbbc.Hy.",
    "..HJgHJb.yx.",
    "..otuuto.n..",
    "...stts.bn..",
    "..bmMMmbb...",
    "..bmMmmb....",
    "..bmmmmb....",
]
ALCHEMIST_MASTER = [
    "....cb......",
    "...cbbb.....",
    "..cbbbbb..m.",
    ".cbbbbbbb.Hy",
    "deeeeeeed.yx",
    ".dotuutod.t.",
    ".ebsttsbebt.",
    "ebbbbbbbbe..",
    "ebbbwwbbbe..",
    "ebbbbbbbbe..",
]

FLASK = [
    "........",
    "...mm...",
    "...HG...",
    "..gYyg..",
    ".gyZyyg.",
    ".gyyyxg.",
    "..gxxg..",
    "........",
]


@dataclass(frozen=True)
class AlchemistLevel:
    operator: list[str]
    operator_left: int
    rail_top_y: int
    turret_x: int


LEVELS = {
    1: AlchemistLevel(ALCHEMIST_APPRENTICE, 4, 31, 6),
    2: AlchemistLevel(ALCHEMIST_ADEPT, 4, 26, 6),
    3: AlchemistLevel(ALCHEMIST_MASTER, 4, 21, 6),
}


@dataclass(frozen=True)
class ThrowPose:
    operator_y: int = 0
    wave: int = 0
    bubble: int = 0


def draw_turret(level_number: int, pose: ThrowPose) -> Image.Image:
    level = LEVELS[level_number]
    operator_layer = Layer()
    top = WAIST_ROW + 1 - len(level.operator) + pose.operator_y
    stamp(operator_layer, level.operator, level.operator_left, top, COLORS)
    erase_below(operator_layer, WAIST_ROW)
    return layers_to_image(TURRET_WIDTH, TURRET_HEIGHT, operator_layer)


def green_smoke(layer: Layer, x: int, top: int, phase: int):
    for index, (offset_x, offset_y) in enumerate([(0, 0), (1, -3), (0, -6)]):
        drift = (phase + index) % 2
        y = top + offset_y
        put(layer, x + offset_x + drift, y, ACID.light)
        put(layer, x + offset_x + drift + 1, y, ACID.base if index else ACID.light)
        put(layer, x + offset_x + drift, y - 1, ACID.shine if index == 2 else ACID.light)


def bench_flask(layer: Layer, x: int, bottom: int, liquid_tone):
    put(layer, x, bottom - 2, GLASS.light)
    put(layer, x, bottom - 1, liquid_tone)
    put(layer, x + 1, bottom - 1, GLASS.dark)
    put(layer, x, bottom, GLASS.dark)
    put(layer, x + 1, bottom, liquid_tone)


def cauldron(layer: Layer, left: int, top: int):
    stamp(layer, [
        ".yYyZy.",
        "jkkkkkj",
        "ijjjjji",
        "ijjjjji",
        ".iiiii.",
        ".r.R.r.",
    ], left, top, COLORS)


def alembic(layer: Layer, left: int, top: int):
    # Pote de cobre com cúpula; o tubo de vidro desce até o frasco coletor.
    stamp(layer, [
        "..44......",
        ".4433.....",
        "3443322...",
        "33333221g.",
        ".333221..g",
        "..rRr....H",
        "..rqr...gyg",
        "..rRr...gyg",
    ], left, top, COLORS)


# --- Bases no pipeline em 5 etapas (material_map) --------------------------------------------------
def acid_smoke(sprite: Sprite, x: int, top: int, phase: int):
    for index, (offset_x, offset_y) in enumerate([(0, 0), (1, -3), (0, -6)]):
        drift = (phase + index) % 2
        sprite.set(x + offset_x + drift, top + offset_y, "acid", tone=LIGHT)
        sprite.set(x + offset_x + drift + 1, top + offset_y, "acid", tone=BASE if index else LIGHT)
        sprite.set(x + offset_x + drift, top + offset_y - 1, "acid", tone=SHINE if index == 2 else LIGHT)


def props_layer(pose: ThrowPose, level_number: int) -> Layer:
    layer = Layer()
    rail = LEVELS[level_number].rail_top_y
    if level_number == 1:
        cauldron(layer, 1, 37)
        for x, tone in ((21, ACID.base), (23, GLASS.base)):
            bench_flask(layer, x, rail - 1, tone)
    elif level_number == 2:
        alembic(layer, 20, 37)
    return layer


# nv1: bancada com caldeirão
def bench_shape(pose: ThrowPose):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    rail = LEVELS[1].rail_top_y
    for leg_x in (8, 24):
        sprite.fill(leg_x, rail + 3, leg_x + 1, GROUND_Y, "wood", tone=DARK)
    sprite.fill(9, rail + 7, 24, rail + 7, "wood", tone=DARK)
    sprite.fill(7, rail, 26, rail, "wood", "top")
    sprite.fill(7, rail + 1, 26, rail + 2, "wood")
    sprite.fill(12, 41, 22, GROUND_Y, "brick")
    sprite.fill(12, 41, 22, 41, "brick", "top")
    team_pennant(sprite, 26, rail - 10, rail - 1, pose.wave)
    return sprite


def bench_shading(sprite: Sprite, pose: ThrowPose):
    rail = LEVELS[1].rail_top_y
    sprite.fill(7, rail + 2, 26, rail + 2, "wood", tone=DEEP)
    shade_volume(sprite, 12, 42, 22, GROUND_Y, ("brick",))
    cast_shadow(sprite, 9, 24, rail + 3, depth=1, materials=("wood",))


def bench_details(sprite: Sprite, pose: ThrowPose, rng):
    rail = LEVELS[1].rail_top_y
    planks(sprite, 7, rail + 1, 26, rail + 1, rng, vertical=False, plank_width=5, nails=False)
    brick_courses(sprite, 12, 42, 22, GROUND_Y, rng)
    for x in (10, 17, 23):
        sprite.set(x, rail, "wood", tone=SHINE)
    acid_smoke(sprite, 3, 34, pose.bubble)


# nv2: cabana de taipa com alambique (telhado de telha de tijolo atrás do operador)
def hut_shape(pose: ThrowPose):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    rail = LEVELS[2].rail_top_y
    for row in range(rail - 12, rail):
        half = (row - (rail - 12)) + 2
        sprite.fill(max(3, 16 - half), row, min(28, 16 + half - 1), row, "brick", "top")
    sprite.fill(22, rail - 11, 23, rail - 4, "copper", tone=LIGHT)
    sprite.fill(21, rail - 12, 24, rail - 12, "copper", tone=SHINE)
    sprite.fill(9, rail - 8, 20, rail - 1, "wood", tone=DARK)
    sprite.fill(10, rail - 7, 19, rail - 1, "opening")
    sprite.fill(6, rail + 3, 25, GROUND_Y, "brick", tone=LIGHT)
    sprite.fill(10, 38, 13, GROUND_Y, "opening")
    sprite.fill(9, 36, 14, 37, "primary")
    sprite.fill(9, rail + 4, 11, rail + 7, "glass")
    sprite.fill(5, rail, 26, rail, "wood", "top")
    sprite.fill(5, rail + 1, 26, rail + 2, "wood")
    team_shield(sprite, 17, rail + 4)
    team_pennant(sprite, 16, rail - 20, rail - 13, pose.wave)
    return sprite


def hut_shading(sprite: Sprite, pose: ThrowPose):
    rail = LEVELS[2].rail_top_y
    for (x, y), cell in sprite.cells.items():
        if cell.material == "brick" and cell.plane == "top":
            cell.tone = BASE if x < 16 else DARK
    for (x, y), cell in list(sprite.cells.items()):
        if cell.material == "brick" and cell.plane == "front":
            cell.tone = LIGHT
    shade_volume(sprite, 6, rail + 3, 25, GROUND_Y, ("brick",), shadow_columns=3)
    cast_shadow(sprite, 6, 25, rail + 3, depth=2, materials=("brick",))
    sprite.fill(9, 36, 14, 36, "primary", tone=LIGHT)
    sprite.fill(9, 37, 14, 37, "primary", tone=DARK)
    sprite.fill(5, rail + 2, 26, rail + 2, "wood", tone=DEEP)
    ambient_occlusion(sprite, 6, 25, GROUND_Y, ("brick",))


def hut_details(sprite: Sprite, pose: ThrowPose, rng):
    rail = LEVELS[2].rail_top_y
    tile_roof(sprite, range(rail - 12, rail), 16, "brick", lit_tone=LIGHT, shadow_tone=BASE)
    # Taipa: reboco claro com tijolo à mostra onde caiu, vigas de madeira nas quinas e no meio.
    plaster_wear(sprite, 7, rail + 3, 24, GROUND_Y, rng, material="brick", exposed="brick")
    for beam_x in (6, 25):
        sprite.fill(beam_x, rail + 3, beam_x, GROUND_Y, "wood", tone=DARK)
    sprite.fill(6, rail + 10, 25, rail + 10, "wood", tone=DARK)
    sprite.set(9, rail + 4, "glass", tone=SHINE)
    sprite.fill(9, rail + 6, 11, rail + 7, "acid")
    sprite.fill(8, rail + 3, 12, rail + 3, "wood", tone=DARK)
    planks(sprite, 5, rail + 1, 26, rail + 1, rng, vertical=False, plank_width=5, nails=False)
    acid_smoke(sprite, 22, rail - 14, pose.bubble)


# nv3: torre com cúpula de cobre e vidro
def dome_shape(pose: ThrowPose):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    rail = LEVELS[3].rail_top_y
    for x, y, _, _ in ellipse_pixels(15.5, rail - 1, 10.5, 13):
        if y <= rail - 1:
            sprite.set(x, y, "copper", "top")
    sprite.fill(14, rail - 16, 17, rail - 14, "copper", "top")
    sprite.fill(7, rail + 3, 24, GROUND_Y, "brick")
    for window_x in (9, 21):
        sprite.fill(window_x, rail + 7, window_x + 1, rail + 10, "glass")
    sprite.fill(14, 39, 17, GROUND_Y, "opening")
    sprite.fill(5, rail, 26, rail, "stone", "top")
    sprite.fill(5, rail + 1, 26, rail + 2, "stone")
    team_banner(sprite, 13, rail + 4, 10)
    team_pennant(sprite, 26, rail - 15, rail - 1, pose.wave)
    return sprite


def dome_shading(sprite: Sprite, pose: ThrowPose):
    rail = LEVELS[3].rail_top_y
    for (x, y), cell in sprite.cells.items():
        if cell.material == "copper":
            horizontal = (x - 15.5) / 10.5
            cell.tone = SHINE if horizontal < -0.75 else (LIGHT if horizontal < 0.5 else BASE)
    shade_volume(sprite, 7, rail + 3, 24, GROUND_Y, ("brick",))
    cast_shadow(sprite, 7, 24, rail + 3, depth=2, materials=("brick",))
    sprite.fill(5, rail + 2, 26, rail + 2, "stone", tone=DARK)
    ambient_occlusion(sprite, 7, 24, GROUND_Y, ("brick",))


def dome_details(sprite: Sprite, pose: ThrowPose, rng):
    rail = LEVELS[3].rail_top_y
    brick_courses(sprite, 7, rail + 3, 24, GROUND_Y, rng)
    for rib_x in (10, 15, 20):
        for y in range(rail - 12, rail):
            if sprite.is_material(rib_x, y, "copper"):
                sprite.set(rib_x, y, "glass", tone=LIGHT if y % 3 else BASE)
                if y % 3 == 0:
                    sprite.set(rib_x, y, "acid", tone=LIGHT)
    sprite.set(15, rail - 17, "glass", tone=SHINE)
    for window_x in (9, 21):
        sprite.set(window_x, rail + 7, "glass", tone=SHINE)
        sprite.fill(window_x, rail + 9, window_x + 1, rail + 10, "acid")
    for x in range(5, 27, 4):
        sprite.set(x, rail + 1, "stone", tone=DARK)


SHAPES = {1: bench_shape, 2: hut_shape, 3: dome_shape}
SHADERS = {1: bench_shading, 2: hut_shading, 3: dome_shading}
DETAILS = {1: bench_details, 2: hut_details, 3: dome_details}


def build_base(level_number: int, pose: ThrowPose, stage: int = 5) -> Image.Image:
    sprite = SHAPES[level_number](pose)
    props = layers_to_image(BASE_WIDTH, BASE_HEIGHT, props_layer(pose, level_number))
    if stage == 1:
        image = sprite.render(silhouette=True)
        mask = props.split()[3].point(lambda alpha: 255 if alpha else 0)
        image.paste(Image.new("RGBA", image.size, (60, 56, 80, 255)), (0, 0), mask)
        return image
    sprite.reset_tones()
    if stage >= 3:
        SHADERS[level_number](sprite, pose)
    if stage >= 4:
        DETAILS[level_number](sprite, pose, random.Random(level_number * 23))
    image = sprite.render()
    image.alpha_composite(props)
    return image


def draw_base(level_number: int, pose: ThrowPose) -> Image.Image:
    return build_base(level_number, pose)


def compose(level_number: int, pose: ThrowPose, preset=None) -> Image.Image:
    level = LEVELS[level_number]
    return compose_tower(draw_base(level_number, pose), draw_turret(level_number, pose),
                         turret_origin(level.turret_x, level.rail_top_y), preset)


def draw_flask() -> Image.Image:
    layer = Layer()
    stamp(layer, FLASK, 0, 0, COLORS)
    return layers_to_image(8, 8, layer)


# --- Poça ácida (zona de 1 tile de raio) ----------------------------------------------------------
PUDDLE_SIZE = 32


def draw_puddle(phase: int = 0) -> Image.Image:
    layer = Layer()
    # Borda com mossas fixas para não ler como disco perfeito; o raio bate com a área do sim.
    dents = {(2, 13), (2, 14), (29, 18), (29, 19), (12, 29), (13, 29), (20, 2), (21, 2), (6, 5), (25, 26)}
    area = {(x, y) for x, y, _, _ in ellipse_pixels(15.5, 15.5, 14.5, 14.5) if (x, y) not in dents}
    for x, y in area:
        neighbors = sum((x + step_x, y + step_y) in area for step_x, step_y in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        put(layer, x, y, ACID.base if neighbors < 4 else ACID.dark)
    # Ondulações em arco (base) e reflexo do lado da luz: lê como líquido, não como tufo de grama.
    for radius, start_angle, end_angle in ((7.5, 30, 80), (11.5, 300, 340)):
        for step in range(start_angle, end_angle, 4):
            x = round(15.5 + radius * math.cos(math.radians(step)))
            y = round(15.5 + radius * math.sin(math.radians(step)))
            if (x, y) in area:
                put(layer, x, y, ACID.base)
    for x, y in [(8, 7), (9, 7), (10, 7), (7, 8), (12, 8), (13, 8)]:
        if (x, y) in area:
            put(layer, x, y, ACID.light)
    bubbles = [[(15, 16), (21, 19), (11, 20), (19, 11)], [(17, 14), (20, 21), (12, 18), (22, 12)]][phase % 2]
    for x, y in bubbles:
        put(layer, x, y, ACID.shine)
        put(layer, x, y + 1, ACID.base)
    return layers_to_image(PUDDLE_SIZE, PUDDLE_SIZE, layer)


if __name__ == "__main__":
    from balista import row_of
    frames = [compose(level, ThrowPose(), PRESETS["real"]) for level in (1, 2, 3)]
    frames += [compose(level, ThrowPose(), PRESETS["rubi"]) for level in (1, 2, 3)]
    row_of(frames + [draw_puddle(), draw_flask()], gap=4, scale=6).save("alquimista_preview.png")
