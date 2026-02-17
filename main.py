import cv2
import json
import os
import numpy as np


# Configuration

VIDEO_PATH = "data/carPark.mp4"
JSON_PATH = "parking_slots.json"
THRESHOLD_PIXEL = 650
DASHBOARD_WIDTH = 350

# Load Parking Slot Coordinates
if not os.path.exists(JSON_PATH):
    print(f"Error: {JSON_PATH} not found.")
    exit()

with open(JSON_PATH, "r") as f:
    try:
        parking_slots = json.load(f)
        if not parking_slots:
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        print(f"Error: {JSON_PATH} is empty or invalid.")
        exit()

# Video capture
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"Error: Cannot open video {VIDEO_PATH}")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
        continue

    # --- Preprocessing ---
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

    available_count = 0
    total_slots = len(parking_slots)

    # --- Check slots ---
    for (x, y, w, h) in parking_slots:
        slot_crop = thresh[y:y+h, x:x+w]
        white_pixels = cv2.countNonZero(slot_crop)

        if white_pixels > THRESHOLD_PIXEL:
            color = (0, 0, 255)  # Occupied
        else:
            color = (0, 255, 0)  # Available
            available_count += 1

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, str(white_pixels),
                    (x, y - 5 if y - 5 > 10 else y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # --- Dashboard ---
    occupied_count = total_slots - available_count
    occupancy_percent = int((occupied_count / total_slots) * 100) if total_slots > 0 else 0

    height = frame.shape[0]
    dashboard = np.zeros((height, DASHBOARD_WIDTH, 3), dtype=np.uint8)
    dashboard[:] = (40, 40, 40)  # Background

    # Title
    cv2.putText(dashboard, "PARKING DASHBOARD", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.line(dashboard, (20, 60), (DASHBOARD_WIDTH - 20, 60), (100, 100, 100), 2)

    # Slot Info
    cv2.putText(dashboard, f"Total Slots: {total_slots}", (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(dashboard, f"Available: {available_count}", (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(dashboard, f"Occupied: {occupied_count}", (20, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(dashboard, f"Occupancy: {occupancy_percent}%", (20, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    # Progress Bar
    cv2.rectangle(dashboard, (20, 260), (DASHBOARD_WIDTH - 20, 290), (80, 80, 80), -1)
    bar_width = int((DASHBOARD_WIDTH - 40) * occupancy_percent / 100)
    cv2.rectangle(dashboard, (20, 260), (20 + bar_width, 290), (0, 0, 255), -1)

    # --- Show two separate windows ---
    cv2.imshow("Parking Feed", frame)
    cv2.imshow("Dashboard", dashboard)

    # Press Q to quit
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()

