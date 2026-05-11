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

export async function persistMemberSession(user) {
  if (!user) throw new Error("Missing Firebase user")

  const token = await user.getIdToken()
  const response = await fetch("/api/auth/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error("Unable to persist member session")
  }
}

export async function clearMemberSession() {
  await fetch("/api/auth/session", {
    method: "DELETE",
    cache: "no-store",
  })
}

export function replaceWithMemberRedirect(redirect) {
  window.location.replace(getSafeMemberRedirect(redirect))
}
