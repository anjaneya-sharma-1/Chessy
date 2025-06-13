import cv2
import numpy as np
import torch
from ultralytics import YOLO
import math


def reorder(myPoints):
    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4, 1, 2), np.int32)
    add = myPoints.sum(1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]
    diff = np.diff(myPoints, axis=1)
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew

def detect_chess_board(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply adaptive thresholding to binarize the image
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Find contours in the binary image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize variables for chess board dimensions
    board_contour = None
    board_area = 0

    # Loop through the contours to find the largest quadrilateral (the chess board)
    for cnt in contours:
        # Approximate the contour to a polygon with less vertices
        epsilon = 0.1 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # Check if the approximated contour has 4 vertices (quadrilateral)
        if len(approx) == 4:
            # Calculate the area of the contour
            area = cv2.contourArea(cnt)

            # Update the board contour and area if the current contour is larger
            if area > board_area:
                board_contour = approx
                board_area = area

    return board_contour




def warp_chess_board(frame, board_contour, new_width, new_height):
    # Order the points of the chess board contour
    ordered_points = reorder(board_contour)

    # Compute the perspective transform matrix
    pts1 = np.float32(ordered_points)
    pts2 = np.float32([[0, 0], [new_width, 0], [0, new_height], [new_width, new_height]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)

    # Apply the perspective transform to the frame
    warped = cv2.warpPerspective(frame, matrix, (new_width, new_height))

    return warped

def localize_squares(warped, square_size, grid_width, grid_height):
    # Localize the squares on the warped chess board
    # Adjust square size based on smaller dimension
    board_width = grid_width
    board_height = grid_height

    # Calculate the starting position for the chess board
    start_x = (warped.shape[1] - board_width) // 2
    start_y = (warped.shape[0] - board_height) // 2

    # Initialize a variable to keep track of the square number
    square_number = 1

    for i in range(8):
        for j in range(8):
            x = start_x + j * square_size
            y = start_y + i * square_size
            cv2.rectangle(warped, (x, y),
                          (x + square_size, y + square_size),
                          (0, 255, 0), 2)

            # Assign a position to the square
            square_position = chr(ord('a') + i) + str(j + 1)
            # Draw the position text on the square
            cv2.putText(warped, square_position, (x + 10, y + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            square_number += 1

    return warped

def detect_objects(frame, model, classNames):
    results = model(frame, stream=True)
    bounding_boxes = []

    # coordinates
    for r in results:
        boxes = r.boxes

        for box in boxes:
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # convert to int values

            # put box in frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 1)

            # Append the bounding box coordinates to the list
            bounding_boxes.append((x1, y1, x2, y2))

            # confidence
            confidence = math.ceil((box.conf[0] * 100)) / 100
            print("Confidence --->", confidence)

            # class name
            cls = int(box.cls[0])
            print("Class name -->", classNames[cls])

            # object details
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 0.5
            color = (0, 255, 255)
            thickness = 1

            cv2.putText(frame, classNames[cls], org, font, fontScale, color, thickness)

    return frame, bounding_boxes


# Load YOLO model
model = YOLO("../runs/detect/train6/weights/best.pt")

# Object classes
classNames = ["B", "K", "N", "P", "Q", "R", "b", "k", "n", "p", "q", "r"]
# Load the video
cap = cv2.VideoCapture("../Video/16.mp4")

# Get the original video dimensions
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

square_size = 65
# Define the desired resolution
new_width = 640
new_height = 600

grid_width = square_size * 8
grid_height = square_size * 8

while True:
    # Read a frame from the video
    ret, frame = cap.read()

    if not ret:
        break

    # Resize the frame to the desired resolution
    frame = cv2.resize(frame, (new_width, new_height))

    # Detect the chess board contour
    board_contour = detect_chess_board(frame)

    # Draw the detected chess board on the original frame
    if board_contour is not None:
        cv2.drawContours(frame, [board_contour], 0, (0, 255, 0), 2)

        # Warp the chess board to a top-down view
        warped = warp_chess_board(frame, board_contour, new_width, new_height)

        # Detect objects on the original frame
        detected_frame, bounding_boxes = detect_objects(frame, model, classNames)

        # Draw bounding boxes on the original frame
        for bbox in bounding_boxes:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(detected_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Display the original frame with the detected chess board and objects
        cv2.imshow('Chess Board Detection', detected_frame)

        # Localize the squares on the warped chess board
        warped = localize_squares(warped, square_size, grid_width, grid_height)

        # Display the warped chess board with localized squares
        cv2.imshow('Warped Chess Board', warped)

    else:
        cv2.imshow('Chess Board Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()




