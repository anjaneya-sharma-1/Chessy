import Link from "next/link"
import { Camera, Upload, ChevronRight } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-white mb-4">Chess Vision AI</h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Convert real chess boards to digital format using computer vision. Monitor live games or upload images to
            start playing online.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-all duration-300 group">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4 group-hover:bg-blue-500 transition-colors">
                <Camera className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl text-white">Live Feed Monitoring</CardTitle>
              <CardDescription className="text-slate-300">
                Real-time chess board detection with move suggestions
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-slate-300 space-y-2 mb-6 text-left">
                <li>• Live camera feed analysis</li>
                <li>• Real-time FEN notation detection</li>
                <li>• Synchronized digital board</li>
                <li>• AI move suggestions</li>
              </ul>
              <Link href="/live-feed">
                <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                  Start Live Monitoring
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-all duration-300 group">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mb-4 group-hover:bg-green-500 transition-colors">
                <Upload className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl text-white">Offline to Online</CardTitle>
              <CardDescription className="text-slate-300">
                Convert chess board images to playable online games
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-slate-300 space-y-2 mb-6 text-left">
                <li>• Upload or capture board images</li>
                <li>• Automatic piece detection</li>
                <li>• Generate playable position</li>
                <li>• Continue game online</li>
              </ul>
              <Link href="/offline-mode">
                <Button className="w-full bg-green-600 hover:bg-green-700 text-white">
                  Upload Board Image
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <div className="text-center mt-16">
          <p className="text-slate-400">Powered by computer vision and chess AI</p>
        </div>
      </div>
    </div>
  )
}
