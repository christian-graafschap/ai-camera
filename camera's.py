"""
Toon welke camera's beschikbaar zijn, met hun nummer en naam.

Eenmalig installeren (voor de namen):
    .\.venv\Scripts\python.exe -m pip install pygrabber

Gebruik:
    .\.venv\Scripts\python.exe cameras.py
"""
import cv2

# Namen ophalen via DirectShow (alleen Windows, vereist pygrabber)
try:
    from pygrabber.dshow_graph import FilterGraph
    namen = FilterGraph().get_input_devices()
except Exception:
    namen = []
    print("Tip: installeer pygrabber om ook de namen te zien.\n")

MAX = max(len(namen), 6)  # probeer minstens 6 nummers

print("Beschikbare camera's:")
for i in range(MAX):
    cap = cv2.VideoCapture(i)
    werkt = cap.isOpened() and cap.read()[0]
    if werkt:
        breedte = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        hoogte = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        naam = namen[i] if i < len(namen) else "(naam onbekend)"
        print(f"  source={i}: {naam}  [{breedte}x{hoogte}]")
    cap.release()