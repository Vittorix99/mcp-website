const ACC = "#E07800"

export function SectionLabel({ text, accent = ACC }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "20px", marginBottom: "48px" }}>
      <div style={{ width: "36px", height: "1px", background: accent, flexShrink: 0 }} />
      <p style={{
        fontFamily: "var(--font-helvetica), Helvetica, Arial, sans-serif",
        fontSize: "9px", fontWeight: 700,
        letterSpacing: "0.4em", textTransform: "uppercase",
        color: accent, margin: 0,
      }}>
        {text}
      </p>
    </div>
  )
}
