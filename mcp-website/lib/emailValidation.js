const COMMON_EMAIL_DOMAINS = [
  "gmail.com",
  "yahoo.com",
  "hotmail.com",
  "icloud.com",
  "outlook.com",
  "libero.it",
  "virgilio.it",
]

function levenshteinDistance(a, b) {
  const source = String(a || "")
  const target = String(b || "")
  if (source === target) return 0
  if (!source.length) return target.length
  if (!target.length) return source.length

  const rows = source.length + 1
  const cols = target.length + 1
  const matrix = Array.from({ length: rows }, () => Array(cols).fill(0))

  for (let i = 0; i < rows; i += 1) matrix[i][0] = i
  for (let j = 0; j < cols; j += 1) matrix[0][j] = j

  for (let i = 1; i < rows; i += 1) {
    for (let j = 1; j < cols; j += 1) {
      const cost = source[i - 1] === target[j - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost,
      )
    }
  }

  return matrix[source.length][target.length]
}

export function detectEmailTypo(email) {
  if (!email || typeof email !== "string") return null
  const normalized = email.trim().toLowerCase()
  const atIndex = normalized.lastIndexOf("@")
  if (atIndex <= 0 || atIndex === normalized.length - 1) return null

  const typedDomain = normalized.slice(atIndex + 1)
  if (!typedDomain.includes(".")) return null
  if (COMMON_EMAIL_DOMAINS.includes(typedDomain)) return null

  let bestDomain = null
  let bestDistance = Number.POSITIVE_INFINITY

  COMMON_EMAIL_DOMAINS.forEach((domain) => {
    const distance = levenshteinDistance(typedDomain, domain)
    if (distance < bestDistance) {
      bestDistance = distance
      bestDomain = domain
    }
  })

  if (!bestDomain || bestDistance < 1 || bestDistance > 2) return null
  return {
    typedDomain,
    suggestedDomain: bestDomain,
    suggestedEmail: `${normalized.slice(0, atIndex)}@${bestDomain}`,
    distance: bestDistance,
  }
}

export { COMMON_EMAIL_DOMAINS, levenshteinDistance }
