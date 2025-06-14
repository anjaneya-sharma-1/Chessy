"use client"

import { useState, useRef, useEffect } from "react"
import { Camera, CameraOff, Lightbulb, LightbulbOff, ArrowLeft, AlertTriangle, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import EditableChessBoard from "@/components/editable-chess-board"
import MoveHistory, { type GameMove } from "@/components/move-history"

export default function LiveFeedPage() {
  const [isStreaming, setIsStreaming] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [currentFen, setCurrentFen] = useState("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
  const [detectedFen, setDetectedFen] = useState("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
  const [suggestedMove, setSuggestedMove] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [hasManualEdits, setHasManualEdits] = useState(false)
  const [detectionConfidence, setDetectionConfidence] = useState(0)
  const [lastDetectionTime, setLastDetectionTime] = useState<Date | null>(null)

  // Move history state
  const [gameHistory, setGameHistory] = useState<GameMove[]>([])
  const [currentMoveIndex, setCurrentMoveIndex] = useState(-1)
  const [isLiveMode, setIsLiveMode] = useState(true)
  const [moveCounter, setMoveCounter] = useState(1)
  const [isWhiteTurn, setIsWhiteTurn] = useState(true)

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // Helper function to detect if position changed significantly
  const hasPositionChanged = (oldFen: string, newFen: string) => {
    if (!oldFen || !newFen) return true

    // Compare just the board position part (before the first space)
    const oldBoard = oldFen.split(" ")[0]
    const newBoard = newFen.split(" ")[0]

    return oldBoard !== newBoard
  }

  // Helper function to generate simple move notation
  const generateMoveNotation = (fromFen: string, toFen: string) => {
    // This is a simplified move notation generator
    // In a real implementation, you'd use a chess library to generate proper algebraic notation
    const fromBoard = fromFen.split(" ")[0]
    const toBoard = toFen.split(" ")[0]

    if (fromBoard === toBoard) return undefined

    // For now, just return a placeholder - you could integrate with chess.js for proper notation
    return `Move ${gameHistory.length + 1}`
  }

  const addMoveToHistory = (fen: string, isManualEdit = false, confidence?: number) => {
    const newMove: GameMove = {
      id: `${Date.now()}-${Math.random()}`,
      fen,
      timestamp: new Date(),
      confidence,
      isManualEdit,
      moveNumber: moveCounter,
      isWhiteMove: isWhiteTurn,
      moveNotation:
        gameHistory.length > 0 ? generateMoveNotation(gameHistory[gameHistory.length - 1].fen, fen) : undefined,
    }

    setGameHistory((prev) => [...prev, newMove])
    setCurrentMoveIndex((prev) => prev + 1)

    // Update move counter and turn
    if (isWhiteTurn) {
      setIsWhiteTurn(false)
    } else {
      setIsWhiteTurn(true)
      setMoveCounter((prev) => prev + 1)
    }
  }

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
        setIsStreaming(true)

        // Add initial position to history if it's the first time
        if (gameHistory.length === 0) {
          addMoveToHistory(currentFen, false, 1.0)
        }
      }
    } catch (error) {
      console.error("Error accessing camera:", error)
      alert("Unable to access camera. Please check permissions.")
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsStreaming(false)
  }

  const captureFrame = async () => {
    if (!videoRef.current || !canvasRef.current || !isLiveMode) return

    const canvas = canvasRef.current
    const video = videoRef.current
    const ctx = canvas.getContext("2d")

    if (!ctx) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    ctx.drawImage(video, 0, 0)

    canvas.toBlob(
      async (blob) => {
        if (!blob) return

        setIsProcessing(true)

        try {
          const formData = new FormData()
          formData.append("image", blob)

          const response = await fetch("/api/detect-chess-position", {
            method: "POST",
            body: formData,
          })

          if (response.ok) {
            const data = await response.json()
            setDetectedFen(data.fen)
            setDetectionConfidence(data.confidence || 0)
            setLastDetectionTime(new Date())

            // Check if position has changed significantly
            if (hasPositionChanged(currentFen, data.fen) && !hasManualEdits) {
              setCurrentFen(data.fen)
              addMoveToHistory(data.fen, false, data.confidence)
            }

            if (showSuggestions && data.suggestedMove) {
              setSuggestedMove(data.suggestedMove)
            }
          }
        } catch (error) {
          console.error("Error processing frame:", error)
        } finally {
          setIsProcessing(false)
        }
      },
      "image/jpeg",
      0.8,
    )
  }

  const handleFenChange = (newFen: string) => {
    setCurrentFen(newFen)
    setHasManualEdits(true)

    // Add manual edit to history if in live mode
    if (isLiveMode) {
      addMoveToHistory(newFen, true)
    }

    // Get new move suggestion for edited position
    if (showSuggestions) {
      getMovesuggestion(newFen)
    }
  }

  const handleMoveSelect = (index: number) => {
    if (index >= 0 && index < gameHistory.length) {
      setCurrentMoveIndex(index)
      setCurrentFen(gameHistory[index].fen)
      setIsLiveMode(false) // Switch to review mode when navigating history
    }
  }

  const handleToggleLiveMode = () => {
    if (!isLiveMode) {
      // Switching back to live mode - go to latest position
      if (gameHistory.length > 0) {
        const latestIndex = gameHistory.length - 1
        setCurrentMoveIndex(latestIndex)
        setCurrentFen(gameHistory[latestIndex].fen)
      }
      setHasManualEdits(false)
    }
    setIsLiveMode(!isLiveMode)
  }

  const handleClearHistory = () => {
    if (confirm("Are you sure you want to clear the game history? This cannot be undone.")) {
      setGameHistory([])
      setCurrentMoveIndex(-1)
      setMoveCounter(1)
      setIsWhiteTurn(true)
      setCurrentFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
      setHasManualEdits(false)
    }
  }

  const getMovesuggestion = async (fen: string) => {
    try {
      const response = await fetch("/api/analyze-position", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fen }),
      })

      if (response.ok) {
        const data = await response.json()
        setSuggestedMove(data.suggestedMove || "")
      }
    } catch (error) {
      console.error("Error getting move suggestion:", error)
    }
  }

  const acceptDetectedPosition = () => {
    setCurrentFen(detectedFen)
    setHasManualEdits(false)

    if (hasPositionChanged(currentFen, detectedFen)) {
      addMoveToHistory(detectedFen, false, detectionConfidence)
    }
  }

  const saveCurrentPosition = () => {
    const gameData = {
      history: gameHistory,
      currentPosition: currentFen,
      timestamp: new Date().toISOString(),
      moveCount: gameHistory.length,
    }

    localStorage.setItem(`chess-game-${Date.now()}`, JSON.stringify(gameData))

    alert("Game saved successfully!")
  }

  useEffect(() => {
    let interval: NodeJS.Timeout

    if (isStreaming && isLiveMode) {
      interval = setInterval(captureFrame, 3000) // Capture every 3 seconds
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isStreaming, showSuggestions, hasManualEdits, isLiveMode, currentFen])

  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="flex items-center mb-8">
          <Link href="/">
            <Button variant="ghost" className="text-white hover:bg-slate-800">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>

        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Live Feed Monitoring</h1>
          <p className="text-slate-300">Real-time chess board detection with move history</p>
        </div>

        {/* Manual Edit Alert */}
        {hasManualEdits && isLiveMode && (
          <Alert className="mb-6 bg-orange-600/20 border-orange-600/30">
            <AlertTriangle className="h-4 w-4 text-orange-400" />
            <AlertDescription className="text-orange-300">
              <strong>Manual edits active:</strong> Position detection is paused. The board shows your edited position.
              <Button
                onClick={acceptDetectedPosition}
                variant="outline"
                size="sm"
                className="ml-3 text-orange-300 border-orange-600 hover:bg-orange-600/20"
              >
                Accept Latest Detection
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Review Mode Alert */}
        {!isLiveMode && (
          <Alert className="mb-6 bg-blue-600/20 border-blue-600/30">
            <AlertTriangle className="h-4 w-4 text-blue-400" />
            <AlertDescription className="text-blue-300">
              <strong>Review Mode:</strong> You're viewing move history. Live detection is paused.
            </AlertDescription>
          </Alert>
        )}

        <div className="grid xl:grid-cols-3 lg:grid-cols-2 gap-6">
          {/* Camera Feed */}
          <div className="xl:col-span-1">
            <Card className="bg-slate-800/50 border-slate-700 h-fit">
              <CardHeader className="pb-4">
                <CardTitle className="text-white flex items-center justify-between text-lg">
                  <div className="flex items-center gap-3">
                    Camera Feed
                    {lastDetectionTime && (
                      <div className="text-sm text-slate-400">{lastDetectionTime.toLocaleTimeString()}</div>
                    )}
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2">
                      <Switch id="suggestions" checked={showSuggestions} onCheckedChange={setShowSuggestions} />
                      <Label htmlFor="suggestions" className="text-white flex items-center text-sm">
                        {showSuggestions ? (
                          <Lightbulb className="w-4 h-4 mr-1" />
                        ) : (
                          <LightbulbOff className="w-4 h-4 mr-1" />
                        )}
                        AI
                      </Label>
                    </div>
                    <Button
                      onClick={isStreaming ? stopCamera : startCamera}
                      variant={isStreaming ? "destructive" : "default"}
                      size="sm"
                    >
                      {isStreaming ? <CameraOff className="w-4 h-4 mr-2" /> : <Camera className="w-4 h-4 mr-2" />}
                      {isStreaming ? "Stop" : "Start"}
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                <div className="relative bg-black rounded-lg overflow-hidden mb-4">
                  <video ref={videoRef} autoPlay playsInline muted className="w-full h-auto max-h-64 object-contain" />
                  {!isStreaming && (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-900">
                      <div className="text-center text-slate-400">
                        <Camera className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p className="text-sm">Click "Start" to begin monitoring</p>
                      </div>
                    </div>
                  )}
                  {isProcessing && (
                    <div className="absolute top-4 right-4 bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
                      Processing...
                    </div>
                  )}
                </div>
                <canvas ref={canvasRef} className="hidden" />

                {/* Detection Info */}
                {detectionConfidence > 0 && (
                  <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                    <div className="text-sm text-slate-400">
                      Confidence: <span className="text-white">{(detectionConfidence * 100).toFixed(1)}%</span>
                    </div>
                    <Button
                      onClick={saveCurrentPosition}
                      variant="outline"
                      size="sm"
                      className="text-white border-slate-600"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      Save
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Editable Digital Board */}
          <div className="xl:col-span-1">
            <EditableChessBoard
              fen={currentFen}
              onFenChange={handleFenChange}
              title="Digital Board"
              showEditControls={isLiveMode}
            />
          </div>

          {/* Move History */}
          <div className="xl:col-span-1 lg:col-span-2 xl:col-span-1">
            <MoveHistory
              moves={gameHistory}
              currentMoveIndex={currentMoveIndex}
              onMoveSelect={handleMoveSelect}
              onClearHistory={handleClearHistory}
              isLiveMode={isLiveMode}
              onToggleLiveMode={handleToggleLiveMode}
            />
          </div>
        </div>

        {/* Move Suggestions */}
        {showSuggestions && suggestedMove && (
          <Card className="mt-6 bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-white text-lg">Move Suggestion</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="bg-green-600/20 border border-green-600/30 rounded-lg p-4">
                <p className="text-green-400 font-medium text-lg">Suggested Move: {suggestedMove}</p>
                <p className="text-green-300 text-sm mt-1">
                  {hasManualEdits
                    ? "Based on your edited position"
                    : !isLiveMode
                      ? "Based on selected historical position"
                      : "Based on detected position"}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Detected vs Current Position Comparison */}
        {hasManualEdits && isLiveMode && (
          <Card className="mt-6 bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-white text-lg">Position Comparison</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-slate-400 text-sm mb-2">Latest Detection:</h4>
                  <div className="p-3 bg-slate-900/50 rounded-lg">
                    <p className="text-slate-300 text-xs font-mono break-all">{detectedFen}</p>
                  </div>
                </div>
                <div>
                  <h4 className="text-slate-400 text-sm mb-2">Current (Edited):</h4>
                  <div className="p-3 bg-blue-900/50 rounded-lg">
                    <p className="text-blue-300 text-xs font-mono break-all">{currentFen}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
