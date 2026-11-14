from pathlib import Path
from PIL import Image
from pixel_canvas import Canvas, Layer, stamp, load_style, load_palette, preview_background

STYLE = load_style(Path(__file__).resolve().parents[1] / "docs" / "art-style.json")
PLAYER = load_palette(STYLE, "player_index")
REGION1 = load_palette(STYLE, "region1_vale")
BACKGROUND = preview_background(STYLE)
PRESETS = STYLE["recolor"]["presets"]
INDEX_LEVELS = STYLE["recolor"]["index_levels"]
NEUTRAL_TOLERANCE = STYLE["recolor"]["neutral_tolerance"]

SKIN = PLAYER.ramp("SKIN")
PLAYER_COLORS = {
    "o": PLAYER.color("IDX0_OUTLINE"),
    "a": PLAYER.color("IDX1_PRIMARY_DARK"),
    "b": PLAYER.color("IDX2_PRIMARY_BASE"),
    "c": PLAYER.color("IDX3_PRIMARY_LIGHT"),
    "d": PLAYER.color("IDX4_SECONDARY_DARK"),
    "e": PLAYER.color("IDX5_SECONDARY_BASE"),
    "f": PLAYER.color("IDX6_SECONDARY_LIGHT"),
    "w": PLAYER.color("IDX7_HIGHLIGHT"),
    "s": SKIN.dark,
    "t": SKIN.base,
    "u": SKIN.light,
}

# Soldado da Forja: elmo de metal (secundária), tabardo com emblema (primária), escudo à frente,
# espada de pé ao lado — nunca cruzando o corpo no idle.
FORGE_SOLDIER = [
    "................",
    "......oco.......",
    "....oocbooo.oo..",
    "...odfwwffdowfo.",
    "..oeeeeeeeeowfo.",
    "...outtttssowfo.",
    "...otttotosowfo.",
    "....osttssoowfo.",
    "...ocbbbbbaowfo.",
    "oeeeobbwbbaoeeeo",
    "obcbobbbbbabtuo.",
    "obwaobbbbbaoddo.",
    "oabaodeeeddooo..",
    ".oaoobbbbbao....",
    "..o.oddoddo.....",
    "....ooooooo.....",
]

DEMON = REGION1.ramp("DEMON")
HELLFIRE = REGION1.ramp("HELLFIRE")
IMP_COLORS = {
    "o": REGION1.color("OUTLINE"),
    "a": DEMON.dark,
    "b": DEMON.base,
    "c": DEMON.light,
    "h": HELLFIRE.base,
    "y": HELLFIRE.light,
    "e": REGION1.color("EYE_WHITE"),
}

# Diabrete: chifres, olhos de fogo, sorriso com presa, asinha atrás e cauda — leve e curvado.
IMP = [
    "................",
    "................",
    "................",
    "................",
    ".....o...o......",
    "....oco.oco.....",
    "o...obbcbbbo....",
    "oaoobcbbbbbbo...",
    "oaaobyhbbyhbo...",
    "oaaoabboeobao...",
    ".o.ooabbbbao....",
    "....oabcbbao.oo.",
    ".....oabbbaoobo.",
    ".....oaaaaaoo...",
    ".....oao.oao....",
    ".....ooo.ooo....",
]


def build(rows: list[str], colors: dict) -> Image.Image:
    canvas = Canvas(len(rows[0]), len(rows))
    layer = Layer()
    stamp(layer, rows, 0, 0, colors)
    canvas.put_layer(layer)
    return canvas.to_image()


def recolor(index_image: Image.Image, preset: list[list[int]]) -> Image.Image:
    # Simula o shader: só cinza neutro vira índice da paleta; pele, madeira, pedra e ferro têm tom e passam direto.
    result = index_image.copy()
    for y in range(result.height):
        for x in range(result.width):
            red, green, blue, alpha = result.getpixel((x, y))
            if alpha == 0:
                continue
            if max(red, green, blue) - min(red, green, blue) > NEUTRAL_TOLERANCE:
                continue
            palette_index = round(red / 255 * (INDEX_LEVELS - 1))
            result.putpixel((x, y), (*preset[palette_index], 255))
    return result


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
    soldier_index.save("forge_soldier_index.png")
    imp.save("imp.png")
    variants = [soldier_index] + [recolor(soldier_index, PRESETS[name])
                                  for name in ("real", "rubi", "floresta", "daltonismo")]
    lineup(variants + [imp], scale=8, gap=3).save("style_test_lineup.png")
    lineup([variants[1], imp, variants[2], imp], scale=1, gap=3).save("style_test_1x.png")
    lineup([variants[1], imp, variants[2], imp], scale=3, gap=3).save("style_test_3x.png")
