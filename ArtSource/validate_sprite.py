"""Confere um spritesheet contra a art bible do projeto.

Uso:
  python3 validate_sprite.py SHEET.png --style art-style.json --palette act1 --size-class medium
  python3 validate_sprite.py SHEET.png --style art-style.json --palette act1 --frame 32x32

O relatório separa ERRO (quebra o import ou a regra da bible) de AVISO (vale olhar a imagem).
Não substitui olhar o sprite ampliado: serve para pegar o que o olho deixa passar.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

from pixel_canvas import frame_spec, load_palette, load_style

NEIGHBORS_8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def luminance(color) -> float:
    red, green, blue = color[:3]
    return 0.299 * red + 0.587 * green + 0.114 * blue


def allowed_colors(palette) -> set[tuple[int, int, int]]:
    allowed = set(palette.colors.values())
    for ramp in palette.ramps.values():
        for tone in (ramp.deep, ramp.dark, ramp.base, ramp.light, ramp.shine):
            if tone is not None:
                allowed.add(tone)
    return allowed


def parse_frame_size(text: str) -> tuple[int, int]:
    width_text, height_text = text.lower().split("x")
    return int(width_text), int(height_text)


def analyze_frame(frame: Image.Image, allowed: set, edge_margin: int):
    width, height = frame.size
    pixels = frame.load()
    opaque_positions = set()
    off_palette = Counter()
    partial_alpha = 0
    colors_used = set()
    edge_sides = Counter()
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            opaque_positions.add((x, y))
            if alpha < 255:
                partial_alpha += 1
            rgb = (red, green, blue)
            colors_used.add(rgb)
            if alpha == 255 and rgb not in allowed:
                off_palette[rgb] += 1
            if x < edge_margin:
                edge_sides["esquerda"] += 1
            if x >= width - edge_margin:
                edge_sides["direita"] += 1
            if y < edge_margin:
                edge_sides["topo"] += 1
            if y >= height - edge_margin:
                edge_sides["base"] += 1
    isolated = [
        (x, y) for x, y in opaque_positions
        if not any((x + offset_x, y + offset_y) in opaque_positions for offset_x, offset_y in NEIGHBORS_8)
    ]
    mean_luminance = None
    if opaque_positions:
        mean_luminance = sum(luminance(pixels[x, y]) for x, y in opaque_positions) / len(opaque_positions)
    return {
        "empty": not opaque_positions,
        "off_palette": off_palette,
        "partial_alpha": partial_alpha,
        "colors_used": len(colors_used),
        "edge_sides": edge_sides,
        "isolated": isolated,
        "mean_luminance": mean_luminance,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet")
    parser.add_argument("--style", required=True, help="art-style.json do projeto")
    parser.add_argument("--palette", required=True, help="nome da paleta (bioma/área) na art bible")
    size_group = parser.add_mutually_exclusive_group(required=True)
    size_group.add_argument("--size-class", help="classe de tamanho definida em sizes (tier, tipo de asset)")
    size_group.add_argument("--frame", help="tamanho do frame, ex.: 32x32")
    parser.add_argument("--max-colors", type=int, default=None, help="sobrescreve validation.max_colors_per_frame")
    args = parser.parse_args()

    style = load_style(args.style)
    palette = load_palette(style, args.palette)
    validation = style.get("validation", {})
    edge_margin = validation.get("edge_margin", 1)
    max_colors = args.max_colors or validation.get("max_colors_per_frame")
    luminance_range = validation.get("frame0_luminance_range")
    allowed = allowed_colors(palette)

    if args.size_class:
        frame_width, frame_height, _ = frame_spec(style, args.size_class)
    else:
        frame_width, frame_height = parse_frame_size(args.frame)

    sheet = Image.open(args.sheet).convert("RGBA")
    errors, warnings, notes = [], [], []

    if sheet.width % frame_width or sheet.height % frame_height:
        errors.append(f"Folha {sheet.width}x{sheet.height} não divide em frames {frame_width}x{frame_height}.")
        print_report(args.sheet, errors, warnings, notes)
        return 1

    columns = sheet.width // frame_width
    rows = sheet.height // frame_height
    notes.append(f"{rows} linha(s) × {columns} coluna(s) de frames {frame_width}x{frame_height}, paleta '{args.palette}'.")

    total_off_palette = Counter()
    edge_sides_total = Counter()
    frames_on_edge = 0
    for row_index in range(rows):
        filled_columns = []
        for column_index in range(columns):
            box = (column_index * frame_width, row_index * frame_height,
                   (column_index + 1) * frame_width, (row_index + 1) * frame_height)
            result = analyze_frame(sheet.crop(box), allowed, edge_margin)
            label = f"linha {row_index} frame {column_index}"
            if result["empty"]:
                continue
            filled_columns.append(column_index)
            total_off_palette.update(result["off_palette"])
            if result["edge_sides"]:
                frames_on_edge += 1
                edge_sides_total.update(result["edge_sides"])
            if result["partial_alpha"] and not palette.translucent:
                errors.append(f"{label}: {result['partial_alpha']} pixel(s) com alpha parcial e a paleta não tem rampa translúcida.")
            if max_colors and result["colors_used"] > max_colors:
                warnings.append(f"{label}: {result['colors_used']} cores (limite {max_colors}); risco de ruído.")
            if result["isolated"]:
                sample = ", ".join(str(position) for position in result["isolated"][:5])
                warnings.append(f"{label}: {len(result['isolated'])} pixel(s) solto(s) sem vizinho: {sample}")
            if row_index == 0 and column_index == 0 and luminance_range and result["mean_luminance"] is not None:
                low, high = luminance_range
                value = result["mean_luminance"]
                message = f"luminância média do frame 0 = {value:.1f} (faixa da bible {low}–{high})"
                (notes if low <= value <= high else warnings).append(message)
        if filled_columns and filled_columns != list(range(len(filled_columns))):
            warnings.append(f"linha {row_index}: há célula vazia no meio da animação (colunas {filled_columns}).")

    if frames_on_edge:
        sides = ", ".join(f"{side}×{count}" for side, count in edge_sides_total.most_common())
        warnings.append(f"conteúdo na faixa de {edge_margin}px da borda em {frames_on_edge} frame(s) ({sides} pixels). "
                        "Pode ser intencional (efeito de golpe, corpo encostado); confira se nenhum contorno foi cortado.")

    if total_off_palette:
        top = ", ".join(f"{color}×{count}" for color, count in total_off_palette.most_common(8))
        target = warnings if palette.translucent else errors
        hint = " (esperado onde houver composição translúcida)" if palette.translucent else ""
        target.append(f"{len(total_off_palette)} cor(es) fora da paleta{hint}: {top}")
    else:
        notes.append("Todas as cores opacas estão na paleta.")

    print_report(args.sheet, errors, warnings, notes)
    return 1 if errors else 0


def print_report(sheet_path, errors, warnings, notes):
    print(f"== {Path(sheet_path).name} ==")
    for message in errors:
        print(f"ERRO   {message}")
    for message in warnings:
        print(f"AVISO  {message}")
    for message in notes:
        print(f"ok     {message}")


if __name__ == "__main__":
    sys.exit(main())
