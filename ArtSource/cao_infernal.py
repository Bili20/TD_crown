"""Cão Infernal (`cao_infernal`), 16x16: corcunda tipo hiena, pelo preto-violeta (`HOUND_FUR`) e brasa.

Design aprovado em 16/11 no teste da skill pixel-art-2d (silhueta B). O rig é feito de partes (meio de
trás e meio da frente do tronco, cabeça, 4 patas, cauda, tufos) e cada animação é uma lista de poses,
para o movimento sair com sobreposição (ombro antes do quadril, cabeça um frame atrás, ponta antes da
base) em vez de blocos que pulam juntos.

Uso: python cao_infernal.py            -> exporta idle, walk (galope) e attack e registra no manifesto
     python cao_infernal.py --preview  -> só a prancha das 5 etapas e os GIFs em ArtSource/
"""
import sys
from dataclasses import dataclass
from PIL import Image, ImageDraw

from art_export import export_animation
from style_test import BACKGROUND, REGION1

HOUND_FUR = REGION1.ramp("HOUND_FUR")
DEMON = REGION1.ramp("DEMON")
HELLFIRE = REGION1.ramp("HELLFIRE")
OUTLINE = REGION1.color("OUTLINE")
EYE_WHITE = REGION1.color("EYE_WHITE")
SHADOW_BLOB = REGION1.color("SHADOW_BLOB")
SILHOUETTE = (38, 26, 30)

ASSET = dict(category="Enemies", asset_folder="CaoInfernal", asset_id="cao_infernal", controller="Unit")
FRAME = 16
GROUND_ROW = 13
TILE_PX = 16


# --- Poses ----------------------------------------------------------------------------------------

@dataclass(frozen=True)
class LegPose:
    foot_dx: int = 0   # em relação à base em pé
    lift: int = 0


@dataclass(frozen=True)
class Pose:
    body_x: int = 0
    hip_y: int = 0
    shoulder_y: int = 0
    head_dx: int = 0
    head_dy: int = 0
    jaw: str = "snarl"
    far_hind: LegPose = LegPose()
    near_hind: LegPose = LegPose()
    near_front: LegPose = LegPose()
    far_front: LegPose = LegPose()
    tail_sway: float = 0.0
    tail_lift: float = 0.0
    ember_phase: int = 0
    ember_flare: int = 0
    eye_glow: int = 0
    spark: bool = False
    impact: int = 0


# --- Partes ---------------------------------------------------------------------------------------
# Letras: S brilho do pelo, T topo, l topo que escurece no detalhe, h tufo claro, F flanco, f tufo
# escuro, D sombra própria, U baixo, O oclusão, K lado de longe, N nariz, e órbita, E olho, W presa,
# M boca em brasa, q/x/z brasa fraca/média/forte.

TORSO_ORIGIN = (2, 6)
TORSO_SPLIT = 4  # colunas 0-3 seguem o quadril, 4-7 seguem o ombro
TORSO = [
    "...STTTD",
    "..TTlTFD",
    ".TTFFfDD",
    "ThFfFFDD",
    "..DDUUUO",
    "..UO..UO",
]
LEG_TOP_Y = TORSO_ORIGIN[1] + len(TORSO) - 1

HEAD_ORIGIN = (10, 4)
HEADS = {
    "snarl": [
        "T...",
        "STT.",
        "eEFN",
        ".OWU",
    ],
    "shut": [
        "T...",
        "STT.",
        "eEFN",
        ".OUU",
    ],
    "open": [
        "T...",
        "STTN",
        "eEW.",
        ".M..",
        ".UUU",
    ],
    "wide": [
        "T...",
        "STTN",
        "eEW.",
        "OMMW",
        ".UU.",
    ],
}
NOSE_COLUMN, NOSE_ROW = 3, 2


@dataclass(frozen=True)
class Leg:
    top_x: int
    rest_dx: int
    near: bool
    hind: bool


LEGS = {
    "far_hind": Leg(top_x=4, rest_dx=-1, near=False, hind=True),
    "near_hind": Leg(top_x=5, rest_dx=0, near=True, hind=True),
    "near_front": Leg(top_x=8, rest_dx=0, near=True, hind=False),
    "far_front": Leg(top_x=9, rest_dx=2, near=False, hind=False),
}

TAIL_ROOT = (2, 10)
TAIL_POINTS = [(0, 0), (-1, 1)]
# Tufos de pelo e uma brasa só no dorso: duas brasas lado a lado liam como um segundo par de olhos.
TUFTS = [(2, "fur"), (4, "ember"), (6, "fur")]
EMBER_CYCLE = ["q", "x", "q", "x", "x", "q"]


class FrameMap:
    def __init__(self):
        self.cells: dict[tuple[int, int], str] = {}
        self.leg_cells: set[tuple[int, int]] = set()
        self.foot_cells: set[tuple[int, int]] = set()

    def put(self, x: int, y: int, letter: str):
        if 0 <= x < FRAME and 0 <= y < FRAME:
            self.cells[(x, y)] = letter

    def stamp(self, rows, origin_x, origin_y, columns=None):
        for row_index, row in enumerate(rows):
            for column_index, letter in enumerate(row):
                if letter != "." and (columns is None or column_index in columns):
                    self.put(origin_x + column_index, origin_y + row_index, letter)


def line_cells(start, end):
    steps = max(abs(end[0] - start[0]), abs(end[1] - start[1]), 1)
    cells = []
    for step in range(steps + 1):
        fraction = step / steps
        cell = (round(start[0] + (end[0] - start[0]) * fraction), round(start[1] + (end[1] - start[1]) * fraction))
        if not cells or cells[-1] != cell:
            cells.append(cell)
    return cells


def foot_position(name: str, leg_pose: LegPose) -> tuple[int, int]:
    leg = LEGS[name]
    return leg.top_x + leg.rest_dx + leg_pose.foot_dx, GROUND_ROW - leg_pose.lift


def draw_leg(frame: FrameMap, name: str, leg_pose: LegPose, pose: Pose):
    leg = LEGS[name]
    bob = pose.hip_y if leg.hind else pose.shoulder_y
    top = (leg.top_x + pose.body_x, LEG_TOP_Y + bob)
    foot = foot_position(name, leg_pose)
    cells = [cell for cell in line_cells(top, foot) if cell != top]
    for index, (x, y) in enumerate(cells):
        if not leg.near:
            frame.put(x, y, "K")
        else:
            frame.put(x, y, "F" if index == 0 and len(cells) > 1 else "D")
        frame.leg_cells.add((x, y))
    frame.foot_cells.add(foot)
    if leg.near and leg_pose.lift == 0:
        frame.put(foot[0] + 1, foot[1], "U")
        frame.foot_cells.add((foot[0] + 1, foot[1]))


def draw_tail(frame: FrameMap, pose: Pose):
    root_x, root_y = TAIL_ROOT[0] + pose.body_x, TAIL_ROOT[1] + pose.hip_y
    points = []
    for index, (relative_x, relative_y) in enumerate(TAIL_POINTS):
        weight = index / (len(TAIL_POINTS) - 1)
        points.append((max(1, round(root_x + relative_x + pose.tail_sway * weight)),
                       round(root_y + relative_y - pose.tail_lift * weight)))
    cells = []
    for start, end in zip(points, points[1:]):
        cells += [cell for cell in line_cells(start, end) if cell not in cells]
    for index, (x, y) in enumerate(cells):
        frame.put(x, y, "F" if index == 0 else "U")


def draw_tufts(frame: FrameMap, pose: Pose):
    torso_x, torso_y = TORSO_ORIGIN
    for index, (column, kind) in enumerate(TUFTS):
        is_front = column >= TORSO_SPLIT
        top_row = next(row for row in range(len(TORSO)) if TORSO[row][column] != ".")
        x = torso_x + column + pose.body_x
        y = torso_y + top_row + (pose.shoulder_y if is_front else pose.hip_y) - 1
        if kind == "fur":
            frame.put(x, y, "T")
            if pose.ember_flare:
                frame.put(x - 1, y - 1, "T")
            continue
        ember = EMBER_CYCLE[(pose.ember_phase + index * 2) % len(EMBER_CYCLE)]
        if pose.ember_flare:
            frame.put(x, y, "T")
            frame.put(x - 1, y - 1, "x")
        else:
            frame.put(x, y, ember)
        if pose.spark:
            rise = pose.ember_phase % 3
            if rise:
                frame.put(x - (rise - 1), y - rise - 1, "x" if rise == 1 else "q")


def draw_impact(frame: FrameMap, head_x: int, head_y: int, impact: int):
    nose_x, mouth_y = head_x + NOSE_COLUMN, head_y + NOSE_ROW
    if impact == 1:
        # Colchete de brasa em volta do focinho: o "chomp" virado para o alvo.
        sparks = [(-1, -2, "x"), (0, -1, "z"), (0, 2, "z"), (-1, 3, "x")]
    else:
        sparks = [(-1, -3, "x"), (0, -2, "x"), (0, 3, "x")]
    for offset_x, offset_y, letter in sparks:
        if (nose_x + offset_x, mouth_y + offset_y) not in frame.cells:
            frame.put(nose_x + offset_x, mouth_y + offset_y, letter)


def draw_frame(pose: Pose) -> FrameMap:
    frame = FrameMap()
    torso_x, torso_y = TORSO_ORIGIN[0] + pose.body_x, TORSO_ORIGIN[1]
    # De trás para frente: patas de longe, cauda, tufos, tronco, patas de perto, cabeça, efeitos.
    draw_leg(frame, "far_hind", pose.far_hind, pose)
    draw_leg(frame, "far_front", pose.far_front, pose)
    draw_tail(frame, pose)
    draw_tufts(frame, pose)
    frame.stamp(TORSO, torso_x, torso_y + pose.hip_y, set(range(TORSO_SPLIT)))
    frame.stamp(TORSO, torso_x, torso_y + pose.shoulder_y, set(range(TORSO_SPLIT, len(TORSO[0]))))
    draw_leg(frame, "near_hind", pose.near_hind, pose)
    draw_leg(frame, "near_front", pose.near_front, pose)
    head_x = HEAD_ORIGIN[0] + pose.body_x + pose.head_dx
    head_y = HEAD_ORIGIN[1] + pose.shoulder_y + pose.head_dy
    frame.stamp(HEADS[pose.jaw], head_x, head_y)
    if pose.impact:
        draw_impact(frame, head_x, head_y, pose.impact)
    return frame


# --- Cor por etapa --------------------------------------------------------------------------------

# letra -> (etapa 2 blocagem, etapa 3 luz e sombra, etapa 4 material e detalhe)
LEGEND = {
    "S": (HOUND_FUR.light, HOUND_FUR.light, HOUND_FUR.shine),
    "T": (HOUND_FUR.light, HOUND_FUR.light, HOUND_FUR.light),
    "l": (HOUND_FUR.light, HOUND_FUR.light, HOUND_FUR.base),
    "h": (HOUND_FUR.base, HOUND_FUR.base, HOUND_FUR.light),
    "F": (HOUND_FUR.base, HOUND_FUR.base, HOUND_FUR.base),
    "f": (HOUND_FUR.base, HOUND_FUR.base, HOUND_FUR.dark),
    "D": (HOUND_FUR.base, HOUND_FUR.dark, HOUND_FUR.dark),
    "U": (HOUND_FUR.dark, HOUND_FUR.dark, HOUND_FUR.dark),
    "O": (HOUND_FUR.dark, OUTLINE, OUTLINE),
    "K": (HOUND_FUR.dark, OUTLINE, OUTLINE),
    "N": (HOUND_FUR.dark, OUTLINE, OUTLINE),
    "e": (HOUND_FUR.base, HOUND_FUR.dark, DEMON.base),
    "E": (HELLFIRE.dark, HELLFIRE.dark, HELLFIRE.base),
    "W": (EYE_WHITE, EYE_WHITE, EYE_WHITE),
    "M": (DEMON.base, DEMON.base, HELLFIRE.dark),
    "q": (HELLFIRE.dark, DEMON.base, DEMON.base),
    "x": (HELLFIRE.dark, HELLFIRE.dark, HELLFIRE.dark),
    "z": (HELLFIRE.dark, HELLFIRE.base, HELLFIRE.light),
}
FUR_LETTERS = set("STlhFfDUO")
STAGE_NAMES = ["1 silhueta", "2 blocagem", "3 luz e sombra", "4 material e detalhe", "5 acabamento"]


def cell_color(letter: str, stage: int, pose: Pose):
    color = LEGEND[letter][min(stage, 4) - 2]
    if stage >= 4 and letter == "E" and pose.eye_glow:
        color = HELLFIRE.light
    return color


def finishing_pass(frame: FrameMap, colors: dict):
    # Sem contorno externo (bible §1): só a borda de baixo do pelo vai para o OUTLINE, para assentar no chão.
    # Na pata, só o pé: numa pata em diagonal todo pixel fica sem vizinho embaixo e ela inteira escureceria.
    for (x, y), letter in frame.cells.items():
        if (x, y) in frame.leg_cells and (x, y) not in frame.foot_cells:
            continue
        if letter in FUR_LETTERS and y >= 9 and (x, y + 1) not in frame.cells:
            colors[(x, y)] = OUTLINE


def render(frame: FrameMap, stage: int, pose: Pose) -> Image.Image:
    image = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    if stage == 1:
        colors = {cell: SILHOUETTE for cell in frame.cells}
    else:
        colors = {cell: cell_color(letter, stage, pose) for cell, letter in frame.cells.items()}
        if stage == 5:
            finishing_pass(frame, colors)
    for (x, y), color in colors.items():
        image.putpixel((x, y), (*color, 255))
    return image


def final_frame(pose: Pose) -> Image.Image:
    return render(draw_frame(pose), 5, pose)


# --- Animações ------------------------------------------------------------------------------------

IDLE = [
    Pose(jaw="snarl", ember_phase=0, spark=True),
    # inspira: a corcunda sobe primeiro e a cabeça fica (o pescoço estica)
    Pose(shoulder_y=-1, head_dy=1, ember_phase=1, tail_sway=-0.3, spark=True),
    # a cabeça alcança; o olho acende no topo da respiração
    Pose(shoulder_y=-1, ember_phase=2, tail_lift=1, eye_glow=1, spark=True),
    # expira: a corcunda desce e a cabeça demora
    Pose(shoulder_y=0, head_dy=-1, ember_phase=3, tail_lift=1, eye_glow=1),
    # bufada: boca abre com a brasa por dentro
    Pose(jaw="open", ember_phase=4, tail_sway=0.0),
    # assenta abaixo do neutro antes de recomeçar, para o laço não ter um frame parado
    Pose(jaw="shut", shoulder_y=1, head_dy=-1, ember_phase=5, tail_sway=0.3),
]
IDLE_DURATIONS_MS = [180, 160, 240, 160, 220, 170]


def gallop_leg(name: str, foot_dx_from_top: int, lift: int) -> LegPose:
    return LegPose(foot_dx_from_top - LEGS[name].rest_dx, lift)


# Galope rotativo em 6 frames: extensão no ar → pouso da frente → apoio da frente → recolhido →
# apoio de trás → impulso. Cada pé apoiado recua 2 px por frame, então o ciclo não desliza na
# velocidade de GALLOP_GROUND_SPEED; o Animator escala a partir dela.
GALLOP_FEET = {
    #               extensão   pouso F    apoio F    recolhido  apoio T    impulso
    "near_front": [(3, 1), (3, 1), (1, 0), (-1, 0), (0, 2), (2, 1)],
    "far_front": [(2, 1), (2, 0), (0, 0), (-2, 1), (-1, 2), (1, 1)],
    "near_hind": [(-2, 1), (0, 2), (2, 1), (3, 1), (1, 0), (-1, 0)],
    "far_hind": [(-3, 1), (-1, 2), (1, 1), (2, 0), (0, 0), (-2, 0)],
}
GALLOP_HIP = [-1, -1, -1, 0, 1, 0]
GALLOP_SHOULDER = [-1, 0, 1, 0, -1, -1]
GALLOP_TAIL = [-1.0, -0.6, 0.0, 0.4, 0.0, -0.6]
GALLOP_DURATIONS_MS = [65] * 6


def build_gallop() -> list[Pose]:
    poses = []
    for index in range(6):
        feet = {name: gallop_leg(name, *GALLOP_FEET[name][index]) for name in LEGS}
        shoulder = GALLOP_SHOULDER[index]
        poses.append(Pose(
            hip_y=GALLOP_HIP[index],
            shoulder_y=shoulder,
            head_dy=GALLOP_SHOULDER[index - 1] - shoulder,  # a cabeça chega um frame depois do ombro
            tail_sway=GALLOP_TAIL[index],
            tail_lift=1 if index in (0, 1) else 0,
            ember_phase=index,
            **feet,
        ))
    return poses


def ground_speed_tiles_per_second(poses: list[Pose], durations_ms: list[int]) -> float:
    # Média do recuo dos pés apoiados entre frames seguidos: é a velocidade em que o ciclo não desliza.
    speeds = []
    for index, pose in enumerate(poses):
        following = poses[(index + 1) % len(poses)]
        for name in LEGS:
            current_leg, next_leg = getattr(pose, name), getattr(following, name)
            if current_leg.lift == 0 and next_leg.lift == 0:
                shift_px = foot_position(name, current_leg)[0] - foot_position(name, next_leg)[0]
                speeds.append(shift_px / (durations_ms[index] / 1000))
    return sum(speeds) / len(speeds) / TILE_PX


WALK = build_gallop()
WALK_DURATIONS_MS = GALLOP_DURATIONS_MS
GALLOP_GROUND_SPEED = ground_speed_tiles_per_second(WALK, WALK_DURATIONS_MS)

ATTACK = [
    # prontidão: cabeça baixa, brasas do dorso sobem
    Pose(head_dy=1, ember_phase=0, ember_flare=1, tail_lift=1),
    # antecipação: peso nas ancas, cabeça recolhida
    Pose(body_x=-1, hip_y=1, head_dx=-1, head_dy=1, ember_phase=1, ember_flare=1, tail_lift=1, eye_glow=1),
    # bote: corpo vai à frente, corcunda sobe, boca escancarada, patas da frente no ar
    Pose(body_x=1, shoulder_y=-1, head_dy=-1, jaw="wide", ember_phase=2, ember_flare=1, tail_sway=-1.0,
         near_front=LegPose(2, 1), far_front=LegPose(1, 1), eye_glow=1),
    # mordida: mandíbula fecha, colchete de brasa no focinho
    Pose(body_x=1, head_dy=1, jaw="shut", ember_phase=3, tail_sway=-0.6,
         near_front=LegPose(2, 0), far_front=LegPose(1, 0), eye_glow=1, impact=1),
    # continuidade: cabeça sacode, brasas se espalham
    Pose(body_x=1, head_dy=0, jaw="shut", ember_phase=4, tail_sway=0.2,
         near_front=LegPose(2, 0), far_front=LegPose(1, 0), impact=2),
    # volta: recolhe a pata da frente
    Pose(jaw="snarl", ember_phase=5, tail_sway=0.5, near_front=LegPose(1, 1), far_front=LegPose(1, 0)),
    # assenta, com um leve exagero para baixo antes do idle
    Pose(hip_y=1, head_dy=1, jaw="snarl", ember_phase=0, tail_sway=0.2),
]
ATTACK_DURATIONS_MS = [140, 180, 70, 70, 110, 120, 150]
ATTACK_IMPACT_FRAME = 3

ANIMATIONS = {
    "idle": (IDLE, IDLE_DURATIONS_MS),
    "walk": (WALK, WALK_DURATIONS_MS),
    "attack": (ATTACK, ATTACK_DURATIONS_MS),
}


# --- Prévia e exportação --------------------------------------------------------------------------

def with_blob(sprite: Image.Image, pose: Pose) -> Image.Image:
    # Prévia com a sombra separada da bible (no jogo ela é outro SpriteRenderer, que não pula).
    framed = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
    left = 3 + pose.body_x
    for x in range(left, left + 9):
        framed.putpixel((x, GROUND_ROW), (*SHADOW_BLOB, 255))
    for x in range(left + 1, left + 8):
        framed.putpixel((x, GROUND_ROW + 1), (*SHADOW_BLOB, 255))
    framed.alpha_composite(sprite)
    return framed


def upscale(image: Image.Image, scale: int) -> Image.Image:
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def stage_board(path: str, scale: int = 12):
    pose = IDLE[0]
    frame = draw_frame(pose)
    cell = FRAME * scale
    board = Image.new("RGBA", (16 + 5 * (cell + 16), cell + 40), (*BACKGROUND, 255))
    draw = ImageDraw.Draw(board)
    for stage in range(1, 6):
        image = render(frame, stage, pose)
        backdrop = Image.new("RGBA", image.size, (*((196, 188, 170) if stage == 1 else BACKGROUND), 255))
        backdrop.alpha_composite(image if stage < 3 else with_blob(image, pose))
        origin_x = 16 + (stage - 1) * (cell + 16)
        board.alpha_composite(upscale(backdrop, scale), (origin_x, 24))
        draw.text((origin_x, 6), STAGE_NAMES[stage - 1], fill=(236, 230, 214, 255))
    board.save(path)


def preview_gif(poses: list[Pose], durations: list[int], path: str, scale: int = 8):
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
    stage_board("cao_infernal_etapas.png")
    contact_sheet("cao_infernal_frames.png")
    for name, (poses, durations) in ANIMATIONS.items():
        preview_gif(poses, durations, f"cao_infernal_{name}.gif")
    print(f"galope sem deslizar a {GALLOP_GROUND_SPEED:.2f} tile/s")
    if "--preview" in sys.argv:
        sys.exit(0)
    export_animation([final_frame(pose) for pose in IDLE], animation="idle", durations_ms=IDLE_DURATIONS_MS,
                     ground_row=GROUND_ROW, **ASSET)
    export_animation([final_frame(pose) for pose in WALK], animation="walk", durations_ms=WALK_DURATIONS_MS,
                     ground_row=GROUND_ROW, ground_speed_tiles_per_second=GALLOP_GROUND_SPEED, **ASSET)
    export_animation([final_frame(pose) for pose in ATTACK], animation="attack", durations_ms=ATTACK_DURATIONS_MS,
                     ground_row=GROUND_ROW, loop=False, impact_frame=ATTACK_IMPACT_FRAME, **ASSET)
