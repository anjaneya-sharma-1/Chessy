"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { ChevronLeft, ChevronRight, SkipBack, SkipForward, Play, Pause, RotateCcw, Download, Clock } from "lucide-react"

export interface GameMove {
  id: string
  fen: string
  moveNotation?: string
  timestamp: Date
  confidence?: number
  isManualEdit?: boolean
  moveNumber: number
  isWhiteMove: boolean
}

interface MoveHistoryProps {
  moves: GameMove[]
  currentMoveIndex: number
  onMoveSelect: (index: number) => void
  onClearHistory: () => void
  isLiveMode?: boolean
  onToggleLiveMode?: () => void
}

export default function MoveHistory({
  moves,
  currentMoveIndex,
  onMoveSelect,
  onClearHistory,
  isLiveMode = true,
  onToggleLiveMode,
}: MoveHistoryProps) {
  const [autoPlay, setAutoPlay] = useState(false)
  const [autoPlaySpeed, setAutoPlaySpeed] = useState(2000) // 2 seconds

  // Auto-play functionality
  useEffect(() => {
    if (!autoPlay || currentMoveIndex >= moves.length - 1) {
      setAutoPlay(false)
      return
    }

    const timer = setTimeout(() => {
      onMoveSelect(currentMoveIndex + 1)
    }, autoPlaySpeed)

    return () => clearTimeout(timer)
  }, [autoPlay, currentMoveIndex, moves.length, autoPlaySpeed, onMoveSelect])

  const goToFirstMove = () => {
    if (moves.length > 0) {
      onMoveSelect(0)
    }
  }

  const goToPreviousMove = () => {
    if (currentMoveIndex > 0) {
      onMoveSelect(currentMoveIndex - 1)
    }
  }

  const goToNextMove = () => {
    if (currentMoveIndex < moves.length - 1) {
      onMoveSelect(currentMoveIndex + 1)
    }
  }

  const goToLastMove = () => {
    if (moves.length > 0) {
      onMoveSelect(moves.length - 1)
    }
  }

  const toggleAutoPlay = () => {
    setAutoPlay(!autoPlay)
  }

  const exportGamePGN = () => {
    if (moves.length === 0) return

    let pgn = '[Event "Live Chess Detection"]\n'
    pgn += `[Date "${new Date().toISOString().split("T")[0]}"]\n`
    pgn += '[White "Player"]\n'
    pgn += '[Black "Player"]\n'
    pgn += '[Result "*"]\n\n'

    // Add moves in PGN format
    let moveText = ""
    for (let i = 0; i < moves.length; i++) {
      const move = moves[i]
      if (move.isWhiteMove) {
        moveText += `${move.moveNumber}. `
      }
      if (move.moveNotation) {
        moveText += `${move.moveNotation} `
      }
      if (i % 6 === 5) moveText += "\n" // Line break every 6 moves
    }

    pgn += moveText + "*"

    // Download PGN file
    const blob = new Blob([pgn], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `chess-game-${new Date().toISOString().split("T")[0]}.pgn`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
  }

  const getCurrentMove = () => {
    return moves[currentMoveIndex]
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Game History
            <Badge variant="secondary" className="bg-slate-700 text-slate-300">
              {moves.length} moves
            </Badge>
          </CardTitle>
          <div className="flex items-center gap-2">
            {onToggleLiveMode && (
              <Button
                onClick={onToggleLiveMode}
                variant={isLiveMode ? "default" : "outline"}
                size="sm"
                className={isLiveMode ? "bg-green-600 hover:bg-green-700" : "text-white border-slate-600"}
              >
                {isLiveMode ? "Live" : "Review"}
              </Button>
            )}
            <Button
              onClick={exportGamePGN}
              variant="outline"
              size="sm"
              className="text-white border-slate-600"
              disabled={moves.length === 0}
            >
              <Download className="w-4 h-4" />
            </Button>
            <Button
              onClick={onClearHistory}
              variant="outline"
              size="sm"
              className="text-red-400 border-red-600 hover:bg-red-600/20"
              disabled={moves.length === 0}
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Navigation Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Button
              onClick={goToFirstMove}
              variant="outline"
              size="sm"
              disabled={currentMoveIndex === 0 || moves.length === 0}
              className="text-white border-slate-600"
            >
              <SkipBack className="w-4 h-4" />
            </Button>
            <Button
              onClick={goToPreviousMove}
              variant="outline"
              size="sm"
              disabled={currentMoveIndex === 0 || moves.length === 0}
              className="text-white border-slate-600"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              onClick={toggleAutoPlay}
              variant="outline"
              size="sm"
              disabled={moves.length === 0 || currentMoveIndex >= moves.length - 1}
              className="text-white border-slate-600"
            >
              {autoPlay ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
            <Button
              onClick={goToNextMove}
              variant="outline"
              size="sm"
              disabled={currentMoveIndex >= moves.length - 1 || moves.length === 0}
              className="text-white border-slate-600"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button
              onClick={goToLastMove}
              variant="outline"
              size="sm"
              disabled={currentMoveIndex >= moves.length - 1 || moves.length === 0}
              className="text-white border-slate-600"
            >
              <SkipForward className="w-4 h-4" />
            </Button>
          </div>

          <div className="text-sm text-slate-400">
            {moves.length > 0 ? `Move ${currentMoveIndex + 1} of ${moves.length}` : "No moves recorded"}
          </div>
        </div>

        {/* Current Move Info */}
        {getCurrentMove() && (
          <div className="p-3 bg-slate-900/50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="bg-blue-600 text-white">
                  Move {getCurrentMove().moveNumber}
                </Badge>
                {getCurrentMove().isManualEdit && (
                  <Badge variant="secondary" className="bg-orange-600 text-white">
                    Edited
                  </Badge>
                )}
              </div>
              <div className="text-xs text-slate-400">{formatTime(getCurrentMove().timestamp)}</div>
            </div>
            <div className="text-sm">
              <div className="text-slate-400">FEN:</div>
              <div className="text-slate-300 font-mono text-xs break-all">{getCurrentMove().fen}</div>
              {getCurrentMove().confidence && (
                <div className="text-slate-400 mt-1">
                  Confidence: <span className="text-white">{(getCurrentMove().confidence! * 100).toFixed(1)}%</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Move List */}
        <ScrollArea className="h-64">
          <div className="space-y-1">
            {moves.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No moves recorded yet</p>
                <p className="text-xs">Start the camera to begin recording</p>
              </div>
            ) : (
              moves.map((move, index) => (
                <div
                  key={move.id}
                  onClick={() => onMoveSelect(index)}
                  className={`p-2 rounded-lg cursor-pointer transition-all ${
                    index === currentMoveIndex
                      ? "bg-blue-600/30 border border-blue-600/50"
                      : "bg-slate-900/30 hover:bg-slate-900/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        className={`text-xs ${move.isWhiteMove ? "bg-white text-black" : "bg-gray-800 text-white"}`}
                      >
                        {move.moveNumber}
                        {move.isWhiteMove ? "." : "..."}
                      </Badge>
                      {move.moveNotation && <span className="text-white font-medium">{move.moveNotation}</span>}
                      {move.isManualEdit && (
                        <Badge variant="secondary" className="bg-orange-600/20 text-orange-400 text-xs">
                          Edit
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {move.confidence && (
                        <span className="text-xs text-slate-400">{(move.confidence * 100).toFixed(0)}%</span>
                      )}
                      <span className="text-xs text-slate-500">{formatTime(move.timestamp)}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {/* Auto-play Speed Control */}
        {autoPlay && (
          <div className="p-3 bg-blue-600/10 border border-blue-600/30 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-400 text-sm">Auto-play Speed</span>
              <span className="text-blue-300 text-sm">{autoPlaySpeed / 1000}s per move</span>
            </div>
            <input
              type="range"
              min="500"
              max="5000"
              step="500"
              value={autoPlaySpeed}
              onChange={(e) => setAutoPlaySpeed(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
