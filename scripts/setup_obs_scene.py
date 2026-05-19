from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.config import ConfigError, load_config
from src.obs_client import OBSController, OBSStatus


def pick_first(available: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"ERRORE: {exc}")
        return 1

    controller = OBSController(config)
    report = controller.diagnose_connection()
    print(report.message)
    if report.detail:
        print(report.detail)
    if report.status != OBSStatus.CONNECTED:
        return 1

    input_kinds = controller.get_input_kind_list()
    media_kind = pick_first(input_kinds, ["ffmpeg_source"])
    spout_kind = pick_first(input_kinds, ["spout_capture"])
    color_kind = pick_first(input_kinds, ["color_source_v3", "color_source"])
    if not media_kind or not color_kind:
        print("ERRORE: OBS non espone Media Source o Color Source.")
        print("Input kind disponibili:")
        for kind in input_kinds:
            print(f"- {kind}")
        return 1
    if not spout_kind:
        print("ERRORE: plugin Spout2 non trovato in OBS.")
        print("Installa il plugin Spout2 durante il setup, poi riapri OBS.")
        print("Input kind disponibili:")
        for kind in input_kinds:
            print(f"- {kind}")
        return 1

    filter_kinds = controller.get_source_filter_kind_list()
    chroma_kind = pick_first(filter_kinds, ["chroma_key_filter_v2", "chroma_key_filter"])
    if not chroma_kind:
        print("ERRORE: filtro Chroma Key non trovato in OBS.")
        return 1

    obs = config.obs
    controller.create_scene(obs.scene_name)
    print(f"OK: scena pronta - {obs.scene_name}")

    controller.create_input(
        scene_name=obs.scene_name,
        input_name=obs.background_source_name,
        input_kind=spout_kind,
        input_settings={
            "spoutsenders": "usefirstavailablesender",
            "tickspeedlimit": 100,
            "compositemode": 1,
        },
        scene_item_enabled=True,
    )
    print(f"OK: sorgente Spout pronta - {obs.background_source_name}")

    controller.create_input(
        scene_name=obs.scene_name,
        input_name=obs.overlay_source_name,
        input_kind=media_kind,
        input_settings={
            "is_local_file": True,
            "local_file": "",
            "looping": False,
            "restart_on_activate": True,
            "clear_on_media_end": True,
            "close_when_inactive": False,
            "hw_decode": True,
        },
        scene_item_enabled=False,
    )
    print(f"OK: sorgente overlay pronta - {obs.overlay_source_name}")

    controller.create_source_filter(
        source_name=obs.overlay_source_name,
        filter_name=obs.chroma_filter_name,
        filter_kind=chroma_kind,
        filter_settings={
            "key_color_type": "green",
            "similarity": 400,
            "smoothness": 80,
            "spill": 100,
            "opacity": 1.0,
            "contrast": 0.0,
            "brightness": 0.0,
            "gamma": 0.0,
        },
    )
    print(f"OK: filtro green-screen pronto - {obs.chroma_filter_name}")

    controller.create_input(
        scene_name=obs.scene_name,
        input_name=obs.flash_source_name,
        input_kind=color_kind,
        input_settings={"color": 0xFFFFFFFF, "width": 1920, "height": 1080},
        scene_item_enabled=False,
    )
    controller.create_input(
        scene_name=obs.scene_name,
        input_name=obs.blackout_source_name,
        input_kind=color_kind,
        input_settings={"color": 0xFF000000, "width": 1920, "height": 1080},
        scene_item_enabled=False,
    )
    print("OK: FLASH_WHITE e BLACKOUT pronti")

    transform = {
        "positionX": 0,
        "positionY": 0,
        "boundsType": "OBS_BOUNDS_SCALE_INNER",
        "boundsWidth": 1920,
        "boundsHeight": 1080,
        "alignment": 5,
    }
    for source_name in [
        obs.background_source_name,
        obs.overlay_source_name,
        obs.flash_source_name,
        obs.blackout_source_name,
    ]:
        try:
            controller.set_scene_item_transform(obs.scene_name, source_name, transform)
        except Exception as exc:
            print(f"ATTENZIONE: transform non applicato a {source_name}: {exc}")

    controller.hide_show_layers()
    print("OK: overlay, flash e blackout nascosti.")
    print("Prossimo passo: scegli un MP4 test e usa il dashboard o il doctor per provarlo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
