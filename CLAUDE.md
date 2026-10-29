# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A thin wrapper around the Ultralytics YOLO CLI that runs real-time object detection on the local webcam. There is no custom Python source — the entire project is a batch launcher that shells out to `yolo.exe` from a vendored virtualenv.

Key pieces:
- `start-camera.bat` — entry point. Runs `.\.venv\Scripts\yolo.exe predict model=yolo26n.pt source=0 show=True` (webcam index 0, live preview window).
- `yolo26n.pt` — the pretrained Ultralytics YOLO26-nano weights used for prediction.
- `.venv\` — Python 3.11.5 virtualenv with `ultralytics` installed; `yolo.exe` is the Ultralytics CLI shim.
- `runs\detect\predict*\` — Ultralytics' default output directory. A new `predict-N` folder is created per run.

## Running

```bat
start-camera.bat
```

To change behavior, edit the single `yolo predict` command in `start-camera.bat`. Common knobs (Ultralytics CLI syntax, `key=value`):
- `source=0` → webcam index; use a file path or RTSP URL for other inputs.
- `model=yolo26n.pt` → swap weights (e.g. `yolo26s.pt`, custom-trained `.pt`).
- `conf=0.25`, `iou=0.7`, `imgsz=640`, `device=0` (GPU) / `device=cpu`, `save=True` to persist annotated frames to `runs\detect\predict-N\`.

## Notes for editing

- There is no build, lint, or test step — nothing to run beyond the batch file.
- The venv's Python is `C:\temp\AI-Camera\.venv\Scripts\python.exe` (3.11.5). Use `.\.venv\Scripts\pip install ...` to add packages.
- If adding Python scripts, invoke them via the venv's `python.exe` so Ultralytics resolves correctly.
