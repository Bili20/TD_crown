"""Soldados da Forja nv1 (recruta), nv2 (aprovado em 10/11) e nv3 (veterano): rig de partes e as 3 animações.

O desenho de cada nível continua nos grids originais (animate_v2.SOLDIER_UPPER para o nv2, forja.py para o
nv1 e o nv3). Aqui cada grid é separado em tronco, braço da espada, ponta da pluma e pernas, para o walk
sair com sobreposição: o tronco sobe e desce, a espada chega um frame depois e a pluma tremula.

O idle e o ataque usam as poses aprovadas do nv2 (o nv2 sai idêntico ao aprovado, conferido no export).

Uso: python soldados_forja.py            -> exporta idle, walk e attack dos 3 níveis e registra no manifesto
     python soldados_forja.py --preview  -> só as prévias em ArtSource/
"""
import sys
from dataclasses import dataclass
from PIL import Image

from animate_v2 import SLASH_ARC, SOLDIER_PLUME_TIP, SOLDIER_UPPER, SWORD_FORWARD, SWORD_REST
from art_export import export_animation
from forja import COLORS, SOLDIER_RECRUIT, SOLDIER_VETERAN
from style_test import BACKGROUND, PRESETS, recolor
from style_test_v2 import on_shadow

FRAME = 16
GROUND_ROW = 14
LEGS_ROW = 14
SHADOW_TOP = GROUND_ROW + 1  # sombra separada 1 linha abaixo dos pés (bible §3)


@dataclass
class Level:
    asset_id: str
    body: dict            # (x, y) -> letra: tronco, cabeça, escudo
    sword: dict           # braço da espada em repouso, com a mão
    plume: dict           # ponta da pluma (vazio no recruta)
    legs_x: tuple[int, int]
    sword_forward: dict   # espada na estocada


def cells_of(rows: list[str], origin_x: int = 0, origin_y: int = 0) -> dict:
    return {(origin_x + column, origin_y + row): letter
            for row, line in enumerate(rows) for column, letter in enumerate(line) if letter != "."}


def split_grid(rows: list[str], sword_from_x: int, plume_rows: tuple[int, ...]) -> tuple[dict, dict, dict]:
    body, sword, plume = {}, {}, {}
    for (x, y), letter in cells_of(rows).items():
        if y == LEGS_ROW:
            continue
        if x >= sword_from_x:
            sword[(x, y)] = letter
        elif y in plume_rows:
            plume[(x, y)] = letter
        else:
            body[(x, y)] = letter
    return body, sword, plume


def build_levels() -> dict[int, Level]:
    recruit_body, recruit_sword, _ = split_grid(SOLDIER_RECRUIT, 12, ())
    veteran_body, veteran_sword, veteran_plume = split_grid(SOLDIER_VETERAN, 12, (3,))
    return {
        # A espada curta do recruta não tem guarda em cruz: na estocada fica só a linha da lâmina.
        1: Level("forge_soldier_lv1", recruit_body, recruit_sword, {}, (6, 9), cells_of(SWORD_FORWARD[1:2], 0, 10)),
        2: Level("forge_soldier_lv2", cells_of(SOLDIER_UPPER), cells_of(SWORD_REST, 0, 5),
                 cells_of(SOLDIER_PLUME_TIP, 0, 4), (5, 8), cells_of(SWORD_FORWARD, 0, 9)),
        3: Level("forge_soldier_lv3", veteran_body, veteran_sword, veteran_plume, (6, 9), cells_of(SWORD_FORWARD, 0, 9)),
    }


LEVELS = build_levels()


@dataclass(frozen=True)
class Pose:
    body_y: int = 0
    sword: str = "rest"          # rest | forward
    sword_y: int = 0             # além do tronco (atraso do braço)
    slash: bool = False
    plume_x: int = 0
    left_leg: tuple[int, int] = (0, 0)    # (deslocamento x, erguida 0/1)
    right_leg: tuple[int, int] = (0, 0)


def hand_of(level: Level) -> tuple[int, int]:
    return next(position for position, letter in level.sword.items() if letter == "t")


def draw(level: Level, pose: Pose) -> Image.Image:
    cells: dict[tuple[int, int], str] = {}
    for leg_x, (offset_x, lifted) in zip(level.legs_x, (pose.left_leg, pose.right_leg)):
        x = leg_x + offset_x
        rows = [LEGS_ROW - 1] if lifted else ([LEGS_ROW - 1, LEGS_ROW] if pose.body_y < 0 else [LEGS_ROW])
        for y in rows:
            cells[(x, y)] = "o"
            cells[(x + 1, y)] = "o"
    for (x, y), letter in level.body.items():
        cells[(x, y + pose.body_y)] = letter
    for (x, y), letter in level.plume.items():
        cells[(x + pose.plume_x, y + pose.body_y)] = letter
    if pose.sword == "rest":
        for (x, y), letter in level.sword.items():
            cells[(x, y + pose.body_y + pose.sword_y)] = letter
    else:
        # Estocada: a mão vem para a frente do corpo, no mesmo ponto nos 3 níveis.
        for (x, y), letter in level.sword_forward.items():
            cells[(x, y + pose.body_y)] = letter
    if pose.slash:
        for (x, y), letter in cells_of(SLASH_ARC, 0, 8).items():
            cells[(x, y + pose.body_y)] = letter
    image = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    for (x, y), letter in cells.items():
        if 0 <= x < FRAME and 0 <= y < FRAME:
            image.putpixel((x, y), (*COLORS[letter], 255))
    return image


# --- Animações ------------------------------------------------------------------------------------
# idle e ataque: as poses aprovadas do nv2 (animate_v2), escritas no rig.
IDLE = [Pose(), Pose(body_y=-1), Pose(body_y=-1, plume_x=1), Pose()]
IDLE_DURATIONS_MS = [240, 180, 240, 180]
ATTACK = [Pose(body_y=-1, sword_y=-2), Pose(sword="forward"), Pose(sword="forward", slash=True), Pose()]
ATTACK_DURATIONS_MS = [140, 70, 110, 160]
ATTACK_IMPACT_FRAME = 1

# Passo de 6 frames, 2 passos por ciclo e 1 tile por ciclo. Nos contatos (f0, f3) os dois pés no chão
# e abertos; nos outros o corpo sobe 1 px e um pé fica erguido. A espada repete a altura do frame
# anterior (o braço atrasa) e a pluma tremula no começo de cada subida.
WALK_BODY = [0, -1, -1, 0, -1, -1]
WALK_LEFT = [(-1, 0), (-1, 0), (-1, 0), (-1, 0), (-1, 1), (0, 1)]
WALK_RIGHT = [(1, 0), (1, 1), (0, 1), (1, 0), (1, 0), (1, 0)]
WALK_DURATIONS_MS = [110] * 6
WALK_GROUND_SPEED = 1000 / sum(WALK_DURATIONS_MS)


def build_walk() -> list[Pose]:
    return [Pose(body_y=WALK_BODY[index], sword_y=max(WALK_BODY[index], WALK_BODY[index - 1]) - WALK_BODY[index],
                 plume_x=1 if index in (1, 4) else 0, left_leg=WALK_LEFT[index], right_leg=WALK_RIGHT[index])
            for index in range(6)]


WALK = build_walk()
ANIMATIONS = {
    "idle": (IDLE, IDLE_DURATIONS_MS),
    "walk": (WALK, WALK_DURATIONS_MS),
    "attack": (ATTACK, ATTACK_DURATIONS_MS),
}


# --- Prévia e exportação --------------------------------------------------------------------------

def upscale(image: Image.Image, scale: int) -> Image.Image:
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def contact_sheet(path: str, preset_names=("real", "rubi"), scale: int = 6):
    rows = [(level, name, preset) for level in LEVELS.values() for name in ANIMATIONS for preset in preset_names]
    columns = max(len(poses) for poses, _ in ANIMATIONS.values())
    sheet = Image.new("RGBA", (columns * (FRAME + 1) * scale, len(rows) * (FRAME + 1) * scale), (*BACKGROUND, 255))
    for row_index, (level, name, preset_name) in enumerate(rows):
        for column, pose in enumerate(ANIMATIONS[name][0]):
            backdrop = Image.new("RGBA", (FRAME, FRAME), (108, 150, 88, 255))
            backdrop.alpha_composite(on_shadow(recolor(draw(level, pose), PRESETS[preset_name]), 4, 8, SHADOW_TOP))
            sheet.alpha_composite(upscale(backdrop, scale), (column * (FRAME + 1) * scale, row_index * (FRAME + 1) * scale))
    sheet.save(path)


def preview_gif(level: Level, path: str, scale: int = 8):
    # As três animações em sequência, recoloridas no preset padrão.
    frames, durations = [], []
    for name, (poses, timings) in ANIMATIONS.items():
        repeats = 3 if name != "attack" else 2
        for _ in range(repeats):
            for pose, duration in zip(poses, timings):
                backdrop = Image.new("RGBA", (FRAME, FRAME), (*BACKGROUND, 255))
                backdrop.alpha_composite(on_shadow(recolor(draw(level, pose), PRESETS["real"]), 4, 8, SHADOW_TOP))
                frames.append(upscale(backdrop, scale).convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=32))
                durations.append(duration)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)


def matches_approved_lv2() -> bool:
    level = LEVELS[2]
    for name in ("idle", "attack"):
        approved = Image.open(f"../Assets/_Project/Art/PlayerUnits/ForgeSoldier/forge_soldier_lv2_{name}.png").convert("RGBA")
        for index, pose in enumerate(ANIMATIONS[name][0]):
            frame = approved.crop((index * FRAME, 0, (index + 1) * FRAME, FRAME))
            if frame.tobytes() != draw(level, pose).tobytes():
                print(f"nv2 {name} frame {index} difere do aprovado")
                return False
    return True


if __name__ == "__main__":
    contact_sheet("soldados_frames.png")
    for level_number, level in LEVELS.items():
        preview_gif(level, f"soldado_nv{level_number}.gif")
    print(f"passo sem deslizar a {WALK_GROUND_SPEED:.2f} tile/s; nv2 igual ao aprovado: {matches_approved_lv2()}")
    if "--preview" in sys.argv:
        sys.exit(0)
    if not matches_approved_lv2():
        sys.exit("O rig mudou o nv2 aprovado; nada foi exportado.")
    for level in LEVELS.values():
        asset = dict(category="PlayerUnits", asset_folder="ForgeSoldier", asset_id=level.asset_id,
                     controller="Unit", ground_row=GROUND_ROW)
        export_animation([draw(level, pose) for pose in IDLE], animation="idle", durations_ms=IDLE_DURATIONS_MS, **asset)
        export_animation([draw(level, pose) for pose in WALK], animation="walk", durations_ms=WALK_DURATIONS_MS,
                         ground_speed_tiles_per_second=WALK_GROUND_SPEED, **asset)
        export_animation([draw(level, pose) for pose in ATTACK], animation="attack", durations_ms=ATTACK_DURATIONS_MS,
                         loop=False, impact_frame=ATTACK_IMPACT_FRAME, **asset)
