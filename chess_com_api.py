import requests
import webbrowser
import chess

class ChessComAPI:
    BASE_URL = "https://www.chess.com/analysis"
    
    @staticmethod
    def open_analysis(fen):
        """
        Open chess.com analysis board with the given FEN position
        """
        try:
            # Validate FEN
            chess.Board(fen)
            
            # Create analysis URL with FEN
            url = f"{ChessComAPI.BASE_URL}?fen={fen}"
            
            # Open in default browser
            webbrowser.open(url)
            return True
            
        except Exception as e:
            print(f"Error opening chess.com analysis: {e}")
            return False
