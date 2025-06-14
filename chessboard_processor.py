import cv2
import numpy as np
from ultralytics import YOLO

# Object classes for chess pieces
classNames = ["B", "K", "N", "P", "Q", "R", "b", "k", "n", "p", "q", "r"]

def initialize_model():
    return YOLO("runs/detect/train4/weights/best.pt")

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
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    kernel = np.ones((5,5),np.uint8)
    morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    board_contour = None
    board_area = 0
    
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            area = cv2.contourArea(cnt)
            if area > board_area:
                board_contour = approx
                board_area = area
    
    return board_contour

def warp_chess_board(frame, board_contour, new_width, new_height):
    ordered_points = reorder(board_contour)
    pts1 = np.float32(ordered_points)
    pts2 = np.float32([[0, 0], [new_width, 0], [0, new_height], [new_width, new_height]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(frame, matrix, (new_width, new_height))
    warped_rotated = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return warped_rotated

def localize_squares(warped, square_size, grid_width, grid_height):
    board_width = grid_width
    board_height = grid_height
    start_x = (warped.shape[1] - board_width) // 2
    start_y = (warped.shape[0] - board_height) // 2
    
    for i in range(8):
        for j in range(8):
            x = start_x + j * square_size
            y = start_y + i * square_size
            cv2.rectangle(warped, (x, y),
                          (x + square_size, y + square_size),
                          (0, 255, 0), 2)
            square_position = chr(ord('a') + j) + str(8 - i)
            cv2.putText(warped, square_position, (x + 5,y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    return warped, start_x, start_y

def detect_chess_pieces(frame, warped, start_x, start_y, square_size, model):
    results = model(frame, stream=True)
    piece_positions = {}

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            square_x = (center_y - start_y) // square_size
            square_y = (center_x - start_x) // square_size

            square_x = max(0, min(square_x, 7))
            square_y = max(0, min(square_y, 7))

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 1)
            cls = int(box.cls[0])
            piece_name = classNames[cls]
            
            org = [x1, y1 - 5]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 0.5
            color = (255, 0, 0)
            thickness = 1
            
            cv2.putText(frame, piece_name, org, font, fontScale, color, thickness)
            square_position = chr(ord('a') + square_y) + str(8 - square_x)
            piece_positions[square_position] = piece_name

    return frame, warped, piece_positions

def generate_fen_notation(piece_positions):
    fen_notation = ""
    for rank in range(8, 0, -1):
        empty_squares = 0
        for file in range(ord('a'), ord('i')):
            square_position = chr(file) + str(rank)
            if square_position in piece_positions:
                if empty_squares > 0:
                    fen_notation += str(empty_squares)
                    empty_squares = 0
                fen_notation += piece_positions[square_position].lower()
            else:
                empty_squares += 1
        if empty_squares > 0:
            fen_notation += str(empty_squares)
        if rank!= 1:
            fen_notation += "/"
    return fen_notation

def process_frame(frame, model, square_size=65, new_width=600, new_height=600):
    frame = cv2.resize(frame, (new_width, new_height))
    board_contour = detect_chess_board(frame)
    
    if board_contour is not None:
        cv2.drawContours(frame, [board_contour], 0, (0, 255, 0), 2)
        
        grid_width = square_size * 8
        grid_height = square_size * 8
        
        warped = warp_chess_board(frame, board_contour, new_width, new_height)
        warped, start_x, start_y = localize_squares(warped, square_size, grid_width, grid_height)
        
        frame, warped, piece_positions = detect_chess_pieces(frame, warped, start_x, start_y, square_size, model)
        fen_notation = generate_fen_notation(piece_positions)
        
        return frame, fen_notation
    
    return frame, None
