from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .clip_library import Clip
from .config import AppConfig
from .utils import obs_process_running, probe_tcp


class OBSStatus(str, Enum):
    CONNECTED = "connected"
    OBS_NOT_OPEN = "obs_not_open"
    WEBSOCKET_DISABLED = "websocket_disabled"
    PASSWORD_INVALID = "password_invalid"
    ERROR = "error"


@dataclass(frozen=True)
class OBSConnectionReport:
    status: OBSStatus
    message: str
    detail: str = ""


class OBSClientError(RuntimeError):
    pass


class OBSController:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client: Any | None = None
        self._scene_item_cache: dict[str, int] = {}

    def diagnose_connection(self) -> OBSConnectionReport:
        if not probe_tcp(self.config.obs.host, self.config.obs.port):
            if obs_process_running():
                return OBSConnectionReport(
                    OBSStatus.WEBSOCKET_DISABLED,
                    "ERRORE: OBS aperto ma WebSocket non attivo",
                    "Apri Tools -> WebSocket Server Settings e attiva il server sulla porta 4455.",
                )
            return OBSConnectionReport(
                OBSStatus.OBS_NOT_OPEN,
                "ERRORE: OBS non aperto",
                "Apri OBS e poi rilancia il controllo.",
            )
        try:
            self.connect()
            return OBSConnectionReport(OBSStatus.CONNECTED, "OK: OBS collegato")
        except Exception as exc:
            text = str(exc).lower()
            if "auth" in text or "password" in text:
                return OBSConnectionReport(
                    OBSStatus.PASSWORD_INVALID,
                    "ERRORE: password OBS errata",
                    "Controlla OBS_WS_PASSWORD nel file .env.",
                )
            return OBSConnectionReport(OBSStatus.ERROR, "ERRORE: OBS non collegabile", str(exc))

    def connect(self) -> None:
        if self.client is not None:
            return
        try:
            import obsws_python as obs
        except ImportError as exc:
            raise OBSClientError("obsws-python non e' installato. Esegui setup.bat.") from exc
        self.client = obs.ReqClient(
            host=self.config.obs.host,
            port=self.config.obs.port,
            password=self.config.obs_password(),
            timeout=3,
        )

    def send(self, request_type: str, data: dict[str, Any] | None = None) -> Any:
        self.connect()
        assert self.client is not None
        return self.client.send(request_type, data or {}, raw=True)

    def _call(self, method_name: str, *args: Any, fallback_request: str | None = None, **kwargs: Any) -> Any:
        self.connect()
        assert self.client is not None
        method = getattr(self.client, method_name, None)
        if method is not None:
            return method(*args, **kwargs)
        if fallback_request is None:
            raise OBSClientError(f"Metodo OBS non disponibile: {method_name}")
        return self.send(fallback_request, kwargs)

    def get_version(self) -> Any:
        return self._call("get_version", fallback_request="GetVersion")

    def get_input_kind_list(self) -> list[str]:
        raw = self.send("GetInputKindList", {"unversioned": True})
        data = raw.get("responseData", raw)
        return list(data.get("inputKinds", data.get("input_kinds", [])))

    def get_source_filter_kind_list(self) -> list[str]:
        raw = self.send("GetSourceFilterKindList")
        data = raw.get("responseData", raw)
        return list(data.get("sourceFilterKinds", data.get("source_filter_kinds", [])))

    def create_scene(self, scene_name: str) -> None:
        try:
            self.send("CreateScene", {"sceneName": scene_name})
        except Exception as exc:
            if "already" not in str(exc).lower() and "exists" not in str(exc).lower():
                raise

    def create_input(
        self,
        *,
        scene_name: str,
        input_name: str,
        input_kind: str,
        input_settings: dict[str, Any],
        scene_item_enabled: bool,
    ) -> None:
        payload = {
            "sceneName": scene_name,
            "inputName": input_name,
            "inputKind": input_kind,
            "inputSettings": input_settings,
            "sceneItemEnabled": scene_item_enabled,
        }
        try:
            self.send("CreateInput", payload)
        except Exception as exc:
            if "already" not in str(exc).lower() and "exists" not in str(exc).lower():
                raise

    def create_source_filter(
        self,
        *,
        source_name: str,
        filter_name: str,
        filter_kind: str,
        filter_settings: dict[str, Any],
    ) -> None:
        payload = {
            "sourceName": source_name,
            "filterName": filter_name,
            "filterKind": filter_kind,
            "filterSettings": filter_settings,
        }
        try:
            self.send("CreateSourceFilter", payload)
        except Exception as exc:
            if "already" not in str(exc).lower() and "exists" not in str(exc).lower():
                raise

    def get_scene_item_id(self, scene_name: str, source_name: str) -> int:
        cache_key = f"{scene_name}:{source_name}"
        if cache_key in self._scene_item_cache:
            return self._scene_item_cache[cache_key]
        raw = self.send(
            "GetSceneItemId",
            {"sceneName": scene_name, "sourceName": source_name},
        )
        data = raw.get("responseData", raw)
        item_id = int(data.get("sceneItemId", data.get("scene_item_id")))
        self._scene_item_cache[cache_key] = item_id
        return item_id

    def set_scene_item_enabled(self, scene_name: str, source_name: str, enabled: bool) -> None:
        item_id = self.get_scene_item_id(scene_name, source_name)
        self.send(
            "SetSceneItemEnabled",
            {
                "sceneName": scene_name,
                "sceneItemId": item_id,
                "sceneItemEnabled": bool(enabled),
            },
        )

    def set_scene_item_transform(self, scene_name: str, source_name: str, transform: dict[str, Any]) -> None:
        item_id = self.get_scene_item_id(scene_name, source_name)
        self.send(
            "SetSceneItemTransform",
            {"sceneName": scene_name, "sceneItemId": item_id, "sceneItemTransform": transform},
        )

    def set_input_settings(self, input_name: str, settings: dict[str, Any], *, overlay: bool = True) -> None:
        self.send(
            "SetInputSettings",
            {"inputName": input_name, "inputSettings": settings, "overlay": overlay},
        )

    def trigger_media_action(self, input_name: str, action: str) -> None:
        self.send("TriggerMediaInputAction", {"inputName": input_name, "mediaAction": action})

    def hide_show_layers(self) -> None:
        obs = self.config.obs
        for source_name in [obs.overlay_source_name, obs.flash_source_name, obs.blackout_source_name]:
            try:
                self.set_scene_item_enabled(obs.scene_name, source_name, False)
            except Exception:
                continue

    def play_clip(self, clip: Clip, *, base_path: Path | None = None) -> None:
        obs = self.config.obs
        path = clip.absolute_path(base_path).as_posix()
        try:
            self.trigger_media_action(obs.overlay_source_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP")
        except Exception:
            pass
        self.set_input_settings(
            obs.overlay_source_name,
            {
                "is_local_file": True,
                "local_file": path,
                "looping": False,
                "restart_on_activate": True,
                "clear_on_media_end": True,
                "close_when_inactive": False,
                "hw_decode": True,
            },
            overlay=True,
        )
        self.trigger_media_action(obs.overlay_source_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART")
        self.set_scene_item_enabled(obs.scene_name, obs.overlay_source_name, True)

    def flash(self, duration_ms: int) -> None:
        obs = self.config.obs
        self.set_scene_item_enabled(obs.scene_name, obs.flash_source_name, True)
        time.sleep(max(0, duration_ms) / 1000.0)
        self.set_scene_item_enabled(obs.scene_name, obs.flash_source_name, False)
