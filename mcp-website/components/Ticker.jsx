"use client"

export function Ticker({ items = [], color = "#E07800", speed = 38 }) {
  const text = items.join("  ·  ") + "  ·  "
  return (
    <div style={{ overflow: "hidden", whiteSpace: "nowrap", padding: "10px 0", background: "transparent" }}>
      <span style={{
        display: "inline-block",
        animation: `ticker ${speed}s linear infinite`,
        fontFamily: "var(--font-helvetica), Helvetica, Arial, sans-serif",
        fontWeight: 700,
        fontSize: "10px",
        letterSpacing: "0.28em",
        textTransform: "uppercase",
        color,
      }}>
        {text}{text}{text}{text}
      </span>
    </div>
  )
}
