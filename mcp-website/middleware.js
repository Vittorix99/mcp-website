import { NextResponse } from "next/server"

const MCP_AUTH_TOKEN_KEY = "mcp_auth_token"

export function middleware(request) {
  const { pathname } = request.nextUrl

  const requiresAuth =
    pathname.startsWith("/dashboard") ||
    /^\/events\/[^/]+\/guide(\/|$)/.test(pathname)

  if (requiresAuth) {
    const token = request.cookies.get(MCP_AUTH_TOKEN_KEY)?.value
    if (!token) {
      const loginUrl = new URL("/login", request.url)
      loginUrl.searchParams.set("redirect", pathname)
      return NextResponse.redirect(loginUrl)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*", "/events/:slug/guide"],
}
