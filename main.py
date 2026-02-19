import cv2
import json
import os
import numpy as np
import sys
import subprocess
from tkinter import Tk, simpledialog
from tkinter.filedialog import askopenfilename


# Default Configuration

DEFAULT_THRESHOLD = 650
THRESHOLD_PIXEL = DEFAULT_THRESHOLD
JSON_PATH = "parking_slots.json"

VIDEO_PATH = None
cap = None
parking_slots = []


# Load Parking Slots

def load_slots():
    global parking_slots

    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            slots = json.load(f)

        parking_slots.clear()

        for s in slots:
            if isinstance(s, dict):
                parking_slots.append(s)
            elif isinstance(s, (list, tuple)):
                x, y, w, h = s
                parking_slots.append({"x": x, "y": y, "w": w, "h": h})
    else:
        parking_slots.clear()


# Select Video

def select_video():
    global VIDEO_PATH, cap

    Tk().withdraw()
    path = askopenfilename(filetypes=[("Video files", "*.mp4 *.avi")])

    if path:
        VIDEO_PATH = os.path.abspath(path)
        cap = cv2.VideoCapture(VIDEO_PATH)
        print("Video Loaded:", VIDEO_PATH)


# Open Slot Selector(Json)

def open_slot_selector():
    if VIDEO_PATH is None:
        print("Please load video first.")
        return

    script_path = os.path.join(os.path.dirname(__file__), "slots_selection_section.py")

    try:
        subprocess.run([sys.executable, script_path, VIDEO_PATH], check=True)
    except subprocess.CalledProcessError as e:
        print("Error running slot selector:", e)

    load_slots()


# Input exact threshold

def input_threshold():
    global THRESHOLD_PIXEL

    Tk().withdraw()
    value = simpledialog.askinteger(
        "Input Threshold",
        "Enter exact threshold value:",
        initialvalue=THRESHOLD_PIXEL,
        minvalue=0
    )

    if value is not None:
        THRESHOLD_PIXEL = value
        print("Threshold set to:", THRESHOLD_PIXEL)


# Control Panel Click Event

def control_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:

        if 20 < x < 200 and 20 < y < 60:
            select_video()

        if 220 < x < 420 and 20 < y < 60:
            open_slot_selector()

        if 440 < x < 580 and 20 < y < 60:
            input_threshold()


# Create Windows

cv2.namedWindow("Result Panel", cv2.WINDOW_NORMAL)
cv2.namedWindow("Dashboard", cv2.WINDOW_NORMAL)
cv2.namedWindow("Control Panel", cv2.WINDOW_NORMAL)

cv2.resizeWindow("Control Panel", 600, 420)
cv2.setMouseCallback("Control Panel", control_mouse)

load_slots()


# Main Loop

while True:

    available_count = 0
    occupied_count = 0

    available_pixels = []
    occupied_pixels = []

    available_max = 0
    occupied_min = 0
    suggested_average = 0


    # Result Panel

    if cap is not None and cap.isOpened():

        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 1)

        thresh = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            25,
            16
        )

        for slot in parking_slots:

            x, y, w, h = slot["x"], slot["y"], slot["w"], slot["h"]

            slot_crop = thresh[y:y+h, x:x+w]
            white_pixels = cv2.countNonZero(slot_crop)

            if white_pixels > THRESHOLD_PIXEL:
                color = (0, 0, 255)
                occupied_count += 1
                occupied_pixels.append(white_pixels)
            else:
                color = (0, 255, 0)
                available_count += 1
                available_pixels.append(white_pixels)

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

            cv2.putText(
                frame,
                str(white_pixels),
                (x, y - 5 if y - 5 > 10 else y + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )

        if len(available_pixels) > 0:
            available_max = int(np.max(available_pixels))

        if len(occupied_pixels) > 0:
            occupied_min = int(np.min(occupied_pixels))

        if available_max > 0 and occupied_min > 0:
            suggested_average = int((available_max + occupied_min) / 2)

        cv2.imshow("Result Panel", frame)

    else:
        cv2.imshow("Result Panel", np.zeros((480, 640, 3), dtype=np.uint8))


    # Dashboard

    dashboard = np.zeros((150, 600, 3), dtype=np.uint8)

    cv2.putText(dashboard, f"TOTAL SLOTS: {len(parking_slots)}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.putText(dashboard, f"AVAILABLE: {available_count}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.putText(dashboard, f"OCCUPIED: {occupied_count}", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("Dashboard", dashboard)


    # Control Panel

    control_ui = np.zeros((420, 600, 3), dtype=np.uint8)

    # Buttons
    cv2.rectangle(control_ui, (20, 20), (200, 60), (255, 255, 255), 2)
    cv2.putText(control_ui, "Load Video", (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.rectangle(control_ui, (220, 20), (420, 60), (255, 255, 255), 2)
    cv2.putText(control_ui, "Select Slots", (250, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.rectangle(control_ui, (440, 20), (580, 60), (255, 255, 255), 2)
    cv2.putText(control_ui, "Set Threshold", (450, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # Threshold Info
    cv2.putText(control_ui, f"Threshold Value: {THRESHOLD_PIXEL}",
                (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2)

    # Statistics
    cv2.putText(control_ui, f"Available Max White: {available_max}",
                (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2)

    cv2.putText(control_ui, f"Occupied Min White: {occupied_min}",
                (20, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2)

    cv2.putText(control_ui, f"Suggested Threshold: {suggested_average}",
                (20, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 255),
                2)

    #  Decision Rule Instruction
    cv2.putText(control_ui, "Decision Rule:",
                (20, 290),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2)

    cv2.putText(control_ui, "Available  <  Threshold Value",
                (40, 330),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2)

    cv2.putText(control_ui, "Occupied   >  Threshold Value",
                (40, 370),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2)

    cv2.imshow("Control Panel", control_ui)

    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
