"use client"

const MAX_TICKETS = parseInt(process.env.NEXT_PUBLIC_MAX_TICKETS || "5")
const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

export default function QuantitySelector({ quantity, setQuantity, disabled = false }) {
  const handleQuantityChange = (e) => {
    const value = Number.parseInt(e.target.value)
    if (!isNaN(value) && value >= 1 && value <= MAX_TICKETS) {
      setQuantity(value)
    }
  }

  return (
    <div style={{ marginTop: "8px", marginBottom: "28px" }}>
      <label
        htmlFor="quantity"
        style={{
          display: "block",
          fontFamily: HN,
          fontSize: "8px",
          fontWeight: 700,
          letterSpacing: "0.35em",
          textTransform: "uppercase",
          color: ACC,
          marginBottom: "12px",
        }}
      >
        Partecipanti
      </label>
      <div style={{ display: "grid", gridTemplateColumns: "44px 1fr 44px", gap: "8px", alignItems: "stretch" }}>
        <button
          type="button"
          onClick={() => quantity > 1 && setQuantity(quantity - 1)}
          disabled={quantity <= 1 || disabled}
          style={{
            height: "44px",
            border: "1px solid rgba(245,243,239,0.14)",
            background: "transparent",
            color: quantity <= 1 || disabled ? "rgba(245,243,239,0.22)" : "rgba(245,243,239,0.78)",
            cursor: quantity <= 1 || disabled ? "not-allowed" : "pointer",
            fontFamily: HN,
            fontSize: "16px",
          }}
        >
          -
        </button>
        <input
          id="quantity"
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          value={quantity}
          disabled={disabled}
          onChange={handleQuantityChange}
          style={{
            height: "44px",
            width: "100%",
            border: "1px solid rgba(245,243,239,0.14)",
            background: "rgba(245,243,239,0.025)",
            color: "#F5F3EF",
            textAlign: "center",
            fontFamily: HN,
            fontWeight: 700,
            fontSize: "15px",
            outline: "none",
          }}
        />
        <button
          type="button"
          onClick={() => quantity < MAX_TICKETS && setQuantity(quantity + 1)}
          disabled={quantity >= MAX_TICKETS || disabled}
          style={{
            height: "44px",
            border: "1px solid rgba(245,243,239,0.14)",
            background: "transparent",
            color: quantity >= MAX_TICKETS || disabled ? "rgba(245,243,239,0.22)" : "rgba(245,243,239,0.78)",
            cursor: quantity >= MAX_TICKETS || disabled ? "not-allowed" : "pointer",
            fontFamily: HN,
            fontSize: "16px",
          }}
        >
          +
        </button>
      </div>
      <p style={{ fontFamily: CH, fontSize: "12px", color: "rgba(245,243,239,0.35)", margin: "8px 0 0" }}>
        Massimo {MAX_TICKETS} partecipanti per acquisto.
      </p>
    </div>
  )
}
