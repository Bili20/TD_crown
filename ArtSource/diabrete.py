"""Diabrete (asset `imp`), 16x16: o desenho aprovado em 10/11 (v2), remontado em partes para animar solto.

Partes: cabeça (chifres, olhos, boca), tronco, asa esquerda e direita (3 formas cada, girando em torno do
ombro), cauda e pernas. A cabeça chega um frame depois do tronco, a ponta da asa e a da cauda atrasam em
relação à base, e o piscar entra num frame próprio.

Uso: python diabrete.py            -> exporta idle, walk e attack e registra no manifesto
     python diabrete.py --preview  -> só as prévias em ArtSource/
"""
import sys
from dataclasses import dataclass
from PIL import Image, ImageDraw

from art_export import export_animation
from style_test import BACKGROUND, REGION1
from style_test_v2 import IMP_COLORS

DEMON = REGION1.ramp("DEMON")
SHADOW_BLOB = REGION1.color("SHADOW_BLOB")
COLORS = dict(IMP_COLORS, Y=REGION1.ramp("HELLFIRE").shine)

ASSET = dict(category="Enemies", asset_folder="Imp", asset_id="imp", controller="Unit")
FRAME = 16
GROUND_ROW = 13

HEAD_ORIGIN = (4, 5)
HEADS = {
    "closed": [
        "..c..c...",
        "..cbbc...",
        ".bbbbbb..",
        "ayybbyyba",
        "abbbkkba.",
    ],
    "blink": [
        "..c..c...",
        "..cbbc...",
        ".bbbbbb..",
        "aaabbaaba",
        "abbbkkba.",
    ],
    "open": [
        "..c..c...",
        "..cbbc...",
        ".bbbbbb..",
        "ayybbyyba",
        "abbkkkba.",
        ".abkeka..",
    ],
}
TORSO_ORIGIN = (5, 10)
TORSO = [
    "abcbba",
    "abbba.",
    ".abba.",
]
# Asa esquerda em 3 ângulos em volta do ombro (3, 8); a direita é o espelho. A ponta é o que mais anda.
LEFT_WING = {
    "up": [
        ".a..",
        ".aa.",
        "abaa",
        "a.ba",
        "...a",
    ],
    "mid": [
        "....",
        "a...",
        "aa..",
        "aba.",
        "a.a.",
    ],
    "down": [
        "....",
        "....",
        "aa..",
        "abba",
        "a.a.",
    ],
}
# A asa direita do desenho aprovado não é o espelho exato da esquerda na ponta de baixo.
RIGHT_WING = {name: [row[::-1] for row in rows] for name, rows in LEFT_WING.items()}
RIGHT_WING["mid"] = RIGHT_WING["mid"][:-1] + ["..a."]
WING_ORIGIN_Y = 4
LEFT_WING_X = 1
RIGHT_WING_X = 11
# O cuspe sai na linha da boca: na linha dos olhos ele lia como um olho esticado.
FIRE_SPIT = {
    1: [(13, 9, "y")],
    2: [(13, 9, "y"), (14, 10, "h"), (13, 11, "h")],
    3: [(14, 10, "h")],
}


@dataclass(frozen=True)
class Pose:
    body_x: int = 0
    body_y: int = 0
    head_dx: int = 0
    head_dy: int = 0
    face: str = "closed"
    left_wing: str = "mid"
    right_wing: str = "mid"
    tail_sway: int = 0       # -1 enrola para baixo, 1 sobe
    left_leg: int = 0        # 0 no chão, 1 erguida
    right_leg: int = 0
    spit: int = 0


def stamp(cells: dict, rows: list[str], origin_x: int, origin_y: int):
    for row_index, row in enumerate(rows):
        for column_index, letter in enumerate(row):
            if letter != ".":
                cells[(origin_x + column_index, origin_y + row_index)] = letter


def draw_tail(cells: dict, pose: Pose):
    base_x, base_y = 11 + pose.body_x, 10 + pose.body_y
    # A base segue o corpo e a ponta atrasa: o enrolado muda de forma, não só de lugar.
    shapes = {
        -1: [(base_x, base_y + 1), (base_x - 1, base_y + 2)],
        0: [(base_x, base_y), (base_x, base_y + 1), (base_x - 1, base_y + 2)],
        1: [(base_x, base_y), (base_x + 1, base_y - 1), (base_x + 2, base_y - 1)],
    }
    for x, y in shapes[pose.tail_sway]:
        cells[(x, y)] = "a"


def draw_legs(cells: dict, pose: Pose):
    torso_bottom = TORSO_ORIGIN[1] + len(TORSO) - 1 + pose.body_y
    for leg_x, lifted, outward in ((6, pose.left_leg, -1), (9, pose.right_leg, 1)):
        x = leg_x + pose.body_x
        if lifted:
            # Pata erguida aparece ao lado do tronco, um pixel acima do chão.
            cells[(x + outward, GROUND_ROW - 1)] = "a"
            continue
        for y in range(torso_bottom + 1, GROUND_ROW + 1):
            cells[(x, y)] = "a"


def draw_frame(pose: Pose) -> dict:
    cells: dict[tuple[int, int], str] = {}
    wing_y = WING_ORIGIN_Y + pose.body_y
    stamp(cells, LEFT_WING[pose.left_wing], LEFT_WING_X + pose.body_x, wing_y)
    stamp(cells, RIGHT_WING[pose.right_wing], RIGHT_WING_X + pose.body_x, wing_y)
    draw_legs(cells, pose)
    draw_tail(cells, pose)
    stamp(cells, TORSO, TORSO_ORIGIN[0] + pose.body_x, TORSO_ORIGIN[1] + pose.body_y)
    stamp(cells, HEADS[pose.face], HEAD_ORIGIN[0] + pose.body_x + pose.head_dx, HEAD_ORIGIN[1] + pose.head_dy)
    for x, y, letter in FIRE_SPIT.get(pose.spit, []):
        cells[(x + pose.body_x, y)] = letter
    return cells


def final_frame(pose: Pose) -> Image.Image:
    image = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    for (x, y), letter in draw_frame(pose).items():
        if 0 <= x < FRAME and 0 <= y < FRAME:
            image.putpixel((x, y), (*COLORS[letter], 255))
    return image


# --- Animações ------------------------------------------------------------------------------------
# head_dy é absoluto (a cabeça não fica pendurada no tronco): na descida a cabeça vai antes e cobre o
# topo do tronco; na subida o tronco vai antes. Assim nunca abre um buraco no pescoço.

IDLE = [
    Pose(left_wing="mid", right_wing="mid"),
    Pose(left_wing="up", right_wing="mid", tail_sway=1),
    Pose(head_dy=1, left_wing="up", right_wing="up", tail_sway=1),
    Pose(body_y=1, head_dy=1, left_wing="mid", right_wing="up"),
    Pose(body_y=0, head_dy=1, face="blink", left_wing="down", right_wing="mid", tail_sway=-1),
    Pose(left_wing="mid", right_wing="down"),
]
IDLE_DURATIONS_MS = [180, 150, 170, 170, 130, 160]

# Passo de enxame: 2 passos por tile, como o andar procedural, então o ciclo de 720 ms cobre 1 tile.
WALK = [
    Pose(body_y=1, head_dy=1, left_wing="mid", right_wing="mid"),
    Pose(body_y=0, head_dy=1, right_leg=1, left_wing="up", right_wing="up", tail_sway=1),
    Pose(body_y=0, head_dy=0, right_leg=1, left_wing="mid", right_wing="mid", tail_sway=0),
    Pose(body_y=1, head_dy=1, left_wing="down", right_wing="down", tail_sway=-1),
    Pose(body_y=0, head_dy=1, left_leg=1, left_wing="up", right_wing="up", tail_sway=0),
    Pose(body_y=0, head_dy=0, left_leg=1, left_wing="mid", right_wing="mid", tail_sway=1),
]
WALK_DURATIONS_MS = [120] * 6
WALK_GROUND_SPEED = 1000 / sum(WALK_DURATIONS_MS)

# O tempo até o impacto continua 140 ms (o attackWindup do Diabrete não muda).
ATTACK = [
    Pose(body_y=1, head_dy=1, left_wing="up", right_wing="up", tail_sway=1),
    Pose(body_y=1, head_dx=-1, head_dy=1, left_wing="up", right_wing="up", tail_sway=1),
    # o bote é da cabeça: o corpo fica, para as asas não encostarem na borda do frame
    Pose(head_dx=1, face="open", left_wing="down", right_wing="down", spit=1),
    Pose(head_dx=1, face="open", left_wing="mid", right_wing="down", spit=2, tail_sway=-1),
    Pose(face="closed", left_wing="up", right_wing="mid", spit=3),
    Pose(left_wing="mid", right_wing="mid"),
]
ATTACK_DURATIONS_MS = [80, 60, 70, 90, 110, 120]
ATTACK_IMPACT_FRAME = 2

ANIMATIONS = {
    "idle": (IDLE, IDLE_DURATIONS_MS),
    "walk": (WALK, WALK_DURATIONS_MS),
    "attack": (ATTACK, ATTACK_DURATIONS_MS),
}


# --- Prévia e exportação --------------------------------------------------------------------------

def with_blob(sprite: Image.Image, pose: Pose) -> Image.Image:
    framed = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
    left = 5 + pose.body_x
    for x in range(left, left + 6):
        framed.putpixel((x, GROUND_ROW), (*SHADOW_BLOB, 255))
    for x in range(left + 1, left + 5):
        framed.putpixel((x, GROUND_ROW + 1), (*SHADOW_BLOB, 255))
    framed.alpha_composite(sprite)
    return framed


def upscale(image: Image.Image, scale: int) -> Image.Image:
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def preview_gif(poses, durations, path: str, scale: int = 8):
    frames = []
    for pose in poses:
        backdrop = Image.new("RGBA", (FRAME, FRAME), (*BACKGROUND, 255))
        backdrop.alpha_composite(with_blob(final_frame(pose), pose))
        frames.append(upscale(backdrop, scale).convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=32))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)


def contact_sheet(path: str, scale: int = 8):
    columns = max(len(poses) for poses, _ in ANIMATIONS.values())
    sheet = Image.new("RGBA", (columns * (FRAME + 1) * scale, len(ANIMATIONS) * (FRAME + 1) * scale), (*BACKGROUND, 255))
    for row, (poses, _) in enumerate(ANIMATIONS.values()):
        for column, pose in enumerate(poses):
            backdrop = Image.new("RGBA", (FRAME, FRAME), (108, 150, 88, 255))
            backdrop.alpha_composite(with_blob(final_frame(pose), pose))
            sheet.alpha_composite(upscale(backdrop, scale), (column * (FRAME + 1) * scale, row * (FRAME + 1) * scale))
    sheet.save(path)


if __name__ == "__main__":
    contact_sheet("diabrete_frames.png")
    for name, (poses, durations) in ANIMATIONS.items():
        preview_gif(poses, durations, f"diabrete_{name}.gif")
    if "--preview" in sys.argv:
        sys.exit(0)
    export_animation([final_frame(pose) for pose in IDLE], animation="idle", durations_ms=IDLE_DURATIONS_MS,
                     ground_row=GROUND_ROW, **ASSET)
    export_animation([final_frame(pose) for pose in WALK], animation="walk", durations_ms=WALK_DURATIONS_MS,
                     ground_row=GROUND_ROW, ground_speed_tiles_per_second=WALK_GROUND_SPEED, **ASSET)
    export_animation([final_frame(pose) for pose in ATTACK], animation="attack", durations_ms=ATTACK_DURATIONS_MS,
                     ground_row=GROUND_ROW, loop=False, impact_frame=ATTACK_IMPACT_FRAME, **ASSET)
