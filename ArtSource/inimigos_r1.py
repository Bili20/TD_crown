"""Brutamontes do lote da demo pública (pose base antiga, em redesenho: ver Art Bible §10).

O Cão Infernal saiu daqui e está em cao_infernal.py.
Brutamontes: sai do chibi de propósito — cabeça pequena afundada entre ombros enormes, placas de
ferro negro cravadas na pele com brasas nas juntas e uma clava apoiada no chão.
"""
from PIL import Image
from pixel_canvas import Layer, stamp
from style_test import REGION1
from tower_parts import layers_to_image, ground_shadow

DEMON = REGION1.ramp("DEMON")
HELLFIRE = REGION1.ramp("HELLFIRE")
BLACK_IRON = REGION1.ramp("BLACK_IRON")
WOOD = REGION1.ramp("WOOD")

COLORS = {
    "a": DEMON.dark, "b": DEMON.base, "c": DEMON.light,
    "r": HELLFIRE.dark, "h": HELLFIRE.base, "y": HELLFIRE.light, "Y": HELLFIRE.shine,
    "k": REGION1.color("OUTLINE"), "e": REGION1.color("EYE_WHITE"),
    "i": BLACK_IRON.dark, "j": BLACK_IRON.base, "l": BLACK_IRON.light, "L": BLACK_IRON.shine,
    "n": WOOD.dark, "m": WOOD.base, "M": WOOD.light,
}

BRUTE_HEAD = [
    "c......c",
    "cb....bc",
    ".bbccbb.",
    "abcccbba",
    "abybbyba",
    "abbbbbba",
    "abkeekba",
    ".aabbaa.",
]
BRUTE_CLUB = [
    ".iiii.",
    "LlljiL",
    "illjji",
    "iljjji",
    "illjji",
    "LljjiL",
    ".ijji.",
    "..mn..",
    "..mn..",
    "..mn..",
    "..mn..",
    "..mn..",
]


def draw_brute() -> Image.Image:
    from pixel_canvas import ellipse_pixels, polygon_pixels, shaded_ellipse, tube_layer
    from tower_parts import put, fill
    layer = Layer()
    # Pernas curtas e grossas com grevas de ferro negro.
    for leg_left in (7, 12):
        fill(layer, leg_left, 16, leg_left + 3, 21, DEMON.dark)
        fill(layer, leg_left, 16, leg_left + 1, 18, DEMON.base)
        fill(layer, leg_left, 19, leg_left + 3, 20, BLACK_IRON.base)
        fill(layer, leg_left, 19, leg_left + 3, 19, BLACK_IRON.light)
        put(layer, leg_left + 2, 18, HELLFIRE.base)
        fill(layer, leg_left - 1, 22, leg_left + 3, 22, COLORS["k"])
    # Tronco em V: largo nos ombros, cintura estreita. A luz vem da esquerda.
    for x, y in polygon_pixels([(5, 8), (17, 8), (14, 15), (8, 15)]):
        horizontal = (x - 11) / 6
        put(layer, x, y, DEMON.light if horizontal < -0.55 else (DEMON.dark if horizontal > 0.6 else DEMON.base))
    # Peitoral de ferro negro com rebites e brasa nas frestas.
    for x, y in polygon_pixels([(8, 10), (14, 10), (13, 13), (9, 13)]):
        put(layer, x, y, BLACK_IRON.base)
    fill(layer, 8, 10, 14, 10, BLACK_IRON.light)
    for x, y in ((8, 10), (14, 10), (9, 13), (13, 13)):
        put(layer, x, y, BLACK_IRON.shine)
    fill(layer, 11, 11, 11, 12, HELLFIRE.base)
    put(layer, 11, 11, HELLFIRE.light)
    fill(layer, 9, 14, 13, 14, BLACK_IRON.dark)
    put(layer, 11, 14, HELLFIRE.light)
    fill(layer, 7, 15, 15, 15, BLACK_IRON.dark)
    put(layer, 11, 15, HELLFIRE.light)
    # Braço de quem olha à direita: ombro redondo e a mão fechada no cabo da clava.
    arm_right = tube_layer([(18, 9), (19, 11), (19, 13)], lambda progress: 2.0 - 0.3 * progress, DEMON)
    layer.pixels.update(arm_right.pixels)
    shaded_ellipse(layer, DEMON, 17.5, 8, 3.5, 2.8)
    fill(layer, 18, 11, 21, 11, BLACK_IRON.base)
    # Ombreira de ferro negro com espinho e o braço esquerdo pendendo até o punho grande.
    arm_left = tube_layer([(4, 9), (3, 12), (3, 15)], lambda progress: 2.0 + 0.2 * progress, DEMON)
    layer.pixels.update(arm_left.pixels)
    fill(layer, 1, 13, 5, 13, BLACK_IRON.base)
    shaded_ellipse(layer, DEMON, 3.5, 16.5, 2.4, 1.9)
    put(layer, 3, 17, DEMON.dark)
    for x, y, _, normalized_y in ellipse_pixels(4.8, 8, 3.2, 2.8):
        if normalized_y < 0.35:
            put(layer, x, y, BLACK_IRON.light if normalized_y < -0.1 else BLACK_IRON.base)
    fill(layer, 1, 10, 8, 10, DEMON.dark)
    put(layer, 3, 10, HELLFIRE.base)
    put(layer, 3, 6, BLACK_IRON.shine)
    put(layer, 4, 4, BLACK_IRON.light)
    put(layer, 4, 5, BLACK_IRON.shine)
    # Cabeça pequena afundada entre os ombros: o anel escuro em volta separa a cabeça do tronco.
    stamp(layer, BRUTE_HEAD, 8, 1, COLORS)
    fill(layer, 9, 9, 13, 9, DEMON.dark)
    # Clava de pé, apoiada no chão, com a mão fechada no cabo.
    stamp(layer, BRUTE_CLUB, 17, 1, COLORS)
    for x, y, _, _ in ellipse_pixels(19.5, 12.5, 2.2, 1.6):
        put(layer, x, y, DEMON.base)
    fill(layer, 18, 12, 21, 12, DEMON.light)
    put(layer, 21, 13, DEMON.dark)
    return layers_to_image(24, 24, layer)


BRUTE_FRAME = 24
BRUTE_GROUND_ROW = 22


def draw(rows: list[str]) -> Image.Image:
    layer = Layer()
    stamp(layer, rows, 0, 0, COLORS)
    return layers_to_image(len(rows[0]), len(rows), layer)


def with_shadow(sprite: Image.Image, ground_row: int, radius_x: float) -> Image.Image:
    framed = ground_shadow(sprite.width, sprite.height, sprite.width / 2 - 0.5, ground_row - 1, radius_x, 1.6)
    framed.alpha_composite(sprite)
    return framed


if __name__ == "__main__":
    from balista import row_of
    import cao_infernal
    hound = cao_infernal.with_blob(cao_infernal.final_frame(cao_infernal.IDLE[0]), cao_infernal.IDLE[0])
    brute = with_shadow(draw_brute(), BRUTE_GROUND_ROW, 8.5)
    imp = Image.open("../Assets/_Project/Art/Enemies/Imp/imp_idle.png").convert("RGBA").crop((0, 0, 16, 16))
    row_of([imp, hound, brute], gap=3, scale=10).save("inimigos_preview.png")
