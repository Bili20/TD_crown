import json
from pathlib import Path
from PIL import Image
from pixel_canvas import save_spritesheet

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_ROOT = PROJECT_ROOT / "Assets" / "_Project" / "Art"
MANIFEST_PATH = ART_ROOT / "art-manifest.json"
MANIFEST_VERSION = 1


def pivot_from_ground_row(frame_height: int, ground_row: int) -> float:
    # O pivô fica na borda de baixo da linha do chão: é ali que o objeto encosta no mundo.
    return (frame_height - 1 - ground_row) / frame_height


def export_animation(frames: list[Image.Image], *, category: str, asset_folder: str, asset_id: str,
                     animation: str, durations_ms: list[int], controller: str, ground_row: int,
                     loop: bool = True, impact_frame: int = -1,
                     turret_anchor_px: tuple[int, int] | None = None) -> Path:
    if durations_ms and len(durations_ms) != len(frames):
        raise ValueError(f"{asset_id}_{animation}: {len(frames)} frames e {len(durations_ms)} durações")
    frame_width, frame_height = frames[0].size
    folder = ART_ROOT / category / asset_folder
    folder.mkdir(parents=True, exist_ok=True)
    sheet_path = folder / f"{asset_id}_{animation}.png"
    save_spritesheet([frames], str(sheet_path))

    entry = {
        "sheetPath": sheet_path.relative_to(PROJECT_ROOT).as_posix(),
        "assetId": asset_id,
        "animation": animation,
        "category": category,
        "controller": controller,
        "frameWidth": frame_width,
        "frameHeight": frame_height,
        "pivotX": 0.5,
        "pivotY": pivot_from_ground_row(frame_height, ground_row),
        "durationsMs": list(durations_ms),
        "loop": loop,
        "impactFrame": impact_frame,
        "turretAnchorPx": list(turret_anchor_px) if turret_anchor_px else [],
    }
    _update_manifest(entry)
    return sheet_path


def export_directions(frames: list[Image.Image], *, category: str, asset_folder: str, asset_id: str) -> Path:
    # Projéteis: um frame por direção (E, SE, S, SW, W, NW, N, NE), fatiados mas sem clip.
    frame_width, frame_height = frames[0].size
    folder = ART_ROOT / category / asset_folder
    folder.mkdir(parents=True, exist_ok=True)
    sheet_path = folder / f"{asset_id}_directions.png"
    save_spritesheet([frames], str(sheet_path))
    _update_manifest({
        "sheetPath": sheet_path.relative_to(PROJECT_ROOT).as_posix(),
        "assetId": asset_id,
        "animation": "directions",
        "category": category,
        "controller": "",
        "frameWidth": frame_width,
        "frameHeight": frame_height,
        "pivotX": 0.5,
        "pivotY": 0.5,
        "durationsMs": [],
        "loop": False,
        "impactFrame": -1,
        "turretAnchorPx": [],
    })
    return sheet_path


def _update_manifest(entry: dict):
    manifest = {"version": MANIFEST_VERSION, "sheets": []}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sheets = [sheet for sheet in manifest["sheets"] if sheet["sheetPath"] != entry["sheetPath"]]
    sheets.append(entry)
    sheets.sort(key=lambda sheet: sheet["sheetPath"])
    manifest["version"] = MANIFEST_VERSION
    manifest["sheets"] = sheets
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
