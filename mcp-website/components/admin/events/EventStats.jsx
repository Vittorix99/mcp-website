"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"

export function EventStats({ participants, onRefresh }) {
  const total = participants.length

  const new24h = participants.filter((p) => new Date(p.createdAt) >= Date.now() - 86400000).length

  const totalRevenue = participants.reduce((sum, p) => {
    const price = Number.parseFloat(p.price)
    return sum + (isNaN(price) ? 0 : price)
  }, 0)

  const omaggiCount = participants.filter((p) => Number.parseFloat(p.price) === 0).length

  // Calcolo statistiche genere
const genderStats = participants.reduce(
  (acc, p) => {
    const gender = (p.gender || "").toLowerCase()
    if (gender === "male") acc.male++
    else if (gender === "female") acc.female++
    else acc.na++
    return acc
  },
  { male: 0, female: 0, na: 0 },
)

  const genderData = [
    { name: "Maschio", value: genderStats.male, color: "#3b82f6" },
    { name: "Femmina", value: genderStats.female, color: "#ec4899" },
    { name: "N/A", value: genderStats.na, color: "#6b7280" },
  ].filter((item) => item.value > 0)

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0]
      const percentage = total > 0 ? ((data.value / total) * 100).toFixed(1) : 0
      return (
        <div className="bg-zinc-800 p-2 rounded border border-zinc-600 text-white">
          <p>{`${data.payload.name}: ${data.value} (${percentage}%)`}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-4">
      {/* Statistiche esistenti */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-zinc-900 border border-zinc-700 text-white shadow-md">
          <CardContent className="p-4">
            <p className="text-sm text-gray-400">Partecipanti totali</p>
            <p className="text-2xl font-bold">{total}</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border border-zinc-700 text-white shadow-md">
          <CardContent className="p-4">
            <p className="text-sm text-gray-400">Ultime 24 ore</p>
            <p className="text-2xl font-bold">{new24h}</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border border-zinc-700 text-white shadow-md">
          <CardContent className="p-4">
            <p className="text-sm text-gray-400">Totale incassato</p>
            <p className="text-2xl font-bold">{totalRevenue.toFixed(2)} €</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border border-zinc-700 text-white shadow-md">
          <CardContent className="p-4">
            <p className="text-sm text-gray-400">Totale omaggi</p>
            <p className="text-2xl font-bold">{omaggiCount}</p>
          </CardContent>
        </Card>
      </div>

      {/* Grafico distribuzione genere */}
      {total > 0 && (
        <Card className="bg-zinc-900 border border-zinc-700 text-white shadow-md">
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4 text-center text-white">Distribuzione per Genere</h3>
            <div className="flex flex-col lg:flex-row items-center gap-6">
              <div className="w-full lg:w-1/2 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={genderData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {genderData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="w-full lg:w-1/2 space-y-3">
                {genderData.map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-zinc-800 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: item.color }}></div>
                      <span className="font-medium text-white">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-white">{item.value}</div>
                      <div className="text-sm text-gray-400">
                        {total > 0 ? ((item.value / total) * 100).toFixed(1) : 0}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pulsante aggiorna */}
      <div className="sm:col-span-2 lg:col-span-4 flex justify-end">
        <Button onClick={onRefresh}>Aggiorna</Button>
      </div>
    </div>
  )
}
