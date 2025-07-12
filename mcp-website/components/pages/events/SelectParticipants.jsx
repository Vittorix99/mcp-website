"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function SelectParticipants({ participants }) {
  return (
    <div className="mt-6 text-center">
      <Select >
        <SelectTrigger className="w-full max-w-xs mx-auto bg-black/40 border-gray-700 text-white">
          <SelectValue placeholder="Partecipanti confermati" />
        </SelectTrigger>
        <SelectContent className="bg-black text-white border border-mcp-orange/30">
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