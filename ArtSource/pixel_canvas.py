"""Biblioteca de desenho de pixel art por código. Copie para a pasta de trabalho e importe."""
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image

Color = tuple[int, int, int]


@dataclass(frozen=True)
class Ramp:
    dark: Color
    base: Color
    light: Color
    shine: Color | None = None
    deep: Color | None = None  # 5º tom, usado em boss/peças grandes


@dataclass
class Layer:
    pixels: dict[tuple[int, int], Color] = field(default_factory=dict)

    def mask(self) -> set[tuple[int, int]]:
        return set(self.pixels)


class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.pixels: dict[tuple[int, int], Color] = {}

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def put(self, x: int, y: int, color: Color):
        if self.inside(x, y):
            self.pixels[(x, y)] = color

    def put_layer(self, layer: Layer, outline_color: Color | None = None):
        # O contorno de cada parte é desenhado antes do preenchimento: onde as partes se sobrepõem,
        # o contorno da parte da frente vira a linha de separação entre elas.
        if outline_color is not None:
            for x, y in outline_ring(layer.mask()):
                self.put(x, y, outline_color)
        for (x, y), color in layer.pixels.items():
            self.put(x, y, color)

    def to_image(self) -> Image.Image:
        image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        for (x, y), color in self.pixels.items():
            image.putpixel((x, y), (*color, 255))
        return image


def outline_ring(mask: set[tuple[int, int]]) -> set[tuple[int, int]]:
    ring = set()
    for x, y in mask:
        for neighbor in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if neighbor not in mask:
                ring.add(neighbor)
    return ring


def stamp(layer: Layer, rows: list[str], origin_x: int, origin_y: int, colors: dict[str, Color]):
    # Peça desenhada à mão numa grade de texto; "." é transparente.
    for row_index, row in enumerate(rows):
        for column_index, symbol in enumerate(row):
            if symbol != ".":
                layer.pixels[(origin_x + column_index, origin_y + row_index)] = colors[symbol]


def ellipse_pixels(center_x: float, center_y: float, radius_x: float, radius_y: float):
    for y in range(int(center_y - radius_y) - 1, int(center_y + radius_y) + 2):
        for x in range(int(center_x - radius_x) - 1, int(center_x + radius_x) + 2):
            normalized_x = (x + 0.5 - center_x) / radius_x
            normalized_y = (y + 0.5 - center_y) / radius_y
            if normalized_x * normalized_x + normalized_y * normalized_y <= 1.0:
                yield x, y, normalized_x, normalized_y


def rotated_ellipse_pixels(center_x, center_y, radius_long, radius_short, angle_degrees):
    angle = math.radians(angle_degrees)
    reach = int(max(radius_long, radius_short)) + 2
    for y in range(int(center_y) - reach, int(center_y) + reach + 1):
        for x in range(int(center_x) - reach, int(center_x) + reach + 1):
            offset_x, offset_y = x + 0.5 - center_x, y + 0.5 - center_y
            along = offset_x * math.cos(angle) + offset_y * math.sin(angle)
            across = -offset_x * math.sin(angle) + offset_y * math.cos(angle)
            if (along / radius_long) ** 2 + (across / radius_short) ** 2 <= 1:
                yield x, y, along / radius_long, across / radius_short


def shaded_ellipse(layer: Layer, ramp: Ramp, center_x, center_y, radius_x, radius_y, plate_columns=()):
    for x, y, normalized_x, normalized_y in ellipse_pixels(center_x, center_y, radius_x, radius_y):
        if normalized_y > 0.45:
            color = ramp.dark
        elif normalized_y < -0.5:
            color = ramp.light
        else:
            color = ramp.base
        if x in plate_columns and normalized_y < 0.45:
            color = ramp.dark
        layer.pixels[(x, y)] = color


def polygon_pixels(points: list[tuple[int, int]]):
    min_y = min(point_y for _, point_y in points)
    max_y = max(point_y for _, point_y in points)
    for y in range(min_y, max_y + 1):
        crossings = []
        for (start_x, start_y), (end_x, end_y) in zip(points, points[1:] + points[:1]):
            if (start_y <= y < end_y) or (end_y <= y < start_y):
                crossings.append(start_x + (y - start_y) * (end_x - start_x) / (end_y - start_y))
        crossings.sort()
        for left, right in zip(crossings[::2], crossings[1::2]):
            for x in range(round(left), round(right) + 1):
                yield x, y


def line_pixels(start: tuple[int, int], end: tuple[int, int]):
    start_x, start_y = start
    end_x, end_y = end
    delta_x = abs(end_x - start_x)
    delta_y = -abs(end_y - start_y)
    step_x = 1 if start_x < end_x else -1
    step_y = 1 if start_y < end_y else -1
    error = delta_x + delta_y
    x, y = start_x, start_y
    while True:
        yield x, y
        if (x, y) == (end_x, end_y):
            return
        doubled_error = 2 * error
        if doubled_error >= delta_y:
            error += delta_y
            x += step_x
        if doubled_error <= delta_x:
            error += delta_x
            y += step_y


def polyline_pixels(points: list[tuple[int, int]]):
    for start, end in zip(points, points[1:]):
        yield from line_pixels(start, end)


def thick_limb(layer: Layer, points: list[tuple[int, int]], ramp: Ramp):
    # Pincel de 2px: luz em cima, base embaixo, juntas em destaque. Use em vez de membros de 1px soltos.
    for x, y in polyline_pixels(points):
        layer.pixels[(x, y)] = ramp.light
        layer.pixels[(x, y + 1)] = ramp.base
    for joint_x, joint_y in points[1:-1]:
        layer.pixels[(joint_x, joint_y)] = ramp.shine or ramp.light


def sample_path(points: list[tuple[float, float]], samples_per_pixel: int = 3):
    lengths = [math.dist(start, end) for start, end in zip(points, points[1:])]
    total = sum(lengths)
    samples = []
    walked = 0.0
    direction_x, direction_y = 1.0, 0.0
    for (start, end), length in zip(zip(points, points[1:]), lengths):
        steps = max(1, int(length * samples_per_pixel))
        direction_x, direction_y = (end[0] - start[0]) / length, (end[1] - start[1]) / length
        for step in range(steps):
            fraction = step / steps
            x = start[0] + (end[0] - start[0]) * fraction
            y = start[1] + (end[1] - start[1]) * fraction
            samples.append((x, y, direction_x, direction_y, (walked + length * fraction) / total))
        walked += length
    samples.append((*points[-1], direction_x, direction_y, 1.0))
    return samples


def tube_layer(points, radius_at, ramp: Ramp, ring_every: float = 0.0) -> Layer:
    # Tubo (caule, tentáculo, cauda) sombreado pela distância perpendicular ao eixo, com luz no lado de
    # cima/esquerda. Cada pixel usa a amostra mais próxima do eixo, então curvas e inchaços sombreiam certo.
    # radius_at(progress) recebe 0..1 ao longo do caminho: afinar a ponta, inchar no meio (presa engolida).
    best_by_pixel: dict[tuple[int, int], tuple[float, float, float]] = {}
    for sample_x, sample_y, direction_x, direction_y, progress in sample_path(points):
        radius = radius_at(progress)
        reach = int(radius) + 1
        normal_x, normal_y = -direction_y, direction_x
        light_sign = 1 if (normal_y < 0 or (normal_y == 0 and normal_x < 0)) else -1
        for y in range(int(sample_y) - reach, int(sample_y) + reach + 1):
            for x in range(int(sample_x) - reach, int(sample_x) + reach + 1):
                offset_x, offset_y = x + 0.5 - sample_x, y + 0.5 - sample_y
                distance = math.hypot(offset_x, offset_y)
                if distance > radius:
                    continue
                light_side = light_sign * (offset_x * normal_x + offset_y * normal_y) / max(radius, 0.5)
                previous = best_by_pixel.get((x, y))
                if previous is None or distance / radius < previous[0]:
                    best_by_pixel[(x, y)] = (distance / radius, light_side, progress)
    layer = Layer()
    for (x, y), (_, light_side, progress) in best_by_pixel.items():
        if light_side > 0.45:
            color = ramp.light
        elif light_side < -0.45:
            color = ramp.dark
        else:
            color = ramp.base
        if ring_every and (progress * 100) % ring_every < 1.2 and color != ramp.light:
            color = ramp.dark
        layer.pixels[(x, y)] = color
    return layer


def save_spritesheet(rows: list[list[Image.Image]], path: str):
    frame_width, frame_height = rows[0][0].size
    columns = max(len(row) for row in rows)
    sheet = Image.new("RGBA", (columns * frame_width, len(rows) * frame_height), (0, 0, 0, 0))
    for row_index, row in enumerate(rows):
        for column_index, frame in enumerate(row):
            sheet.alpha_composite(frame, (column_index * frame_width, row_index * frame_height))
    sheet.save(path)


def save_preview_gif(frames: list[Image.Image], path: str, scale: int, frame_duration_ms: list[int],
                     background: Color = (42, 38, 52)):
    scaled_frames = []
    for frame in frames:
        backdrop = Image.new("RGBA", frame.size, (*background, 255))
        backdrop.alpha_composite(frame)
        scaled_frames.append(backdrop.resize((frame.width * scale, frame.height * scale), Image.NEAREST).convert("P"))
    scaled_frames[0].save(path, save_all=True, append_images=scaled_frames[1:], duration=frame_duration_ms,
                          loop=0, disposal=2)


# --- Leitura da art bible (art-style.json) ---------------------------------------------------------


@dataclass
class Palette:
    name: str
    colors: dict[str, Color]
    ramps: dict[str, Ramp]
    accent: str | None = None
    translucent: dict[str, object] = field(default_factory=dict)  # rampa -> alpha sugerido

    def ramp(self, ramp_name: str) -> Ramp:
        return self.ramps[ramp_name]

    def color(self, color_name: str) -> Color:
        return self.colors[color_name]

    def accent_ramp(self) -> Ramp | None:
        return self.ramps.get(self.accent) if self.accent else None


def load_style(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_color(value) -> Color:
    return tuple(value)  # type: ignore[return-value]


def _ramp_from_json(ramp_json: dict) -> Ramp:
    def optional(key):
        value = ramp_json.get(key)
        return _as_color(value) if value is not None else None
    return Ramp(dark=_as_color(ramp_json["dark"]), base=_as_color(ramp_json["base"]),
                light=_as_color(ramp_json["light"]), shine=optional("shine"), deep=optional("deep"))


def load_palette(style: dict, palette_name: str) -> Palette:
    """Junta a paleta compartilhada (shared) com a paleta pedida (bioma, área, facção)."""
    palettes = style["palettes"]
    if palette_name not in palettes:
        raise KeyError(f"Paleta '{palette_name}' não existe na art bible. Disponíveis: {list(palettes)}")
    colors: dict[str, Color] = {}
    ramps: dict[str, Ramp] = {}
    translucent: dict[str, int] = {}
    accent = None
    for source_name in ("shared", palette_name):
        source = palettes.get(source_name, {})
        colors.update({name: _as_color(value) for name, value in source.get("colors", {}).items()})
        ramps.update({name: _ramp_from_json(value) for name, value in source.get("ramps", {}).items()})
        translucent.update(source.get("translucent", {}))
        # Cores que aparecem em assets aprovados mas ainda não têm rampa nomeada na bible.
        for extra_index, value in enumerate(source.get("approved_extras", [])):
            colors[f"{source_name.upper()}_EXTRA_{extra_index}"] = _as_color(value)
        accent = source.get("accent", accent)
    for alias, target in palettes.get(palette_name, {}).get("aliases", {}).items():
        if target in ramps:
            ramps[alias] = ramps[target]
        elif target in colors:
            colors[alias] = colors[target]
    return Palette(name=palette_name, colors=colors, ramps=ramps, accent=accent, translucent=translucent)


def frame_spec(style: dict, size_class: str) -> tuple[int, int, int]:
    """Retorna (largura, altura, ground_y) da classe de tamanho (tier, tipo de asset)."""
    spec = style["sizes"][size_class]
    width, height = spec["frame"]
    return width, height, spec.get("ground_y", height - 4)


def preview_background(style: dict) -> Color:
    return _as_color(style.get("preview_background", [42, 38, 52]))
