import { NextResponse } from "next/server"

const MCP_AUTH_TOKEN_KEY = "mcp_auth_token"
const SESSION_MAX_AGE = 60 * 60 * 24 * 7

function isHttpsRequest(request) {
  const forwardedProto = request.headers.get("x-forwarded-proto")
  if (forwardedProto) return forwardedProto.split(",")[0].trim() === "https"
  return new URL(request.url).protocol === "https:"
}

function cookieOptions(request) {
  return {
    httpOnly: true,
    sameSite: "lax",
    secure: isHttpsRequest(request),
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
  response.cookies.set(MCP_AUTH_TOKEN_KEY, token, cookieOptions(request))
  return response
}

export async function GET(request) {
  const authenticated = Boolean(request.cookies.get(MCP_AUTH_TOKEN_KEY)?.value)
  return NextResponse.json({ authenticated }, { status: 200 })
}

export async function DELETE(request) {
  const response = NextResponse.json({ success: true }, { status: 200 })
  response.cookies.set(MCP_AUTH_TOKEN_KEY, "", {
    ...cookieOptions(request),
    maxAge: 0,
  })
  return response
}
