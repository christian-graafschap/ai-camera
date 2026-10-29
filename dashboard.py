r"""
Schermvullend dashboard voor de AI-camera.

    links          : de AI-infographic (AI-camera_infographic.png)
    rechts boven   : live camerabeeld met YOLO-detecties
    rechts onder   : de uitvoer van Python / Ultralytics

Gebruik (instellingen in Ultralytics-stijl, key=value):
    .\.venv\Scripts\python.exe dashboard.py model=yolo26n.pt source=0 conf=0.25

Sluiten met Esc (of Alt+F4). F11 wisselt tussen schermvullend en venster.
"""
import logging
import queue
import re
import sys
import threading
import tkinter as tk
from pathlib import Path

import cv2
from PIL import Image, ImageTk

MAP = Path(__file__).resolve().parent
INFOGRAPHIC = MAP / "AI-camera_infographic.png"
MAX_REGELS = 500  # oudere uitvoerregels worden weggegooid
ANSI = re.compile(r"\x1b\[[0-9;]*m")

ACHTERGROND = "#111111"
TEKST_ACHTERGROND = "#0b0b0b"
TEKST_KLEUR = "#d0d0d0"


def lees_argumenten(argv):
    """Zet 'key=value'-argumenten om naar een dict met int/float/bool waar mogelijk."""
    opties = {"model": "yolo26n.pt", "source": 0}
    for arg in argv:
        if "=" not in arg:
            continue
        sleutel, waarde = arg.split("=", 1)
        if waarde.lower() in ("true", "false"):
            waarde = waarde.lower() == "true"
        else:
            for soort in (int, float):
                try:
                    waarde = soort(waarde)
                    break
                except ValueError:
                    pass
        opties[sleutel] = waarde
    return opties


class UitvoerNaarQueue:
    """Vervangt sys.stdout/sys.stderr: tekst gaat naar de console én naar het dashboard."""

    def __init__(self, origineel, wachtrij):
        self.origineel = origineel
        self.wachtrij = wachtrij

    def write(self, tekst):
        if self.origineel:
            self.origineel.write(tekst)
        if tekst:
            self.wachtrij.put(tekst)

    def flush(self):
        if self.origineel:
            self.origineel.flush()


class QueueHandler(logging.Handler):
    """Stuurt Ultralytics-logregels naar het dashboard."""

    def __init__(self, wachtrij):
        super().__init__()
        self.wachtrij = wachtrij
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record):
        self.wachtrij.put(self.format(record) + "\n")


class Dashboard:
    def __init__(self, opties):
        self.opties = opties
        self.tekst_queue = queue.Queue()
        self.beeld_queue = queue.Queue(maxsize=1)
        self.stoppen = threading.Event()

        sys.stdout = UitvoerNaarQueue(sys.__stdout__, self.tekst_queue)
        sys.stderr = UitvoerNaarQueue(sys.__stderr__, self.tekst_queue)

        self.root = tk.Tk()
        self.root.title("AI-Camera")
        self.root.configure(bg=ACHTERGROND)
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.afsluiten())
        self.root.bind("<F11>", lambda e: self.root.attributes(
            "-fullscreen", not self.root.attributes("-fullscreen")))
        self.root.protocol("WM_DELETE_WINDOW", self.afsluiten)

        # Raster: 2 even brede kolommen, rechts 2 even hoge rijen
        self.root.columnconfigure(0, weight=1, uniform="kolom")
        self.root.columnconfigure(1, weight=1, uniform="kolom")
        self.root.rowconfigure(0, weight=1, uniform="rij")
        self.root.rowconfigure(1, weight=1, uniform="rij")

        self.info_label = tk.Label(self.root, bg=ACHTERGROND)
        self.info_label.grid(row=0, column=0, rowspan=2, sticky="nsew")

        self.camera_label = tk.Label(self.root, bg="black", fg=TEKST_KLEUR,
                                     text="Camera wordt gestart...", font=("Segoe UI", 16))
        self.camera_label.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=(0, 2))

        tekst_frame = tk.Frame(self.root, bg=TEKST_ACHTERGROND)
        tekst_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0), pady=(2, 0))
        scrollbar = tk.Scrollbar(tekst_frame)
        scrollbar.pack(side="right", fill="y")
        self.tekst = tk.Text(tekst_frame, bg=TEKST_ACHTERGROND, fg=TEKST_KLEUR,
                             font=("Consolas", 11), wrap="none", bd=0,
                             highlightthickness=0, yscrollcommand=scrollbar.set)
        self.tekst.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scrollbar.config(command=self.tekst.yview)
        self.tekst.configure(state="disabled")

        self.infographic = Image.open(INFOGRAPHIC) if INFOGRAPHIC.exists() else None
        self.info_foto = None
        self.camera_foto = None
        self.info_label.bind("<Configure>", self.toon_infographic)

    # ---------- linkerhelft: infographic ----------
    def toon_infographic(self, event):
        if self.infographic is None:
            self.info_label.configure(text=f"{INFOGRAPHIC.name} niet gevonden", fg=TEKST_KLEUR)
            return
        schaal = min(event.width / self.infographic.width, event.height / self.infographic.height)
        if schaal <= 0:
            return
        maat = (int(self.infographic.width * schaal), int(self.infographic.height * schaal))
        self.info_foto = ImageTk.PhotoImage(self.infographic.resize(maat, Image.LANCZOS))
        self.info_label.configure(image=self.info_foto)

    # ---------- YOLO in een achtergrond-thread ----------
    def yolo_thread(self):
        try:
            from ultralytics import YOLO
            from ultralytics.utils import LOGGER

            LOGGER.addHandler(QueueHandler(self.tekst_queue))
            opties = dict(self.opties)
            model = YOLO(opties.pop("model"))
            bron = opties.pop("source")
            opties.pop("show", None)
            for resultaat in model.predict(source=bron, stream=True, **opties):
                if self.stoppen.is_set():
                    break
                beeld = resultaat.plot()  # BGR-afbeelding met kaders en labels
                try:
                    self.beeld_queue.get_nowait()  # alleen het nieuwste beeld bewaren
                except queue.Empty:
                    pass
                self.beeld_queue.put(beeld)
            print("Voorspelling gestopt.")
        except Exception as fout:
            print(f"FOUT: {fout!r}")

    # ---------- periodiek het scherm bijwerken ----------
    def bijwerken(self):
        try:
            beeld = self.beeld_queue.get_nowait()
        except queue.Empty:
            beeld = None
        if beeld is not None:
            breedte = self.camera_label.winfo_width()
            hoogte = self.camera_label.winfo_height()
            schaal = min(breedte / beeld.shape[1], hoogte / beeld.shape[0])
            if schaal > 0:
                beeld = cv2.resize(beeld, (int(beeld.shape[1] * schaal), int(beeld.shape[0] * schaal)))
                beeld = cv2.cvtColor(beeld, cv2.COLOR_BGR2RGB)
                self.camera_foto = ImageTk.PhotoImage(Image.fromarray(beeld))
                self.camera_label.configure(image=self.camera_foto, text="")

        stukken = []
        while True:
            try:
                stukken.append(self.tekst_queue.get_nowait())
            except queue.Empty:
                break
        if stukken:
            nieuw = ANSI.sub("", "".join(stukken)).replace("\r", "\n")
            onderaan = self.tekst.yview()[1] >= 0.999
            self.tekst.configure(state="normal")
            self.tekst.insert("end", nieuw)
            regels = int(self.tekst.index("end-1c").split(".")[0])
            if regels > MAX_REGELS:
                self.tekst.delete("1.0", f"{regels - MAX_REGELS}.0")
            self.tekst.configure(state="disabled")
            if onderaan:
                self.tekst.see("end")

        if not self.stoppen.is_set():
            self.root.after(30, self.bijwerken)

    def afsluiten(self):
        self.stoppen.set()
        self.root.destroy()

    def start(self):
        print(f"AI-Camera dashboard  |  {self.opties}")
        threading.Thread(target=self.yolo_thread, daemon=True).start()
        self.root.after(30, self.bijwerken)
        self.root.mainloop()


if __name__ == "__main__":
    Dashboard(lees_argumenten(sys.argv[1:])).start()
