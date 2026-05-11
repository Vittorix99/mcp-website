"use client"

import {
  ResponsiveContainer,
  ComposedChart,
  BarChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from "recharts"

import SnapshotChartCard from "./SnapshotChartCard"

const C_ORANGE = "#e8820c"
const C_PURPLE = "#511a6c"
const C_YELLOW = "#f0d44a"
const C_WHITE = "#ffffff"
const C_OFF = "#b0b0b0"
const C_RED = "#e8241a"
const C_GREEN = "#4ade80"

const TIER_META = {
  super_early: { label: "Super Early", color: C_GREEN },
  early:       { label: "Early",       color: C_YELLOW },
  regular:     { label: "Regular",     color: C_ORANGE },
  late:        { label: "Late",        color: C_RED },
}

const TOOLTIP_STYLE = {
  contentStyle: { background: "#111111", border: "1px solid #1e1e1e", color: "#ffffff", borderRadius: 0 },
  labelStyle: { color: C_ORANGE },
}

const AXIS_TICK = { fill: C_OFF, fontSize: 11 }
const AXIS_LINE = { stroke: "#3a3a3a" }
const GRID_PROPS = { strokeDasharray: "3 3", stroke: "#1e1e1e" }

function fmtEur(value) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(Number(value || 0))
}

function KpiRow({ label, value }) {
  return (
    <div className="flex items-baseline justify-between border-b border-[#1e1e1e] py-2 last:border-b-0">
      <span style={{ fontFamily: '"Helvetica Neue", sans-serif', fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: C_OFF }}>
        {label}
      </span>
      <span style={{ fontFamily: '"Helvetica Neue", sans-serif', fontSize: 15, fontWeight: 800, color: "#ffffff" }}>
        {value}
      </span>
    </div>
  )
}

export default function EventCharts({
  selectedEventId,
  entranceFlow,
  salesOverTime,
  audienceRetention,
  revenueBreakdown,
  eventFunnel,
  genderDistribution,
  ageDistribution,
}) {
  const flowBuckets = entranceFlow.data?.buckets || []
  const salesDays = salesOverTime.data?.dailySales || []
  const funnelData = eventFunnel.data
  const revenueData = revenueBreakdown.data
  const genderData = genderDistribution.data
  const ageData = ageDistribution.data
  const retentionData = audienceRetention.data

  // Funnel bar data
  const funnelBars = funnelData ? [
    { stage: "Ticket venduti", value: funnelData.ticketsSold },
    { stage: "Entrati (flag)", value: funnelData.enteredFlag },
    { stage: "Scansionati", value: funnelData.scanned },
  ] : []

  // Gender pie
  const genderPie = genderData ? [
    { key: "male", count: genderData.male, label: "Maschi" },
    { key: "female", count: genderData.female, label: "Femmine" },
    { key: "unknown", count: genderData.unknown, label: "N/D" },
  ].filter((d) => d.count > 0) : []

  const genderColors = { male: C_ORANGE, female: C_PURPLE, unknown: C_OFF }

  // Revenue tier chart data
  const revTiers = revenueData?.byTier || []

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">

      {/* Event Funnel — KPI card con progress bars CSS */}
      <SnapshotChartCard
        title="Event Funnel"
        loading={eventFunnel.loading}
        error={eventFunnel.error}
        empty={!funnelData}
      >
        {funnelData && (
          <div className="flex h-full flex-col justify-between py-1">
            <KpiRow label="Max partecipanti" value={funnelData.maxParticipants || "—"} />
            <KpiRow label="Ticket venduti" value={funnelData.ticketsSold} />
            <KpiRow label="Fill rate" value={`${funnelData.fillRatePct}%`} />
            <KpiRow label="Entrati (flag)" value={funnelData.enteredFlag} />
            <KpiRow label="Show rate" value={`${funnelData.showRatePct}%`} />
            <KpiRow label="Scansionati" value={funnelData.scanned} />
            <KpiRow label="Scan coverage" value={`${funnelData.scanCoveragePct}%`} />
            {/* Progress bars CSS — non usano Recharts, non possono sforare */}
            <div className="mt-2 space-y-2">
              {funnelBars.map(({ stage, value }) => {
                const max = funnelData.ticketsSold || 1
                const pct = Math.min(100, Math.round((value / max) * 100))
                return (
                  <div key={stage}>
                    <div className="mb-0.5 flex justify-between text-[10px] uppercase tracking-wide" style={{ color: C_OFF, fontFamily: '"Helvetica Neue", sans-serif' }}>
                      <span>{stage}</span>
                      <span style={{ color: "#fff", fontWeight: 700 }}>{value}</span>
                    </div>
                    <div className="h-1.5 w-full bg-[#1e1e1e]">
                      <div className="h-full bg-[#e8820c] transition-all" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </SnapshotChartCard>

      {/* Entrance Flow */}
      <SnapshotChartCard
        title="Entrance Flow"
        loading={entranceFlow.loading}
        error={entranceFlow.error}
        empty={flowBuckets.length === 0}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={flowBuckets} margin={{ top: 8, right: 0, left: 0, bottom: 8 }}>
            <CartesianGrid {...GRID_PROPS} />
            <XAxis
              dataKey="hourLabel"
              tick={AXIS_TICK}
              axisLine={AXIS_LINE}
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={20}
              tickMargin={8}
              tickFormatter={(v) => String(v || "").slice(0, 5)}
            />
            <YAxis yAxisId="l" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} allowDecimals={false} width={28} />
            <YAxis yAxisId="r" orientation="right" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} allowDecimals={false} width={32} />
            <Tooltip {...TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11, color: C_OFF }} />
            <Bar yAxisId="l" dataKey="count" name="Ingressi" fill={C_ORANGE} radius={[2, 2, 0, 0]} />
            <Line yAxisId="r" type="monotone" dataKey="cumulative" name="Cumulativo" stroke={C_WHITE} strokeWidth={1.5} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </SnapshotChartCard>

      {/* Sales Over Time */}
      <SnapshotChartCard
        title="Sales Over Time"
        loading={salesOverTime.loading}
        error={salesOverTime.error}
        empty={salesDays.length === 0}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={salesDays}>
            <CartesianGrid {...GRID_PROPS} />
            <XAxis dataKey="day" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false}
              tickFormatter={(v) => `G${v}`} interval="preserveStartEnd" />
            <YAxis yAxisId="l" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} allowDecimals={false} />
            <YAxis yAxisId="r" orientation="right" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} allowDecimals={false} />
            <Tooltip
              {...TOOLTIP_STYLE}
              labelFormatter={(v, payload) => {
                const date = payload?.[0]?.payload?.date || `G${v}`
                return `Giorno ${v} · ${date}`
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: C_OFF }} />
            <Bar yAxisId="l" dataKey="ticketsSold" name="Ticket" fill={C_ORANGE} radius={[2, 2, 0, 0]} />
            <Line yAxisId="r" type="monotone" dataKey="cumulative" name="Cumulativo" stroke={C_WHITE} strokeWidth={1.5} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </SnapshotChartCard>

      {/* Revenue Breakdown */}
      <SnapshotChartCard
        title="Revenue Breakdown per Tier"
        loading={revenueBreakdown.loading}
        error={revenueBreakdown.error}
        empty={revTiers.length === 0}
      >
        {revenueData && (
          <div className="flex h-full flex-col">
            <div className="mb-3 flex gap-4 text-xs" style={{ fontFamily: '"Helvetica Neue", sans-serif' }}>
              <span style={{ color: C_OFF }}>
                Lordo: <span style={{ color: "#fff", fontWeight: 700 }}>{fmtEur(revenueData.totalGross)}</span>
              </span>
              <span style={{ color: C_OFF }}>
                Netto: <span style={{ color: "#fff", fontWeight: 700 }}>{fmtEur(revenueData.totalNet)}</span>
              </span>
              <span style={{ color: C_OFF }}>
                Fee: <span style={{ color: C_RED, fontWeight: 700 }}>{fmtEur(revenueData.paypalFees)}</span>
              </span>
            </div>
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={revTiers}>
                  <CartesianGrid {...GRID_PROPS} />
                  <XAxis dataKey="tier" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
                  <YAxis tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
                  <Tooltip {...TOOLTIP_STYLE} />
                  <Legend wrapperStyle={{ fontSize: 11, color: C_OFF }} />
                  <Bar dataKey="gross" name="Lordo" fill={C_ORANGE} radius={[2, 2, 0, 0]} />
                  <Bar dataKey="net" name="Netto" fill={C_YELLOW} radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </SnapshotChartCard>

      {/* Ticket per Tier */}
      <SnapshotChartCard
        title="Ticket per Tier"
        loading={revenueBreakdown.loading}
        error={revenueBreakdown.error}
        empty={revTiers.length === 0}
      >
        {revenueData && (() => {
          const TIER_ORDER = ["super_early", "early", "regular", "late"]
          const sorted = TIER_ORDER
            .map(key => revTiers.find(t => t.tier === key))
            .filter(Boolean)
          const totalTierCount = sorted.reduce((s, t) => s + (t.count || 0), 0) || 1
          const totalGross = sorted.reduce((s, t) => s + (t.gross || 0), 0)
          const totalNet   = sorted.reduce((s, t) => s + (t.net   || 0), 0)
          const totalFee   = totalGross - totalNet
          return (
            <div className="flex h-full flex-col justify-between">
              <div className="mb-3 flex flex-wrap gap-x-4 gap-y-1 text-xs" style={{ fontFamily: '"Helvetica Neue", sans-serif' }}>
                <span style={{ color: C_OFF }}>
                  Ticket: <span style={{ color: "#fff", fontWeight: 700 }}>{totalTierCount}</span>
                </span>
                <span style={{ color: C_OFF }}>
                  Incassato: <span style={{ color: "#fff", fontWeight: 700 }}>{fmtEur(totalGross)}</span>
                </span>
                <span style={{ color: C_OFF }}>
                  Netto: <span style={{ color: C_YELLOW, fontWeight: 700 }}>{fmtEur(totalNet)}</span>
                </span>
                <span style={{ color: C_OFF }}>
                  Fee: <span style={{ color: C_RED, fontWeight: 700 }}>{fmtEur(totalFee)}</span>
                </span>
              </div>
              <div className="flex-1 space-y-4">
                {sorted.map((t) => {
                  const meta = TIER_META[t.tier] || { label: t.tier, color: C_OFF }
                  const pct = Math.round((t.count / totalTierCount) * 100)
                  const avgPrice = t.count > 0 ? (t.gross / t.count) : 0
                  const tierFee = (t.gross || 0) - (t.net || 0)
                  return (
                    <div key={t.tier}>
                      <div className="mb-1 flex items-baseline justify-between" style={{ fontFamily: '"Helvetica Neue", sans-serif' }}>
                        <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: meta.color }}>
                          {meta.label}
                        </span>
                        <span style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>
                          {t.count}
                          <span style={{ fontSize: 11, fontWeight: 400, color: C_OFF, marginLeft: 4 }}>({pct}%)</span>
                        </span>
                      </div>
                      <div className="h-2 w-full bg-[#1e1e1e]">
                        <div className="h-full transition-all" style={{ width: `${pct}%`, background: meta.color }} />
                      </div>
                      <div className="mt-0.5 flex justify-between" style={{ fontSize: 10, color: C_OFF, fontFamily: '"Helvetica Neue", sans-serif' }}>
                        <span>avg {fmtEur(avgPrice)}/ticket · fee {fmtEur(tierFee)}</span>
                        <span>lordo <span style={{ color: "#fff" }}>{fmtEur(t.gross)}</span> · netto <span style={{ color: C_YELLOW }}>{fmtEur(t.net)}</span></span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })()}
      </SnapshotChartCard>

      {/* Gender Distribution */}
      <SnapshotChartCard
        title="Distribuzione Genere"
        loading={genderDistribution.loading}
        error={genderDistribution.error}
        empty={genderPie.length === 0}
      >
        {genderData && (
          <div className="flex h-full flex-col items-center gap-4 sm:flex-row sm:items-center sm:gap-6">
            <div className="h-[170px] w-[170px] flex-shrink-0 sm:h-[180px] sm:w-[180px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={genderPie} dataKey="count" nameKey="label" innerRadius="55%" outerRadius="82%" paddingAngle={2}>
                    {genderPie.map((entry) => (
                      <Cell key={entry.key} fill={genderColors[entry.key] || C_OFF} />
                    ))}
                  </Pie>
                  <Tooltip {...TOOLTIP_STYLE} formatter={(v) => [v, ""]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="w-full min-w-0 flex-1 space-y-3">
              {[
                { key: "male", label: "Maschi", count: genderData.male, pct: genderData.malePct },
                { key: "female", label: "Femmine", count: genderData.female, pct: genderData.femalePct },
                { key: "unknown", label: "N/D", count: genderData.unknown, pct: genderData.unknownPct },
              ].map(({ key, label, count, pct }) => (
                <div key={key}>
                  <div className="mb-1 flex justify-between text-[11px] sm:text-xs" style={{ fontFamily: '"Helvetica Neue", sans-serif' }}>
                    <span style={{ color: C_OFF, textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</span>
                    <span style={{ color: "#fff", fontWeight: 700 }}>{count} <span style={{ color: C_OFF }}>({pct}%)</span></span>
                  </div>
                  <div className="h-1.5 w-full bg-[#1e1e1e]">
                    <div className="h-full" style={{ width: `${pct}%`, background: genderColors[key] || C_OFF }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </SnapshotChartCard>

      {/* Age Distribution */}
      <SnapshotChartCard
        title="Distribuzione Età"
        loading={ageDistribution.loading}
        error={ageDistribution.error}
        empty={!ageData || ageData.total === 0}
      >
        {ageData && (
          <div className="flex h-full flex-col justify-between gap-2 py-1">
            <p className="text-xs" style={{ fontFamily: '"Helvetica Neue", sans-serif', color: C_OFF }}>
              Fascia dominante:{" "}
              <span style={{ color: C_ORANGE, fontWeight: 700 }}>{ageData.dominant}</span>
              {" · "}totale{" "}
              <span style={{ color: "#fff", fontWeight: 700 }}>{ageData.total}</span>
            </p>
            <div className="flex-1 space-y-3">
              {(ageData.bands || []).filter((b) => b.band !== "unknown").map((b) => (
                <div key={b.band}>
                  <div className="mb-1 flex justify-between text-[11px]" style={{ fontFamily: '"Helvetica Neue", sans-serif' }}>
                    <span style={{ color: C_OFF, textTransform: "uppercase", letterSpacing: "0.08em" }}>{b.band}</span>
                    <span style={{ color: "#fff", fontWeight: 700 }}>{b.count} <span style={{ color: C_OFF }}>({b.pct}%)</span></span>
                  </div>
                  <div className="h-1.5 w-full bg-[#1e1e1e]">
                    <div className="h-full bg-[#e8820c]" style={{ width: `${b.pct}%` }} />
                  </div>
                </div>
              ))}
              {ageData.bands?.find((b) => b.band === "unknown")?.count > 0 && (() => {
                const u = ageData.bands.find((b) => b.band === "unknown")
                return (
                  <div key="unknown">
                    <div className="mb-1 flex justify-between text-[11px]" style={{ fontFamily: '"Helvetica Neue", sans-serif' }}>
                      <span style={{ color: C_OFF, textTransform: "uppercase", letterSpacing: "0.08em" }}>N/D</span>
                      <span style={{ color: "#fff", fontWeight: 700 }}>{u.count} <span style={{ color: C_OFF }}>({u.pct}%)</span></span>
                    </div>
                    <div className="h-1.5 w-full bg-[#1e1e1e]">
                      <div className="h-full" style={{ width: `${u.pct}%`, background: C_OFF }} />
                    </div>
                  </div>
                )
              })()}
            </div>
          </div>
        )}
      </SnapshotChartCard>

      {/* Audience Retention */}
      <SnapshotChartCard
        title="Audience Retention"
        loading={audienceRetention.loading}
        error={audienceRetention.error}
        empty={!retentionData}
      >
        {retentionData && (
          <div className="flex h-full flex-col justify-between">
            <div className="mb-4 flex gap-6 text-xs" style={{ fontFamily: '"Helvetica Neue", sans-serif' }}>
              <span style={{ color: C_OFF }}>
                Totale: <span style={{ color: "#fff", fontWeight: 700 }}>{retentionData.totalParticipants}</span>
              </span>
              <span style={{ color: C_OFF }}>
                Nuovi: <span style={{ color: C_ORANGE, fontWeight: 700 }}>{retentionData.new}</span>
              </span>
              <span style={{ color: C_OFF }}>
                Ritorno: <span style={{ color: C_YELLOW, fontWeight: 700 }}>{retentionData.returning}</span>
              </span>
            </div>
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={retentionData.breakdown} layout="vertical" margin={{ left: 8, right: 32 }}>
                  <CartesianGrid {...GRID_PROPS} horizontal={false} />
                  <XAxis type="number" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
                  <YAxis dataKey="category" type="category" tick={{ fill: C_OFF, fontSize: 10 }} width={110} axisLine={false} tickLine={false} />
                  <Tooltip
                    {...TOOLTIP_STYLE}
                    formatter={(v, name, props) => [`${v} (${props.payload.pct}%)`, ""]}
                  />
                  <Bar dataKey="count" fill={C_ORANGE} radius={[0, 2, 2, 0]}>
                    {retentionData.breakdown.map((entry, i) => (
                      <Cell key={i} fill={i === 0 ? C_ORANGE : i === 1 ? C_YELLOW : C_WHITE} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </SnapshotChartCard>

    </div>
  )
}
