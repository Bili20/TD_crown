"""Comparativo de escala: frame 0 de vários spritesheets lado a lado, alinhados pelo chão.

Uso:
  python3 lineup.py --out lineup.png --scale 6 --background 42,38,52 \
      hero.png@32x32 ankheg_sheet.png@32x32 lich_sheet.png@64x64

O chão de cada sprite é o pixel opaco mais baixo do frame 0, então criaturas que flutuam
devem ter a sombra no chão para alinhar certo.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

GAP = 4
LABEL_HEIGHT = 10


def parse_entry(text: str):
    path_text, size_text = text.rsplit("@", 1)
    width_text, height_text = size_text.lower().split("x")
    return Path(path_text), int(width_text), int(height_text)


def first_frame(path: Path, width: int, height: int) -> Image.Image:
    sheet = Image.open(path).convert("RGBA")
    frame = sheet.crop((0, 0, width, height))
    bounding_box = frame.getbbox()
    return frame.crop(bounding_box) if bounding_box else frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("entries", nargs="+", help="caminho@LxA, ex.: ankheg_sheet.png@32x32")
    parser.add_argument("--out", required=True)
    parser.add_argument("--scale", type=int, default=6)
    parser.add_argument("--background", default="42,38,52")
    args = parser.parse_args()

    background = tuple(int(channel) for channel in args.background.split(","))
    sprites = [(path.stem.replace("_sheet", ""), first_frame(path, width, height))
               for path, width, height in map(parse_entry, args.entries)]
    tallest = max(sprite.height for _, sprite in sprites)
    total_width = sum(sprite.width for _, sprite in sprites) + GAP * (len(sprites) + 1)
    total_height = tallest + GAP * 2

    canvas = Image.new("RGBA", (total_width, total_height), (*background, 255))
    cursor_x = GAP
    label_positions = []
    for name, sprite in sprites:
        canvas.alpha_composite(sprite, (cursor_x, GAP + tallest - sprite.height))
        label_positions.append((name, cursor_x))
        cursor_x += sprite.width + GAP

    scaled = canvas.resize((total_width * args.scale, total_height * args.scale), Image.NEAREST)
    with_labels = Image.new("RGBA", (scaled.width, scaled.height + LABEL_HEIGHT * 2), (*background, 255))
    with_labels.alpha_composite(scaled, (0, 0))
    draw = ImageDraw.Draw(with_labels)
    for name, position_x in label_positions:
        draw.text((position_x * args.scale, scaled.height + 4), name, fill=(220, 214, 200, 255))
    with_labels.save(args.out)
    print(f"Comparativo salvo em {args.out}")


if __name__ == "__main__":
    main()
