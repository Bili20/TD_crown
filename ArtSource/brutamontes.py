"""Brutamontes (`brutamontes`), 24x24: o carcereiro (silhueta B, escolhida em 16/11).

Corcunda de ombros enormes e cintura estreita, cabeça miúda afundada entre os ombros com um chifre só,
placas de ferro negro (ombreira, colar, algemas, cinto) e uma bola de ferro presa por corrente na algema
do braço de trás. No walk ele arrasta a bola atrás; no ataque gira a bola por cima da cabeça e bate no chão
à frente.

A massa é feita de elipses e membros em tubo (nada de retângulo: o antigo, todo em blocos, ficou duro).
Cada pixel guarda material, tom e plano; as etapas do pipeline só mudam como a cor sai daí.

Uso: python brutamontes.py            -> exporta idle, walk e attack e registra no manifesto
     python brutamontes.py --preview  -> só a prancha das 5 etapas e os GIFs em ArtSource/
"""
import math
import sys
from dataclasses import dataclass, field
from PIL import Image, ImageDraw

from art_export import export_animation
from style_test import BACKGROUND, REGION1

DEMON = REGION1.ramp("DEMON")
IRON = REGION1.ramp("BLACK_IRON")
FIRE = REGION1.ramp("HELLFIRE")
OUTLINE = REGION1.color("OUTLINE")
EYE_WHITE = REGION1.color("EYE_WHITE")
SHADOW_BLOB = REGION1.color("SHADOW_BLOB")
SILHOUETTE = (38, 26, 30)

ASSET = dict(category="Enemies", asset_folder="Brutamontes", asset_id="brutamontes", controller="Unit")
FRAME = 24
GROUND_ROW = 22
TILE_PX = 16
DEEP, DARK, BASE, LIGHT, SHINE = range(5)
STAGE_NAMES = ["1 silhueta", "2 blocagem", "3 luz e sombra", "4 material e detalhe", "5 acabamento"]

_light_length = math.sqrt(0.55 ** 2 + 0.75 ** 2 + 0.4 ** 2)
LIGHT_X, LIGHT_Y, LIGHT_Z = -0.55 / _light_length, -0.75 / _light_length, 0.4 / _light_length


@dataclass
class Cell:
    material: str   # skin | iron | fire | horn | bone | dark
    tone: int
    plane: str      # top | front | side


class Sprite:
    def __init__(self):
        self.cells: dict[tuple[int, int], Cell] = {}

    def put(self, x: int, y: int, material: str, tone: int, plane: str = "front"):
        if 0 <= x < FRAME and 0 <= y < FRAME:
            self.cells[(x, y)] = Cell(material, tone, plane)

    def shift(self, x: int, y: int, amount: int, only: tuple[str, ...] = ("skin", "iron")):
        cell = self.cells.get((x, y))
        if cell and cell.material in only:
            cell.tone = max(DEEP, min(SHINE, cell.tone + amount))


def shade(normal_x: float, normal_y: float) -> tuple[int, str]:
    normal_z = math.sqrt(max(0.0, 1 - normal_x * normal_x - normal_y * normal_y))
    intensity = normal_x * LIGHT_X + normal_y * LIGHT_Y + normal_z * LIGHT_Z
    tone = LIGHT if intensity > 0.62 else (BASE if intensity > 0.18 else DARK)
    plane = "top" if normal_y < -0.5 else ("side" if normal_x > 0.45 or normal_y > 0.55 else "front")
    return tone, plane


def blob(sprite: Sprite, center_x: float, center_y: float, radius_x: float, radius_y: float, material: str,
         tone_shift: int = 0):
    for y in range(int(center_y - radius_y) - 1, int(center_y + radius_y) + 2):
        for x in range(int(center_x - radius_x) - 1, int(center_x + radius_x) + 2):
            normal_x = (x + 0.5 - center_x) / radius_x
            normal_y = (y + 0.5 - center_y) / radius_y
            if normal_x * normal_x + normal_y * normal_y <= 1.0:
                tone, plane = shade(normal_x, normal_y)
                sprite.put(x, y, material, max(DARK, tone + tone_shift), plane)


def mass(sprite: Sprite, ellipses: list[tuple[float, float, float, float]], material: str, sharpness: float = 7.0):
    # União suave de elipses sombreada pelo gradiente do campo: o tronco vira uma massa só, sem as
    # costuras que cada elipse sombreada separada deixava no meio do corpo.
    def field(point_x: float, point_y: float) -> float:
        total = 0.0
        for center_x, center_y, radius_x, radius_y in ellipses:
            inside = 1 - ((point_x - center_x) / radius_x) ** 2 - ((point_y - center_y) / radius_y) ** 2
            total += math.exp(sharpness * inside)
        return math.log(total) / sharpness

    left = int(min(center_x - radius_x for center_x, _, radius_x, _ in ellipses)) - 1
    right = int(max(center_x + radius_x for center_x, _, radius_x, _ in ellipses)) + 2
    top = int(min(center_y - radius_y for _, center_y, _, radius_y in ellipses)) - 1
    bottom = int(max(center_y + radius_y for _, center_y, _, radius_y in ellipses)) + 2
    for y in range(top, bottom):
        for x in range(left, right):
            center_x, center_y = x + 0.5, y + 0.5
            value = field(center_x, center_y)
            if value <= 0:
                continue
            gradient_x = field(center_x + 0.5, center_y) - field(center_x - 0.5, center_y)
            gradient_y = field(center_x, center_y + 0.5) - field(center_x, center_y - 0.5)
            length = math.hypot(gradient_x, gradient_y) or 1.0
            depth = math.sqrt(min(1.0, value * 1.6))
            lateral = math.sqrt(max(0.0, 1 - depth * depth))
            tone, plane = shade(-gradient_x / length * lateral, -gradient_y / length * lateral)
            sprite.put(x, y, material, tone, plane)


def limb(sprite: Sprite, points: list[tuple[float, float]], radius_at, material: str, tone_shift: int = 0):
    # Tubo sombreado pela normal em volta do eixo: braço, perna, chifre.
    samples = []
    for (start_x, start_y), (end_x, end_y) in zip(points, points[1:]):
        steps = max(1, int(math.dist((start_x, start_y), (end_x, end_y)) * 4))
        for step in range(steps + 1):
            fraction = step / steps
            samples.append((start_x + (end_x - start_x) * fraction, start_y + (end_y - start_y) * fraction))
    total = len(samples) - 1
    best: dict[tuple[int, int], tuple[float, float, float]] = {}
    for index, (sample_x, sample_y) in enumerate(samples):
        radius = radius_at(index / max(total, 1))
        reach = int(radius) + 2
        for y in range(int(sample_y) - reach, int(sample_y) + reach + 1):
            for x in range(int(sample_x) - reach, int(sample_x) + reach + 1):
                offset_x, offset_y = x + 0.5 - sample_x, y + 0.5 - sample_y
                distance = math.hypot(offset_x, offset_y)
                if distance > radius:
                    continue
                previous = best.get((x, y))
                if previous is None or distance / radius < previous[0]:
                    best[(x, y)] = (distance / radius, offset_x / radius, offset_y / radius)
    for (x, y), (_, normal_x, normal_y) in best.items():
        tone, plane = shade(normal_x, normal_y)
        sprite.put(x, y, material, max(DARK, tone + tone_shift), plane)


def line(sprite: Sprite, start: tuple[float, float], end: tuple[float, float], material: str, tone: int):
    steps = max(1, int(max(abs(end[0] - start[0]), abs(end[1] - start[1]))))
    for step in range(steps + 1):
        fraction = step / steps
        sprite.put(round(start[0] + (end[0] - start[0]) * fraction - 0.5),
                   round(start[1] + (end[1] - start[1]) * fraction - 0.5), material, tone)


# --- Pose -----------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Pose:
    body_x: float = 0          # tronco, ombros e braços
    body_y: float = 0
    hip_y: float = 0           # quadril (topo das pernas)
    head_x: float = 0          # cabeça, além do tronco
    head_y: float = 0
    back_elbow: tuple[float, float] = (-0.4, 2.2)   # braço de trás (o da bola), em relação ao ombro
    back_wrist: tuple[float, float] = (1.0, 3.6)
    front_elbow: tuple[float, float] = (1.4, 2.4)
    front_wrist: tuple[float, float] = (2.2, 4.2)
    back_foot: tuple[float, float] = (0, 0)          # (deslocamento x, altura do pé)
    front_foot: tuple[float, float] = (0, 0)
    ball: tuple[float, float] = (2.8, 20.3)          # centro da bola, absoluto
    ball_in_front: bool = False                      # bola na frente das pernas e do tronco
    ball_roll: int = 0
    chain_sag: float = 0.6
    eye_glow: int = 0
    impact: int = 0
    swing_trail: tuple[tuple[float, float], ...] = field(default=())


BACK_SHOULDER = (5.4, 9.4)
FRONT_SHOULDER = (18.0, 9.2)
# Quadris afastados e pernas afinando: o vão entre as coxas devolve a perna arqueada da silhueta B.
BACK_HIP, FRONT_HIP = (9.8, 16.0), (14.8, 16.0)
BACK_FOOT_REST, FRONT_FOOT_REST = 8.4, 16.2
BALL_RADIUS = 2.3


def offset(point, delta_x, delta_y):
    return point[0] + delta_x, point[1] + delta_y


def leg_points(hip, foot_x, lift):
    foot = (foot_x, GROUND_ROW - 0.3 - lift)
    distance = math.dist(hip, foot)
    # O joelho dobra para a frente quando a perna encurta (pé erguido ou quadril baixo).
    bend = 0.6 + max(0.0, 6.2 - distance) * 0.8
    knee = ((hip[0] + foot[0]) / 2 + bend, (hip[1] + foot[1]) / 2)
    return [hip, knee, foot], foot


def draw_ball(sprite: Sprite, pose: Pose, stage: int):
    ball_x, ball_y = pose.ball
    if pose.swing_trail:
        # Rastro do giro: um fio claro de 1 px no arco, afinando no fim (grosso, lia como alça ou foice).
        trail = list(pose.swing_trail)
        for (start_x, start_y), (end_x, end_y) in zip(trail, trail[1:]):
            line(sprite, (start_x, start_y), (end_x, end_y), "iron", LIGHT)
    blob(sprite, ball_x, ball_y, BALL_RADIUS, BALL_RADIUS, "iron")
    if stage >= 4:
        # Espigões e o brilho que gira: é o que tira a bola de "bomba" e mostra que ela rola.
        sprite.put(int(ball_x), int(ball_y - BALL_RADIUS - 0.2), "iron", LIGHT)
        sprite.put(int(ball_x + BALL_RADIUS + 0.2), int(ball_y), "iron", BASE)
        angle = math.radians(225 + pose.ball_roll * 90)
        sprite.put(int(ball_x + math.cos(angle) * BALL_RADIUS * 0.45),
                   int(ball_y + math.sin(angle) * BALL_RADIUS * 0.45), "iron", SHINE)


def draw_chain(sprite: Sprite, pose: Pose, fist: tuple[float, float], stage: int):
    ball_x, ball_y = pose.ball
    direction_x, direction_y = ball_x - fist[0], ball_y - fist[1]
    length = math.hypot(direction_x, direction_y) or 1.0
    unit_x, unit_y = direction_x / length, direction_y / length
    anchor = (fist[0] + unit_x * 1.6, fist[1] + unit_y * 1.6)
    target = (ball_x - unit_x * BALL_RADIUS * 0.95, ball_y - unit_y * BALL_RADIUS * 0.95)
    links = max(2, int(math.dist(anchor, target)) + 1)
    for index in range(links + 1):
        fraction = index / links
        sag = math.sin(fraction * math.pi) * pose.chain_sag
        x = anchor[0] + (target[0] - anchor[0]) * fraction
        y = anchor[1] + (target[1] - anchor[1]) * fraction + sag
        tone = (LIGHT if index % 2 == 0 else DARK) if stage >= 4 else BASE
        sprite.put(int(x), int(y), "iron", tone)


TORSO_DROP = 2  # o corpo mais baixo encurta as pernas: brutamontes de perna curta e arqueada


def whole(value: float) -> int:
    return math.floor(value + 0.5)


def build(pose: Pose, stage: int) -> Sprite:
    from dataclasses import replace
    # Tronco, quadril e cabeça andam em pixel inteiro: deslocadas por fração, as elipses rasterizam
    # diferente a cada frame e a luz da corcunda "ferve". Só os braços usam fração.
    pose = replace(pose, body_x=whole(pose.body_x), body_y=whole(pose.body_y) + TORSO_DROP,
                   hip_y=whole(pose.hip_y) + TORSO_DROP, head_x=whole(pose.head_x), head_y=whole(pose.head_y))
    sprite = Sprite()
    body = (pose.body_x, pose.body_y)
    back_shoulder = offset(BACK_SHOULDER, *body)
    front_shoulder = offset(FRONT_SHOULDER, *body)
    back_elbow = offset(back_shoulder, *pose.back_elbow)
    back_wrist = offset(back_shoulder, *pose.back_wrist)
    back_fist = offset(back_wrist, 0, 1.1)
    front_elbow = offset(front_shoulder, *pose.front_elbow)
    front_wrist = offset(front_shoulder, *pose.front_wrist)
    front_fist = offset(front_wrist, 0.2, 1.2)
    back_hip = offset(BACK_HIP, pose.body_x, pose.hip_y)
    front_hip = offset(FRONT_HIP, pose.body_x, pose.hip_y)

    # De trás para frente.
    if not pose.ball_in_front:
        draw_ball(sprite, pose, stage)
    # Braço de trás: atrás do tronco, um tom abaixo (lado de longe). Antebraço mais grosso que o braço.
    forearm = lambda progress: 2.0 - 0.9 * progress if progress < 0.5 else 1.55 + 1.1 * (progress - 0.5)
    limb(sprite, [back_shoulder, back_elbow, back_wrist], forearm, "skin", -1)
    blob(sprite, back_fist[0], back_fist[1], 2.0, 1.7, "skin", -1)
    blob(sprite, back_wrist[0], back_wrist[1] - 0.3, 2.1, 0.9, "iron")
    if not pose.ball_in_front:
        draw_chain(sprite, pose, back_fist, stage)
    # Pernas curtas, arqueadas, de coxa grossa; a de trás um tom abaixo.
    for hip, rest_x, (foot_dx, lift), shift in ((back_hip, BACK_FOOT_REST, pose.back_foot, -1),
                                                (front_hip, FRONT_FOOT_REST, pose.front_foot, 0)):
        points, foot = leg_points(hip, rest_x + foot_dx, lift)
        limb(sprite, points, lambda progress: 2.1 - 0.9 * progress, "skin", shift)
        blob(sprite, foot[0] + 0.8, foot[1] - 0.3, 2.2, 1.0, "skin", shift)
    # Tronco: corcunda alta atrás, peito caído à frente, cintura estreita, quadril.
    mass(sprite, [
        (8.6 + pose.body_x, 7.4 + pose.body_y, 5.0, 3.5),
        (13.4 + pose.body_x, 10.0 + pose.body_y, 5.0, 3.6),
        (BACK_SHOULDER[0] + pose.body_x, BACK_SHOULDER[1] + pose.body_y - 0.6, 2.6, 2.4),
        (12.2 + pose.body_x, 13.6 + (pose.body_y + pose.hip_y) / 2, 2.8, 2.3),
        (12.2 + pose.body_x, 16.0 + pose.hip_y, 3.4, 1.4),
    ], "skin")
    # Ombreira de ferro negro no ombro da frente; o espigão fica abaixo da sobrancelha.
    blob(sprite, FRONT_SHOULDER[0] - 0.2 + pose.body_x, 9.0 + pose.body_y, 3.0, 2.2, "iron")
    limb(sprite, [(18.8 + pose.body_x, 7.8 + pose.body_y), (20.0 + pose.body_x, 6.9 + pose.body_y)],
         lambda progress: 0.9 - 0.4 * progress, "iron")
    # Cabeça miúda, baixa e à frente, afundada entre os ombros; o chifre em cunha varre para trás.
    head_x = 14.8 + pose.body_x + pose.head_x
    head_y = 6.6 + pose.body_y + pose.head_y
    limb(sprite, [(head_x - 0.6, head_y - 1.2), (head_x - 1.6, head_y - 3.4), (head_x - 3.2, head_y - 4.7)],
         lambda progress: 1.6 - 1.1 * progress, "horn")
    blob(sprite, head_x, head_y, 2.2, 1.8, "skin")
    blob(sprite, head_x - 0.6, 8.6 + pose.body_y, 2.8, 0.9, "iron")
    # Braço da frente, por cima de tudo.
    limb(sprite, [front_shoulder, front_elbow, front_wrist], forearm, "skin")
    blob(sprite, front_fist[0], front_fist[1], 2.1, 1.8, "skin")
    blob(sprite, front_wrist[0], front_wrist[1] - 0.3, 2.2, 0.9, "iron")
    # Cinto de ferro, cedendo 1 px no meio da barriga.
    for x in range(int(9 + pose.body_x), int(16 + pose.body_x)):
        sag = 1 if 11 <= x - pose.body_x <= 13 else 0
        sprite.put(x, int(15.0 + pose.hip_y) + sag, "iron", BASE, "front")
    if pose.ball_in_front:
        draw_ball(sprite, pose, stage)
        draw_chain(sprite, pose, back_fist, stage)

    # Olhos e boca fazem parte da leitura desde a blocagem.
    eye_y = int(head_y - 0.4)
    for eye_x in (int(head_x), int(head_x) + 1):
        sprite.put(eye_x, eye_y, "fire", BASE)
    sprite.put(int(head_x) + 1, eye_y + 1, "dark", DEEP)
    sprite.put(int(head_x), eye_y + 1, "dark", DEEP)

    if stage >= 3:
        apply_light_and_shadow(sprite, pose, head_x, head_y, eye_y, back_fist, front_fist)
    if stage >= 4:
        apply_details(sprite, pose, head_x, eye_y, back_elbow, front_elbow, front_shoulder)
    if stage >= 5:
        apply_finishing(sprite, pose, eye_y, head_x)
    return sprite


def apply_light_and_shadow(sprite, pose, head_x, head_y, eye_y, back_fist, front_fist):
    # Sombra projetada: sobrancelha sobre os olhos, colar sobre o peito, ombreira sobre o braço.
    for x in range(int(head_x) - 1, int(head_x) + 3):
        sprite.shift(x, eye_y - 1, -1)
    for x in range(int(head_x - 3), int(head_x + 2)):
        sprite.shift(x, int(9.6 + pose.body_y), -1)
    for y in range(int(10.6 + pose.body_y), int(12 + pose.body_y)):
        sprite.shift(int(18.4 + pose.body_x), y, -1)
    # Oclusão: virilha, sob o cinto, entre braço e tronco, embaixo dos punhos.
    for x in range(int(11 + pose.body_x), int(14 + pose.body_x)):
        sprite.shift(x, int(16.8 + pose.hip_y), -2)
    for fist in (back_fist, front_fist):
        sprite.shift(int(fist[0]), int(fist[1] + 1.4), -1)


def apply_details(sprite, pose, head_x, eye_y, back_elbow, front_elbow, front_shoulder):
    # Rebites na ombreira e no colar (brilho só em metal, bible §1).
    for rivet_x, rivet_y in ((16.4, 7.2), (12.6, 8.6)):
        cell = sprite.cells.get((int(rivet_x + pose.body_x), int(rivet_y + pose.body_y)))
        if cell and cell.material == "iron":
            cell.tone = SHINE
    # Brasas nas juntas, nunca mais claras que o olho: cotovelo da frente, fresta do cinto e joelho.
    for ember_x, ember_y in ((front_elbow[0] + 0.6, front_elbow[1]), (9.4 + pose.body_x, 15.0 + pose.hip_y)):
        sprite.put(int(ember_x), int(ember_y), "fire", DARK)
    # Músculo: linha do peitoral e do abdome no tom escuro, poucos traços.
    for x, y in ((12, 11), (13, 11), (12, 13)):
        sprite.shift(int(x + pose.body_x), int(y + pose.body_y), -1, only=("skin",))
    # Presa saindo da boca.
    sprite.put(int(head_x) + 2, eye_y + 1, "bone", LIGHT)
    # Chifre: base escura com anéis, ponta clara.
    horn_cells = sorted((y, x) for (x, y), cell in sprite.cells.items() if cell.material == "horn")
    for y, x in horn_cells[:1]:
        sprite.cells[(x, y)].tone = SHINE


def apply_finishing(sprite, pose, eye_y, head_x):
    # Sem contorno externo (bible §1): só a borda de baixo de pele e ferro vai para o OUTLINE.
    for (x, y), cell in list(sprite.cells.items()):
        if cell.material in ("skin", "iron") and y >= 12 and (x, y + 1) not in sprite.cells:
            cell.tone = DEEP
    # Borda de cima da pele em base, com a luz 1 px para dentro: o claro na borda se perdia na terra.
    for (x, y), cell in list(sprite.cells.items()):
        if cell.material == "skin" and cell.tone == LIGHT and (x, y - 1) not in sprite.cells:
            cell.tone = BASE
    # O olho é o pixel mais claro do inimigo.
    for eye_x in (int(head_x), int(head_x) + 1):
        sprite.put(eye_x, eye_y, "fire", SHINE if pose.eye_glow else LIGHT)
    if pose.impact:
        draw_impact(sprite, pose)


def draw_impact(sprite: Sprite, pose: Pose):
    ball_x, ball_y = pose.ball
    if pose.impact == 1:
        # Meias-luas de brasa dos dois lados da bola e poeira no chão (pixels soltos sumiam a 1×).
        sparks = [(-3, 0, "fire", BASE), (-3, -1, "fire", LIGHT), (-2, -2, "fire", BASE),
                  (2, -2, "fire", BASE), (2, -3, "fire", LIGHT), (1, -3, "fire", DARK),
                  (-4, 2, "iron", LIGHT), (-5, 2, "iron", BASE)]
    else:
        sparks = [(-4, -2, "fire", DARK), (-3, -3, "fire", DARK), (2, -4, "fire", DARK), (-5, 2, "iron", BASE)]
    for offset_x, offset_y, material, tone in sparks:
        x, y = int(ball_x) + offset_x, int(ball_y) + offset_y
        if 1 <= x <= FRAME - 2 and 1 <= y <= FRAME - 2 and (x, y) not in sprite.cells:
            sprite.put(x, y, material, tone)


# --- Cor por etapa --------------------------------------------------------------------------------

def color(cell: Cell, stage: int):
    tone = cell.tone
    if stage == 2 and cell.material in ("skin", "iron"):
        tone = {"top": LIGHT, "front": BASE, "side": DARK}[cell.plane]
    if cell.material == "skin":
        return OUTLINE if tone == DEEP else (DEMON.dark, DEMON.base, DEMON.light, DEMON.light)[tone - 1]
    if cell.material == "iron":
        return OUTLINE if tone == DEEP else (IRON.dark, IRON.base, IRON.light, IRON.shine)[tone - 1]
    if cell.material == "fire":
        return (FIRE.dark, FIRE.dark, FIRE.base, FIRE.light, FIRE.shine)[tone if stage >= 3 else BASE]
    if cell.material == "horn":
        return (IRON.dark, IRON.dark, IRON.base, IRON.light, IRON.light)[tone] if stage >= 3 else IRON.base
    if cell.material == "bone":
        return EYE_WHITE
    return OUTLINE


def render(pose: Pose, stage: int) -> Image.Image:
    image = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    sprite = build(pose, max(stage, 2))
    for (x, y), cell in sprite.cells.items():
        image.putpixel((x, y), (*(SILHOUETTE if stage == 1 else color(cell, stage)), 255))
    return image


def final_frame(pose: Pose) -> Image.Image:
    return render(pose, 5)


# --- Animações ------------------------------------------------------------------------------------

REST = Pose()

IDLE = [
    REST,
    # inspira: o peito sobe antes; cabeça e punhos ficam (atrasam)
    Pose(body_y=-1, head_y=1, back_wrist=(1.0, 4.6), front_wrist=(2.2, 5.2), chain_sag=0.9),
    # a cabeça alcança, o olho acende
    Pose(body_y=-1, back_wrist=(1.0, 4.2), front_wrist=(2.2, 4.8), chain_sag=0.7, eye_glow=1),
    # expira: o peito desce, a cabeça demora em cima
    Pose(body_y=0, head_y=-1, eye_glow=1, chain_sag=0.4),
    # assenta abaixo do neutro; os punhos ainda balançam
    Pose(body_y=1, hip_y=1, head_y=-1, back_wrist=(1.0, 3.0), front_wrist=(2.2, 3.6), chain_sag=0.2),
    Pose(body_y=1, back_wrist=(1.0, 3.4), front_wrist=(2.2, 4.0), chain_sag=0.5),
]
IDLE_DURATIONS_MS = [220, 180, 260, 200, 200, 180]

# Passo pesado de 8 frames: o pé apoiado recua 1 px por frame. A bola vem arrastada atrás,
# rolando (o brilho gira) e quicando de leve nas pedras do caminho.
WALK_FOOT = [(2, 0), (1, 0), (0, 0), (-1, 0), (-2, 0), (-1, 1.5), (1, 2), (2, 1)]
# Sobe e desce em pixel inteiro, 2 frames em cada altura; a cabeça repete a altura do frame anterior.
WALK_BODY_Y = [1, 1, 0, 0, 1, 1, 0, 0]
WALK_DURATIONS_MS = [140] * 8


def build_walk() -> list[Pose]:
    poses = []
    for index in range(8):
        back_dx, back_lift = WALK_FOOT[index]
        front_dx, front_lift = WALK_FOOT[(index + 4) % 8]
        # Braço da frente balança ao contrário da perna da frente; o de trás, preso à bola, mal se mexe.
        swing = math.sin(index / 8 * math.tau)
        poses.append(Pose(
            body_y=WALK_BODY_Y[index],
            hip_y=WALK_BODY_Y[index],
            head_y=WALK_BODY_Y[index - 1] - WALK_BODY_Y[index],
            back_foot=(back_dx, back_lift),
            front_foot=(front_dx, front_lift),
            front_elbow=(1.4 - 0.6 * swing, 2.4),
            front_wrist=(1.2 - 1.0 * swing, 4.2 - 0.4 * abs(swing)),
            back_wrist=(1.0 + 0.4 * swing, 3.6),
            ball=(2.8, 20.3 - (1 if index in (3, 7) else 0)),
            ball_roll=index // 2,
            chain_sag=0.2 if swing > 0.3 else 0.9,
        ))
    return poses


WALK = build_walk()
WALK_GROUND_SPEED = 1000 / WALK_DURATIONS_MS[0] / TILE_PX

ATTACK = [
    # puxa a bola pelo chão; o corpo inclina para trás
    Pose(body_x=-1, head_x=-1, back_elbow=(-1.6, 1.6), back_wrist=(-0.4, 3.0),
         front_elbow=(1.6, 2.0), front_wrist=(2.8, 3.4), ball=(4.6, 19.6), ball_roll=1, chain_sag=0.0, eye_glow=1),
    # antecipação: bola lá em cima, atrás da cabeça; peso no pé de trás
    Pose(body_x=-1, body_y=1, hip_y=1, head_x=-1, back_elbow=(-0.8, -0.4), back_wrist=(0.2, -2.4),
         front_elbow=(2.2, 1.6), front_wrist=(3.4, 2.6), ball=(3.2, 3.6), chain_sag=0.2, eye_glow=1,
         front_foot=(1, 0)),
    # giro: a bola passa por cima e à frente, com um fio de rastro; o corpo vai junto
    Pose(body_x=1, head_x=1, back_elbow=(3.6, -2.4), back_wrist=(6.6, -1.0),
         front_elbow=(1.2, 2.8), front_wrist=(1.0, 5.0), ball=(17.6, 4.6), ball_in_front=True, chain_sag=0.0,
         swing_trail=((4.6, 4.2), (7.4, 1.8), (11.0, 1.4), (14.4, 2.2)), front_foot=(1, 0), eye_glow=1),
    # impacto: a bola afunda no chão à frente, estouro de brasa e poeira
    Pose(body_x=1, body_y=2, hip_y=1, head_x=1, head_y=1, back_elbow=(4.6, 1.4), back_wrist=(7.0, 4.2),
         front_elbow=(0.4, 2.0), front_wrist=(-1.4, 2.4), ball=(20.4, 20.3), ball_in_front=True, chain_sag=0.4,
         front_foot=(-1, 0), impact=1),
    # continuidade: brasas se espalham; o corpo ainda curvado
    Pose(body_x=1, body_y=1, hip_y=1, back_elbow=(4.2, 1.8), back_wrist=(6.4, 4.6), front_wrist=(-1.0, 2.8),
         ball=(20.4, 20.3), ball_in_front=True, chain_sag=0.8, front_foot=(-1, 0), impact=2),
    # volta: arrasta a bola por baixo do corpo, na frente das pernas
    Pose(body_y=1, back_elbow=(0.6, 2.8), back_wrist=(1.6, 4.6), ball=(12.6, 20.3), ball_in_front=True,
         ball_roll=2, chain_sag=0.6),
    # assenta com a bola de novo atrás
    Pose(body_y=1, hip_y=1, ball=(2.8, 20.3), ball_roll=3, chain_sag=0.5),
]
ATTACK_DURATIONS_MS = [160, 200, 70, 80, 120, 140, 160]
ATTACK_IMPACT_FRAME = 3

ANIMATIONS = {
    "idle": (IDLE, IDLE_DURATIONS_MS),
    "walk": (WALK, WALK_DURATIONS_MS),
    "attack": (ATTACK, ATTACK_DURATIONS_MS),
}


# --- Prévia e exportação --------------------------------------------------------------------------

def with_blob(sprite_image: Image.Image) -> Image.Image:
    # Sombra separada com o topo na linha dos pés (bible §3); no jogo é outro SpriteRenderer.
    framed = Image.new("RGBA", sprite_image.size, (0, 0, 0, 0))
    for x in range(7, 18):
        framed.putpixel((x, GROUND_ROW), (*SHADOW_BLOB, 255))
    for x in range(8, 17):
        framed.putpixel((x, GROUND_ROW + 1), (*SHADOW_BLOB, 255))
    framed.alpha_composite(sprite_image)
    return framed


def upscale(image: Image.Image, scale: int) -> Image.Image:
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def stage_board(path: str, scale: int = 10):
    cell = FRAME * scale
    board = Image.new("RGBA", (16 + 5 * (cell + 16), cell + 40), (*BACKGROUND, 255))
    draw = ImageDraw.Draw(board)
    for stage in range(1, 6):
        image = render(REST, stage)
        backdrop = Image.new("RGBA", image.size, (*((196, 188, 170) if stage == 1 else BACKGROUND), 255))
        backdrop.alpha_composite(image if stage < 3 else with_blob(image))
        origin_x = 16 + (stage - 1) * (cell + 16)
        board.alpha_composite(upscale(backdrop, scale), (origin_x, 24))
        draw.text((origin_x, 6), STAGE_NAMES[stage - 1], fill=(236, 230, 214, 255))
    board.save(path)


def contact_sheet(path: str, scale: int = 6):
    columns = max(len(poses) for poses, _ in ANIMATIONS.values())
    sheet = Image.new("RGBA", (columns * (FRAME + 1) * scale, len(ANIMATIONS) * (FRAME + 1) * scale), (*BACKGROUND, 255))
    for row, (poses, _) in enumerate(ANIMATIONS.values()):
        for column, pose in enumerate(poses):
            backdrop = Image.new("RGBA", (FRAME, FRAME), (156, 102, 72, 255))
            backdrop.alpha_composite(with_blob(final_frame(pose)))
            sheet.alpha_composite(upscale(backdrop, scale), (column * (FRAME + 1) * scale, row * (FRAME + 1) * scale))
    sheet.save(path)


def preview_gif(poses, durations, path: str, scale: int = 6):
    frames = []
    for pose in poses:
        backdrop = Image.new("RGBA", (FRAME, FRAME), (156, 102, 72, 255))
        backdrop.alpha_composite(with_blob(final_frame(pose)))
        frames.append(upscale(backdrop, scale).convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=32))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)


if __name__ == "__main__":
    stage_board("brutamontes_etapas.png")
    contact_sheet("brutamontes_frames.png")
    for name, (poses, durations) in ANIMATIONS.items():
        preview_gif(poses, durations, f"brutamontes_{name}.gif")
    print(f"passo sem deslizar a {WALK_GROUND_SPEED:.2f} tile/s")
    if "--preview" in sys.argv:
        sys.exit(0)
    export_animation([final_frame(pose) for pose in IDLE], animation="idle", durations_ms=IDLE_DURATIONS_MS,
                     ground_row=GROUND_ROW, **ASSET)
    export_animation([final_frame(pose) for pose in WALK], animation="walk", durations_ms=WALK_DURATIONS_MS,
                     ground_row=GROUND_ROW, ground_speed_tiles_per_second=WALK_GROUND_SPEED, **ASSET)
    export_animation([final_frame(pose) for pose in ATTACK], animation="attack", durations_ms=ATTACK_DURATIONS_MS,
                     ground_row=GROUND_ROW, loop=False, impact_frame=ATTACK_IMPACT_FRAME, **ASSET)
