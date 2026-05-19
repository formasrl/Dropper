from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .audio_features import AudioFeatures, silence_features
from .state_machine import ShowState


@dataclass
class RuntimeStatus:
    obs_connected: bool = False
    audio_input_device: str | None = None
    features: AudioFeatures = field(default_factory=silence_features)
    state: ShowState = ShowState.CALIBRATING
    current_clip: str | None = None
    last_clip: str | None = None
    last_trigger_reason: str = ""
    cooldown_remaining: float = 0.0
    confidence_score: float = 0.0
    paused: bool = False
    blackout: bool = False
    setup_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "obs_connected": self.obs_connected,
            "audio_input_device": self.audio_input_device,
            "features": self.features.to_dict(),
            "state": self.state.value,
            "current_clip": self.current_clip,
            "last_clip": self.last_clip,
            "last_trigger_reason": self.last_trigger_reason,
            "cooldown_remaining": self.cooldown_remaining,
            "confidence_score": self.confidence_score,
            "paused": self.paused,
            "blackout": self.blackout,
            "setup_messages": list(self.setup_messages),
        }


def create_dashboard_app(status: RuntimeStatus, controls: Any | None = None) -> Any:
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse
    except ImportError as exc:
        raise RuntimeError("FastAPI non e' installato. Esegui setup.bat.") from exc

    app = FastAPI(title="OBS Auto-Drop Agent", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return """
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OBS Auto-Drop Agent</title>
  <style>
    body { font-family: system-ui, Segoe UI, sans-serif; margin: 24px; background: #101318; color: #eef2f5; }
    main { max-width: 960px; margin: 0 auto; }
    section { border: 1px solid #2d3742; border-radius: 8px; padding: 16px; margin: 12px 0; background: #171c23; }
    button { margin: 4px; padding: 10px 12px; border-radius: 6px; border: 1px solid #536170; background: #26313d; color: white; cursor: pointer; }
    button:hover { background: #334150; }
    code { color: #93e6b3; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }
    .item { background: #0f141a; padding: 12px; border-radius: 6px; }
  </style>
</head>
<body>
<main>
  <h1>OBS Auto-Drop Agent</h1>
  <section class="grid" id="status"></section>
  <section>
    <button onclick="post('/api/control/pause')">Pausa</button>
    <button onclick="post('/api/control/resume')">Riprendi</button>
    <button onclick="post('/api/control/hide-overlay')">Nascondi overlay</button>
    <button onclick="post('/api/control/test-random')">Test random</button>
    <button onclick="post('/api/control/test-drop')">Test drop</button>
    <button onclick="post('/api/control/blackout')">Blackout</button>
    <button onclick="post('/api/control/clear-blackout')">Togli blackout</button>
  </section>
</main>
<script>
async function post(url) { await fetch(url, {method: 'POST'}); await refresh(); }
async function refresh() {
  const data = await (await fetch('/api/status')).json();
  const items = [
    ['OBS', data.obs_connected ? 'collegato' : 'non collegato'],
    ['Stato', data.state],
    ['Audio', data.audio_input_device || 'non scelto'],
    ['RMS', data.features.rms.toFixed(4)],
    ['Bassi', data.features.bass_energy.toFixed(4)],
    ['BPM', data.features.bpm_estimate || '-'],
    ['Clip', data.current_clip || '-'],
    ['Ultimo trigger', data.last_trigger_reason || '-'],
    ['Cooldown', Math.round(data.cooldown_remaining) + ' sec'],
    ['Confidence', data.confidence_score.toFixed(2)]
  ];
  document.getElementById('status').innerHTML = items.map(([k,v]) => `<div class="item"><strong>${k}</strong><br><code>${v}</code></div>`).join('');
}
setInterval(refresh, 1000);
refresh();
</script>
</body>
</html>
"""

    @app.get("/api/status")
    def api_status() -> dict[str, Any]:
        return status.to_dict()

    @app.get("/api/setup/doctor")
    def api_doctor() -> dict[str, Any]:
        return {"messages": list(status.setup_messages), "status": status.to_dict()}

    @app.post("/api/control/pause")
    def pause() -> dict[str, Any]:
        status.paused = True
        status.state = ShowState.PAUSED
        if controls and hasattr(controls, "pause"):
            controls.pause()
        return {"ok": True}

    @app.post("/api/control/resume")
    def resume() -> dict[str, Any]:
        status.paused = False
        status.state = ShowState.NORMAL
        if controls and hasattr(controls, "resume"):
            controls.resume()
        return {"ok": True}

    @app.post("/api/control/hide-overlay")
    def hide_overlay() -> dict[str, Any]:
        if controls and hasattr(controls, "hide_overlay"):
            controls.hide_overlay()
        status.current_clip = None
        return {"ok": True}

    @app.post("/api/control/test-random")
    def test_random() -> dict[str, Any]:
        status.last_trigger_reason = "test_random"
        if controls and hasattr(controls, "test_random"):
            controls.test_random()
        return {"ok": True}

    @app.post("/api/control/test-drop")
    def test_drop() -> dict[str, Any]:
        status.last_trigger_reason = "test_drop"
        if controls and hasattr(controls, "test_drop"):
            controls.test_drop()
        return {"ok": True}

    @app.post("/api/control/blackout")
    def blackout() -> dict[str, Any]:
        status.blackout = True
        if controls and hasattr(controls, "blackout"):
            controls.blackout()
        return {"ok": True}

    @app.post("/api/control/clear-blackout")
    def clear_blackout() -> dict[str, Any]:
        status.blackout = False
        if controls and hasattr(controls, "clear_blackout"):
            controls.clear_blackout()
        return {"ok": True}

    return app
