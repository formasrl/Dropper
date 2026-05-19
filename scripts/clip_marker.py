from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import unquote

import _bootstrap  # noqa: F401

from src.video_tools import VideoToolError, probe_video


HTML = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clip Drop Marker</title>
  <style>
    body { font-family: system-ui, Segoe UI, sans-serif; margin: 24px; background: #101318; color: #f2f4f7; }
    main { max-width: 1120px; margin: 0 auto; }
    video { width: 100%; max-height: 68vh; background: #00ff00; border: 1px solid #29323d; border-radius: 8px; }
    .bar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 14px 0; }
    input[type=range] { flex: 1; min-width: 240px; }
    button, select, input { padding: 9px 11px; border-radius: 6px; border: 1px solid #4c5b6a; background: #202b36; color: white; }
    button { cursor: pointer; }
    button:hover { background: #2d3a47; }
    code { color: #93e6b3; }
    .panel { background: #171d24; border: 1px solid #2b3540; border-radius: 8px; padding: 14px; margin-top: 12px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
  </style>
</head>
<body>
<main>
  <h1>Clip Drop Marker</h1>
  <div class="panel">
    <strong>Clip:</strong> <code id="clipName"></code><br>
    <strong>Drop scelto:</strong> <code id="dropValue">non scelto</code>
  </div>
  <video id="video" controls></video>
  <div class="bar">
    <button onclick="step(-1/60)">-1 frame</button>
    <input id="timeline" type="range" min="0" max="1000" value="0">
    <button onclick="step(1/60)">+1 frame</button>
    <button onclick="markDrop()">Questo e' il drop</button>
    <button onclick="saveManifest()">Salva nel manifest</button>
  </div>
  <div class="grid">
    <label>ID clip<br><input id="clipId"></label>
    <label>Categoria<br>
      <select id="category">
        <option value="drop">drop</option>
        <option value="random">random</option>
        <option value="peak">peak</option>
        <option value="calm">calm</option>
        <option value="test">test</option>
      </select>
    </label>
    <label>Durata ms<br><input id="durationMs" readonly></label>
    <label>Impact ms<br><input id="impactMs"></label>
  </div>
  <div class="panel" id="status"></div>
</main>
<script>
const video = document.getElementById('video');
const timeline = document.getElementById('timeline');
let metadata = null;
let clipPath = null;

function ms(sec) { return Math.round(sec * 1000); }
function setStatus(text) { document.getElementById('status').innerHTML = text; }
function step(delta) {
  video.pause();
  video.currentTime = Math.max(0, Math.min(video.duration || 0, video.currentTime + delta));
}
function markDrop() {
  const value = ms(video.currentTime);
  document.getElementById('impactMs').value = value;
  document.getElementById('dropValue').textContent = value + ' ms';
}
timeline.addEventListener('input', () => {
  if (!video.duration) return;
  video.currentTime = (Number(timeline.value) / 1000) * video.duration;
});
video.addEventListener('timeupdate', () => {
  if (!video.duration) return;
  timeline.value = Math.round((video.currentTime / video.duration) * 1000);
});

async function loadClip() {
  const response = await fetch('/api/clip');
  metadata = await response.json();
  clipPath = metadata.file;
  video.src = '/video?path=' + encodeURIComponent(clipPath);
  document.getElementById('clipName').textContent = clipPath;
  document.getElementById('clipId').value = metadata.suggested_id;
  document.getElementById('category').value = metadata.category;
  document.getElementById('durationMs').value = metadata.duration_ms;
  document.getElementById('impactMs').value = metadata.impact_ms || '';
  setStatus((metadata.notes || []).length ? metadata.notes.map(n => 'ATTENZIONE: ' + n).join('<br>') : 'OK: formato compatibile.');
}

async function saveManifest() {
  const body = {
    id: document.getElementById('clipId').value,
    category: document.getElementById('category').value,
    duration_ms: Number(document.getElementById('durationMs').value),
    impact_ms: document.getElementById('impactMs').value ? Number(document.getElementById('impactMs').value) : null
  };
  const response = await fetch('/api/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const result = await response.json();
  setStatus(result.ok ? 'OK: manifest aggiornato.' : 'ERRORE: ' + result.error);
}

loadClip();
</script>
</body>
</html>
"""


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"clips": []}


def save_clip_entry(manifest_path: Path, clip_file: Path, root: Path, payload: dict) -> None:
    manifest = load_json(manifest_path)
    clips = manifest.setdefault("clips", [])
    try:
        clip_path = clip_file.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        clip_path = clip_file.resolve().as_posix()
    entry = {
        "id": payload["id"],
        "file": clip_path,
        "category": payload["category"],
        "duration_ms": int(payload["duration_ms"]),
        "impact_ms": payload.get("impact_ms"),
        "weight": 1.0,
        "min_seconds_between_repeats": 3600 if payload["category"] in {"drop", "peak"} else 2400,
        "tags": [],
        "allowed_states": ["BUILD", "PEAK"] if payload["category"] in {"drop", "peak"} else ["NORMAL", "BREAKDOWN"],
        "max_plays_per_event": 2,
    }
    for index, existing in enumerate(clips):
        if existing.get("id") == entry["id"] or existing.get("file") == entry["file"]:
            clips[index] = entry
            break
    else:
        clips.append(entry)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def open_browser_soon(url: str) -> None:
    def worker() -> None:
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=worker, daemon=True).start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Dashboard locale per marcare impact_ms di una clip.")
    parser.add_argument("clip", help="File MP4 da marcare")
    parser.add_argument("--manifest", default="clips_manifest.json")
    parser.add_argument("--category", choices=["drop", "random", "peak", "calm", "test"], default="drop")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    clip = Path(args.clip).resolve()
    manifest_path = (root / args.manifest).resolve()
    if args.host not in {"127.0.0.1", "localhost"}:
        print("ERRORE: questo tool deve restare locale su 127.0.0.1.")
        return 1
    try:
        probe = probe_video(clip)
    except VideoToolError as exc:
        print(f"ERRORE: {exc}")
        return 1

    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
        import uvicorn
    except ImportError:
        print("ERRORE: FastAPI/uvicorn non installati. Esegui setup.bat.")
        return 1

    app = FastAPI(title="Clip Drop Marker", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML

    @app.get("/api/clip")
    def api_clip() -> dict:
        return {
            "file": str(clip),
            "suggested_id": clip.stem.lower().replace(" ", "_"),
            "category": args.category,
            "duration_ms": probe.duration_ms,
            "impact_ms": 5200 if args.category in {"drop", "peak"} else None,
            "notes": probe.compatibility_notes(),
        }

    @app.get("/video")
    def video(path: str) -> FileResponse:
        requested = Path(unquote(path)).resolve()
        if requested != clip:
            return JSONResponse({"error": "File non autorizzato"}, status_code=403)
        media_type = mimetypes.guess_type(str(clip))[0] or "video/mp4"
        return FileResponse(clip, media_type=media_type)

    @app.post("/api/save")
    async def save(request: Request) -> dict:
        payload = await request.json()
        try:
            save_clip_entry(manifest_path, clip, root, payload)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    url = f"http://{args.host}:{args.port}"
    print(f"Clip marker: {url}")
    print("Apro il browser. Cerca il frame del drop, premi 'Questo e' il drop', poi salva.")
    if not args.no_browser:
        open_browser_soon(url)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
