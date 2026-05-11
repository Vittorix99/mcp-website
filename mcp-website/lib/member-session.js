const DEFAULT_MEMBER_REDIRECT = "/dashboard"

export function getSafeMemberRedirect(value, fallback = DEFAULT_MEMBER_REDIRECT) {
  if (typeof value !== "string") return fallback

  const trimmed = value.trim()
  if (!trimmed || trimmed.startsWith("//")) return fallback

  try {
    const baseOrigin =
      typeof window !== "undefined" ? window.location.origin : "https://musiconnectingpeople.com"
    const url = new URL(trimmed, baseOrigin)
    if (url.origin !== baseOrigin) return fallback
    return `${url.pathname}${url.search}${url.hash}` || fallback
  } catch {
    return fallback
  }
}

export function getCurrentMemberRedirect(fallback = DEFAULT_MEMBER_REDIRECT) {
  if (typeof window === "undefined") return fallback

  const params = new URLSearchParams(window.location.search)
  return getSafeMemberRedirect(params.get("redirect"), fallback)
}

export function redirectNeedsServerSession(redirect) {
  const target = getSafeMemberRedirect(redirect)
  return /^\/events\/[^/]+\/guide(\/|$)/.test(target)
}

export async function persistMemberSession(user) {
  if (!user) throw new Error("Missing Firebase user")

  const token = await user.getIdToken()
  const response = await fetch("/api/auth/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
    cache: "no-store",
    credentials: "same-origin",
  })

  if (!response.ok) {
    throw new Error("Unable to persist member session")
  }
}

export async function verifyMemberSessionCookie() {
  const check = await fetch("/api/auth/session", {
    method: "GET",
    cache: "no-store",
    credentials: "same-origin",
  })
  const payload = await check.json().catch(() => null)

  if (!check.ok || !payload?.authenticated) {
    throw new Error("Member session cookie was not stored")
  }
}

export async function persistVerifiedMemberSession(user) {
  await persistMemberSession(user)
  await verifyMemberSessionCookie()
}

export async function clearMemberSession() {
  await fetch("/api/auth/session", {
    method: "DELETE",
    cache: "no-store",
    credentials: "same-origin",
  })
}

export function replaceWithMemberRedirect(redirect) {
  const target = getSafeMemberRedirect(redirect)
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
  if (current === target) return
  window.location.replace(target)
}
