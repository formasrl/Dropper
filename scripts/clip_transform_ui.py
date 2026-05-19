from __future__ import annotations

import argparse
import re
import tempfile
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from src.video_tools import probe_video, transform_video


HTML = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clip Transformer</title>
  <style>
    body { font-family: system-ui, Segoe UI, sans-serif; margin: 24px; background: #101318; color: #f2f4f7; }
    main { max-width: 1080px; margin: 0 auto; }
    .drop { border: 2px dashed #647587; border-radius: 8px; padding: 34px; background: #171d24; text-align: center; cursor: pointer; }
    .drop.active { border-color: #93e6b3; background: #1c2a25; }
    button, select, label.option { padding: 10px 12px; border-radius: 6px; border: 1px solid #4c5b6a; background: #202b36; color: white; }
    button { cursor: pointer; }
    button:hover { background: #2d3a47; }
    label.option { display: inline-flex; gap: 8px; align-items: center; cursor: pointer; }
    .bar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin: 14px 0; }
    .result { background: #171d24; border: 1px solid #2b3540; border-radius: 8px; padding: 12px; margin: 10px 0; }
    .ok { color: #93e6b3; }
    .err { color: #ff9f9f; }
    code { color: #93e6b3; overflow-wrap: anywhere; }
  </style>
</head>
<body>
<main>
  <h1>Clip Transformer</h1>
  <div id="drop" class="drop">
    <strong>Trascina qui una o piu' clip</strong><br>
    oppure clicca per scegliere i file.
    <input id="files" type="file" multiple accept="video/*" hidden>
  </div>
  <div class="bar">
    <label class="option"><input id="hflip" type="checkbox"> Flip orizzontale</label>
    <label class="option"><input id="vflip" type="checkbox"> Flip verticale</label>
    <label class="option"><input id="reverse" type="checkbox"> Reverse</label>
  </div>
  <div class="bar">
    <label>Cartella output:
      <select id="folder">
        <option value="transformed">clips/transformed</option>
        <option value="drop">clips/drop</option>
        <option value="random">clips/random</option>
        <option value="peak">clips/peak</option>
        <option value="calm">clips/calm</option>
        <option value="test">clips/test</option>
      </select>
    </label>
    <button onclick="transformClips()">Trasforma clip selezionate</button>
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
  selection.innerHTML = selectedFiles.length
    ? '<p>File selezionati: ' + selectedFiles.map(f => '<code>' + f.name + '</code>').join(', ') + '</p>'
    : '';
}

function renderResult(item) {
  if (!item.ok) {
    return `<div class="result"><strong class="err">${item.name}</strong><br>${item.error}</div>`;
  }
  return `<div class="result">
    <strong class="ok">${item.name}</strong><br>
    Operazioni: ${item.operations.join(', ')}<br>
    Output: <code>${item.output}</code><br>
    Prima: ${item.before.width}x${item.before.height}, ${item.before.fps.toFixed(2)} fps, ${item.before.video_codec}, audio ${item.before.audio_streams ? 'presente' : 'assente'}<br>
    Dopo: ${item.after.width}x${item.after.height}, ${item.after.fps.toFixed(2)} fps, ${item.after.video_codec}, audio ${item.after.audio_streams ? 'presente' : 'assente'}
  </div>`;
}

async function transformClips() {
  if (!selectedFiles.length) {
    results.innerHTML = '<p class="err">Scegli almeno una clip.</p>';
    return;
  }
  const hflip = document.getElementById('hflip').checked;
  const vflip = document.getElementById('vflip').checked;
  const reverse = document.getElementById('reverse').checked;
  if (!hflip && !vflip && !reverse) {
    results.innerHTML = '<p class="err">Scegli almeno una trasformazione.</p>';
    return;
  }
  results.innerHTML = '<p>Trasformazione in corso...</p>';
  const form = new FormData();
  for (const file of selectedFiles) form.append('files', file);
  form.append('folder', document.getElementById('folder').value);
  form.append('hflip', hflip ? 'true' : 'false');
  form.append('vflip', vflip ? 'true' : 'false');
  form.append('reverse', reverse ? 'true' : 'false');
  const response = await fetch('/api/transform', { method: 'POST', body: form });
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


def suffix_for(hflip: bool, vflip: bool, reverse: bool) -> str:
    parts: list[str] = []
    if hflip:
        parts.append("hflip")
    if vflip:
        parts.append("vflip")
    if reverse:
        parts.append("reverse")
    return "_".join(parts)


def unique_output_path(root: Path, folder: str, filename: str, suffix: str) -> Path:
    target_dir = root / "clips" / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    base = safe_stem(filename)
    candidate = target_dir / f"{base}_{suffix}.mp4"
    counter = 1
    while candidate.exists():
        candidate = target_dir / f"{base}_{suffix}_{counter:02d}.mp4"
        counter += 1
    return candidate


def process_upload(
    temp_path: Path,
    original_name: str,
    root: Path,
    folder: str,
    *,
    hflip: bool,
    vflip: bool,
    reverse: bool,
) -> dict[str, Any]:
    before = probe_video(temp_path)
    operations = []
    if hflip:
        operations.append("flip orizzontale")
    if vflip:
        operations.append("flip verticale")
    if reverse:
        operations.append("reverse")
    output = unique_output_path(root, folder, original_name, suffix_for(hflip, vflip, reverse))
    transform_video(
        temp_path,
        output,
        hflip=hflip,
        vflip=vflip,
        reverse=reverse,
        overwrite=False,
    )
    after = probe_video(output)
    return {
        "ok": True,
        "name": original_name,
        "operations": operations,
        "output": str(output),
        "before": before.to_dict(),
        "after": after.to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="UI locale per flip/reverse video in batch.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8792)
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
    app = FastAPI(title="Clip Transformer", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML

    @app.post("/api/transform")
    async def transform(
        folder: str = Form("transformed"),
        hflip: bool = Form(False),
        vflip: bool = Form(False),
        reverse: bool = Form(False),
        files: list[UploadFile] = File(...),
    ) -> dict:
        if folder not in {"transformed", "drop", "random", "peak", "calm", "test"}:
            return {"results": [{"ok": False, "name": folder, "error": "Cartella output non valida."}]}
        if not any([hflip, vflip, reverse]):
            return {"results": [{"ok": False, "name": "operazioni", "error": "Scegli almeno una trasformazione."}]}
        results: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory(prefix="dropper_transform_") as temp_dir:
            temp_root = Path(temp_dir)
            for upload in files:
                name = upload.filename or "clip"
                temp_path = temp_root / name
                try:
                    temp_path.write_bytes(await upload.read())
                    results.append(
                        process_upload(
                            temp_path,
                            name,
                            root,
                            folder,
                            hflip=hflip,
                            vflip=vflip,
                            reverse=reverse,
                        )
                    )
                except Exception as exc:
                    results.append({"ok": False, "name": name, "error": str(exc)})
        return {"results": results}

    url = f"http://{args.host}:{args.port}"
    print(f"Clip transformer: {url}")
    print("Apro il browser. Trascina una o piu' clip nella pagina per flip/reverse.")
    if not args.no_browser:
        open_browser_soon(url)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
