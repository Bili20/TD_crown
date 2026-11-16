import random
from dataclasses import dataclass, replace
from PIL import Image
from art_export import export_animation, export_directions
from pixel_canvas import Ramp, Canvas, Layer, stamp, line_pixels, ellipse_pixels, save_spritesheet, save_preview_gif
from style_test import PLAYER, PLAYER_COLORS, PRESETS, BACKGROUND, REGION1, recolor
from material_map import (Sprite, DEEP, DARK, BASE, LIGHT, SHINE, shade_volume, cast_shadow,
                          ambient_occlusion, recess, stone_courses, planks, team_pennant, team_shield,
                          team_banner)

BASE_WIDTH, BASE_HEIGHT, GROUND_Y = 32, 48, 44
TURRET_WIDTH, TURRET_HEIGHT = 20, 16
# O operador é cortado na cintura (WAIST_ROW); abaixo disso só o arco e o suporte, por cima do parapeito.
WAIST_ROW = 12

WOOD = PLAYER.ramp("WOOD")
STONE = PLAYER.ramp("STONE")
IRON = PLAYER.ramp("IRON")
STRING = PLAYER.color("STRING")
DARKEST = PLAYER_COLORS["o"]
PRIMARY_DARK, PRIMARY, PRIMARY_LIGHT = PLAYER_COLORS["a"], PLAYER_COLORS["b"], PLAYER_COLORS["c"]
SECONDARY_DARK, SECONDARY, SECONDARY_LIGHT = PLAYER_COLORS["d"], PLAYER_COLORS["e"], PLAYER_COLORS["f"]
HIGHLIGHT = PLAYER_COLORS["w"]
DOOR = REGION1.color("OUTLINE")
SHADOW = REGION1.color("SHADOW_BLOB")


def put(layer: Layer, x: int, y: int, color):
    layer.pixels[(x, y)] = color


def fill(layer: Layer, left: int, top: int, right: int, bottom: int, color):
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            layer.pixels[(x, y)] = color


def draw_line(layer: Layer, start, end, color):
    for x, y in line_pixels(start, end):
        layer.pixels[(x, y)] = color


# --- Operadores: a mesma figura evolui com a torre (Recruta → Besteiro → Mestre-Balisteiro) ----------
# Cortados na cintura: o parapeito da base esconde as pernas.
OPERATOR_RECRUIT = [
    "..bbc...",
    ".abbbbc.",
    "aabbbbbb",
    ".otuuto.",
    "..stts..",
    ".abbbbt.",
    ".abbbba.",
    ".abbbba.",
]
OPERATOR_CROSSBOWMAN = [
    "...c....",
    "..cb....",
    "..fwf...",
    ".dfwffd.",
    "ddeeeedd",
    ".otuuto.",
    "..stts..",
    ".abbbbt.",
    ".abwbba.",
    ".deeeed.",
]
OPERATOR_MASTER = [
    "...cc...",
    "..cbb...",
    "..cb....",
    "..fwf...",
    ".dfwffd.",
    "deeeeeed",
    "dotuutod",
    ".dsttsd.",
    "fefbbeft",
    ".ebwwbe.",
    ".dfeefd.",
]
OPERATOR_MASTER_PLUME_SWAY = ["....cc..", "...cbb..", "..cb...."]


@dataclass(frozen=True)
class BallistaLevel:
    operator: list[str]
    stock_left: int
    stock_right: int
    bow_x: int
    bow_reach: int          # quantos px o arco sobe/desce a partir da coronha
    bow_thickness: int
    bolt_right: int
    stock_ramp: object
    band_color: object      # cinta da coronha: ferro no nv2, secundária (dourado no preset real) no nv3
    band_columns: tuple
    bow_ramp: object
    bow_tip_color: object
    rail_top_y: int
    turret_x: int


LEVELS = {
    1: BallistaLevel(OPERATOR_RECRUIT, 7, 13, 12, 3, 1, 15, WOOD, None, (), Ramp(WOOD.base, WOOD.light, WOOD.light), STRING, 30, 6),
    2: BallistaLevel(OPERATOR_CROSSBOWMAN, 7, 15, 13, 4, 2, 17, WOOD, IRON.base, (10, 13), IRON, IRON.light, 22, 6),
    3: BallistaLevel(OPERATOR_MASTER, 7, 16, 14, 5, 2, 19, WOOD, SECONDARY, (9, 12, 15), IRON, SECONDARY_LIGHT, 15, 6),
}

STOCK_Y = 9


@dataclass(frozen=True)
class TurretPose:
    operator_y: int = 0
    bow_flex: int = 0        # -1 tensionado (pontas para trás), +1 soltando (pontas para frente)
    bolt: str = "loaded"     # loaded | none | reloading
    recoil: int = 0
    streak: bool = False
    plume_swayed: bool = False


def draw_ballista(layer: Layer, level: BallistaLevel, pose: TurretPose):
    shift = -pose.recoil
    left, right = level.stock_left + shift, level.stock_right + shift
    bow_x = level.bow_x + shift

    stand_x = (left + right) // 2
    fill(layer, stand_x, STOCK_Y + 2, stand_x + 1, WAIST_ROW, WOOD.dark)
    put(layer, stand_x - 1, WAIST_ROW, WOOD.dark)
    put(layer, stand_x + 2, WAIST_ROW, WOOD.dark)

    fill(layer, left, STOCK_Y, right, STOCK_Y, level.stock_ramp.light)
    fill(layer, left, STOCK_Y + 1, right, STOCK_Y + 1, level.stock_ramp.dark)
    put(layer, right + 1, STOCK_Y, level.stock_ramp.base)
    for column in level.band_columns:
        put(layer, column + shift, STOCK_Y, level.band_color)
        put(layer, column + shift, STOCK_Y + 1, level.band_color)

    # Arco: braços saem da frente da coronha e se curvam para trás nas pontas.
    tip_x = bow_x - 1 + pose.bow_flex
    for direction in (-1, 1):
        anchor_y = STOCK_Y if direction < 0 else STOCK_Y + 1
        for step in range(1, level.bow_reach + 1):
            y = anchor_y + direction * step
            x = bow_x if step < level.bow_reach else tip_x
            put(layer, x, y, level.bow_ramp.base if step < level.bow_reach else level.bow_tip_color)
            if level.bow_thickness == 2 and step < level.bow_reach:
                put(layer, x + 1, y, level.bow_ramp.dark)
        tip_y = anchor_y + direction * level.bow_reach
        nock = (left + 2, STOCK_Y - 1) if direction < 0 else (left + 2, STOCK_Y + 2)
        if pose.bolt == "none":
            nock = (tip_x - 1, anchor_y + direction)
        for x, y in list(line_pixels((tip_x - 1, tip_y), nock))[:-1]:
            if (x, y) not in layer.pixels:
                put(layer, x, y, STRING)

    bolt_row = STOCK_Y - 1
    if pose.bolt == "loaded":
        bolt_left, bolt_right = left + 1, level.bolt_right + shift
    elif pose.bolt == "reloading":
        bolt_left, bolt_right = left - 1, left + 4
    else:
        bolt_left = bolt_right = None
    if bolt_left is not None:
        fill(layer, bolt_left + 2, bolt_row, bolt_right - 1, bolt_row, IRON.light)
        put(layer, bolt_left, bolt_row, PRIMARY)
        put(layer, bolt_left + 1, bolt_row, PRIMARY_LIGHT)
        put(layer, bolt_left, bolt_row - 1, PRIMARY_DARK)
        put(layer, bolt_right, bolt_row, HIGHLIGHT)
    if pose.streak:
        for x in range(right + 2, TURRET_WIDTH, 2):
            put(layer, x, bolt_row, STRING)


def draw_turret(level_number: int, pose: TurretPose) -> Image.Image:
    level = LEVELS[level_number]
    canvas = Canvas(TURRET_WIDTH, TURRET_HEIGHT)
    operator_layer = Layer()
    operator_top = WAIST_ROW + 1 - len(level.operator) + pose.operator_y
    stamp(operator_layer, level.operator, -pose.recoil, operator_top, PLAYER_COLORS)
    for (x, y) in [(x, y) for (x, y) in operator_layer.pixels if y > WAIST_ROW]:
        del operator_layer.pixels[(x, y)]
    if level_number == 3 and pose.plume_swayed:
        for (x, y) in [(x, y) for (x, y) in operator_layer.pixels if y < operator_top + 3]:
            del operator_layer.pixels[(x, y)]
        stamp(operator_layer, OPERATOR_MASTER_PLUME_SWAY, -pose.recoil, operator_top, PLAYER_COLORS)
    ballista_layer = Layer()
    draw_ballista(ballista_layer, level, pose)
    canvas.put_layer(operator_layer)
    canvas.put_layer(ballista_layer)
    return canvas.to_image()


TURRET_IDLE = [TurretPose(), TurretPose(operator_y=1), TurretPose(operator_y=1, plume_swayed=True), TurretPose()]
TURRET_IDLE_DURATIONS_MS = [260, 200, 260, 200]
TURRET_FIRE = [
    TurretPose(operator_y=1, bow_flex=-1),                     # tensiona: operador firma o corpo
    TurretPose(bow_flex=1, bolt="none", streak=True),           # dispara
    TurretPose(bolt="none", recoil=1),                          # recuo
    TurretPose(bolt="reloading"),                               # recarrega
]
TURRET_FIRE_DURATIONS_MS = [140, 60, 120, 200]
TURRET_FIRE_IMPACT_FRAME = 1


# --- Bases -----------------------------------------------------------------------------------------
def draw_pennant(layer: Layer, pole_x: int, pole_top: int, pole_bottom: int, wave: int):
    fill(layer, pole_x, pole_top, pole_x, pole_bottom, WOOD.dark)
    put(layer, pole_x, pole_top - 1, SECONDARY_LIGHT)
    rows = [
        ["c", "b", "b", "b"],
        ["b", "b", "a"] if wave % 2 == 0 else ["b", "b", "b", "a"],
        ["a", "a"] if wave % 2 == 0 else ["a"],
    ]
    for row_index, row in enumerate(rows):
        offset = 1 if (wave in (1, 2) and row_index == 2) else 0
        for column_index, symbol in enumerate(row):
            put(layer, pole_x + 1 + column_index + offset, pole_top + row_index, PLAYER_COLORS[symbol])


def platform_shape(wave: int):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    for leg_x in (10, 21):
        sprite.fill(leg_x, 35, leg_x, 41, "wood", tone=DARK)
    for start, end in (((9, 36), (22, 43)), ((22, 36), (9, 43))):
        for x, y in line_pixels(start, end):
            sprite.set(x, y, "wood", tone=DARK)
    for leg_x in (7, 23):
        sprite.fill(leg_x, 35, leg_x + 1, GROUND_Y, "wood")
    sprite.fill(5, 32, 26, 32, "wood", "top")
    sprite.fill(5, 33, 26, 34, "wood")
    sprite.fill(6, 30, 25, 30, "wood", "top")
    sprite.fill(6, 31, 25, 31, "wood")
    for post_x in (6, 15, 25):
        sprite.fill(post_x, 29, post_x, 31, "wood", tone=DARK)
    team_pennant(sprite, 26, 20, 31, wave)
    return sprite


def platform_shading(sprite: Sprite):
    sprite.fill(5, 34, 26, 34, "wood", tone=DEEP)
    for leg_x in (7, 23):
        for y in range(35, GROUND_Y + 1):
            sprite.shift(leg_x + 1, y, -1, ("wood",))
    cast_shadow(sprite, 9, 22, 35, depth=1, materials=("wood",))


def platform_details(sprite: Sprite, rng):
    planks(sprite, 5, 33, 26, 33, rng, vertical=False, plank_width=4, nails=False)
    for x in range(8, 26, 4):
        sprite.set(x, 33, "wood", tone=DARK)
    for x in (9, 14, 19, 24):
        sprite.set(x, 32, "iron", tone=LIGHT)
    sprite.set(7, GROUND_Y, "wood", tone=DARK)


def watchtower_shape(wave: int):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    sprite.fill(7, 26, 24, GROUND_Y, "wood")
    sprite.fill(14, 37, 17, GROUND_Y, "opening")
    for start, end in (((5, 25), (7, 28)), ((26, 25), (24, 28))):
        for x, y in line_pixels(start, end):
            sprite.set(x, y, "wood", tone=DARK)
    sprite.fill(4, 24, 27, 24, "wood", tone=DARK)
    sprite.fill(4, 25, 27, 25, "opening")
    for column in range(4, 28):
        sprite.fill(column, 20 if column % 2 == 0 else 21, column, 23, "wood")
    team_shield(sprite, 13, 31)
    team_pennant(sprite, 5, 9, 19, wave)
    return sprite


def watchtower_shading(sprite: Sprite):
    # Troncos redondos: cada tronco de 3 px tem luz, base e sombra.
    for column in range(7, 25):
        offset = (column - 7) % 3
        for y in range(26, GROUND_Y + 1):
            sprite.shift(column, y, {0: +1, 1: 0, 2: -1}[offset], ("wood",))
    for column in range(4, 28):
        offset = column % 3
        for y in range(20, 24):
            sprite.shift(column, y, {0: +1, 1: 0, 2: -1}[offset], ("wood",))
    shade_volume(sprite, 7, 26, 24, GROUND_Y, ("wood",), shadow_columns=2, lit_columns=0)
    cast_shadow(sprite, 7, 24, 26, depth=2, materials=("wood",))
    ambient_occlusion(sprite, 7, 24, GROUND_Y, ("wood",))


def watchtower_details(sprite: Sprite, rng):
    for band_y in (29, 39):
        sprite.fill(6, band_y, 25, band_y, "iron")
        sprite.fill(6, band_y + 1, 25, band_y + 1, "iron", tone=DARK)
        for x in range(8, 25, 5):
            sprite.set(x, band_y, "iron", tone=SHINE)
    for column in range(4, 28):
        top = 20 if column % 2 == 0 else 21
        sprite.set(column, top, "wood", tone=LIGHT if column % 3 == 0 else BASE)
    sprite.fill(13, 36, 18, 36, "wood", tone=DARK)
    sprite.fill(13, 37, 13, GROUND_Y, "wood", tone=DARK)
    sprite.fill(18, 37, 18, GROUND_Y, "wood", tone=DEEP)
    for _ in range(4):
        x, y = rng.randint(8, 23), rng.randint(31, 43)
        if sprite.is_material(x, y, "wood"):
            sprite.shift(x, y, -1, ("wood",))
            sprite.shift(x, y + 1, -1, ("wood",))


def bastion_shape(wave: int):
    sprite = Sprite(BASE_WIDTH, BASE_HEIGHT)
    sprite.fill(6, 20, 25, GROUND_Y, "stone")
    sprite.fill(5, 41, 26, GROUND_Y, "stone")
    for slit_x in (9, 22):
        sprite.fill(slit_x, 25, slit_x, 28, "opening")
    sprite.fill(13, 38, 18, GROUND_Y, "wood")
    sprite.set(13, 38, "stone")
    sprite.set(18, 38, "stone")
    sprite.fill(3, 18, 28, 18, "stone", "top")
    sprite.fill(3, 19, 28, 19, "stone")
    sprite.fill(4, 15, 27, 15, "stone", "top")
    sprite.fill(4, 16, 27, 17, "stone")
    for merlon_left in (4, 24):
        sprite.fill(merlon_left, 12, merlon_left + 3, 14, "stone")
        sprite.fill(merlon_left, 11, merlon_left + 3, 11, "stone", "top")
    team_banner(sprite, 13, 20, 10)
    team_pennant(sprite, 5, 2, 10, wave)
    return sprite


def bastion_shading(sprite: Sprite):
    shade_volume(sprite, 6, 20, 25, GROUND_Y, ("stone",))
    sprite.fill(3, 19, 28, 19, "stone", tone=DARK)
    for x in range(4, 28, 3):
        sprite.set(x, 19, "opening")
    cast_shadow(sprite, 6, 25, 20, depth=2, materials=("stone",))
    for merlon_left in (4, 24):
        for y in range(12, 15):
            sprite.shift(merlon_left + 3, y, -1, ("stone",))
    recess(sprite, 13, 38, 18, GROUND_Y, ("wood",))
    ambient_occlusion(sprite, 5, 26, GROUND_Y, ("stone",))


def bastion_details(sprite: Sprite, rng):
    stone_courses(sprite, 6, 22, 25, GROUND_Y, rng)
    stone_courses(sprite, 4, 16, 27, 17, rng, heights=(2,), widths=(4, 5, 6), protrude=False)
    planks(sprite, 13, 39, 18, GROUND_Y, rng, plank_width=2, nails=False)
    for stud_y in (40, 43):
        sprite.set(14, stud_y, "iron", tone=LIGHT)
        sprite.set(17, stud_y, "iron", tone=LIGHT)
    sprite.fill(12, 37, 19, 37, "stone", tone=LIGHT)


SHAPES = {1: platform_shape, 2: watchtower_shape, 3: bastion_shape}
SHADERS = {1: platform_shading, 2: watchtower_shading, 3: bastion_shading}
DETAILS = {1: platform_details, 2: watchtower_details, 3: bastion_details}


def build_base(level_number: int, wave: int = 0, stage: int = 5) -> Image.Image:
    sprite = SHAPES[level_number](wave)
    if stage == 1:
        return sprite.render(silhouette=True)
    sprite.reset_tones()
    if stage >= 3:
        SHADERS[level_number](sprite)
    if stage >= 4:
        DETAILS[level_number](sprite, random.Random(level_number * 11))
    return sprite.render()


def draw_base(level_number: int, wave: int) -> Image.Image:
    return build_base(level_number, wave)


BASE_IDLE_WAVES = [0, 1, 2, 3]
BASE_IDLE_DURATIONS_MS = [200, 200, 200, 200]


# --- Projétil --------------------------------------------------------------------------------------
BOLT_DIRECTIONS = {"E": (1, 0), "SE": (1, 1), "S": (0, 1), "SW": (-1, 1),
                   "W": (-1, 0), "NW": (-1, -1), "N": (0, -1), "NE": (1, -1)}


def draw_bolt(direction: tuple[int, int]) -> Image.Image:
    canvas = Canvas(8, 8)
    layer = Layer()
    step_x, step_y = direction
    length = 6 if step_x and step_y else 7
    start = (3 - step_x * (length // 2), 3 - step_y * (length // 2))
    end = (start[0] + step_x * length, start[1] + step_y * length)
    points = list(line_pixels(start, end))
    for index, (x, y) in enumerate(points):
        if index < 2:
            color = PRIMARY if index == 0 else PRIMARY_LIGHT
        elif index == len(points) - 1:
            color = HIGHLIGHT
        else:
            color = IRON.light
        put(layer, x, y, color)
    canvas.put_layer(layer)
    return canvas.to_image()


# --- Composição para preview -----------------------------------------------------------------------
def compose(level_number: int, wave: int, turret_pose: TurretPose, preset=None) -> Image.Image:
    level = LEVELS[level_number]
    frame = Image.new("RGBA", (BASE_WIDTH, BASE_HEIGHT), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (BASE_WIDTH, BASE_HEIGHT), (0, 0, 0, 0))
    for x, y, _, _ in ellipse_pixels(15.5, GROUND_Y + 0.5, 12.5, 2.2):
        if 0 <= x < BASE_WIDTH and 0 <= y < BASE_HEIGHT:
            shadow.putpixel((x, y), (*SHADOW, 255))
    frame.alpha_composite(shadow)
    frame.alpha_composite(draw_base(level_number, wave))
    frame.alpha_composite(draw_turret(level_number, turret_pose), (level.turret_x, level.rail_top_y - WAIST_ROW - 1))
    return recolor(frame, preset) if preset else frame


def on_background(image: Image.Image) -> Image.Image:
    framed = Image.new("RGBA", image.size, (*BACKGROUND, 255))
    framed.alpha_composite(image)
    return framed


def row_of(images: list[Image.Image], gap: int, scale: int) -> Image.Image:
    width = sum(image.width for image in images) + gap * (len(images) + 1)
    height = max(image.height for image in images) + gap * 2
    sheet = Image.new("RGBA", (width, height), (*BACKGROUND, 255))
    cursor_x = gap
    for image in images:
        sheet.alpha_composite(image, (cursor_x, gap + height - gap * 2 - image.height))
        cursor_x += image.width + gap
    return sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)


if __name__ == "__main__":
    royal = PRESETS["real"]
    levels_real = [compose(level, 0, TurretPose(), royal) for level in (1, 2, 3)]
    levels_rubi = [compose(level, 0, TurretPose(), PRESETS["rubi"]) for level in (1, 2, 3)]
    row_of(levels_real + levels_rubi, gap=4, scale=6).save("balista_levels.png")

    for level in (1, 2, 3):
        base_frames = [draw_base(level, wave) for wave in BASE_IDLE_WAVES]
        # Um arquivo por animação (Art Bible §8), gravado direto no projeto e registrado no art-manifest.json.
        tower = dict(category="Towers", asset_folder="Balista")
        turret_anchor = (LEVELS[level].turret_x + TURRET_WIDTH // 2 - BASE_WIDTH // 2,
                         GROUND_Y + 1 - LEVELS[level].rail_top_y)
        export_animation(base_frames, asset_id=f"balista_base_lv{level}", animation="idle",
                         durations_ms=BASE_IDLE_DURATIONS_MS, controller="TowerBase", ground_row=GROUND_Y,
                         turret_anchor_px=turret_anchor, **tower)
        turret = dict(asset_id=f"balista_turret_lv{level}", controller="TowerTurret", ground_row=WAIST_ROW, **tower)
        export_animation([draw_turret(level, pose) for pose in TURRET_IDLE], animation="idle",
                         durations_ms=TURRET_IDLE_DURATIONS_MS, **turret)
        export_animation([draw_turret(level, pose) for pose in TURRET_FIRE], animation="attack",
                         durations_ms=TURRET_FIRE_DURATIONS_MS, loop=False,
                         impact_frame=TURRET_FIRE_IMPACT_FRAME, **turret)
        idle = [on_background(compose(level, wave, pose, royal)) for wave, pose in zip(BASE_IDLE_WAVES, TURRET_IDLE)]
        save_preview_gif(idle, f"balista_lv{level}_idle.gif", 6, TURRET_IDLE_DURATIONS_MS, BACKGROUND)
        fire = [on_background(compose(level, 0, pose, royal)) for pose in TURRET_FIRE]
        save_preview_gif(fire, f"balista_lv{level}_fire.gif", 6, TURRET_FIRE_DURATIONS_MS, BACKGROUND)

    turret_contact = [recolor(draw_turret(level, pose), royal) for level in (1, 2, 3) for pose in TURRET_FIRE]
    row_of(turret_contact, gap=2, scale=6).save("balista_fire_contact.png")
    bolts = [draw_bolt(direction) for direction in BOLT_DIRECTIONS.values()]
    export_directions(bolts, category="Projectiles", asset_folder="BalistaBolt", asset_id="balista_bolt")
    row_of([recolor(bolt, royal) for bolt in bolts], gap=2, scale=8).save("balista_bolts_preview.png")
