"""Peças comuns das torres: helpers de desenho, flâmula do time, operadores e composição de preview."""
from PIL import Image
from pixel_canvas import Canvas, Layer, line_pixels, ellipse_pixels, stamp
from style_test import PLAYER, PLAYER_COLORS, REGION1, recolor

BASE_WIDTH, BASE_HEIGHT, GROUND_Y = 32, 48, 44
TURRET_WIDTH, TURRET_HEIGHT = 20, 16
WAIST_ROW = 12

WOOD = PLAYER.ramp("WOOD")
STONE = PLAYER.ramp("STONE")
IRON = PLAYER.ramp("IRON")
SKIN = PLAYER.ramp("SKIN")
HOLY = PLAYER.ramp("HOLY")
STRING = PLAYER.color("STRING")
DARKEST = PLAYER_COLORS["o"]
PRIMARY_DARK, PRIMARY, PRIMARY_LIGHT = PLAYER_COLORS["a"], PLAYER_COLORS["b"], PLAYER_COLORS["c"]
SECONDARY_DARK, SECONDARY, SECONDARY_LIGHT = PLAYER_COLORS["d"], PLAYER_COLORS["e"], PLAYER_COLORS["f"]
HIGHLIGHT = PLAYER_COLORS["w"]
OPENING = REGION1.color("OUTLINE")
SHADOW = REGION1.color("SHADOW_BLOB")
GRASS = REGION1.ramp("GRASS")
DIRT = REGION1.ramp("DIRT")


def put(layer: Layer, x: int, y: int, color):
    layer.pixels[(x, y)] = color


def fill(layer: Layer, left: int, top: int, right: int, bottom: int, color):
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            layer.pixels[(x, y)] = color


def draw_line(layer: Layer, start, end, color):
    for x, y in line_pixels(start, end):
        layer.pixels[(x, y)] = color


def erase_below(layer: Layer, row: int):
    for position in [position for position in layer.pixels if position[1] > row]:
        del layer.pixels[position]


def draw_pennant(layer: Layer, pole_x: int, pole_top: int, pole_bottom: int, wave: int):
    # Mesma flâmula da Balista: a cor do time aparece acima da torre em qualquer nível.
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


def draw_shield(layer: Layer, left: int, top: int):
    stamp(layer, [".bbbb.", "abwwbb", "abbwbb", ".abbb.", "..ab.."], left, top, PLAYER_COLORS)


def draw_banner(layer: Layer, left: int, top: int, length: int = 10):
    rows = ["eeeeee"] + ["abbbbc"] * 2 + ["abwwbc", "awwwwc", "abwwbc"] + ["abbbbc"] * max(0, length - 8)
    rows += ["ebbbbe", "e.ab.e"]
    stamp(layer, rows, left, top, PLAYER_COLORS)


def ground_shadow(width: int, height: int, center_x: float, ground_y: int, radius_x: float,
                  radius_y: float = 2.2) -> Image.Image:
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for x, y, _, _ in ellipse_pixels(center_x, ground_y + 0.5, radius_x, radius_y):
        if 0 <= x < width and 0 <= y < height:
            shadow.putpixel((x, y), (*SHADOW, 255))
    return shadow


def layers_to_image(width: int, height: int, *layers: Layer) -> Image.Image:
    canvas = Canvas(width, height)
    for layer in layers:
        canvas.put_layer(layer)
    return canvas.to_image()


def compose_tower(base: Image.Image, turret: Image.Image | None, turret_origin: tuple[int, int] | None,
                  preset=None, shadow_radius: float = 12.5) -> Image.Image:
    frame = ground_shadow(BASE_WIDTH, BASE_HEIGHT, 15.5, GROUND_Y, shadow_radius)
    frame.alpha_composite(base)
    if turret is not None:
        frame.alpha_composite(turret, turret_origin)
    return recolor(frame, preset) if preset else frame


def turret_origin(turret_x: int, rail_top_y: int) -> tuple[int, int]:
    return turret_x, rail_top_y - WAIST_ROW - 1


def turret_anchor_px(turret_x: int, rail_top_y: int) -> tuple[int, int]:
    # Âncora da camada de cima em relação ao pivô da base (centro do chão), como no art-manifest.
    return turret_x + TURRET_WIDTH // 2 - BASE_WIDTH // 2, GROUND_Y + 1 - rail_top_y
