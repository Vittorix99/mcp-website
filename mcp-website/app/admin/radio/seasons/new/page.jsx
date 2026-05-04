"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { SeasonForm } from "@/components/admin/radio/SeasonForm"
import { routes } from "@/config/routes"

export default function NewSeasonPage() {
  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <Link
          href={routes.admin.radio.index}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            color: "#b0b0b0",
            textDecoration: "none",
            fontFamily: "Helvetica Neue, sans-serif",
            marginBottom: 16,
          }}
        >
          <ArrowLeft style={{ width: 13, height: 13 }} />
          Radio
        </Link>
        <h1
          style={{
            margin: 0,
            fontSize: 20,
            fontWeight: 900,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            color: "#ffffff",
            fontFamily: "Helvetica Neue, sans-serif",
          }}
        >
          Nuova stagione
        </h1>
      </div>

      <SeasonForm mode="create" />
    </div>
  )
}
