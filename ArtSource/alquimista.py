"""Alquimista: bases nv1–nv3, operador que arremessa o frasco, o frasco e a poça ácida.

O operador mira e vira com flipX, como a besta da Balista. A poça é uma zona no chão (raio de 1 tile)
em ACID, que contrasta com a terra do caminho e não se confunde com o HELLFIRE dos demônios.
"""
import math
from dataclasses import dataclass
from PIL import Image
from pixel_canvas import Layer, stamp, ellipse_pixels
from style_test import PLAYER, PLAYER_COLORS, PRESETS
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


# --- nv1: bancada com caldeirão -------------------------------------------------------------------
def base_bench(pose: ThrowPose) -> Layer:
    layer = Layer()
    rail = LEVELS[1].rail_top_y
    cauldron(layer, 1, 37)
    green_smoke(layer, 3, 34, pose.bubble)
    # Bancada: tampo na altura do parapeito, com frascos e pés de madeira.
    for leg_x in (8, 24):
        fill(layer, leg_x, rail + 3, leg_x + 1, GROUND_Y, WOOD.dark)
    fill(layer, 9, rail + 7, 24, rail + 7, WOOD.dark)
    fill(layer, 7, rail, 26, rail, WOOD.light)
    fill(layer, 7, rail + 1, 26, rail + 2, WOOD.base)
    fill(layer, 7, rail + 2, 26, rail + 2, WOOD.dark)
    for x, tone in ((21, ACID.base), (23, GLASS.base)):
        bench_flask(layer, x, rail - 1, tone)
    # Prateleira baixa com tijolos e um frasco grande.
    fill(layer, 12, 41, 22, GROUND_Y, BRICK.base)
    fill(layer, 12, 41, 22, 41, BRICK.light)
    for column in range(13, 22, 3):
        put(layer, column, 43, BRICK.dark)
    draw_pennant(layer, 26, rail - 10, GROUND_Y, pose.wave)
    return layer


# --- nv2: cabana de taipa com alambique ------------------------------------------------------------
def base_hut(pose: ThrowPose) -> Layer:
    layer = Layer()
    rail = LEVELS[2].rail_top_y
    # Telhado do time atrás do operador: ele aparece na janela do sótão.
    for row in range(rail - 12, rail):
        half = (row - (rail - 12)) + 2
        for column in range(16 - half, 16 + half):
            if 3 <= column <= 28:
                shade = BRICK.dark if (row - rail) % 2 == 0 else BRICK.base
                if column < 16 - half + 2:
                    shade = BRICK.light
                put(layer, column, row, shade)
    fill(layer, 3, rail - 1, 28, rail - 1, BRICK.light)
    fill(layer, 22, rail - 11, 23, rail - 4, COPPER.light)
    fill(layer, 23, rail - 11, 23, rail - 4, COPPER.base)
    fill(layer, 21, rail - 12, 24, rail - 12, COPPER.shine)
    # Janela escura do sótão atrás do operador: o capuz do time não some contra o telhado do time.
    fill(layer, 9, rail - 8, 20, rail - 1, WOOD.dark)
    fill(layer, 10, rail - 7, 19, rail - 1, OPENING)
    # Paredes de taipa com vigas de madeira e telhadinho do time sobre a porta.
    fill(layer, 6, rail + 3, 25, GROUND_Y, BRICK.light)
    for x, y in [(9, rail + 7), (20, rail + 5), (11, GROUND_Y - 3), (22, GROUND_Y - 6)]:
        fill(layer, x, y, x + 2, y, BRICK.base)
    for beam_x in (6, 25):
        fill(layer, beam_x, rail + 3, beam_x, GROUND_Y, WOOD.dark)
    fill(layer, 9, rail + 4, 11, rail + 7, GLASS.base)
    put(layer, 9, rail + 4, GLASS.shine)
    fill(layer, 9, rail + 6, 11, rail + 7, ACID.base)
    fill(layer, 8, rail + 3, 12, rail + 3, WOOD.dark)
    fill(layer, 6, rail + 10, 25, rail + 10, WOOD.dark)
    fill(layer, 10, 38, 13, GROUND_Y, OPENING)
    fill(layer, 9, 36, 14, 36, PRIMARY_LIGHT)
    fill(layer, 9, 37, 14, 37, PRIMARY_DARK)
    draw_shield(layer, 17, rail + 4)
    # Terraço com guarda-corpo de madeira.
    fill(layer, 5, rail, 26, rail, WOOD.light)
    fill(layer, 5, rail + 1, 26, rail + 2, WOOD.base)
    fill(layer, 5, rail + 2, 26, rail + 2, WOOD.dark)
    alembic(layer, 20, 37)
    green_smoke(layer, 22, rail - 14, pose.bubble)
    draw_pennant(layer, 16, rail - 20, rail - 13, pose.wave)
    return layer


# --- nv3: torre com cúpula de cobre e vidro --------------------------------------------------------
def base_dome_tower(pose: ThrowPose) -> Layer:
    layer = Layer()
    rail = LEVELS[3].rail_top_y
    # Cúpula atrás do operador: pátina no lado da sombra, cobre no lado da luz, nervuras de vidro.
    for x, y, _, _ in ellipse_pixels(15.5, rail - 1, 10.5, 13):
        if y > rail - 1:
            continue
        horizontal = (x - 15.5) / 10.5
        if horizontal < -0.75:
            color = COPPER.shine
        elif horizontal < 0.55:
            color = COPPER.light
        else:
            color = COPPER.base
        put(layer, x, y, color)
    for rib_x in (10, 15, 20):
        for y in range(rail - 12, rail):
            if (rib_x, y) in layer.pixels:
                put(layer, rib_x, y, GLASS.light if (y % 3) else ACID.light)
    fill(layer, 14, rail - 16, 17, rail - 14, COPPER.light)
    put(layer, 15, rail - 17, GLASS.shine)
    # Torre de tijolo com janelas de vidro aceso.
    fill(layer, 7, rail + 3, 24, GROUND_Y, BRICK.base)
    for row in range(rail + 3, GROUND_Y + 1, 2):
        fill(layer, 7, row, 24, row, BRICK.dark)
        offset = 0 if (row // 2) % 2 == 0 else 2
        if row + 1 > GROUND_Y:
            continue
        for column in range(8 + offset, 24, 4):
            put(layer, column, row + 1, BRICK.dark)
    fill(layer, 7, rail + 3, 7, GROUND_Y, BRICK.light)
    fill(layer, 24, rail + 3, 24, GROUND_Y, BRICK.dark)
    draw_banner(layer, 13, rail + 4, 10)
    for window_x in (9, 21):
        fill(layer, window_x, rail + 7, window_x + 1, rail + 10, GLASS.base)
        put(layer, window_x, rail + 7, GLASS.shine)
        fill(layer, window_x, rail + 9, window_x + 1, rail + 10, ACID.base)
    fill(layer, 14, 39, 17, GROUND_Y, OPENING)
    # Varanda de pedra.
    fill(layer, 5, rail, 26, rail, STONE.shine)
    fill(layer, 5, rail + 1, 26, rail + 2, STONE.base)
    fill(layer, 5, rail + 2, 26, rail + 2, STONE.dark)
    draw_pennant(layer, 26, rail - 15, rail - 1, pose.wave)
    return layer


BASES = {1: base_bench, 2: base_hut, 3: base_dome_tower}


def draw_base(level_number: int, pose: ThrowPose) -> Image.Image:
    return layers_to_image(BASE_WIDTH, BASE_HEIGHT, BASES[level_number](pose))


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
