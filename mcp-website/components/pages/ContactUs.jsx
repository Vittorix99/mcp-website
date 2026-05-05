"use client"

import { useState } from "react"
import Image from "next/image"
import { SectionLabel } from "@/components/SectionLabel"
import { sendContactRequest } from "@/services/contactService"
import { useReveal } from "@/hooks/useReveal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const CONTACT_DETAILS = [
  { label: "Email", val: "info@musicconnectingpeople.it" },
  { label: "Instagram", val: "@musicconnectingpeople_" },
  { label: "Location", val: "Palermo, Sicily" },
]

export function ContactUs() {
  useReveal()
  const [form, setForm] = useState({ name: "", email: "", message: "" })
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const result = await sendContactRequest(form)
      if (!result?.success) throw new Error(result?.message || "Failed to send message.")
      setSent(true)
      setForm({ name: "", email: "", message: "" })
    } catch (err) {
      setError(err.message || "Failed to send message. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    width: "100%", padding: "14px 16px",
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(245,243,239,0.1)",
    borderRadius: "2px", color: "#F5F3EF",
    fontFamily: HN, fontSize: "14px", outline: "none",
    transition: "border-color 0.2s", boxSizing: "border-box",
  }

  return (
    <section id="contact-section" style={{
      background: "#080808", paddingTop: "120px", paddingBottom: "80px",
      borderTop: "1px solid rgba(245,243,239,0.04)",
    }}>
      <div style={{ maxWidth: "1360px", margin: "0 auto", padding: "0 40px" }}>
        <div className="contact-grid-new">
          {/* Left info */}
          <div className="reveal">
            <SectionLabel text="Get in Touch" />
            <h2 style={{
              fontFamily: HN, fontWeight: 900,
              fontSize: "clamp(36px,4.5vw,64px)", letterSpacing: "-0.03em",
              textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.88,
              marginBottom: "36px",
            }}>Join the<br />community</h2>
            <p style={{ fontFamily: CH, fontSize: "17px", lineHeight: 1.82, color: "rgba(245,243,239,0.55)", marginBottom: "48px" }}>
              Want to collaborate, play at an MCP event, or just say hello?
              Drop us a message — we read everything.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {CONTACT_DETAILS.map(({ label, val }) => (
                <div key={label} style={{
                  display: "flex", gap: "28px", alignItems: "baseline",
                  borderBottom: "1px solid rgba(245,243,239,0.05)",
                  paddingBottom: "18px",
                }}>
                  <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.35em", textTransform: "uppercase", color: ACC, minWidth: "80px", margin: 0 }}>{label}</p>
                  <p style={{ fontFamily: HN, fontSize: "14px", color: "rgba(245,243,239,0.6)", letterSpacing: "0.02em", margin: 0 }}>{val}</p>
                </div>
              ))}
            </div>

            <div style={{ marginTop: "40px" }}>
              <Image
                src="/patterns/pattern-orange.png"
                alt=""
                width={200}
                height={22}
                style={{ height: "22px", width: "auto", opacity: 0.5 }}
              />
            </div>
          </div>

          {/* Right form */}
          <div className="reveal reveal-delay-2">
            {sent ? (
              <div style={{
                padding: "48px 40px",
                border: `1px solid ${ACC}44`,
                background: `${ACC}06`,
                textAlign: "center",
              }}>
                <Image
                  src="/patterns/pattern-orange.png"
                  alt=""
                  width={160}
                  height={20}
                  style={{ height: "20px", width: "auto", opacity: 0.7, marginBottom: "24px" }}
                />
                <h3 style={{ fontFamily: HN, fontWeight: 900, fontSize: "28px", letterSpacing: "-0.02em", textTransform: "uppercase", color: "#F5F3EF", marginBottom: "12px" }}>
                  Message sent.
                </h3>
                <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.5)", margin: 0 }}>
                  We&apos;ll get back to you soon.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                {[
                  { id: "name", label: "Name", type: "text", placeholder: "Your name" },
                  { id: "email", label: "Email", type: "email", placeholder: "your@email.com" },
                ].map(f => (
                  <div key={f.id}>
                    <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.32em", textTransform: "uppercase", color: ACC, marginBottom: "8px" }}>{f.label}</p>
                    <input
                      type={f.type} required value={form[f.id]}
                      onChange={e => setForm(prev => ({ ...prev, [f.id]: e.target.value }))}
                      placeholder={f.placeholder}
                      style={inputStyle}
                      onFocus={e => e.target.style.borderColor = `${ACC}88`}
                      onBlur={e => e.target.style.borderColor = "rgba(245,243,239,0.1)"}
                    />
                  </div>
                ))}
                <div>
                  <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.32em", textTransform: "uppercase", color: ACC, marginBottom: "8px" }}>Message</p>
                  <textarea
                    required rows={5} value={form.message}
                    onChange={e => setForm(prev => ({ ...prev, message: e.target.value }))}
                    placeholder="Tell us what&apos;s on your mind..."
                    style={{ ...inputStyle, fontFamily: CH, fontSize: "15px", lineHeight: 1.65, resize: "vertical" }}
                    onFocus={e => e.target.style.borderColor = `${ACC}88`}
                    onBlur={e => e.target.style.borderColor = "rgba(245,243,239,0.1)"}
                  />
                </div>
                {error && (
                  <p style={{ fontFamily: CH, fontSize: "13px", color: "#D10000", margin: 0 }}>{error}</p>
                )}
                <button type="submit" disabled={loading} style={{
                  padding: "15px 0", background: loading ? "rgba(224,120,0,0.6)" : ACC,
                  border: "none", cursor: loading ? "default" : "pointer",
                  fontFamily: HN, fontWeight: 700,
                  fontSize: "10px", letterSpacing: "0.3em", textTransform: "uppercase",
                  color: "#fff", borderRadius: "2px", transition: "opacity 0.2s",
                }}>
                  {loading ? "Sending..." : "Send Message →"}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
