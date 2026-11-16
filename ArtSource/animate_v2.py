"""Grids e poses do soldado da Forja nv2 (aprovado em 10/11). A exportação fica em soldados_forja.py."""
from dataclasses import dataclass
from PIL import Image
from pixel_canvas import Canvas, Layer, stamp
from style_test import PLAYER_COLORS

FRAME_SIZE = 16

# --- Soldado da Forja ------------------------------------------------------------------------------
SOLDIER_UPPER = [
    "................",
    "................",
    "................",
    "................",
    "................",
    ".....cb.........",
    ".....fwf........",
    "....dfwffd......",
    "...ddeeeedd.....",
    "....otuuto......",
    ".ffe.sttsbb.....",
    "fwdecbbwbba.....",
    "ffdebbbbbaa.....",
    ".fd.deeeedd.....",
]
SOLDIER_PLUME_TIP = ["......c"]
SOLDIER_PLUME_TIP_SWAYED = [".......c"]
SOLDIER_LEGS = [".....oo.oo"]
SOLDIER_GROUND_ROW = 14

SWORD_REST = [
    "............w",
    "............w",
    "............w",
    "............w",
    "...........eee",
    "...........td",
    "............d",
]
SWORD_FORWARD = [
    "............e",
    "...........tewww",
    "............e",
]
SLASH_ARC = [
    "..............f",
    "...............f",
    "...............",
    "...............f",
    "..............f",
]


@dataclass(frozen=True)
class SoldierPose:
    upper_y: int = 0
    plume_swayed: bool = False
    sword: str = "rest"
    sword_y: int = 0
    slash: bool = False


def draw_soldier(pose: SoldierPose) -> Image.Image:
    canvas = Canvas(FRAME_SIZE, FRAME_SIZE)
    layer = Layer()
    # Inspirar levanta o tronco 1 px; as pernas se esticam para não abrir buraco.
    stamp(layer, SOLDIER_LEGS, 0, 14, PLAYER_COLORS)
    if pose.upper_y < 0:
        stamp(layer, SOLDIER_LEGS, 0, 13, PLAYER_COLORS)
    stamp(layer, SOLDIER_UPPER, 0, pose.upper_y, PLAYER_COLORS)
    plume = SOLDIER_PLUME_TIP_SWAYED if pose.plume_swayed else SOLDIER_PLUME_TIP
    stamp(layer, plume, 0, 4 + pose.upper_y, PLAYER_COLORS)
    if pose.sword == "rest":
        stamp(layer, SWORD_REST, 0, 5 + pose.upper_y + pose.sword_y, PLAYER_COLORS)
    else:
        stamp(layer, SWORD_FORWARD, 0, 9 + pose.upper_y, PLAYER_COLORS)
    if pose.slash:
        stamp(layer, SLASH_ARC, 0, 8 + pose.upper_y, PLAYER_COLORS)
    canvas.put_layer(layer)
    return canvas.to_image()


SOLDIER_IDLE = [SoldierPose(), SoldierPose(upper_y=-1), SoldierPose(upper_y=-1, plume_swayed=True), SoldierPose()]
SOLDIER_IDLE_DURATIONS_MS = [240, 180, 240, 180]
SOLDIER_ATTACK = [
    SoldierPose(upper_y=-1, sword_y=-2),            # antecipação: inspira e ergue a espada
    SoldierPose(sword="forward"),                    # golpe
    SoldierPose(sword="forward", slash=True),        # impacto com o arco
    SoldierPose(),                                   # retorno
]
SOLDIER_ATTACK_DURATIONS_MS = [140, 70, 110, 160]
SOLDIER_ATTACK_IMPACT_FRAME = 1

# O Diabrete saiu daqui: ele é animado e exportado por diabrete.py.


if __name__ == "__main__":
    print("O soldado da Forja é exportado por soldados_forja.py (idle, walk e attack dos 3 níveis).")
