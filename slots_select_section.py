import cv2
import json


# Use VIDEO instead of IMAGE

VIDEO_PATH = "carPark.mp4"

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("Error: Cannot open video.")
    exit()

# Read first frame
ret, frame = cap.read()
if not ret:
    print("Error: Cannot read frame from video.")
    exit()

image = frame.copy()     # use frame as image
clone = image.copy()

cap.release()  #  first frame for slot selection

parking_slots = []
points = []

# Mouse callback function
def mouse_click(event, x, y, flags, param):
    global points, parking_slots, image

    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))

        cv2.circle(image, (x, y), 5, (0, 0, 255), -1)

        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]

            x_min = min(x1, x2)
            y_min = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)

            parking_slots.append((x_min, y_min, w, h))

            cv2.rectangle(image, (x_min, y_min),
                          (x_min + w, y_min + h),
                          (0, 255, 0), 2)

            print(f"Slot Added: {(x_min, y_min, w, h)}")

            points = []


cv2.namedWindow("Select Parking Slots")
cv2.setMouseCallback("Select Parking Slots", mouse_click)

print("Instructions:")
print("Click 2 points to create rectangle")
print("Press 's' to save slots")
print("Press 'r' to reset")
print("Press 'q' to quit")

while True:
    cv2.imshow("Select Parking Slots", image)
    key = cv2.waitKey(1)

    if key == ord('s'):
        with open("parking_slots.json", "w") as f:
            json.dump(parking_slots, f)
        print("Slots saved to parking_slots.json")

    elif key == ord('r'):
        image = clone.copy()
        parking_slots = []
        points = []
        print("Reset done.")

    elif key == ord('q'):
        break

cv2.destroyAllWindows()
