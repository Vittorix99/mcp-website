import { NextResponse } from "next/server"

const MCP_AUTH_TOKEN_KEY = "mcp_auth_token"
const SESSION_MAX_AGE = 60 * 60 * 24 * 7

function cookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  }
}

export async function POST(request) {
  const body = await request.json().catch(() => ({}))
  const token = typeof body?.token === "string" ? body.token.trim() : ""

  if (!token) {
    return NextResponse.json({ error: "Token missing" }, { status: 400 })
  }

  const response = NextResponse.json({ success: true }, { status: 200 })
  response.cookies.set(MCP_AUTH_TOKEN_KEY, token, cookieOptions())
  return response
}

export async function DELETE() {
  const response = NextResponse.json({ success: true }, { status: 200 })
  response.cookies.set(MCP_AUTH_TOKEN_KEY, "", {
    ...cookieOptions(),
    maxAge: 0,
  })
  return response
}
