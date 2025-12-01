"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts"
import { useEffect, useState } from "react"

export function EventStats({ participants, onRefresh }) {
  const total = participants.length

  console.debug("[EventStats] participants sample", participants.slice(0, 5))

  const new24h = participants.filter((p) => new Date(p.createdAt) >= Date.now() - 86400000).length

  const totalRevenue = participants.reduce((sum, p) => {
    const price = Number.parseFloat(p.price)
    return sum + (isNaN(price) ? 0 : price)
  }, 0)

  const omaggiCount = participants.filter((p) => Number.parseFloat(p.price) === 0).length

  const [isMobile, setIsMobile] = useState(false)
  useEffect(() => {
    if (typeof window === 'undefined') return
    const mq = window.matchMedia('(max-width: 640px)')
    const update = () => setIsMobile(mq.matches)
    update()
    mq.addEventListener('change', update)
    return () => mq.removeEventListener('change', update)
  }, [])

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

  // ===== Età partecipanti =====
  const parseBirthDate = (raw) => {
    if (!raw) return null

    // Firestore Timestamp-like
    if (raw?.toDate && typeof raw.toDate === "function") {
      try { return raw.toDate() } catch { /* fallthrough */ }
    }
    // epoch ms or seconds
    if (typeof raw === "number") {
      try { return new Date(raw > 1e12 ? raw : raw * 1000) } catch { return null }
    }

    if (typeof raw === "string") {
      const s = raw.trim()
      if (!s) return null

      // Normalize separators
      const norm = s.replace(/\./g, "-").replace(/\//g, "-")

      // dd-mm-yyyy (es: 30-08-1999)
      const mDMY = norm.match(/^([0-3]?\d)-([0-1]?\d)-(\d{4})$/)
      if (mDMY) {
        const d = parseInt(mDMY[1], 10)
        const m = parseInt(mDMY[2], 10)
        const y = parseInt(mDMY[3], 10)
        const dt = new Date(y, m - 1, d)
        return Number.isNaN(dt.getTime()) ? null : dt
      }

      // yyyy-mm-dd
      const mYMD = norm.match(/^(\d{4})-([0-1]?\d)-([0-3]?\d)$/)
      if (mYMD) {
        const y = parseInt(mYMD[1], 10)
        const m = parseInt(mYMD[2], 10)
        const d = parseInt(mYMD[3], 10)
        const dt = new Date(y, m - 1, d)
        return Number.isNaN(dt.getTime()) ? null : dt
      }

      // Fallback: let Date try to parse ISO or locale
      const dt = new Date(s)
      return Number.isNaN(dt.getTime()) ? null : dt
    }

    return null
  }

  const toAge = (p) => {
    // 1) campo numerico `age`
    const a = Number.parseInt(p.age)
    if (!Number.isNaN(a) && a > 0 && a < 120) {
      return a
    }

    // 2) prova a derivare da data di nascita
    const dobRaw = p.birthdate || p.birthDate || p.dateOfBirth || p.dob
    const d = parseBirthDate(dobRaw)
    // debug
    console.debug("[EventStats] dobRaw->parsed", dobRaw, d)
    if (!d) return null

    const now = new Date()
    let age = now.getFullYear() - d.getFullYear()
    const m = now.getMonth() - d.getMonth()
    if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age--

    return (age >= 0 && age < 120) ? age : null
  }

  // Nuovi bucket età: 18–20, 21–25, 26–30, 31+
  const buckets = [
    { key: "18_20", label: "18–20", from: 18, to: 20 },
    { key: "21_25", label: "21–25", from: 21, to: 25 },
    { key: "26_30", label: "26–30", from: 26, to: 30 },
    { key: "31p",   label: "31+",   from: 31, to: 200 },
  ]

  // conteggi per genere all'interno dei bucket
  const ageGenderCounts = buckets.reduce((acc, b) => ({
    ...acc,
    [b.key]: { male: 0, female: 0, nd: 0 },
  }), {})

  let agedTotal = 0
  participants.forEach((p) => {
    const age = toAge(p)
    console.debug("[EventStats] computed age", { name: p.name, surname: p.surname, age })
    if (age == null) return

    const bucket = buckets.find((bk) => age >= bk.from && age <= bk.to)
    if (!bucket) return

    const gRaw = (p.gender || "").toLowerCase()
    const g = gRaw === "male" || gRaw === "maschio" ? "male" : gRaw === "female" || gRaw === "femmina" ? "female" : "nd"

    ageGenderCounts[bucket.key][g] += 1
    agedTotal += 1
  })

  console.debug("[EventStats] ageGenderCounts", ageGenderCounts, "agedTotal", agedTotal)

  // dati per stacked bar chart
  const ageData = buckets
    .map((b) => ({
      name: b.label,
      male: ageGenderCounts[b.key].male,
      female: ageGenderCounts[b.key].female,
      nd: ageGenderCounts[b.key].nd,
      total: ageGenderCounts[b.key].male + ageGenderCounts[b.key].female + ageGenderCounts[b.key].nd,
    }))
    .filter((d) => d.total > 0)

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
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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

      {/* Grafico distribuzione età */}
      {agedTotal > 0 && (
        <Card className="bg-zinc-900 border border-zinc-700 text-white shadow-md">
          <CardContent className="p-3 sm:p-4">
            <h3 className="text-lg font-semibold mb-2 text-center text-white">Distribuzione per Età</h3>
            <div className="w-full -mx-4 sm:-mx-2 mx-auto" style={{ height: isMobile ? 320 : 380 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={ageData}
                  margin={{ top: 6, right: isMobile ? 0 : 8, left: isMobile ? 0 : 4, bottom: isMobile ? 14 : 8 }}
                  barCategoryGap={isMobile ? '38%' : '25%'}
                  barGap={isMobile ? 6 : 4}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="name"
                    stroke="#cbd5e1"
                    interval={0}
                    tick={{ fontSize: isMobile ? 10 : 12 }}
                    angle={isMobile ? -20 : 0}
                    dy={isMobile ? 10 : 0}
                  />
                  <YAxis allowDecimals={false} stroke="#cbd5e1" tick={{ fontSize: isMobile ? 10 : 12 }} />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const male = payload.find((p) => p.dataKey === "male")?.value || 0
                        const female = payload.find((p) => p.dataKey === "female")?.value || 0
                        const nd = payload.find((p) => p.dataKey === "nd")?.value || 0
                        const tot = male + female + nd
                        const perc = agedTotal > 0 ? ((tot / agedTotal) * 100).toFixed(1) : 0
                        return (
                          <div className="bg-zinc-800 p-2 rounded border border-zinc-600 text-white space-y-1">
                            <div className="font-medium">{label}: {tot} ({perc}%)</div>
                            <div className="text-xs text-gray-300">Maschi: {male}</div>
                            <div className="text-xs text-gray-300">Femmine: {female}</div>
                            <div className="text-xs text-gray-300">N/D: {nd}</div>
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                  <Bar dataKey="male" stackId="a" fill="#3b82f6" barSize={isMobile ? 20 : 28} />
                  <Bar dataKey="female" stackId="a" fill="#ec4899" barSize={isMobile ? 20 : 28} />
                  <Bar dataKey="nd" stackId="a" fill="#6b7280" barSize={isMobile ? 20 : 28} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 text-sm text-gray-400 text-center">
              Campione età disponibili: {agedTotal} / {total}
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
