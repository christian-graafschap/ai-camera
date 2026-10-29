# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Real-time object detection on the local webcam using Ultralytics YOLO, shown in a fullscreen Tkinter dashboard. Code comments, docstrings, UI text and docs are in Dutch.

Key pieces:
- `setup.bat` — creates `.venv` (prefers `py -3.11`, falls back to `python`) and installs `ultralytics` and `pygrabber`.
- `start-camera.bat` — entry point. Runs `.\.venv\Scripts\python.exe dashboard.py model=yolo26n.pt source=0`.
- `dashboard.py` — fullscreen dashboard: infographic on the left, live camera feed with YOLO detections top-right, captured stdout/stderr and Ultralytics log output bottom-right. YOLO runs in a background thread (`model.predict(..., stream=True)`) and hands frames/text to the Tk main loop via queues. Esc closes, F11 toggles fullscreen.
- `cameras.py` — lists available webcams with their `source=` index, name (via `pygrabber`/DirectShow) and resolution.
- `AI-camera_infographic.png` — image shown in the left panel of the dashboard.

Not in git (see `.gitignore`): `.venv/`, `runs/`, and `*.pt` weights. Ultralytics downloads official weights like `yolo26n.pt` automatically on first use.

## Running

```bat
setup.bat
start-camera.bat
```

`dashboard.py` takes Ultralytics-style `key=value` arguments; `lees_argumenten()` converts values to int/float/bool and passes everything except `model`, `source` and `show` (dropped, the dashboard does its own display) straight to `model.predict()`. Common knobs:
- `source=0` → webcam index (find it with `cameras.py`); a file path or RTSP URL also works.
- `model=yolo26n.pt` → swap weights (e.g. `yolo26s.pt`, `yolo26x.pt`, custom-trained `.pt`).
- `conf=0.25`, `iou=0.7`, `imgsz=640`, `device=0` (GPU) / `device=cpu`.

## Notes for editing

- There is no build, lint, or test step.
- Windows only (`.bat` launchers, DirectShow camera names). `.gitattributes` forces CRLF for `.bat` files — keep it that way, batch labels/`goto` can break with LF.
- Use the venv's Python: `.\.venv\Scripts\python.exe`. Add packages with `.\.venv\Scripts\python.exe -m pip install ...` and also add them to `setup.bat`.
- The venv has the CPU build of torch; GPU use needs a CUDA build of torch from pytorch.org.
