"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function MembershipStats({ stats, totalTesseramenti, onRefresh }) {
  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <Card className="flex-1 bg-zinc-900 border border-zinc-700">
        <CardContent className="p-4">
          <p className="text-sm text-gray-400">Membri totali</p>
          <p className="text-2xl font-bold">{stats.total}</p>
        </CardContent>
      </Card>
      <Card className="flex-1 bg-zinc-900 border border-zinc-700">
        <CardContent className="p-4">
          <p className="text-sm text-gray-400">Membri validi</p>
          <p className="text-2xl font-bold">{stats.valid}</p>
        </CardContent>
      </Card>
      <Card className="flex-1 bg-zinc-900 border border-zinc-700">
        <CardContent className="p-4">
          <p className="text-sm text-gray-400">Totale incassato</p>
          <p className="text-2xl font-bold">{totalTesseramenti.toFixed(2)} €</p>
        </CardContent>
      </Card>
      <div className="flex items-center">
        <Button onClick={onRefresh}>Aggiorna</Button>
      </div>
    </div>
  )
}