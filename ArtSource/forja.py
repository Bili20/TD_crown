"""Forja de Guerra: bases nv1–nv3 com o ferreiro na bigorna e os soldados nv1 e nv3.

A Forja invoca soldados, então não tem camada de arma: o ferreiro faz parte da base e anima no idle.
O soldado nv2 continua em animate_v2.py.
"""
import random
from dataclasses import dataclass
from PIL import Image
from pixel_canvas import Layer, stamp
from style_test import PLAYER, PLAYER_COLORS, PRESETS, recolor
from material_map import (Sprite, DEEP, DARK, BASE, LIGHT, SHINE, shade_volume, cast_shadow,
                          ambient_occlusion, stone_courses, brick_courses, tile_roof, team_pennant,
                          team_shield, team_banner)
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


# --- Bases no pipeline em 5 etapas (material_map) --------------------------------------------------
def fire_pit(sprite: Sprite, left: int, top: int, width: int, height: int, phase: int):
    sprite.fill(left, top, left + width - 1, top + height - 1, "holy", tone=DARK)
    for column in range(width):
        flame_height = 1 + (column + phase) % 3
        for step in range(min(flame_height, height)):
            y = top + height - 1 - step
            sprite.set(left + column, y, "holy", tone=BASE if step < flame_height - 1 else LIGHT)
    sprite.set(left + width // 2, top + height - 1, "holy", tone=SHINE)


def flame_tongues(sprite: Sprite, left: int, bottom: int, width: int, phase: int):
    heights = [1, 3, 2, 4, 2, 3, 1, 2]
    for column in range(width):
        flame_height = heights[(column + phase) % len(heights)]
        for step in range(flame_height):
            tone = DARK if step == 0 else (LIGHT if step == flame_height - 1 else BASE)
            sprite.set(left + column, bottom - step, "holy", tone=tone)
    sprite.set(left + width // 2, bottom, "holy", tone=SHINE)


def smoke_puffs(sprite: Sprite, x: int, top: int, phase: int, puff_count: int = 3, bright: bool = True):
    highlight = SHINE if bright else LIGHT
    for index, (offset_x, offset_y) in enumerate([(0, 0), (1, -3), (0, -6)][:puff_count]):
        drift = (phase + index) % 2
        y = top + offset_y - (phase % 2)
        sprite.set(x + offset_x + drift, y, "stone", tone=LIGHT)
        sprite.set(x + offset_x + drift + 1, y, "stone", tone=highlight if index == 0 else LIGHT)
        sprite.set(x + offset_x + drift, y - 1, "stone", tone=highlight)


def overlay_layer(pose: ForgePose, smith_rows, smith_left, anvil_left, anvil_top) -> Layer:
    layer = Layer()
    stamp(layer, ANVIL, anvil_left, anvil_top, COLORS)
    draw_smith(layer, smith_rows, smith_left, GROUND_Y, pose)
    return layer


# nv1: barraca de lona com bigorna e fogueira de tijolo
TENT_APEX_X, TENT_APEX_Y = 8, 23


def tent_shape(pose: ForgePose):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    sprite.fill(20, 36, 29, GROUND_Y - 1, "brick")
    sprite.fill(20, 35, 29, 35, "brick", "top")
    sprite.fill(22, 38, 27, 41, "opening")
    for row in range(TENT_APEX_Y, 35):
        half = min(7, (row - TENT_APEX_Y) * 7 // 11 + 1)
        for column in range(TENT_APEX_X - half, TENT_APEX_X + half + 1):
            stripe = (column - TENT_APEX_X + 20) // 2 % 2
            sprite.set(column, row, "secondary" if stripe == 0 else "primary",
                       "left" if column <= TENT_APEX_X else "right")
    sprite.fill(1, 35, 15, 35, "secondary")
    for column in range(1, 16, 2):
        sprite.set(column, 36, "secondary", tone=DARK)
    for column in range(1, 15):
        for row in range(36 if column % 2 == 0 else 37, GROUND_Y + 1):
            sprite.set(column, row, "secondary" if column // 2 % 2 == 0 else "primary")
    sprite.fill(4, 38, 6, GROUND_Y, "opening")
    sprite.fill(21, 42, 25, GROUND_Y, "wood")
    sprite.fill(21, 42, 25, 42, "wood", "top")
    team_pennant(sprite, TENT_APEX_X, TENT_APEX_Y - 9, TENT_APEX_Y - 1, pose.wave)
    return sprite, overlay_layer(pose, SMITH_APPRENTICE, 10, 19, 38)


def tent_shading(sprite: Sprite, pose: ForgePose):
    cast_shadow(sprite, 1, 14, 37, depth=1, materials=("primary", "secondary"))
    shade_volume(sprite, 1, 37, 14, GROUND_Y, ("primary", "secondary"), shadow_columns=3)
    shade_volume(sprite, 20, 36, 29, GROUND_Y - 1, ("brick",))
    ambient_occlusion(sprite, 1, 29, GROUND_Y)


def tent_details(sprite: Sprite, pose: ForgePose, rng):
    brick_courses(sprite, 20, 36, 29, GROUND_Y - 1, rng)
    # Dobras da lona: a costura entre as listras afunda um tom.
    for column in range(1, 15):
        if column % 2 == 1:
            for row in range(38, GROUND_Y + 1, 2):
                sprite.shift(column, row, -1, ("primary", "secondary"))
    fire_pit(sprite, 22, 39, 6, 3, pose.fire)
    flame_tongues(sprite, 21, 34, 8, pose.fire)
    smoke_puffs(sprite, 24, 28, pose.smoke, bright=False)
    sprite.set(TENT_APEX_X, TENT_APEX_Y - 1, "secondary", tone=LIGHT)


# nv2: oficina de tijolo com chaminé
def workshop_shape(pose: ForgePose):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    sprite.fill(22, 13, 26, 26, "brick")
    sprite.fill(21, 12, 27, 12, "brick", "top")
    sprite.fill(4, 30, 27, GROUND_Y, "brick")
    for row in range(19, 30):
        inset = max(0, 22 - row)
        sprite.fill(3 + inset, row, 28 - inset, row, "primary", "top")
    sprite.fill(14, 34, 23, GROUND_Y, "opening")
    sprite.fill(15, 33, 22, 33, "opening")
    team_shield(sprite, 5, 32)
    team_pennant(sprite, 4, 10, 20, pose.wave)
    return sprite, overlay_layer(pose, SMITH_JOURNEYMAN, 11, 19, 41)


def workshop_shading(sprite: Sprite, pose: ForgePose):
    shade_volume(sprite, 4, 30, 27, GROUND_Y, ("brick",))
    shade_volume(sprite, 22, 13, 26, 26, ("brick",))
    cast_shadow(sprite, 4, 27, 30, depth=2, materials=("brick",))
    ambient_occlusion(sprite, 4, 27, GROUND_Y, ("brick",))


def workshop_details(sprite: Sprite, pose: ForgePose, rng):
    brick_courses(sprite, 4, 30, 27, GROUND_Y, rng)
    brick_courses(sprite, 22, 13, 26, 26, rng)
    tile_roof(sprite, range(19, 30), 15.5, "primary")
    sprite.fill(3, 29, 28, 29, "primary", tone=DARK)
    # Arco de tijolo em pé em volta da forja: aduelas claras com junta escura.
    for x in range(13, 25):
        sprite.set(x, 32, "brick", tone=LIGHT if x % 2 else BASE)
    for y in range(33, GROUND_Y + 1):
        sprite.set(13, y, "brick", tone=LIGHT)
        sprite.set(24, y, "brick", tone=DARK)
    fire_pit(sprite, 15, 38, 8, 4, pose.fire)
    sprite.fill(22, 11, 26, 11, "holy", tone=BASE)
    sprite.set(24, 11, "holy", tone=LIGHT)
    smoke_puffs(sprite, 23, 9, pose.smoke)


# nv3: forja-quartel de pedra escura com fornalha
def barracks_shape(pose: ForgePose):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    for chimney_left in (7, 21):
        sprite.fill(chimney_left, 9, chimney_left + 3, 13, "dark_stone")
        sprite.fill(chimney_left - 1, 8, chimney_left + 4, 8, "dark_stone", "top")
    sprite.fill(4, 16, 27, GROUND_Y, "dark_stone")
    sprite.fill(3, 14, 28, 14, "dark_stone", "top")
    sprite.fill(3, 15, 28, 15, "dark_stone")
    for merlon_left in range(3, 28, 5):
        sprite.fill(merlon_left, 12, merlon_left + 2, 13, "dark_stone")
        sprite.fill(merlon_left, 11, merlon_left + 2, 11, "dark_stone", "top")
    sprite.fill(12, 33, 22, GROUND_Y, "opening")
    sprite.fill(13, 32, 21, 32, "opening")
    sprite.fill(14, 31, 20, 31, "opening")
    sprite.fill(23, 20, 25, 22, "opening")
    team_banner(sprite, 6, 18, 10)
    team_pennant(sprite, 26, 2, 10, pose.wave)
    return sprite, overlay_layer(pose, SMITH_MASTER, 6, 19, 41)


def barracks_shading(sprite: Sprite, pose: ForgePose):
    shade_volume(sprite, 4, 16, 27, GROUND_Y, ("dark_stone",))
    cast_shadow(sprite, 4, 27, 16, depth=2, materials=("dark_stone",))
    for merlon_left in range(3, 28, 5):
        sprite.shift(merlon_left + 2, 12, -1, ("dark_stone",))
        sprite.shift(merlon_left + 2, 13, -1, ("dark_stone",))
    ambient_occlusion(sprite, 4, 27, GROUND_Y, ("dark_stone",))


def barracks_details(sprite: Sprite, pose: ForgePose, rng):
    stone_courses(sprite, 4, 18, 27, GROUND_Y, rng, material="dark_stone")
    for chimney_left in (7, 21):
        stone_courses(sprite, chimney_left, 9, chimney_left + 3, 13, rng, material="dark_stone",
                      widths=(2, 3), protrude=False)
        sprite.fill(chimney_left, 7, chimney_left + 3, 7, "holy", tone=BASE)
    # Aduelas da fornalha: pedra clara em volta do arco, brilho quente refletido nas de baixo.
    for x in range(12, 23):
        sprite.set(x, 30 if 14 <= x <= 20 else 31, "dark_stone", tone=LIGHT)
    for y in range(33, GROUND_Y + 1):
        sprite.set(11, y, "dark_stone", tone=LIGHT)
        sprite.set(23, y, "dark_stone", tone=DARK)
    fire_pit(sprite, 13, 37, 9, 5, pose.fire)
    for x in range(13, 22):
        sprite.set(x, 36, "holy", tone=DARK)
    smoke_puffs(sprite, 8, 6, pose.smoke, puff_count=2)
    smoke_puffs(sprite, 22, 6, pose.smoke + 1, puff_count=2)


SHAPES = {1: tent_shape, 2: workshop_shape, 3: barracks_shape}
SHADERS = {1: tent_shading, 2: workshop_shading, 3: barracks_shading}
DETAILS = {1: tent_details, 2: workshop_details, 3: barracks_details}


def build_base(level_number: int, pose: ForgePose, stage: int = 5) -> Image.Image:
    sprite, overlay = SHAPES[level_number](pose)
    overlay_image = layers_to_image(BASE_WIDTH, BASE_HEIGHT, overlay)
    if stage == 1:
        image = sprite.render(silhouette=True)
        mask = overlay_image.split()[3].point(lambda alpha: 255 if alpha else 0)
        image.paste(Image.new("RGBA", image.size, (60, 56, 80, 255)), (0, 0), mask)
        return image
    sprite.reset_tones()
    if stage >= 3:
        SHADERS[level_number](sprite, pose)
    if stage >= 4:
        DETAILS[level_number](sprite, pose, random.Random(level_number * 31))
    image = sprite.render()
    image.alpha_composite(overlay_image)
    return image


def draw_base(level_number: int, pose: ForgePose) -> Image.Image:
    return build_base(level_number, pose)


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
