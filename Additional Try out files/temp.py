import cv2
import numpy as np
import torch
from ultralytics import YOLO
import math

# Object classes for chess pieces
classNames = ["B", "K", "N", "P", "Q", "R", "b", "k", "n", "p", "q", "r"]

# Load the YOLOv8 model
model = YOLO("../runs/detect/train5/weights/best.pt")

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

    # Apply Canny edge detection
    edges = cv2.Canny(blur, 50, 150)

    # Use morphology to remove noise and fill gaps
    kernel = np.ones((5,5),np.uint8)
    morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Find contours in the morphed image
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize variables for chess board dimensions
    board_contour = None
    board_area = 0

    # Loop through the contours to find the largest quadrilateral (the chess board)
    for cnt in contours:
        # Approximate the contour to a polygon
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)

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

    # Rotate the warped image by -90 degrees
    warped_rotated = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)

    return warped_rotated
def localize_squares(warped, square_size, grid_width, grid_height):
    # Localize the squares on the warped chess board
    # Adjust square size based on smaller dimension
    board_width = grid_width
    board_height = grid_height

    # Calculate the starting position for the chess board
    start_x = (warped.shape[1] - board_width) // 2
    start_y = (warped.shape[0] - board_height) // 2

    for i in range(8):
        for j in range(8):
            x = start_x + j * square_size
            y = start_y + i * square_size
            cv2.rectangle(warped, (x, y),
                          (x + square_size, y + square_size),
                          (0, 255, 0), 2)

            # Assign a position to the square
            square_position = chr(ord('a') + j) + str(8 - i)
            # Draw the position text on the square
            cv2.putText(warped, square_position, (x + 5,y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return warped, start_x, start_y

def detect_chess_pieces(frame, warped, start_x, start_y, square_size):
    results = model(frame, stream=True)
    piece_positions = {}  # Dictionary to store piece positions

    for r in results:
        boxes = r.boxes

        for box in boxes:
            # Bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Calculate the center coordinates of the bounding box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Map the center coordinates to the corresponding square on the warped image
            square_x = (center_y - start_y) // square_size
            square_y = (center_x - start_x) // square_size  # Invert the square coordinate

            # Ensure the square coordinates are within the chess board bounds
            square_x = max(0, min(square_x, 7))
            square_y = max(0, min(square_y, 7))

            # Store the piece position
            square_position = chr(ord('a') + square_y) + str(8 - square_x)  # Invert the rank index
            piece_positions[square_position] = piece_name

            # Draw bounding box on the original frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 1)

            # Class name
            cls = int(box.cls[0])
            piece_name = classNames[cls]

            # Object details
            org = [x1, y1 - 5]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 0.5
            color = (255, 0, 0)
            thickness = 1

            # Draw the piece name on the original frame
            cv2.putText(frame, piece_name, org, font, fontScale, color, thickness)

            # Store the piece position
            square_position = chr(ord('a') + square_y) + str(8 - square_x)  # Invert the rank index
            piece_positions[square_position] = piece_name

    fen = ""
    empty_square_count = 0

    for rank in range(8, 0, -1):  # Iterate through ranks from 8 to 1
        for file in range(ord('a'), ord('i')):  # Iterate through files from 'a' to 'h'
            square_position = chr(file) + str(rank)

            if square_position in piece_positions:
                if empty_square_count > 0:
                    fen += str(empty_square_count)
                    empty_square_count = 0
                fen += piece_positions[square_position]
            else:
                empty_square_count += 1

        if empty_square_count > 0:
            fen += str(empty_square_count)
            empty_square_count = 0

        if rank != 1:
            fen += "/"

    print(f"FEN: {fen}")

    # Draw piece names on the warped image
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1
    color = (255, 255, 255)
    thickness = 2

    # for square_position, piece_name in piece_positions.items():
    #     file_idx = ord(square_position[0]) - ord('a')
    #     rank_idx = int(square_position[1]) - 1
    #     x = start_x + rank_idx * square_size + square_size // 2
    #     y = start_y + file_idx * square_size + square_size // 2  # Invert the file index
    #     cv2.putText(warped, piece_name, (x, y), font, fontScale, color, thickness)

    return frame, warped, piece_positions


cap = cv2.VideoCapture("../Video/16.mp4")

# Get the original video dimensions
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

square_size = 65
new_width = 600
new_height = 600

grid_width = square_size * 8
grid_height = square_size * 8

# Flag to indicate if a frame has been captured
frame_captured = False
captured_frame = None

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.resize(frame, (new_width, new_height))

    # Check for keyboard events
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s') and not frame_captured:
        # Capture the current frame
        captured_frame = frame.copy()
        frame_captured = True

    if frame_captured:
        # Perform chess board and piece detection on the captured frame
        board_contour = detect_chess_board(captured_frame)

        if board_contour is not None:
            cv2.drawContours(captured_frame, [board_contour], 0, (0, 255, 0), 2)

            warped = warp_chess_board(captured_frame, board_contour, new_width, new_height)
            warped, start_x, start_y = localize_squares(warped, square_size, grid_width, grid_height)

            # Detect chess pieces on the warped image
            captured_frame, warped, piece_positions = detect_chess_pieces(captured_frame, warped, start_x, start_y, square_size)

            cv2.imshow('Chess Board Detection', captured_frame)
            cv2.imshow('Warped Chess Board', warped)
        else:
            cv2.imshow('Chess Board Detection', captured_frame)

    elif not frame_captured:
        # Display the original frame if no frame has been captured
        cv2.imshow('Chess Board Detection', frame)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()