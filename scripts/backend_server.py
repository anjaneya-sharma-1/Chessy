from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from PIL import Image
import io
import chess
import chess.engine
import torch
from ultralytics import YOLO
from typing import Optional, Dict, List, Tuple
import json
import os
from pathlib import Path
import math
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chess Vision API", version="1.0.0")

# Add CORS middleware with more permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IntegratedChessVisionModel:
    """Integrated chess piece detection model using your YOLOv8 implementation"""
    
    def __init__(self, model_path: str = "best.pt"):
        self.model_path = model_path
        # Object classes for chess pieces (from your code)
        self.classNames = ["B", "K", "N", "P", "Q", "R", "b", "k", "n", "p", "q", "r"]
        
        # Mapping from class names to FEN notation (your format)
        self.piece_to_fen = {
            'B': 'B', 'K': 'K', 'N': 'N', 'P': 'P', 'Q': 'Q', 'R': 'R',
            'b': 'b', 'k': 'k', 'n': 'n', 'p': 'p', 'q': 'q', 'r': 'r'
        }
        
        # Load the YOLOv8 model (from your code)
        try:
            self.model = YOLO(model_path)
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Failed to load model from {model_path}: {e}")
            self.model = None
        
        # Board detection parameters
        self.square_size = 65
        self.new_width = 600
        self.new_height = 600
        self.grid_width = self.square_size * 8
        self.grid_height = self.square_size * 8
    
    def reorder(self, myPoints):
        """Reorder points for perspective transformation (from your code)"""
        myPoints = myPoints.reshape((4, 2))
        myPointsNew = np.zeros((4, 1, 2), np.int32)
        add = myPoints.sum(1)
        myPointsNew[0] = myPoints[np.argmin(add)]
        myPointsNew[3] = myPoints[np.argmax(add)]
        diff = np.diff(myPoints, axis=1)
        myPointsNew[1] = myPoints[np.argmin(diff)]
        myPointsNew[2] = myPoints[np.argmax(diff)]
        return myPointsNew

    def detect_chess_board(self, frame):
        """Detect chess board contour (from your code)"""
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

    def warp_chess_board(self, frame, board_contour, new_width, new_height):
        """Warp chess board to top-down view (from your code)"""
        # Order the points of the chess board contour
        ordered_points = self.reorder(board_contour)

        # Compute the perspective transform matrix
        pts1 = np.float32(ordered_points)
        pts2 = np.float32([[0, 0], [new_width, 0], [0, new_height], [new_width, new_height]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)

        # Apply the perspective transform to the frame
        warped = cv2.warpPerspective(frame, matrix, (new_width, new_height))

        # Rotate the warped image by -90 degrees
        warped_rotated = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)

        return warped_rotated

    def localize_squares(self, warped):
        """Localize squares on the warped chess board (from your code)"""
        # Calculate the starting position for the chess board
        start_x = (warped.shape[1] - self.grid_width) // 2
        start_y = (warped.shape[0] - self.grid_height) // 2

        return start_x, start_y

    def detect_chess_pieces(self, frame, start_x, start_y):
        """Detect chess pieces using YOLO model (adapted from your code)"""
        if self.model is None:
            return {}
        
        results = self.model(frame, stream=True)
        piece_positions = {}  # Dictionary to store piece positions

        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue

            for box in boxes:
                # Bounding box
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # Calculate the center coordinates of the bounding box
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # Map the center coordinates to the corresponding square on the warped image
                square_x = (center_y - start_y) // self.square_size
                square_y = (center_x - start_x) // self.square_size

                # Ensure the square coordinates are within the chess board bounds
                square_x = max(0, min(square_x, 7))
                square_y = max(0, min(square_y, 7))

                # Class name
                cls = int(box.cls[0])
                if cls < len(self.classNames):
                    piece_name = self.classNames[cls]

                    # Store the piece position
                    square_position = chr(ord('a') + square_y) + str(8 - square_x)
                    
                    # Get confidence score
                    confidence = float(box.conf[0]) if box.conf is not None else 0.0
                    
                    # Only store pieces with high confidence
                    if confidence > 0.5:
                        piece_positions[square_position] = {
                            'piece': piece_name,
                            'confidence': confidence
                        }

        return piece_positions

    def generate_fen_notation(self, piece_positions):
        """Generate FEN notation from piece positions (from your code)"""
        fen_notation = ""
        for rank in range(8, 0, -1):
            empty_squares = 0
            for file in range(ord('a'), ord('i')):
                square_position = chr(file) + str(rank)
                if square_position in piece_positions:
                    if empty_squares > 0:
                        fen_notation += str(empty_squares)
                        empty_squares = 0
                    piece_data = piece_positions[square_position]
                    piece_name = piece_data['piece'] if isinstance(piece_data, dict) else piece_data
                    fen_notation += piece_name
                else:
                    empty_squares += 1
            if empty_squares > 0:
                fen_notation += str(empty_squares)
            if rank != 1:
                fen_notation += "/"

        # Add game state (active color, castling, en passant, halfmove, fullmove)
        fen_notation += " w KQkq - 0 1"
        return fen_notation

    def process_image(self, image: np.ndarray) -> Dict:
        """Process image and return chess position data"""
        try:
            # Resize frame to match your processing size
            frame = cv2.resize(image, (self.new_width, self.new_height))
            
            # Detect chess board
            board_contour = self.detect_chess_board(frame)
            
            if board_contour is None:
                return {
                    'success': False,
                    'error': 'Chess board not detected',
                    'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                    'confidence': 0.0,
                    'boardDetected': False
                }
            
            # Warp chess board
            warped = self.warp_chess_board(frame, board_contour, self.new_width, self.new_height)
            
            # Get square positions
            start_x, start_y = self.localize_squares(warped)
            
            # Detect chess pieces
            piece_positions = self.detect_chess_pieces(frame, start_x, start_y)
            
            # Generate FEN notation
            fen = self.generate_fen_notation(piece_positions)
            
            # Calculate average confidence
            confidences = [data['confidence'] for data in piece_positions.values() 
                          if isinstance(data, dict)]
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return {
                'success': True,
                'fen': fen,
                'confidence': round(avg_confidence, 3),
                'piecesDetected': len(piece_positions),
                'boardDetected': True,
                'piecePositions': piece_positions
            }
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return {
                'success': False,
                'error': str(e),
                'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                'confidence': 0.0,
                'boardDetected': False
            }

class ChessEngine:
    """Chess engine for move suggestions"""
    
    def __init__(self):
        self.engine_path = self._find_stockfish()
        
    def _find_stockfish(self) -> Optional[str]:
        """Find Stockfish engine on the system"""
        possible_paths = [
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "stockfish",
            "C:\\stockfish\\stockfish.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                return path
        
        return None
    
    def _command_exists(self, command: str) -> bool:
        """Check if command exists in PATH"""
        try:
            import subprocess
            subprocess.run([command], capture_output=True, timeout=1)
            return True
        except:
            return False
    
    def get_best_move(self, fen: str, time_limit: float = 1.0) -> Optional[str]:
        """Get best move suggestion for given position"""
        if not self.engine_path:
            return self._get_random_legal_move(fen)
        
        try:
            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                board = chess.Board(fen)
                if board.is_game_over():
                    return None
                
                result = engine.play(board, chess.engine.Limit(time=time_limit))
                return str(result.move)
        except Exception as e:
            print(f"Engine error: {e}")
            return self._get_random_legal_move(fen)
    
    def _get_random_legal_move(self, fen: str) -> Optional[str]:
        """Get a random legal move as fallback"""
        try:
            board = chess.Board(fen)
            legal_moves = list(board.legal_moves)
            if legal_moves:
                import random
                return str(random.choice(legal_moves))
        except:
            pass
        return None

# Initialize models
model_path = os.getenv('CHESS_MODEL_PATH', 'best.pt')
vision_model = IntegratedChessVisionModel(model_path)
chess_engine = ChessEngine()

@app.get("/")
async def root():
    return {"message": "Chess Vision API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": vision_model.model is not None,
        "model_path": vision_model.model_path
    }

@app.post("/api/detect-chess-position")
async def detect_chess_position(image: UploadFile = File(...)):
    try:
        logger.info(f"Received image: {image.filename}")
        
        # Read image file
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        logger.info("Processing image with vision model")
        # Process image using the vision model
        result = vision_model.process_image(img)
        
        if not result['success']:
            logger.warning(f"Image processing failed: {result.get('error', 'Unknown error')}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result.get('error', 'Failed to process image'),
                    "fen": result.get('fen', ''),
                    "confidence": result.get('confidence', 0.0)
                }
            )
        
        logger.info(f"Successfully processed image. FEN: {result['fen']}")
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-position")
async def analyze_position(request: dict):
    """Analyze a chess position given FEN notation"""
    try:
        fen = request.get('fen')
        if not fen:
            raise HTTPException(status_code=400, detail="FEN notation required")
        
        # Validate FEN
        try:
            board = chess.Board(fen)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid FEN notation")
        
        # Get analysis
        suggested_move = chess_engine.get_best_move(fen, time_limit=2.0)
        
        # Get position evaluation
        evaluation = await get_position_evaluation(fen)
        
        return JSONResponse({
            "success": True,
            "fen": fen,
            "suggestedMove": suggested_move,
            "evaluation": evaluation,
            "isGameOver": board.is_game_over(),
            "legalMoves": [str(move) for move in board.legal_moves]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing position: {str(e)}")

async def get_position_evaluation(fen: str) -> Dict:
    """Get detailed position evaluation"""
    try:
        board = chess.Board(fen)
        
        # Basic material count
        material_balance = 0
        piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.symbol().lower(), 0)
                material_balance += value if piece.color else -value
        
        return {
            "materialBalance": material_balance,
            "whiteToMove": board.turn,
            "canCastle": {
                "whiteKingside": board.has_kingside_castling_rights(chess.WHITE),
                "whiteQueenside": board.has_queenside_castling_rights(chess.WHITE),
                "blackKingside": board.has_kingside_castling_rights(chess.BLACK),
                "blackQueenside": board.has_queenside_castling_rights(chess.BLACK)
            },
            "inCheck": board.is_check(),
            "moveCount": board.fullmove_number
        }
    except:
        return {"error": "Could not evaluate position"}

@app.get("/api/engine-info")
async def get_engine_info():
    """Get information about the chess engine and model"""
    return {
        "engineAvailable": chess_engine.engine_path is not None,
        "enginePath": chess_engine.engine_path,
        "modelLoaded": vision_model.model is not None,
        "modelPath": model_path,
        "classNames": vision_model.classNames
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Integrated Chess Vision API server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print(f"Model path: {vision_model.model_path}")
    
    # Start the server with proper configuration
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable hot reloading
        workers=4,    # Use multiple workers for better performance
        log_level="info"
    )
