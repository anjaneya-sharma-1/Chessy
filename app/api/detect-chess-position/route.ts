import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const image = formData.get("image") as File

    if (!image) {
      return NextResponse.json({ error: "No image provided" }, { status: 400 })
    }

    // Forward the request to Python backend
    const backendFormData = new FormData()
    backendFormData.append("image", image)

    const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000"
    const response = await fetch(`${backendUrl}/api/detect-chess-position`, {
      method: "POST",
      body: backendFormData,
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error("Error processing chess position:", error)
    return NextResponse.json(
      { error: "Failed to process image", details: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    )
  }
}
