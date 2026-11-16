"""Exporta o idle das bases da Forja, do Campanário e do Alquimista para Assets/_Project/Art/Towers.

A Balista exporta pelo próprio balista.py (base, besta e virote). As camadas de cima do Campanário
e do Alquimista entram quando as animações de disparo forem desenhadas.
"""
from art_export import export_animation
from tower_parts import GROUND_Y, turret_anchor_px
import forja
import campanario
import alquimista

BASE_IDLE_DURATIONS_MS = [200, 200, 200, 200]
# O ferreiro levanta o martelo, segura, bate e volta; a fornalha e a fumaça andam junto.
FORGE_IDLE = [forja.ForgePose(wave=0, fire=0, smoke=0, hammer_up=True),
              forja.ForgePose(wave=1, fire=1, smoke=1, hammer_up=True),
              forja.ForgePose(wave=2, fire=2, smoke=2, hammer_up=False),
              forja.ForgePose(wave=3, fire=0, smoke=3, hammer_up=True)]
FORGE_IDLE_DURATIONS_MS = [220, 160, 120, 200]


def export_towers():
    for level in (1, 2, 3):
        export_animation([forja.build_base(level, pose) for pose in FORGE_IDLE],
                         category="Towers", asset_folder="Forja", asset_id=f"forja_base_lv{level}",
                         animation="idle", durations_ms=FORGE_IDLE_DURATIONS_MS, controller="TowerBase",
                         ground_row=GROUND_Y)
        bell_level = campanario.LEVELS[level]
        export_animation([campanario.build_base(level, wave) for wave in range(4)],
                         category="Towers", asset_folder="Campanario", asset_id=f"campanario_base_lv{level}",
                         animation="idle", durations_ms=BASE_IDLE_DURATIONS_MS, controller="TowerBase",
                         ground_row=GROUND_Y,
                         turret_anchor_px=turret_anchor_px(bell_level.turret_x, bell_level.rail_top_y))
        alchemist_level = alquimista.LEVELS[level]
        export_animation([alquimista.build_base(level, alquimista.ThrowPose(wave=phase, bubble=phase))
                          for phase in range(4)],
                         category="Towers", asset_folder="Alquimista", asset_id=f"alquimista_base_lv{level}",
                         animation="idle", durations_ms=BASE_IDLE_DURATIONS_MS, controller="TowerBase",
                         ground_row=GROUND_Y,
                         turret_anchor_px=turret_anchor_px(alchemist_level.turret_x, alchemist_level.rail_top_y))


if __name__ == "__main__":
    export_towers()
    print("bases exportadas")
