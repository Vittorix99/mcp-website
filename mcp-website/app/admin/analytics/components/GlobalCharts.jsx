"use client"

import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts"

import SnapshotChartCard from "./SnapshotChartCard"

const C_ORANGE = "#e8820c"
const C_WHITE = "#ffffff"
const C_OFF = "#b0b0b0"

const TOOLTIP_STYLE = {
  contentStyle: { background: "#111111", border: "1px solid #1e1e1e", color: "#ffffff", borderRadius: 0 },
  labelStyle: { color: C_ORANGE },
}

const AXIS_TICK = { fill: C_OFF, fontSize: 11 }
const AXIS_LINE = { stroke: "#3a3a3a" }
const GRID_PROPS = { strokeDasharray: "3 3", stroke: "#1e1e1e" }

const TITLE_FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif'
const BODY_FONT = 'Charter, Georgia, "Times New Roman", serif'

export default function GlobalCharts({ membershipTrend }) {
  const trendData = membershipTrend?.data
  const monthly = trendData?.monthly || []

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">

      {/* KPIs */}
      <div className="border border-[#1e1e1e] bg-[#111111] p-4 xl:col-span-1">
        <p
          className="mb-4 uppercase text-[#e8820c]"
          style={{ fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em" }}
        >
          Riepilogo Anno
        </p>
        {membershipTrend?.loading ? (
          <div className="h-24 animate-pulse bg-[#0a0a0a]" />
        ) : membershipTrend?.error ? (
          <p className="text-sm text-[#e8241a]" style={{ fontFamily: BODY_FONT }}>{membershipTrend.error}</p>
        ) : trendData ? (
          <div className="space-y-4">
            <div>
              <p style={{ fontFamily: TITLE_FONT, fontSize: 11, fontWeight: 700, color: C_OFF, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                Nuovi nell&apos;anno
              </p>
              <p className="mt-1 text-3xl text-white" style={{ fontFamily: TITLE_FONT, fontWeight: 900 }}>
                {trendData.totalYear}
              </p>
            </div>
            <div>
              <p style={{ fontFamily: TITLE_FONT, fontSize: 11, fontWeight: 700, color: C_OFF, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                Tessere attive (totale)
              </p>
              <p className="mt-1 text-3xl text-white" style={{ fontFamily: TITLE_FONT, fontWeight: 900 }}>
                {trendData.totalActive}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-[#b0b0b0]" style={{ fontFamily: BODY_FONT }}>Nessun dato</p>
        )}
      </div>

      {/* Membership trend chart */}
      <div className="xl:col-span-2">
        <SnapshotChartCard
          title="Nuove tessere per mese"
          loading={membershipTrend?.loading}
          error={membershipTrend?.error}
          empty={monthly.length === 0 || monthly.every((m) => m.newMembers === 0)}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={monthly}>
              <CartesianGrid {...GRID_PROPS} />
              <XAxis dataKey="label" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
              <YAxis yAxisId="l" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} allowDecimals={false} />
              <Tooltip {...TOOLTIP_STYLE} labelFormatter={(v) => v} />
              <Legend wrapperStyle={{ fontSize: 11, color: C_OFF }} />
              <Bar yAxisId="l" dataKey="newMembers" name="Nuovi membri" fill={C_ORANGE} radius={[2, 2, 0, 0]} />
              <Line
                yAxisId="l"
                type="monotone"
                dataKey="newMembers"
                name="Trend"
                stroke={C_WHITE}
                strokeWidth={1.5}
                dot={false}
                legendType="none"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </SnapshotChartCard>
      </div>

    </div>
  )
}
