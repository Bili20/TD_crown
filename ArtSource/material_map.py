"""Mapa de material: base do pipeline em 5 etapas (silhueta, blocagem, luz e sombra, material, acabamento).

Cada pixel guarda material, plano e tom (índice na rampa). As etapas só mudam esses dados; a cor sai
da rampa no fim. Assim luz, sombra e textura nunca brigam, e o recolor do time continua funcionando:
as rampas PRIMARY e SECONDARY são os cinzas de índice.
"""
import random
from dataclasses import dataclass
from PIL import Image
from style_test import PLAYER, PLAYER_COLORS, REGION1

DEEP, DARK, BASE, LIGHT, SHINE = range(5)
PLANE_TONE = {"top": LIGHT, "front": BASE, "left": BASE, "right": DARK}


def _tones(ramp) -> list:
    return [ramp.deep or ramp.dark, ramp.dark, ramp.base, ramp.light, ramp.shine or ramp.light]


RAMPS = {name.lower(): _tones(PLAYER.ramp(name)) for name in (
    "WOOD", "STONE", "IRON", "BRICK", "DARK_STONE", "WHITEWASH", "SLATE", "BRONZE", "COPPER",
    "GLASS", "MARBLE", "STRAW", "ACID", "HOLY", "SKIN")}
RAMPS["primary"] = [PLAYER_COLORS[symbol] for symbol in ("o", "a", "b", "c", "c")]
RAMPS["secondary"] = [PLAYER_COLORS[symbol] for symbol in ("d", "d", "e", "f", "w")]
OPENING_COLOR = REGION1.color("OUTLINE")
RAMPS["opening"] = [OPENING_COLOR] * 5
SILHOUETTE_COLOR = (60, 56, 80)


@dataclass
class Cell:
    material: str
    plane: str
    tone: int = BASE


class Sprite:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.cells: dict[tuple[int, int], Cell] = {}

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set(self, x, y, material, plane="front", tone=None):
        if self.inside(x, y):
            self.cells[(x, y)] = Cell(material, plane, PLANE_TONE[plane] if tone is None else tone)

    def fill(self, left, top, right, bottom, material, plane="front", tone=None):
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                self.set(x, y, material, plane, tone)

    def get(self, x, y) -> Cell | None:
        return self.cells.get((x, y))

    def is_material(self, x, y, *materials) -> bool:
        cell = self.cells.get((x, y))
        return cell is not None and cell.material in materials

    def shift(self, x, y, amount, only=None):
        cell = self.cells.get((x, y))
        if cell and (only is None or cell.material in only):
            cell.tone = max(DEEP, min(SHINE, cell.tone + amount))

    def remove(self, x, y):
        self.cells.pop((x, y), None)

    def reset_tones(self):
        for cell in self.cells.values():
            if cell.material != "opening":
                cell.tone = PLANE_TONE[cell.plane]

    def render(self, silhouette: bool = False) -> Image.Image:
        image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        for (x, y), cell in self.cells.items():
            color = SILHOUETTE_COLOR if silhouette else RAMPS[cell.material][cell.tone]
            image.putpixel((x, y), (*color, 255))
        return image


# --- Etapa 3: luz e sombra -------------------------------------------------------------------------
def shade_volume(sprite: Sprite, left, top, right, bottom, materials, shadow_columns=2, lit_columns=1):
    """Corpo em 3/4 com luz de cima-esquerda: coluna da esquerda clara, colunas da direita na sombra."""
    for y in range(top, bottom + 1):
        for x in range(left, left + lit_columns):
            sprite.shift(x, y, +1, materials)
        for x in range(right - shadow_columns + 1, right + 1):
            sprite.shift(x, y, -1, materials)


def cast_shadow(sprite: Sprite, left, right, y, depth=2, materials=None):
    """Sombra projetada de um beiral, cornija ou parapeito: forte na 1ª linha, fraca nas seguintes."""
    for row in range(depth):
        for x in range(left, right + 1):
            sprite.shift(x, y + row, -2 if row == 0 else -1, materials)


def ambient_occlusion(sprite: Sprite, left, right, ground_y, materials=None):
    for x in range(left, right + 1):
        sprite.shift(x, ground_y, -1, materials)


def recess(sprite: Sprite, left, top, right, bottom, materials):
    """Vão de porta ou janela: o lado de cima e o da esquerda ficam na sombra do batente."""
    for y in range(top, bottom + 1):
        sprite.shift(left, y, -1, materials)
    for x in range(left, right + 1):
        sprite.shift(x, top, -1, materials)


# --- Etapa 4: receitas de material -----------------------------------------------------------------
def stone_courses(sprite: Sprite, left, top, right, bottom, rng: random.Random, material="stone",
                  heights=(3, 3, 3, 4), widths=(4, 5, 5, 6), protrude=True):
    """Blocos em fiadas desencontradas; junta 1 tom abaixo; aresta de cima clara em parte dos blocos;
    alguns blocos mais claros ou escuros; blocos das quinas saltam 1 px para fora."""
    y = top
    course_index = 0
    while y <= bottom:
        height = rng.choice(heights) if y < bottom - 3 else bottom - y + 1
        x = left - (course_index * 2) % 3
        while x <= right:
            width = rng.choice(widths)
            block_right = min(x + width - 1, right)
            roll = rng.random()
            lit_edge = rng.random() < 0.6
            for block_x in range(max(x, left), block_right + 1):
                for block_y in range(y, min(y + height, bottom + 1)):
                    if not sprite.is_material(block_x, block_y, material):
                        continue
                    cell = sprite.get(block_x, block_y)
                    is_joint = block_x == block_right or block_y == y + height - 1
                    if is_joint:
                        cell.tone = max(DEEP, cell.tone - 1)
                        continue
                    if roll < 0.10:
                        cell.tone = min(LIGHT, cell.tone + 1)
                    elif roll < 0.25:
                        cell.tone = max(DARK, cell.tone - 1)
                    if lit_edge and block_y == y and block_x < block_right - 1:
                        cell.tone = min(LIGHT, cell.tone + 1)
            x = block_right + 1
        y += height
        course_index += 1
    if protrude:
        for corner_x, side in ((left - 1, -1), (right + 1, +1)):
            for course_top in range(top + 2, bottom - 3, 6):
                if rng.random() < 0.75 and sprite.is_material(corner_x + (1 if side < 0 else -1), course_top, material):
                    sprite.set(corner_x, course_top, material, "front", LIGHT if side < 0 else BASE)
                    sprite.set(corner_x, course_top + 1, material, "front", BASE if side < 0 else DARK)


def brick_courses(sprite: Sprite, left, top, right, bottom, rng: random.Random, material="brick"):
    """Tijolo 1:2 (4×2 com a junta); junta escura = construção velha e quente de forja."""
    for y in range(top, bottom + 1):
        row = (y - top) // 2
        is_joint_row = (y - top) % 2 == 1
        offset = 0 if row % 2 == 0 else 2
        for x in range(left, right + 1):
            if not sprite.is_material(x, y, material):
                continue
            cell = sprite.get(x, y)
            if is_joint_row or (x - left + offset) % 4 == 3:
                cell.tone = max(DEEP, cell.tone - 1)
            elif (x - left + offset) % 4 == 0 and rng.random() < 0.5:
                cell.tone = min(LIGHT, cell.tone + 1)
    for _ in range(max(1, (right - left) * (bottom - top) // 60)):
        x, y = rng.randint(left + 1, right - 2), rng.randint(top, bottom - 1)
        if sprite.is_material(x, y, material) and (y - top) % 2 == 0:
            sprite.shift(x, y, -1, (material,))
            sprite.shift(x + 1, y, -1, (material,))


def planks(sprite: Sprite, left, top, right, bottom, rng: random.Random, vertical=True, material="wood",
           plank_width=3, nails=True):
    """Tábuas com junta escura, veio em traços curtos, nó ocasional e pregos de ferro."""
    span = range(left, right + 1) if vertical else range(top, bottom + 1)
    for position in span:
        index = position - (left if vertical else top)
        is_joint = index % plank_width == plank_width - 1
        for other in (range(top, bottom + 1) if vertical else range(left, right + 1)):
            x, y = (position, other) if vertical else (other, position)
            if not sprite.is_material(x, y, material):
                continue
            if is_joint:
                sprite.shift(x, y, -1, (material,))
            elif index % plank_width == 0 and (other % 5 == 2):
                sprite.shift(x, y, +1, (material,))
    grain_count = max(1, (right - left + 1) * (bottom - top + 1) // 40)
    for _ in range(grain_count):
        x, y = rng.randint(left, right), rng.randint(top, bottom)
        for step in range(2):
            grain_x, grain_y = (x, y + step) if vertical else (x + step, y)
            sprite.shift(grain_x, grain_y, -1, (material,))
    if nails:
        for y_row in (top + 1, bottom - 1) if vertical else (top,):
            for x in range(left + 1, right, plank_width):
                if sprite.is_material(x, y_row, material):
                    sprite.set(x, y_row, "iron", "front", LIGHT)


def tile_roof(sprite: Sprite, rows: range, center_x: float, material="slate", row_height=3, tile_width=4,
              lit_side="left", lit_tone=BASE, shadow_tone=DARK):
    """Fileiras de telhas: borda de baixo de cada fileira na sombra, de cima na luz, junta vertical
    desencontrada; a água do lado da luz fica um tom acima."""
    for y in rows:
        row = (y - rows.start) // row_height
        row_y = (y - rows.start) % row_height
        for x in range(sprite.width):
            if not sprite.is_material(x, y, material):
                continue
            cell = sprite.get(x, y)
            lit = x < center_x if lit_side == "left" else x >= center_x
            cell.tone = lit_tone if lit else shadow_tone
            tile_x = (x + (row % 2) * (tile_width // 2)) % tile_width
            if row_y == row_height - 1:
                cell.tone -= 1
            elif row_y == 0 and tile_x != tile_width - 1:
                cell.tone += 1
            if tile_x == tile_width - 1 and row_y < row_height - 1:
                cell.tone -= 1
            cell.tone = max(DEEP, min(SHINE, cell.tone))


def team_pennant(sprite: Sprite, pole_x, pole_top, pole_bottom, wave):
    sprite.fill(pole_x, pole_top, pole_x, pole_bottom, "wood", tone=DARK)
    sprite.set(pole_x, pole_top - 1, "secondary", tone=LIGHT)
    rows = [[LIGHT, BASE, BASE, BASE], [BASE, BASE, DARK] if wave % 2 == 0 else [BASE, BASE, BASE, DARK],
            [DARK, DARK] if wave % 2 == 0 else [DARK]]
    for row_index, tones in enumerate(rows):
        offset = 1 if (wave in (1, 2) and row_index == 2) else 0
        for column_index, tone in enumerate(tones):
            sprite.set(pole_x + 1 + column_index + offset, pole_top + row_index, "primary", tone=tone)


def team_shield(sprite: Sprite, left, top):
    pattern = [".2222.", "123322", "122322", ".1222.", "..12.."]
    for row_index, row in enumerate(pattern):
        for column_index, symbol in enumerate(row):
            if symbol != ".":
                tone = int(symbol)
                material = "secondary" if tone == 3 else "primary"
                sprite.set(left + column_index, top + row_index, material, tone=SHINE if tone == 3 else tone)


def team_banner(sprite: Sprite, left, top, length=10):
    sprite.fill(left, top, left + 5, top, "secondary", tone=BASE)
    for y in range(top + 1, top + length - 1):
        for x in range(left, left + 6):
            tone = DARK if x == left else (LIGHT if x == left + 5 else BASE)
            sprite.set(x, y, "primary", tone=tone)
    emblem_top = top + 3
    for x, y in ((2, 0), (3, 0), (1, 1), (2, 1), (3, 1), (4, 1), (2, 2), (3, 2)):
        sprite.set(left + x, emblem_top + y, "secondary", tone=SHINE)
    bottom = top + length - 1
    sprite.set(left, bottom, "secondary", tone=BASE)
    sprite.set(left + 5, bottom, "secondary", tone=BASE)
    sprite.set(left + 2, bottom, "primary", tone=DARK)
    sprite.set(left + 3, bottom, "primary", tone=BASE)


def pyramid_roof(sprite: Sprite, left, right, bottom, peak, material="slate"):
    center = (left + right) / 2
    height = bottom - peak
    for row in range(peak, bottom + 1):
        half = (right - left) / 2 * (row - peak + 1) / (height + 1)
        for column in range(round(center - half), round(center + half) + 1):
            sprite.set(column, row, material, "top")
    return center


def plaster_wear(sprite: Sprite, left, top, right, bottom, rng: random.Random, material="whitewash",
                 exposed="stone"):
    """Cal sobre pedra: o reboco caiu em poucos pontos (pedra à mostra com borda escura), uma rachadura
    curta e sujeira subindo do pé da parede."""
    area = (right - left + 1) * (bottom - top + 1)
    for _ in range(max(1, area // 110)):
        patch_x = rng.randint(left + 1, max(left + 1, right - 4))
        patch_y = rng.randint(top + 1, max(top + 1, bottom - 3))
        for x in range(patch_x, patch_x + rng.choice((2, 3))):
            for y in range(patch_y, patch_y + 2):
                if sprite.is_material(x, y, material):
                    sprite.set(x, y, exposed, "front", BASE if y == patch_y else DARK)
        sprite.shift(patch_x - 1, patch_y, -1, (material,))
        sprite.shift(patch_x, patch_y + 2, -1, (material,))
    crack_x = rng.randint(left + 1, max(left + 1, right - 2))
    crack_y = rng.randint(top + 1, max(top + 1, bottom - 4))
    for step in range(3):
        sprite.shift(crack_x + (step + 1) // 2, crack_y + step, -2, (material,))
    for x in range(left, right + 1):
        sprite.shift(x, bottom - 1, -1, (material,))
