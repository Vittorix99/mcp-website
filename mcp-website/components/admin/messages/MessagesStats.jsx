"use client"

import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"

export function MessagesStats({ total, last24h, answered }) {
  const stats = [
    { label: "Totale Messaggi", value: total },
    { label: "Ultime 24h", value: last24h },
    { label: "Risposti", value: answered },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="bg-zinc-900 border border-zinc-700">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">{stat.label}</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold">{stat.value}</CardContent>
        </Card>
      ))}
    </div>
  )
}