"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"

export function SelectParticipants({ participants }) {
  return (
    <div style={{ marginTop: "8px", marginBottom: "24px" }}>
      <p
        style={{
          fontFamily: HN,
          fontSize: "8px",
          fontWeight: 700,
          letterSpacing: "0.35em",
          textTransform: "uppercase",
          color: ACC,
          margin: "0 0 12px",
        }}
      >
        Partecipanti confermati
      </p>
      <Select >
        <SelectTrigger className="w-full bg-transparent border-white/15 text-white rounded-none">
          <SelectValue placeholder="Partecipanti confermati" />
        </SelectTrigger>
        <SelectContent className="bg-black text-white border border-white/15">
          {participants.map((p, i) => (
            <SelectItem key={i} value={p.email}>
              {p.name} {p.surname}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
