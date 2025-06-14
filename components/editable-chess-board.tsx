"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RotateCcw, Check, X, Edit3 } from "lucide-react"

interface EditableChessBoardProps {
  fen: string
  onFenChange: (newFen: string) => void
  showEditControls?: boolean
  title?: string
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

const pieceOptions = [
  { symbol: "", display: "Empty", color: "bg-gray-200" },
  { symbol: "K", display: "♔", color: "bg-white border-2 border-gray-800" },
  { symbol: "Q", display: "♕", color: "bg-white border-2 border-gray-800" },
  { symbol: "R", display: "♖", color: "bg-white border-2 border-gray-800" },
  { symbol: "B", display: "♗", color: "bg-white border-2 border-gray-800" },
  { symbol: "N", display: "♘", color: "bg-white border-2 border-gray-800" },
  { symbol: "P", display: "♙", color: "bg-white border-2 border-gray-800" },
  { symbol: "k", display: "♚", color: "bg-gray-800 text-white" },
  { symbol: "q", display: "♛", color: "bg-gray-800 text-white" },
  { symbol: "r", display: "♜", color: "bg-gray-800 text-white" },
  { symbol: "b", display: "♝", color: "bg-gray-800 text-white" },
  { symbol: "n", display: "♞", color: "bg-gray-800 text-white" },
  { symbol: "p", display: "♟", color: "bg-gray-800 text-white" },
]

export default function EditableChessBoard({
  fen,
  onFenChange,
  showEditControls = true,
  title,
}: EditableChessBoardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editingSquare, setEditingSquare] = useState<string | null>(null)
  const [boardState, setBoardState] = useState<string[][]>([])
  const [originalFen, setOriginalFen] = useState(fen)
  const [hasChanges, setHasChanges] = useState(false)

  const parseFen = (fenString: string) => {
    const board = Array(8)
      .fill(null)
      .map(() => Array(8).fill(""))
    const boardPart = fenString.split(" ")[0]
    const rows = boardPart.split("/")

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

  const boardToFen = (board: string[][]) => {
    const fenRows = []
    for (const row of board) {
      let fenRow = ""
      let emptyCount = 0

      for (const cell of row) {
        if (cell === "") {
          emptyCount++
        } else {
          if (emptyCount > 0) {
            fenRow += emptyCount.toString()
            emptyCount = 0
          }
          fenRow += cell
        }
      }

      if (emptyCount > 0) {
        fenRow += emptyCount.toString()
      }

      fenRows.push(fenRow)
    }

    const gameParts = fen.split(" ")
    const gameState = gameParts.slice(1).join(" ") || "w KQkq - 0 1"
    return `${fenRows.join("/")} ${gameState}`
  }

  useEffect(() => {
    setBoardState(parseFen(fen))
    setOriginalFen(fen)
    setHasChanges(false)
  }, [fen])

  const handleSquareClick = (row: number, col: number) => {
    if (!isEditing) return

    const squareKey = `${row}-${col}`
    setEditingSquare(editingSquare === squareKey ? null : squareKey)
  }

  const handlePieceSelect = (piece: string, row: number, col: number) => {
    const newBoard = [...boardState]
    newBoard[row][col] = piece
    setBoardState(newBoard)
    setEditingSquare(null)
    setHasChanges(true)
  }

  const handleSaveChanges = () => {
    const newFen = boardToFen(boardState)
    onFenChange(newFen)
    setIsEditing(false)
    setEditingSquare(null)
    setHasChanges(false)
    setOriginalFen(newFen)
  }

  const handleCancelEdit = () => {
    setBoardState(parseFen(originalFen))
    setIsEditing(false)
    setEditingSquare(null)
    setHasChanges(false)
  }

  const handleResetToOriginal = () => {
    setBoardState(parseFen(originalFen))
    setHasChanges(false)
  }

  const getSquareNotation = (row: number, col: number) => {
    return `${String.fromCharCode(97 + col)}${8 - row}`
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700 h-fit">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2 text-lg">
            {title || "Chess Board"}
            {isEditing && (
              <Badge variant="secondary" className="bg-blue-600 text-white text-xs">
                Editing
              </Badge>
            )}
            {hasChanges && !isEditing && (
              <Badge variant="secondary" className="bg-orange-600 text-white text-xs">
                Modified
              </Badge>
            )}
          </CardTitle>
          {showEditControls && (
            <div className="flex gap-2">
              {!isEditing ? (
                <Button
                  onClick={() => setIsEditing(true)}
                  variant="outline"
                  size="sm"
                  className="text-white border-slate-600 hover:bg-slate-700"
                >
                  <Edit3 className="w-4 h-4 mr-1" />
                  Edit
                </Button>
              ) : (
                <>
                  <Button
                    onClick={handleResetToOriginal}
                    variant="outline"
                    size="sm"
                    className="text-white border-slate-600 hover:bg-slate-700"
                    disabled={!hasChanges}
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                  <Button
                    onClick={handleCancelEdit}
                    variant="outline"
                    size="sm"
                    className="text-red-400 border-red-600 hover:bg-red-600/20"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                  <Button
                    onClick={handleSaveChanges}
                    size="sm"
                    className="bg-green-600 hover:bg-green-700 text-white"
                    disabled={!hasChanges}
                  >
                    <Check className="w-4 h-4" />
                  </Button>
                </>
              )}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-4">
        <div className="flex flex-col items-center space-y-4">
          {/* Chess Board Container */}
          <div className="relative w-full max-w-sm mx-auto">
            {/* Chess Board */}
            <div className="w-full aspect-square border-2 border-slate-600 rounded-lg overflow-hidden bg-amber-100">
              {boardState.map((row, rowIndex) => (
                <div key={rowIndex} className="flex h-[12.5%]">
                  {row.map((piece, colIndex) => {
                    const isLight = (rowIndex + colIndex) % 2 === 0
                    const squareKey = `${rowIndex}-${colIndex}`
                    const isEditingSquare = editingSquare === squareKey
                    const squareNotation = getSquareNotation(rowIndex, colIndex)

                    return (
                      <div
                        key={`${rowIndex}-${colIndex}`}
                        className={`relative w-[12.5%] h-full flex items-center justify-center text-lg sm:text-xl cursor-pointer transition-all select-none ${
                          isLight ? "bg-amber-100" : "bg-amber-800"
                        } ${isEditingSquare ? "ring-2 ring-blue-500 ring-inset" : ""} ${
                          isEditingSquare && isLight ? "bg-amber-200" : ""
                        } ${isEditingSquare && !isLight ? "bg-amber-700" : ""} ${
                          isEditing ? "hover:brightness-110" : ""
                        }`}
                        onClick={() => handleSquareClick(rowIndex, colIndex)}
                        title={`${squareNotation}${piece ? ` - ${piece}` : ""}`}
                      >
                        {piece && <span className="text-center leading-none">{pieceSymbols[piece]}</span>}

                        {/* Square coordinates for editing mode */}
                        {isEditingSquare && (
                          <div className="absolute bottom-0 right-0 text-[8px] bg-blue-600 text-white px-1 rounded-tl leading-none">
                            {squareNotation}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>

            {/* Piece Selection Palette */}
            {editingSquare && (
              <div className="absolute top-0 left-full ml-4 bg-slate-900 border border-slate-600 rounded-lg p-3 z-20 shadow-xl min-w-max">
                <h4 className="text-white text-sm font-medium mb-2">Select Piece:</h4>
                <div className="grid grid-cols-2 gap-2 w-24">
                  {pieceOptions.map((option) => {
                    const [row, col] = editingSquare.split("-").map(Number)
                    return (
                      <button
                        key={option.symbol || "empty"}
                        onClick={() => handlePieceSelect(option.symbol, row, col)}
                        className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg transition-all hover:scale-105 ${option.color}`}
                        title={option.display === "Empty" ? "Remove piece" : `Place ${option.display}`}
                      >
                        {option.display === "Empty" ? "✕" : option.display}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {/* FEN Display */}
          <div className="w-full p-3 bg-slate-900/50 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <p className="text-slate-400 text-sm">FEN Notation:</p>
              {hasChanges && (
                <Badge variant="secondary" className="bg-orange-600/20 text-orange-400 text-xs">
                  Modified
                </Badge>
              )}
            </div>
            <p className="text-slate-300 text-xs font-mono break-all leading-relaxed">
              {isEditing && hasChanges ? boardToFen(boardState) : fen}
            </p>
          </div>

          {/* Edit Instructions */}
          {isEditing && (
            <div className="w-full p-3 bg-blue-600/10 border border-blue-600/30 rounded-lg">
              <p className="text-blue-400 text-sm">
                💡 <strong>Editing Mode:</strong> Click any square to change the piece. Click the checkmark to save
                changes.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
