import chess
import chess.engine
import os
from pathlib import Path
import numpy as np
from fentoboardimage import fenToImage, loadPiecesFolder
from PIL import Image
import io
import shutil

class ChessEngineManager:
    def __init__(self):
        self.engine = None
        self.board = chess.Board()
        self.last_move = None
        self.piece_set = self.setup_piece_set()
        
        # Initialize Stockfish engine
        try:
            # First try the default path
            stockfish_path = str(Path("stockfish/stockfish-windows-x86-64-sse41-popcnt.exe"))
            if not os.path.exists(stockfish_path):
                # Try alternative paths
                alternative_paths = [
                    "stockfish.exe",
                    "stockfish/stockfish.exe",
                    "C:/Program Files/Stockfish/stockfish.exe",
                    "C:/Program Files (x86)/Stockfish/stockfish.exe"
                ]
                for path in alternative_paths:
                    if os.path.exists(path):
                        stockfish_path = path
                        break
            
            if os.path.exists(stockfish_path):
                self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
                self.engine.configure({"Threads": 2, "Hash": 128})
                print(f"Stockfish engine initialized successfully from {stockfish_path}")
            else:
                print("Warning: Stockfish engine not found. Best move suggestions will be disabled.")
        except Exception as e:
            print(f"Error initializing Stockfish: {e}")
            print("Best move suggestions will be disabled.")
    
    def setup_piece_set(self):
        """Set up the piece set for board rendering"""
        pieces_dir = Path("pieces")
        if not pieces_dir.exists():
            pieces_dir.mkdir(parents=True)
            
            # Create white and black piece directories
            white_dir = pieces_dir / "white"
            black_dir = pieces_dir / "black"
            white_dir.mkdir()
            black_dir.mkdir()
            
            # Create default piece images
            pieces = {
                "white": {
                    "Pawn": "♙", "Knight": "♘", "Bishop": "♗",
                    "Rook": "♖", "Queen": "♕", "King": "♔"
                },
                "black": {
                    "Pawn": "♟", "Knight": "♞", "Bishop": "♝",
                    "Rook": "♜", "Queen": "♛", "King": "♚"
                }
            }
            
            # Generate piece images
            for color, color_pieces in pieces.items():
                for piece_name, symbol in color_pieces.items():
                    self.create_piece_image(color, piece_name, symbol)
        
        return loadPiecesFolder(str(pieces_dir))
    
    def create_piece_image(self, color, piece_name, symbol):
        """Create a piece image with the given symbol"""
        size = 100
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        
        # Draw piece symbol
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        text_bbox = draw.textbbox((0, 0), symbol, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2
        
        # Draw piece
        color_rgb = (0, 0, 0) if color == "white" else (128, 128, 128)
        draw.text((text_x, text_y), symbol, font=font, fill=color_rgb)
        
        # Save piece image
        piece_path = Path("pieces") / color / f"{piece_name}.png"
        img.save(piece_path)
    
    def get_best_move(self, time_limit=1.0):
        """Get the best move for the current position"""
        if not self.engine:
            print("Engine not available for best move calculation")
            return None
            
        try:
            # Create a new engine instance if the current one is dead
            if not hasattr(self, '_engine_alive') or not self._engine_alive:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine.path)
                self.engine.configure({"Threads": 2, "Hash": 128})
                self._engine_alive = True
            
            # Get the best move
            result = self.engine.play(self.board, chess.engine.Limit(time=time_limit))
            if result and result.move:
                self.last_move = result.move
                return result.move
            return None
            
        except Exception as e:
            print(f"Error getting best move: {e}")
            self._engine_alive = False
            return None
    
    def update_position(self, fen):
        """Update the board position from FEN string"""
        try:
            new_board = chess.Board(fen)
            self.board = new_board
            return True
        except Exception as e:
            print(f"Invalid FEN: {e}")
            return False
    
    def render_board(self, size=800):
        """Render the current board position using fentoboardimage"""
        try:
            # Get the current FEN
            fen = self.board.fen()
            
            # Create last move highlighting if available
            last_move = None
            if self.last_move:
                last_move = {
                    "before": chess.square_name(self.last_move.from_square),
                    "after": chess.square_name(self.last_move.to_square),
                    "darkColor": "#BACA44",
                    "lightColor": "#F7F769"
                }
            
            # Render the board
            board_image = fenToImage(
                fen=fen,
                squarelength=size // 8,
                pieceSet=self.piece_set,
                darkColor="#B58863",
                lightColor="#F0D9B5",
                lastMove=last_move
            )
            
            # Convert PIL Image to numpy array
            img_array = np.array(board_image)
            
            # Convert RGB to BGR (OpenCV format)
            img_array = img_array[:, :, ::-1]
            
            return img_array
            
        except Exception as e:
            print(f"Error rendering board: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def close(self):
        """Clean up chess engine"""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
            self._engine_alive = False
