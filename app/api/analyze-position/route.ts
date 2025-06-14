import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    if (!body.fen) {
      return NextResponse.json({ error: "FEN notation required" }, { status: 400 })
    }

    // Forward the request to Python backend
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
    const response = await fetch(`${backendUrl}/api/analyze-position`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error("Error analyzing position:", error)
    return NextResponse.json(
      { error: "Failed to analyze position", details: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    )
  }
}
