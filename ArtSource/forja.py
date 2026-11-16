"""Forja de Guerra: bases nv1–nv3 com o ferreiro na bigorna e os soldados nv1 e nv3.

A Forja invoca soldados, então não tem camada de arma: o ferreiro faz parte da base e anima no idle.
O soldado nv2 continua em animate_v2.py.
"""
from dataclasses import dataclass
from PIL import Image
from pixel_canvas import Layer, stamp
from style_test import PLAYER, PLAYER_COLORS, PRESETS, recolor
from tower_parts import (BASE_WIDTH, BASE_HEIGHT, GROUND_Y, WOOD, STONE, IRON, HOLY, OPENING,
                         PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SECONDARY, SECONDARY_DARK, SECONDARY_LIGHT,
                         put, fill, draw_pennant, draw_shield, draw_banner, layers_to_image,
                         compose_tower)

BRICK = PLAYER.ramp("BRICK")
DARK_STONE = PLAYER.ramp("DARK_STONE")

COLORS = {
    **PLAYER_COLORS,
    "i": IRON.dark, "j": IRON.base, "k": IRON.light, "K": IRON.shine,
    "n": WOOD.dark, "m": WOOD.base, "M": WOOD.light,
    "r": BRICK.dark, "R": BRICK.base, "q": BRICK.light,
    "x": DARK_STONE.dark, "X": DARK_STONE.base, "v": DARK_STONE.light,
    "g": HOLY.dark, "G": HOLY.base, "Y": HOLY.light, "Z": HOLY.shine,
    "z": OPENING,
}

ANVIL = [
    ".kkkkkk.",
    "ijjjjjjk",
    "..ijji..",
    ".iijjji.",
]

# Ferreiros virados para a bigorna (direita). O martelo fica de pé acima da mão, nunca em diagonal.
SMITH_APPRENTICE = [
    "......jkj",
    "..bbc..m.",
    ".abbbbcm.",
    "aabbbbbm.",
    ".otuutot.",
    "..stts.b.",
    ".bmmmmbb.",
    ".bmMmmb..",
    ".bmmmmb..",
    "..o..o...",
]
SMITH_JOURNEYMAN = [
    "......jkj",
    ".......m.",
    "..nnnn.m.",
    "abbbbbcm.",
    "a.nnnn.m.",
    ".otuutot.",
    "..stts.b.",
    ".bnmmnbb.",
    ".bmMMmb..",
    ".bmmmmb..",
    "..o..o...",
]
SMITH_MASTER = [
    "......jkkj",
    ".......mm.",
    "...bbc.m..",
    "..bbbbcm..",
    "aabbbbbm..",
    ".otuutot..",
    ".nnnnnnfb.",
    "fnmMMmnf..",
    "fbmMMmbf..",
    ".bmmmmb...",
    ".bmmmmb...",
    "..o..o....",
]
SMITH_HAMMER_DOWN_ROWS = 3


@dataclass(frozen=True)
class ForgePose:
    wave: int = 0          # flâmula
    hammer_up: bool = True
    fire: int = 0          # 0..2: alterna o miolo da fornalha
    smoke: int = 0         # 0..3: fase da fumaça


def draw_smith(layer: Layer, rows: list[str], left: int, feet_row: int, pose: ForgePose):
    top = feet_row + 1 - len(rows)
    body = rows if pose.hammer_up else [row[:-3] + "..." for row in rows[:SMITH_HAMMER_DOWN_ROWS]] + rows[SMITH_HAMMER_DOWN_ROWS:]
    stamp(layer, body, left, top, COLORS)


def draw_fire(layer: Layer, left: int, top: int, width: int, height: int, phase: int):
    fill(layer, left, top, left + width - 1, top + height - 1, HOLY.dark)
    for column in range(width):
        flame_height = 1 + (column + phase) % 3
        for step in range(min(flame_height, height)):
            y = top + height - 1 - step
            put(layer, left + column, y, HOLY.base if step < flame_height - 1 else HOLY.light)
    put(layer, left + width // 2, top + height - 1, HOLY.shine)


def draw_flames(layer: Layer, left: int, bottom: int, width: int, phase: int):
    # Línguas de fogo de alturas diferentes; o padrão gira com a fase para tremular no idle.
    heights = [1, 3, 2, 4, 2, 3, 1, 2]
    for column in range(width):
        flame_height = heights[(column + phase) % len(heights)]
        for step in range(flame_height):
            if step == 0:
                color = HOLY.dark
            elif step == flame_height - 1:
                color = HOLY.light
            else:
                color = HOLY.base
            put(layer, left + column, bottom - step, color)
    put(layer, left + width // 2, bottom, HOLY.shine)


def draw_smoke(layer: Layer, x: int, top: int, phase: int, puff_count: int = 3):
    puffs = [(0, 0), (1, -3), (0, -6)][:puff_count]
    for index, (offset_x, offset_y) in enumerate(puffs):
        drift = (phase + index) % 2
        y = top + offset_y - (phase % 2)
        put(layer, x + offset_x + drift, y, STONE.light)
        put(layer, x + offset_x + drift + 1, y, STONE.shine if index == 0 else STONE.light)
        put(layer, x + offset_x + drift, y - 1, STONE.shine)


def brick_wall(layer: Layer, left: int, top: int, right: int, bottom: int, ramp=BRICK):
    fill(layer, left, top, right, bottom, ramp.base)
    for row in range(top, bottom + 1):
        if (row - top) % 2 == 1:
            fill(layer, left, row, right, row, ramp.dark)
        else:
            offset = 0 if ((row - top) // 2) % 2 == 0 else 2
            for column in range(left + offset, right + 1, 4):
                put(layer, column, row, ramp.dark)
    fill(layer, left, top, right, top, ramp.light)


# --- nv1: barraca de lona com bigorna e fogueira de tijolo ----------------------------------------
def base_tent(pose: ForgePose) -> Layer:
    layer = Layer()
    # Fogueira de tijolo atrás, à direita.
    brick_wall(layer, 20, 35, 29, GROUND_Y - 1)
    fill(layer, 22, 38, 27, 41, OPENING)
    draw_fire(layer, 22, 39, 6, 3, pose.fire)
    draw_flames(layer, 21, 34, 8, pose.fire)
    draw_smoke(layer, 24, 28, pose.smoke)
    # Barraca: cone listrado na cor secundária, sanefa na primária e parede listrada.
    apex_x, apex_y = 8, 23
    for row in range(apex_y, 35):
        half = min(7, (row - apex_y) * 7 // 11 + 1)
        for column in range(apex_x - half, apex_x + half + 1):
            stripe = (column - apex_x + 20) // 2 % 2
            color = SECONDARY_LIGHT if stripe == 0 else PRIMARY
            if column == apex_x - half:
                color = PRIMARY_DARK
            put(layer, column, row, color)
    fill(layer, 1, 35, 15, 35, SECONDARY)
    for column in range(1, 16, 2):
        put(layer, column, 36, SECONDARY_DARK)
    for column in range(2, 15):
        for row in range(36 if column % 2 == 0 else 37, GROUND_Y + 1):
            stripe = column // 2 % 2
            put(layer, column, row, SECONDARY_LIGHT if stripe == 0 else SECONDARY)
    fill(layer, 1, 36, 1, GROUND_Y, SECONDARY_DARK)
    fill(layer, 4, 38, 6, GROUND_Y, OPENING)
    put(layer, apex_x, apex_y - 1, SECONDARY_LIGHT)
    draw_pennant(layer, apex_x, apex_y - 9, apex_y - 2, pose.wave)
    # Bigorna num toco e o aprendiz.
    fill(layer, 21, 42, 25, GROUND_Y, WOOD.dark)
    fill(layer, 21, 42, 25, 42, WOOD.light)
    stamp(layer, ANVIL, 19, 38, COLORS)
    draw_smith(layer, SMITH_APPRENTICE, 10, GROUND_Y, pose)
    return layer


# --- nv2: oficina de tijolo com chaminé -----------------------------------------------------------
def base_workshop(pose: ForgePose) -> Layer:
    layer = Layer()
    # Chaminé à direita, atrás do telhado.
    brick_wall(layer, 22, 12, 26, 26)
    fill(layer, 21, 12, 27, 12, BRICK.light)
    fill(layer, 22, 11, 26, 11, HOLY.base)
    put(layer, 24, 11, HOLY.light)
    draw_smoke(layer, 23, 9, pose.smoke)
    # Paredes de tijolo.
    brick_wall(layer, 4, 30, 27, GROUND_Y)
    fill(layer, 4, 30, 4, GROUND_Y, BRICK.dark)
    fill(layer, 27, 30, 27, GROUND_Y, BRICK.light)
    # Telhado na cor do time: frente inclinada vista de cima.
    for row in range(19, 30):
        inset = max(0, 22 - row)
        fill(layer, 3 + inset, row, 28 - inset, row, PRIMARY if row % 3 else PRIMARY_DARK)
    fill(layer, 3, 29, 28, 29, PRIMARY_DARK)
    fill(layer, 6, 19, 25, 19, PRIMARY_LIGHT)
    fill(layer, 3, 28, 28, 28, PRIMARY_LIGHT)
    # Arco da forja com o fogo sagrado e o escudo do time ao lado.
    fill(layer, 13, 34, 24, GROUND_Y, OPENING)
    fill(layer, 14, 33, 23, 33, OPENING)
    draw_fire(layer, 14, 38, 10, 4, pose.fire)
    fill(layer, 12, 33, 12, GROUND_Y, BRICK.light)
    fill(layer, 25, 33, 25, GROUND_Y, BRICK.dark)
    draw_shield(layer, 5, 32)
    stamp(layer, ANVIL, 19, 41, COLORS)
    draw_smith(layer, SMITH_JOURNEYMAN, 11, GROUND_Y, pose)
    draw_pennant(layer, 4, 10, 20, pose.wave)
    return layer


# --- nv3: forja-quartel de pedra escura com fornalha ---------------------------------------------
def base_barracks(pose: ForgePose) -> Layer:
    layer = Layer()
    # Duas chaminés de tijolo atrás das ameias.
    for chimney_left in (7, 21):
        brick_wall(layer, chimney_left, 8, chimney_left + 3, 14, DARK_STONE)
        fill(layer, chimney_left - 1, 8, chimney_left + 4, 8, DARK_STONE.light)
        fill(layer, chimney_left, 7, chimney_left + 3, 7, HOLY.base)
    draw_smoke(layer, 8, 6, pose.smoke, puff_count=2)
    draw_smoke(layer, 22, 6, pose.smoke + 1, puff_count=2)
    # Corpo de pedra escura.
    brick_wall(layer, 4, 16, 27, GROUND_Y, DARK_STONE)
    fill(layer, 4, 16, 4, GROUND_Y, DARK_STONE.dark)
    fill(layer, 27, 16, 27, GROUND_Y, DARK_STONE.light)
    # Ameias.
    fill(layer, 3, 14, 28, 15, DARK_STONE.light)
    for merlon_left in range(3, 28, 5):
        fill(layer, merlon_left, 11, merlon_left + 2, 13, DARK_STONE.base)
        fill(layer, merlon_left, 11, merlon_left + 2, 11, DARK_STONE.light)
    # Fornalha grande no centro, com o fogo em HOLY.
    fill(layer, 12, 33, 22, GROUND_Y, OPENING)
    fill(layer, 13, 32, 21, 32, OPENING)
    fill(layer, 14, 31, 20, 31, OPENING)
    draw_fire(layer, 13, 37, 9, 5, pose.fire)
    for column in range(12, 23):
        put(layer, column, 30 if 14 <= column <= 20 else 31, DARK_STONE.light)
    # Estandarte do time.
    draw_banner(layer, 6, 18, 10)
    fill(layer, 23, 20, 25, 22, OPENING)
    stamp(layer, ANVIL, 19, 41, COLORS)
    draw_smith(layer, SMITH_MASTER, 6, GROUND_Y, pose)
    draw_pennant(layer, 26, 2, 13, pose.wave)
    return layer


BASES = {1: base_tent, 2: base_workshop, 3: base_barracks}


def draw_base(level_number: int, pose: ForgePose) -> Image.Image:
    return layers_to_image(BASE_WIDTH, BASE_HEIGHT, BASES[level_number](pose))


# --- Soldados nv1 (recruta) e nv3 (veterano) ------------------------------------------------------
SOLDIER_RECRUIT = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "......bbc.......",
    ".....abbbbc.....",
    "....aabbbbbb....",
    ".....otuuto..w..",
    "..mm..sttsbb.w..",
    ".mnMmcbbbbba.w..",
    ".mMnmbbbbbaa.e..",
    "..mm.dnnnndd.td.",
    "......bbbbb.....",
    "......oo.oo.....",
    "................",
]
SOLDIER_VETERAN = [
    "................",
    "................",
    "................",
    ".......cc.......",
    "......cbb.......",
    "......fwf....w..",
    ".....dfwffd..w..",
    "....deeeeeed.w..",
    "....dotuutod.w..",
    ".eee.dsttsd.eee.",
    ".ebe.febbefetd..",
    ".bwbfebwwbe..d..",
    ".wwwfebwwbe.....",
    ".ebe.deeeed.....",
    "......oo.oo.....",
    "................",
]


def draw_soldier(rows: list[str]) -> Image.Image:
    layer = Layer()
    stamp(layer, rows, 0, 0, COLORS)
    return layers_to_image(16, 16, layer)


if __name__ == "__main__":
    royal = PRESETS["real"]
    pose = ForgePose()
    frames = [compose_tower(draw_base(level, pose), None, None, royal) for level in (1, 2, 3)]
    soldiers = [recolor(draw_soldier(rows), royal) for rows in (SOLDIER_RECRUIT, SOLDIER_VETERAN)]
    from balista import row_of
    row_of(frames + soldiers, gap=4, scale=6).save("forja_preview.png")
