from dataclasses import dataclass, replace
from PIL import Image
from pixel_canvas import Canvas, Layer, stamp, save_preview_gif
from art_export import export_animation
from style_test import PLAYER_COLORS, PRESETS, BACKGROUND, REGION1, recolor
from style_test_v2 import on_shadow

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


def preview_frames(frames, shadow_left, shadow_width, shadow_top):
    return [on_shadow(frame, shadow_left, shadow_width, shadow_top) for frame in frames]


if __name__ == "__main__":
    soldier_idle = [draw_soldier(pose) for pose in SOLDIER_IDLE]
    soldier_attack = [draw_soldier(pose) for pose in SOLDIER_ATTACK]

    # Um arquivo por animação (Art Bible §8), gravado direto no projeto e registrado no art-manifest.json.
    soldier = dict(category="PlayerUnits", asset_folder="ForgeSoldier", asset_id="forge_soldier_lv2",
                   controller="Unit", ground_row=SOLDIER_GROUND_ROW)
    export_animation(soldier_idle, animation="idle", durations_ms=SOLDIER_IDLE_DURATIONS_MS, **soldier)
    export_animation(soldier_attack, animation="attack", durations_ms=SOLDIER_ATTACK_DURATIONS_MS,
                     loop=False, impact_frame=SOLDIER_ATTACK_IMPACT_FRAME, **soldier)

    royal = PRESETS["real"]
    for name, frames, durations in (
        ("forge_soldier_idle", soldier_idle, SOLDIER_IDLE_DURATIONS_MS),
        ("forge_soldier_attack", soldier_attack, SOLDIER_ATTACK_DURATIONS_MS),
    ):
        recolored = [recolor(frame, royal) for frame in frames]
        save_preview_gif(preview_frames(recolored, 3, 9, 14), f"{name}.gif", 10, durations, BACKGROUND)

    # Folha de conferência: todos os frames ampliados, soldado já recolorido.
    soldier_rows = [[recolor(frame, royal) for frame in soldier_idle], [recolor(frame, royal) for frame in soldier_attack]]
    contact = Image.new("RGBA", (FRAME_SIZE * 4 * 2 + 8, FRAME_SIZE * 2), (*BACKGROUND, 255))
    for row_index, row in enumerate(soldier_rows):
        for column_index, frame in enumerate(row):
            contact.alpha_composite(frame, (column_index * FRAME_SIZE, row_index * FRAME_SIZE))
    for row_index, row in enumerate([imp_idle, imp_attack]):
        for column_index, frame in enumerate(row):
            contact.alpha_composite(frame, (FRAME_SIZE * 4 + 8 + column_index * FRAME_SIZE, row_index * FRAME_SIZE))
    contact.resize((contact.width * 8, contact.height * 8), Image.NEAREST).save("animation_contact.png")
