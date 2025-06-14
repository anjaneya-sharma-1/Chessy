"use client"

interface ChessBoardProps {
  fen: string
  className?: string
}

const pieceSymbols: { [key: string]: string } = {
  K: "♔",
  Q: "♕",
  R: "♖",
  B: "♗",
  N: "♘",
  P: "♙",
  k: "♚",
  q: "♛",
  r: "♜",
  b: "♝",
  n: "♞",
  p: "♟",
}

export default function ChessBoard({ fen, className = "" }: ChessBoardProps) {
  const parseFen = (fen: string) => {
    const board = Array(8)
      .fill(null)
      .map(() => Array(8).fill(""))
    const rows = fen.split(" ")[0].split("/")

    rows.forEach((row, rowIndex) => {
      let colIndex = 0
      for (const char of row) {
        if (isNaN(Number.parseInt(char))) {
          board[rowIndex][colIndex] = char
          colIndex++
        } else {
          colIndex += Number.parseInt(char)
        }
      }
    })

    return board
  }

  const board = parseFen(fen)

  return (
    <div className={`w-full max-w-sm mx-auto ${className}`}>
      <div className="w-full aspect-square border-2 border-slate-600 rounded-lg overflow-hidden bg-amber-100">
        {board.map((row, rowIndex) => (
          <div key={rowIndex} className="flex h-[12.5%]">
            {row.map((piece, colIndex) => {
              const isLight = (rowIndex + colIndex) % 2 === 0
              return (
                <div
                  key={`${rowIndex}-${colIndex}`}
                  className={`w-[12.5%] h-full flex items-center justify-center text-lg sm:text-xl select-none ${
                    isLight ? "bg-amber-100" : "bg-amber-800"
                  }`}
                >
                  {piece && <span className="text-center leading-none">{pieceSymbols[piece]}</span>}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
