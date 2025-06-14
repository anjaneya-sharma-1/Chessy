"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Upload, Camera, ArrowLeft, Play, AlertTriangle, Save, Share2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import EditableChessBoard from "@/components/editable-chess-board"

export default function OfflineModePage() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [detectedFen, setDetectedFen] = useState("")
  const [currentFen, setCurrentFen] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [gameReady, setGameReady] = useState(false)
  const [hasManualEdits, setHasManualEdits] = useState(false)
  const [detectionConfidence, setDetectionConfidence] = useState(0)
  const [processingError, setProcessingError] = useState<string | null>(null)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isCameraActive, setIsCameraActive] = useState(false)

  // Cleanup camera on component unmount
  useEffect(() => {
    return () => {
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
        tracks.forEach(track => track.stop())
      }
    }
  }, [])

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedImage(URL.createObjectURL(file))
      processImage(file)
    }
  }

  const startCamera = async () => {
    try {
      setCameraError(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera if available
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      })
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setIsCameraActive(true)
      }
    } catch (error) {
      console.error('Error accessing camera:', error)
      setCameraError('Camera access denied. Please allow camera access in your browser settings.')
    }
  }

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
      tracks.forEach(track => track.stop())
      videoRef.current.srcObject = null
      setIsCameraActive(false)
    }
  }

  const captureImage = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas')
      canvas.width = videoRef.current.videoWidth
      canvas.height = videoRef.current.videoHeight
      const ctx = canvas.getContext('2d')
      
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0)
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' })
            setSelectedImage(URL.createObjectURL(blob))
            processImage(file)
            stopCamera()
          }
        }, 'image/jpeg')
      }
    }
  }

  const processImage = async (file: File) => {
    setIsProcessing(true)
    setGameReady(false)
    setProcessingError(null)
    setHasManualEdits(false)

    try {
      const formData = new FormData()
      formData.append('image', file)

      const response = await fetch('/api/detect-chess-position', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        setDetectedFen(data.fen)
        setCurrentFen(data.fen)
        setDetectionConfidence(data.confidence || 0)
        setGameReady(true)
      } else {
        throw new Error(data.error || "Failed to process image")
      }
    } catch (error) {
      console.error("Error processing image:", error)
      setProcessingError(error instanceof Error ? error.message : "Unknown error occurred")

      // Set a default starting position so user can still edit
      const defaultFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
      setDetectedFen(defaultFen)
      setCurrentFen(defaultFen)
      setGameReady(true)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleFenChange = (newFen: string) => {
    setCurrentFen(newFen)
    setHasManualEdits(true)
    setGameReady(true)
  }

  const acceptDetectedPosition = () => {
    setCurrentFen(detectedFen)
    setHasManualEdits(false)
  }

  const startOnlineGame = () => {
    const chessComUrl = `https://www.chess.com/analysis?fen=${encodeURIComponent(currentFen)}`
    window.open(chessComUrl, "_blank")
  }

  const startLichessGame = () => {
    const lichessUrl = `https://lichess.org/analysis/${encodeURIComponent(currentFen)}`
    window.open(lichessUrl, "_blank")
  }

  const sharePosition = async () => {
    try {
      await navigator.share({
        title: "Chess Position",
        text: `Check out this chess position: ${currentFen}`,
        url: `https://lichess.org/analysis/${encodeURIComponent(currentFen)}`,
      })
    } catch (error) {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(currentFen)
      alert("Position FEN copied to clipboard!")
    }
  }

  const savePosition = () => {
    const savedPositions = JSON.parse(localStorage.getItem("savedChessPositions") || "[]")
    const newPosition = {
      id: Date.now(),
      fen: currentFen,
      timestamp: new Date().toISOString(),
      confidence: detectionConfidence,
      hasManualEdits,
      image: selectedImage,
    }

    savedPositions.push(newPosition)
    localStorage.setItem("savedChessPositions", JSON.stringify(savedPositions))
    alert("Position saved successfully!")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="flex items-center mb-8">
          <Link href="/">
            <Button variant="ghost" size="icon" className="mr-4">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">Offline Mode</h1>
            <p className="text-slate-300">Convert chess board images to playable online games</p>
          </div>
        </div>

        {/* Processing Error Alert */}
        {processingError && (
          <Alert className="mb-6 bg-red-600/20 border-red-600/30">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <AlertDescription className="text-red-300">
              <strong>Detection failed:</strong> {processingError}. You can still manually set up the position below.
            </AlertDescription>
          </Alert>
        )}

        {/* Manual Edit Alert */}
        {hasManualEdits && !processingError && (
          <Alert className="mb-6 bg-orange-600/20 border-orange-600/30">
            <AlertTriangle className="h-4 w-4 text-orange-400" />
            <AlertDescription className="text-orange-300">
              <strong>Position edited:</strong> You've modified the detected position.
              <Button
                onClick={acceptDetectedPosition}
                variant="outline"
                size="sm"
                className="ml-3 text-orange-300 border-orange-600 hover:bg-orange-600/20"
              >
                Restore Detected Position
              </Button>
            </AlertDescription>
          </Alert>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Image Upload */}
          <Card className="bg-slate-800/50 border-slate-700 h-fit">
            <CardHeader className="pb-4">
              <CardTitle className="text-white text-lg">Upload Chess Board Image</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="space-y-4">
                <div
                  className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center hover:border-slate-500 transition-colors cursor-pointer"
                  onClick={() => !isCameraActive && fileInputRef.current?.click()}
                >
                  {selectedImage ? (
                    <div className="space-y-4">
                      <img
                        src={selectedImage}
                        alt="Uploaded chess board"
                        className="max-w-full max-h-48 mx-auto rounded-lg object-contain"
                      />
                      <p className="text-slate-300 text-sm">Click to upload a different image</p>
                    </div>
                  ) : isCameraActive ? (
                    <div className="space-y-4">
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        className="max-w-full max-h-48 mx-auto rounded-lg"
                      />
                      <Button onClick={captureImage} className="bg-green-600 hover:bg-green-700">
                        <Camera className="w-4 h-4 mr-2" />
                        Capture Image
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="w-16 h-16 mx-auto bg-slate-700 rounded-lg flex items-center justify-center">
                        <Upload className="w-8 h-8 text-slate-400" />
                      </div>
                      <p className="text-slate-300">Click to upload an image or take a photo</p>
                    </div>
                  )}
                </div>

                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageUpload}
                  accept="image/*"
                  className="hidden"
                />

                <div className="flex space-x-2">
                  <Button 
                    onClick={() => fileInputRef.current?.click()} 
                    className="flex-1" 
                    variant="outline"
                    disabled={isCameraActive}
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload from Gallery
                  </Button>
                  <Button 
                    onClick={isCameraActive ? stopCamera : startCamera} 
                    className="flex-1" 
                    variant="outline"
                  >
                    <Camera className="w-4 h-4 mr-2" />
                    {isCameraActive ? "Stop Camera" : "Take Photo"}
                  </Button>
                </div>

                {cameraError && (
                  <div className="bg-red-600/20 border border-red-600/30 rounded-lg p-4 text-center">
                    <p className="text-red-400">{cameraError}</p>
                  </div>
                )}

                {isProcessing && (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto"></div>
                    <p className="text-slate-300 mt-2">Processing image...</p>
                  </div>
                )}

                {detectionConfidence > 0 && (
                  <div className="p-3 bg-slate-900/50 rounded-lg">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-400">Detection Confidence:</span>
                      <span className="text-white">{(detectionConfidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Editable Position */}
          {(gameReady || currentFen) && (
            <EditableChessBoard fen={currentFen} onFenChange={handleFenChange} title="Detected Position" />
          )}

          {/* Placeholder when no position detected */}
          {!gameReady && !currentFen && (
            <Card className="bg-slate-800/50 border-slate-700 h-fit">
              <CardHeader className="pb-4">
                <CardTitle className="text-white text-lg">Detected Position</CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                <div className="text-center py-16">
                  <div className="w-16 h-16 mx-auto mb-4 bg-slate-700 rounded-lg flex items-center justify-center">
                    <Camera className="w-8 h-8 text-slate-400" />
                  </div>
                  <p className="text-slate-400">Upload an image to see the detected position</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action Buttons */}
        {gameReady && (
          <Card className="mt-8 bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-4">
              <CardTitle className="text-white text-lg">Start Playing Online</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <Button onClick={startOnlineGame} className="w-full bg-green-600 hover:bg-green-700">
                    <Play className="w-4 h-4 mr-2" />
                    Analyze on Chess.com
                  </Button>
                  <Button onClick={startLichessGame} className="w-full bg-blue-600 hover:bg-blue-700">
                    <Play className="w-4 h-4 mr-2" />
                    Analyze on Lichess
                  </Button>
                </div>
                <div className="space-y-3">
                  <Button onClick={savePosition} variant="outline" className="w-full text-white border-slate-600">
                    <Save className="w-4 h-4 mr-2" />
                    Save Position
                  </Button>
                  <Button onClick={sharePosition} variant="outline" className="w-full text-white border-slate-600">
                    <Share2 className="w-4 h-4 mr-2" />
                    Share Position
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Position Comparison */}
        {hasManualEdits && detectedFen && (
          <Card className="mt-8 bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-4">
              <CardTitle className="text-white text-lg">Position Comparison</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-slate-400 text-sm mb-2">Original Detection:</h4>
                  <div className="p-3 bg-slate-900/50 rounded-lg">
                    <p className="text-slate-300 text-xs font-mono break-all">{detectedFen}</p>
                  </div>
                </div>
                <div>
                  <h4 className="text-slate-400 text-sm mb-2">Your Edited Version:</h4>
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
