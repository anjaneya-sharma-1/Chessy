from ultralytics import YOLO
import cv2
import math
# start webcam
cap = cv2.VideoCapture("../Video/16.mp4")
cap.set(3, 640)
cap.set(4, 480)

# model
model = YOLO("../runs/detect/train6/weights/best.pt")

# object classes
classNames = ["B", "K", "N", "P", "Q", "R", "b", "k", "n", "p", "q", "r"]


while True:
    success, img = cap.read()
    results = model(img, stream=True)

    # coordinates
    for r in results:
        boxes = r.boxes

        for box in boxes:
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values

            # put box in cam
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 1)

            # confidence
            confidence = math.ceil((box.conf[0]*100))/100
            print("Confidence --->",confidence)

            # class name
            cls = int(box.cls[0])
            print("Class name -->", classNames[cls])

            # object details
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (255, 0, 0)
            thickness = 2

            cv2.putText(img, classNames[cls], org, font, fontScale, color, thickness)
    resize = cv2.resize(img,(840,780))
    cv2.imshow('Webcam', resize)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()