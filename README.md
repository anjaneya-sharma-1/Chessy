# chessy

chessy is an advanced computer vision system for real-time chessboard and chess piece detection, FEN extraction, and chess engine integration. It leverages YOLOv8 for object detection and Stockfish for move analysis, providing both live and offline analysis modes.

---

## Features

- **Real-time Chessboard and Piece Detection**: Detects chessboard and all 12 chess piece types (white/black: K, Q, R, B, N, P) from live camera or images.
- **FEN Extraction**: Converts detected board state to FEN notation for interoperability.
- **Chess Engine Integration**: Uses Stockfish to suggest best moves and analyze positions.
- **Modern UI**: Built with Kivy for a responsive, modern interface.
- **Offline and Online Modes**: Analyze from live camera, photo, or gallery image.

---

## Project Structure

- `chess_app.py` / `chess_app_fixed.py`: Main Kivy app for UI and logic.
- `chessboard_processor.py`: Board and piece detection logic (YOLOv8-based).
- `chess_engine.py`: Stockfish integration and board rendering.
- `pieces/`: Piece images for rendering.
- `runs/`: Model weights, metrics, and results (see `runs/detect/train4/` for metrics and images).
- `stockfish/`: Stockfish engine binary and related files.
- `Video/`: Example chessboard videos for testing.
- `app/api/detect-chess-position/`: API route for backend integration.

---

## Metrics & Performance

### Chess Piece Detection (YOLOv8, Training Set)
- **Accuracy:** 89%

### Chessboard Detection (YOLOv8, Training Set)
- **Accuracy:** 99.5%

### Overall System (Chess Pieces on Chessboard)
- **Precision:** > 99%
- **Recall:** > 99%
- **Interpretation:** High classification and detection accuracy for both chessboard and pieces in real-world scenarios.

#### Example Metrics from Model Training (see `runs/detect/train4/results.csv`):
- **Precision (last epoch):** 0.92
- **Recall (last epoch):** 0.88
- **mAP@0.5 (last epoch):** 0.93
- **mAP@0.5:0.95 (last epoch):** 0.83

#### Visual Results
- Training and validation curves, confusion matrices, and example predictions are available in `runs/detect/train4/`:
  - `results.png`, `PR_curve.png`, `F1_curve.png`, `R_curve.png`
  - `confusion_matrix.png`, `confusion_matrix_normalized.png`
  - `val_batch*_pred.jpg`, `val_batch*_labels.jpg`

---

## Requirements

- Python 3.8+
- Kivy
- OpenCV
- Ultralytics YOLOv8
- Stockfish (binary included)
- fentoboardimage, PIL, numpy, chess, plyer

---

## Usage

### Running the App

```bash
python chess_app.py
```

### Live Mode
- Detects chessboard and pieces from webcam.
- Shows FEN and best move suggestion.

### Offline Mode
- Analyze a photo or gallery image.
- Opens detected position in chess.com analysis.

---

## Dataset

- **Source:** [Roboflow ChessSense-AI Dataset v3](https://universe.roboflow.com/mohammad-zaid-p9lpu/chesssense-ai/dataset/3)
- **Classes:** 12 (B, K, N, P, Q, R, b, k, n, p, q, r)
- **License:** CC BY 4.0

---

## References

- [YOLOv8 by Ultralytics](https://github.com/ultralytics/ultralytics)
- [Stockfish Chess Engine](https://stockfishchess.org/)
- [Roboflow Dataset](https://universe.roboflow.com/mohammad-zaid-p9lpu/chesssense-ai/dataset/3)

---

## License

- Dataset: CC BY 4.0
- Code: MIT (unless otherwise specified)

---

## Acknowledgements

- Roboflow for dataset hosting.
- Ultralytics for YOLOv8.
- Stockfish for chess engine.

---

> For more details, see the images and CSVs in `runs/detect/train4/`. 