from PIL import Image
from pixel_canvas import Canvas, Layer, stamp
from style_test import (PLAYER, REGION1, PLAYER_COLORS, PRESETS, BACKGROUND, DEMON, HELLFIRE, recolor)

# Versão 2 puxando para a referência KO.DLL: sem contorno externo (a silhueta vem do contraste com
# o fundo e da sombra no chão), figura baixa e larga (~10 px), cabeça/chapéu ocupando metade,
# olhos como pixels escuros nas laterais do rosto, mãos de 1 px e armas grandes em cor clara.
FORGE_SOLDIER = [
    "................",
    "................",
    "................",
    "................",
    "......c.........",
    ".....cb.....w...",
    ".....fwf....w...",
    "....dfwffd..w...",
    "...ddeeeedd.w...",
    "....otuuto.eee..",
    ".ffe.sttsbbtd...",
    "fwdecbbwbba.d...",
    "ffdebbbbbaa.....",
    ".fd.deeeedd.....",
    ".....oo.oo......",
    "................",
]

IMP_COLORS = {
    "a": DEMON.dark,
    "b": DEMON.base,
    "c": DEMON.light,
    "y": HELLFIRE.light,
    "h": HELLFIRE.base,
    "k": REGION1.color("OUTLINE"),
    "e": REGION1.color("EYE_WHITE"),
}

# Diabrete: asas de morcego abertas (membrana escura com nervura), chifres claros, olhos de fogo.
IMP = [
    "................",
    "................",
    "................",
    "................",
    "................",
    ".a....c..c....a.",
    ".aa...cbbc...aa.",
    ".aba.bbbbbb.aba.",
    ".a.abybbbyba.a..",
    "....abkekbba....",
    ".....abcbba.....",
    ".....abbba..aa..",
    "......abba.a....",
    "......a..aa.....",
    "................",
    "................",
]


def build(rows: list[str], colors: dict) -> Image.Image:
    canvas = Canvas(len(rows[0]), len(rows))
    layer = Layer()
    stamp(layer, rows, 0, 0, colors)
    canvas.put_layer(layer)
    return canvas.to_image()


def on_shadow(sprite: Image.Image, shadow_left: int, shadow_width: int, shadow_top: int) -> Image.Image:
    # A sombra é objeto separado no jogo (não pula junto com o andar procedural); aqui só para preview.
    framed = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
    shadow_color = (*REGION1.color("SHADOW_BLOB"), 255)
    for x in range(shadow_left + 1, shadow_left + shadow_width - 1):
        framed.putpixel((x, shadow_top), shadow_color)
    for x in range(shadow_left, shadow_left + shadow_width):
        framed.putpixel((x, shadow_top + 1), shadow_color)
    framed.alpha_composite(sprite)
    return framed


def lineup(sprites: list[Image.Image], scale: int, gap: int) -> Image.Image:
    width = sum(sprite.width for sprite in sprites) + gap * (len(sprites) + 1)
    height = max(sprite.height for sprite in sprites) + gap * 2
    sheet = Image.new("RGBA", (width, height), (*BACKGROUND, 255))
    cursor_x = gap
    for sprite in sprites:
        sheet.alpha_composite(sprite, (cursor_x, gap))
        cursor_x += sprite.width + gap
    return sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)


if __name__ == "__main__":
    soldier_index = build(FORGE_SOLDIER, PLAYER_COLORS)
    imp = build(IMP, IMP_COLORS)
    soldier_index.save("forge_soldier_index_v2.png")
    imp.save("imp_v2.png")
    soldiers = [soldier_index] + [recolor(soldier_index, PRESETS[name])
                                  for name in ("real", "rubi", "floresta", "daltonismo")]
    shadowed = [on_shadow(soldier, 3, 9, 14) for soldier in soldiers] + [on_shadow(imp, 4, 8, 13)]
    lineup(shadowed, scale=8, gap=3).save("style_test_v2_lineup.png")
    lineup([shadowed[1], shadowed[-1], shadowed[2], shadowed[-1]], scale=3, gap=3).save("style_test_v2_3x.png")
