"""Prancha de revisão do lote da demo pública: poses base ao lado dos aprovados e uma cena de teste.

Gera em ArtSource/ (ignorado pelo git):
- prancha_torres.png: as 4 torres da demo nos 3 níveis, presets real e rubi;
- prancha_unidades.png: soldados nv1–nv3, inimigos, frasco, virote e poça sobre terra e grama;
- prancha_cena_3x.png: um trecho de mapa em escala de jogo (3×, como em 1080p).
"""
import random
from PIL import Image, ImageDraw
from style_test import PRESETS, BACKGROUND, recolor
from tower_parts import GRASS, DIRT, ground_shadow
import balista
import forja
import campanario
import alquimista
import inimigos_r1
import cao_infernal
from animate_v2 import draw_soldier as draw_soldier_lv2, SoldierPose

LABEL_COLOR = (236, 230, 214, 255)


def towers(preset_name: str) -> list[tuple[str, Image.Image]]:
    preset = PRESETS[preset_name]
    items = []
    for level in (1, 2, 3):
        items.append((f"balista {level}", balista.compose(level, 0, balista.TurretPose(), preset)))
    for level in (1, 2, 3):
        items.append((f"forja {level}", forja.compose_tower(forja.draw_base(level, forja.ForgePose()), None, None, preset)))
    for level in (1, 2, 3):
        items.append((f"campanario {level}", campanario.compose(level, campanario.BellPose(), preset)))
    for level in (1, 2, 3):
        items.append((f"alquimista {level}", alquimista.compose(level, alquimista.ThrowPose(), preset)))
    return items


def soldier_with_shadow(sprite: Image.Image) -> Image.Image:
    framed = ground_shadow(16, 16, 7.5, 14, 4.5, 1.2)
    framed.alpha_composite(sprite)
    return framed


def units(preset_name: str) -> list[tuple[str, Image.Image]]:
    preset = PRESETS[preset_name]
    imp = Image.open("../Assets/_Project/Art/Enemies/Imp/imp_idle.png").convert("RGBA").crop((0, 0, 16, 16))
    bolt = recolor(balista.draw_bolt((1, 0)), preset)
    return [
        ("soldado 1", soldier_with_shadow(recolor(forja.draw_soldier(forja.SOLDIER_RECRUIT), preset))),
        ("soldado 2", soldier_with_shadow(recolor(draw_soldier_lv2(SoldierPose()), preset))),
        ("soldado 3", soldier_with_shadow(recolor(forja.draw_soldier(forja.SOLDIER_VETERAN), preset))),
        ("diabrete", soldier_with_shadow(imp)),
        ("cao", cao_infernal.with_blob(cao_infernal.final_frame(cao_infernal.IDLE[0]), cao_infernal.IDLE[0])),
        ("brutamontes", inimigos_r1.with_shadow(inimigos_r1.draw_brute(), inimigos_r1.BRUTE_GROUND_ROW, 8.5)),
        ("virote", bolt),
        ("frasco", alquimista.draw_flask()),
        ("poca", alquimista.draw_puddle()),
    ]


def board(items: list[tuple[str, Image.Image]], scale: int, background, gap: int = 4) -> Image.Image:
    width = sum(image.width for _, image in items) + gap * (len(items) + 1)
    height = max(image.height for _, image in items) + gap * 2
    sheet = Image.new("RGBA", (width, height), (*background, 255))
    cursor_x = gap
    positions = []
    for name, image in items:
        sheet.alpha_composite(image, (cursor_x, height - gap - image.height))
        positions.append((name, cursor_x))
        cursor_x += image.width + gap
    scaled = sheet.resize((width * scale, height * scale), Image.NEAREST)
    labeled = Image.new("RGBA", (scaled.width, scaled.height + 14), (*background, 255))
    labeled.alpha_composite(scaled)
    draw = ImageDraw.Draw(labeled)
    for name, position_x in positions:
        draw.text((position_x * scale, scaled.height + 2), name, fill=LABEL_COLOR)
    return labeled


def stack(images: list[Image.Image], background) -> Image.Image:
    width = max(image.width for image in images)
    height = sum(image.height for image in images)
    sheet = Image.new("RGBA", (width, height), (*background, 255))
    cursor_y = 0
    for image in images:
        sheet.alpha_composite(image, (0, cursor_y))
        cursor_y += image.height
    return sheet


# --- Cena de teste ---------------------------------------------------------------------------------
TILE = 16


def ground(width_tiles: int, height_tiles: int, path_tiles: set[tuple[int, int]]) -> Image.Image:
    # Chão provisório só para testar contraste: o tileset real ainda não existe.
    generator = random.Random(7)
    image = Image.new("RGBA", (width_tiles * TILE, height_tiles * TILE))
    for tile_y in range(height_tiles):
        for tile_x in range(width_tiles):
            ramp = DIRT if (tile_x, tile_y) in path_tiles else GRASS
            for y in range(TILE):
                for x in range(TILE):
                    roll = generator.random()
                    color = ramp.base
                    if roll < 0.08:
                        color = ramp.dark
                    elif roll < 0.14:
                        color = ramp.light
                    image.putpixel((tile_x * TILE + x, tile_y * TILE + y), (*color, 255))
    return image


def place(scene: Image.Image, sprite: Image.Image, foot_x: int, foot_y: int):
    scene.alpha_composite(sprite, (foot_x - sprite.width // 2, foot_y - sprite.height + 1))


def scene_3x() -> Image.Image:
    width_tiles, height_tiles = 20, 11
    path = {(x, 5) for x in range(0, 13)} | {(x, 6) for x in range(0, 13)}
    path |= {(11, y) for y in range(0, 7)} | {(12, y) for y in range(0, 7)}
    path |= {(x, 9) for x in range(11, 20)} | {(x, 8) for x in range(11, 20)}
    path |= {(11, y) for y in range(6, 10)} | {(12, y) for y in range(6, 10)}
    scene = ground(width_tiles, height_tiles, path)
    royal = PRESETS["real"]
    # Torres nos pontos de construção (a base encosta no chão na linha 44 do quadro de 48).
    tower_spots = [
        (balista.compose(2, 0, balista.TurretPose(), royal), 3, 4),
        (forja.compose_tower(forja.draw_base(2, forja.ForgePose()), None, None, royal), 6, 4),
        (campanario.compose(2, campanario.BellPose(), royal), 9, 4),
        (alquimista.compose(2, alquimista.ThrowPose(), royal), 15, 7),
        (forja.compose_tower(forja.draw_base(3, forja.ForgePose()), None, None, royal), 8, 10),
        (campanario.compose(3, campanario.BellPose(), royal), 15, 4),
        (alquimista.compose(1, alquimista.ThrowPose(), royal), 4, 10),
        (alquimista.compose(3, alquimista.ThrowPose(), royal), 18, 4),
        (balista.compose(3, 0, balista.TurretPose(), royal), 1, 10),
        (balista.compose(1, 0, balista.TurretPose(), royal), 18, 7),
    ]
    puddle = alquimista.draw_puddle()
    scene.alpha_composite(puddle, (13 * TILE, 8 * TILE - 2))
    sprites = []
    for image, tile_x, tile_y in tower_spots:
        sprites.append((tile_y * TILE, image, tile_x * TILE + 8, tile_y * TILE + 3))
    imp = soldier_with_shadow(Image.open("../Assets/_Project/Art/Enemies/Imp/imp_idle.png").convert("RGBA").crop((0, 0, 16, 16)))
    # Sombra com o topo na linha dos pés: centrada acima dela, cobre as pernas do cão escuro.
    hound = cao_infernal.with_blob(cao_infernal.final_frame(cao_infernal.IDLE[0]), cao_infernal.IDLE[0])
    brute = inimigos_r1.with_shadow(inimigos_r1.draw_brute(), inimigos_r1.BRUTE_GROUND_ROW, 8.5)
    soldier = soldier_with_shadow(recolor(draw_soldier_lv2(SoldierPose()), royal))
    veteran = soldier_with_shadow(recolor(forja.draw_soldier(forja.SOLDIER_VETERAN), royal))
    walkers = [
        (imp, 20, 100), (imp, 34, 96), (imp, 46, 102), (hound, 80, 100), (hound, 104, 96),
        (brute, 150, 102), (soldier, 166, 100), (veteran, 166, 92), (imp, 196, 60), (imp, 192, 40),
        (hound, 240, 148), (brute, 290, 150),
    ]
    for sprite, foot_x, foot_y in walkers:
        sprites.append((foot_y, sprite, foot_x, foot_y))
    for _, sprite, foot_x, foot_y in sorted(sprites, key=lambda entry: entry[0]):
        place(scene, sprite, foot_x, foot_y)
    return scene.resize((scene.width * 3, scene.height * 3), Image.NEAREST)


if __name__ == "__main__":
    tower_board = stack([board(towers("real"), 5, BACKGROUND), board(towers("rubi")[3:], 5, BACKGROUND)], BACKGROUND)
    tower_board.save("prancha_torres.png")
    unit_board = stack([board(units("real"), 7, BACKGROUND), board(units("real"), 7, DIRT.base),
                        board(units("real"), 7, GRASS.base)], BACKGROUND)
    unit_board.save("prancha_unidades.png")
    scene_3x().save("prancha_cena_3x.png")
    print("ok")
