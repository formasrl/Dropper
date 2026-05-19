from __future__ import annotations

import argparse
import re
import shutil
import tempfile
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from src.video_tools import VideoToolError, normalize_video, probe_video


HTML = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clip Normalizer</title>
  <style>
    body { font-family: system-ui, Segoe UI, sans-serif; margin: 24px; background: #101318; color: #f2f4f7; }
    main { max-width: 1080px; margin: 0 auto; }
    .drop { border: 2px dashed #647587; border-radius: 8px; padding: 34px; background: #171d24; text-align: center; cursor: pointer; }
    .drop.active { border-color: #93e6b3; background: #1c2a25; }
    button, select { padding: 10px 12px; border-radius: 6px; border: 1px solid #4c5b6a; background: #202b36; color: white; cursor: pointer; }
    button:hover { background: #2d3a47; }
    .bar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin: 14px 0; }
    .result { background: #171d24; border: 1px solid #2b3540; border-radius: 8px; padding: 12px; margin: 10px 0; }
    .ok { color: #93e6b3; }
    .warn { color: #ffd37a; }
    .err { color: #ff9f9f; }
    code { color: #93e6b3; overflow-wrap: anywhere; }
  </style>
</head>
<body>
<main>
  <h1>Clip Normalizer</h1>
  <div id="drop" class="drop">
    <strong>Trascina qui una o piu' clip</strong><br>
    oppure clicca per scegliere i file.
    <input id="files" type="file" multiple accept="video/*" hidden>
  </div>
  <div class="bar">
    <label>Categoria:
      <select id="category">
        <option value="test">test</option>
        <option value="drop">drop</option>
        <option value="random">random</option>
        <option value="peak">peak</option>
        <option value="calm">calm</option>
      </select>
    </label>
    <button onclick="normalize()">Normalizza clip selezionate</button>
  </div>
  <div id="selection"></div>
  <div id="results"></div>
</main>
<script>
const drop = document.getElementById('drop');
const input = document.getElementById('files');
const selection = document.getElementById('selection');
const results = document.getElementById('results');
let selectedFiles = [];

drop.addEventListener('click', () => input.click());
drop.addEventListener('dragover', (event) => { event.preventDefault(); drop.classList.add('active'); });
drop.addEventListener('dragleave', () => drop.classList.remove('active'));
drop.addEventListener('drop', (event) => {
  event.preventDefault();
  drop.classList.remove('active');
  selectedFiles = Array.from(event.dataTransfer.files || []);
  renderSelection();
});
input.addEventListener('change', () => {
  selectedFiles = Array.from(input.files || []);
  renderSelection();
});

function renderSelection() {
  if (!selectedFiles.length) {
    selection.innerHTML = '';
    return;
  }
  selection.innerHTML = '<p>File selezionati: ' + selectedFiles.map(f => '<code>' + f.name + '</code>').join(', ') + '</p>';
}

function renderResult(item) {
  if (!item.ok) {
    return `<div class="result"><strong class="err">${item.name}</strong><br>${item.error}</div>`;
  }
  const notes = (item.before.notes || []).map(n => `<div class="warn">ATTENZIONE: ${n}</div>`).join('');
  return `<div class="result">
    <strong class="ok">${item.name}</strong><br>
    Azione: ${item.action}<br>
    Output: <code>${item.output}</code><br>
    Prima: ${item.before.width}x${item.before.height}, ${item.before.fps.toFixed(2)} fps, ${item.before.video_codec}, audio ${item.before.audio_streams ? 'presente' : 'assente'}<br>
    Dopo: ${item.after.width}x${item.after.height}, ${item.after.fps.toFixed(2)} fps, ${item.after.video_codec}, audio ${item.after.audio_streams ? 'presente' : 'assente'}<br>
    ${notes}
  </div>`;
}

async function normalize() {
  if (!selectedFiles.length) {
    results.innerHTML = '<p class="err">Scegli almeno una clip.</p>';
    return;
  }
  results.innerHTML = '<p>Conversione in corso...</p>';
  const form = new FormData();
  for (const file of selectedFiles) form.append('files', file);
  form.append('category', document.getElementById('category').value);
  const response = await fetch('/api/normalize', { method: 'POST', body: form });
  const data = await response.json();
  results.innerHTML = data.results.map(renderResult).join('');
}
</script>
</body>
</html>
"""


def open_browser_soon(url: str) -> None:
    def worker() -> None:
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=worker, daemon=True).start()


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9_-]+", "_", stem).strip("_")
    return stem or "clip"


def unique_output_path(root: Path, category: str, filename: str) -> Path:
    folder = root / "clips" / category
    folder.mkdir(parents=True, exist_ok=True)
    base = safe_stem(filename)
    candidate = folder / f"{base}.mp4"
    counter = 1
    while candidate.exists():
        candidate = folder / f"{base}_{counter:02d}.mp4"
        counter += 1
    return candidate


def process_upload(temp_path: Path, original_name: str, root: Path, category: str) -> dict[str, Any]:
    before = probe_video(temp_path)
    output = unique_output_path(root, category, original_name)
    if before.is_target_format:
        shutil.copy2(temp_path, output)
        action = "gia' compatibile, copiata nella cartella clip"
    else:
        normalize_video(temp_path, output, overwrite=False)
        action = "convertita in MP4 H.264 1920x1080 60fps senza audio"
    after = probe_video(output)
    return {
        "ok": True,
        "name": original_name,
        "action": action,
        "output": str(output),
        "before": before.to_dict(),
        "after": after.to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="UI locale per normalizzare clip in batch.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8791)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost"}:
        print("ERRORE: questo tool deve restare locale su 127.0.0.1.")
        return 1

    try:
        from fastapi import FastAPI, File, Form, UploadFile
        from fastapi.responses import HTMLResponse
        import uvicorn
    except ImportError:
        print("ERRORE: FastAPI/uvicorn/python-multipart non installati. Esegui setup.bat.")
        return 1

    root = Path(__file__).resolve().parents[1]
    app = FastAPI(title="Clip Normalizer", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML

    @app.post("/api/normalize")
    async def normalize(category: str = Form("test"), files: list[UploadFile] = File(...)) -> dict:
        if category not in {"drop", "random", "peak", "calm", "test"}:
            return {"results": [{"ok": False, "name": category, "error": "Categoria non valida."}]}
        results: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory(prefix="dropper_normalizer_") as temp_dir:
            temp_root = Path(temp_dir)
            for upload in files:
                name = upload.filename or "clip"
                temp_path = temp_root / name
                try:
                    content = await upload.read()
                    temp_path.write_bytes(content)
                    results.append(process_upload(temp_path, name, root, category))
                except Exception as exc:
                    results.append({"ok": False, "name": name, "error": str(exc)})
        return {"results": results}

    url = f"http://{args.host}:{args.port}"
    print(f"Clip normalizer: {url}")
    print("Apro il browser. Trascina una o piu' clip nella pagina per convertirle.")
    if not args.no_browser:
        open_browser_soon(url)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
