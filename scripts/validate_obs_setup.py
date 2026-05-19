from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.config import ConfigError, load_config
from src.obs_client import OBSController, OBSStatus


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

    obs = config.obs
    ok = True
    for source_name in [
        obs.background_source_name,
        obs.overlay_source_name,
        obs.flash_source_name,
        obs.blackout_source_name,
    ]:
        try:
            controller.get_scene_item_id(obs.scene_name, source_name)
            print(f"OK: sorgente trovata - {source_name}")
        except Exception as exc:
            print(f"ERRORE: sorgente mancante - {source_name} ({exc})")
            ok = False
    try:
        filters = controller.send("GetSourceFilterList", {"sourceName": obs.overlay_source_name})
        data = filters.get("responseData", filters)
        names = [item.get("filterName") for item in data.get("filters", [])]
        if obs.chroma_filter_name in names:
            print(f"OK: filtro trovato - {obs.chroma_filter_name}")
        else:
            print(f"ERRORE: filtro mancante - {obs.chroma_filter_name}")
            ok = False
    except Exception as exc:
        print(f"ERRORE: impossibile leggere i filtri ({exc})")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
