import cv2
import mediapipe as mp
import os
import time
from datetime import datetime
from config import *
from utils import calculate_ear
from alarm import trigger_alarm

if not os.path.exists("logs"):
    os.makedirs("logs")

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

cap = cv2.VideoCapture(0)

eye_closed_start = None
last_blink_time = time.time()
fake_counter = 0

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def log_event(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    current_time = time.time()

    if results.multi_face_landmarks:
        fake_counter = 0

        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape

            # LEFT EYE
            left_points = []
            for idx in LEFT_EYE:
                lm = face_landmarks.landmark[idx]
                left_points.append((int(lm.x * w), int(lm.y * h)))
            left_ear = calculate_ear(left_points)

            # RIGHT EYE
            right_points = []
            for idx in RIGHT_EYE:
                lm = face_landmarks.landmark[idx]
                right_points.append((int(lm.x * w), int(lm.y * h)))
            right_ear = calculate_ear(right_points)

            ear = (left_ear + right_ear) / 2.0

            # DEBUG PRINT (optional)
            # print("EAR:", ear)

            if ear < EAR_THRESHOLD:

                if eye_closed_start is None:
                    eye_closed_start = current_time

                if current_time - eye_closed_start > LONG_CLOSURE_SECONDS:
                    cv2.putText(frame, "ALERT: Eyes Closed Too Long",
                                (30, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (0, 0, 255),
                                2)

                    trigger_alarm()
                    log_event("Long eye closure detected")

                    color = (0, 0, 255)
                else:
                    color = (0, 165, 255)

            else:
                eye_closed_start = None
                last_blink_time = current_time
                color = (0, 255, 0)

            for p in left_points:
                cv2.circle(frame, p, 3, color, -1)

            for p in right_points:
                cv2.circle(frame, p, 3, color, -1)

        # No blink detection
        if current_time - last_blink_time > NO_BLINK_SECONDS:
            cv2.putText(frame, "NO BLINK DETECTED - SPOOF SUSPECTED",
                        (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2)

            trigger_alarm()
            log_event("No blink detected")

    else:
        fake_counter += 1
        if fake_counter > FAKE_ATTEMPT_LIMIT:
            cv2.putText(frame, "FACE LOST - SPOOF ATTEMPT",
                        (30, 110),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2)

            trigger_alarm()
            log_event("Face not detected repeatedly")

    cv2.imshow("Blink Security Tool", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()