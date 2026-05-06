"use client"

import { useEffect, useState } from "react"
import { Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"
import { getAllEventsAdmin } from "@/services/admin/events"
import {
  getEntranceFlow,
  getSalesOverTime,
  getAudienceRetention,
  getRevenueBreakdown,
  getEventFunnel,
  getGenderDistribution,
  getMembershipTrend,
} from "@/services/admin/stats"

import EventCharts from "./components/EventCharts"
import GlobalCharts from "./components/GlobalCharts"

const ADMIN_THEME = {
  "--color-black": "#0a0a0a",
  "--color-surface": "#111111",
  "--color-border": "#1e1e1e",
  "--color-muted": "#3a3a3a",
  "--color-white": "#ffffff",
  "--color-off": "#b0b0b0",
  "--color-orange": "#e8820c",
  "--color-purple": "#511a6c",
  "--color-red": "#e8241a",
  "--color-yellow": "#f0d44a",
}

const TITLE_FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif'
const BODY_FONT = 'Charter, Georgia, "Times New Roman", serif'

const CURRENT_YEAR = new Date().getFullYear()
const YEAR_OPTIONS = [CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2]
const ENTRANCE_SPAN_OPTIONS = [3, 4, 6, 8, 10, 12]
const ENTRANCE_BUCKET_OPTIONS = [5, 10, 15, 30, 60]
const DEFAULT_ENTRANCE_SPAN_HOURS = 6
const DEFAULT_ENTRANCE_BUCKET_MINUTES = 15

function useLiveData(fetcher, deps) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    const [key] = deps
    if (!key) {
      setData(null)
      setLoading(false)
      setError("")
      return
    }
    let cancelled = false
    setLoading(true)
    setError("")
    fetcher(key)
      .then((resp) => {
        if (cancelled) return
        if (resp?.error) {
          setError(resp.error)
          setData(null)
        } else {
          setData(resp)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message || "Errore di rete")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, deps)

  return { data, loading, error, reload: () => setData(null) }
}

function normalizeClock(value) {
  const raw = String(value || "").trim()
  const parts = raw.split(":")
  if (parts.length < 2) return ""
  const hour = Number(parts[0])
  const minute = Number(parts[1])
  if (!Number.isInteger(hour) || !Number.isInteger(minute)) return ""
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return ""
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`
}

export default function AdminAnalyticsPage() {
  const [events, setEvents] = useState([])
  const [eventsLoading, setEventsLoading] = useState(true)
  const [selectedEventId, setSelectedEventId] = useState("")
  const [selectedYear, setSelectedYear] = useState(CURRENT_YEAR)
  const [entranceSpanHours, setEntranceSpanHours] = useState(DEFAULT_ENTRANCE_SPAN_HOURS)
  const [entranceBucketMinutes, setEntranceBucketMinutes] = useState(DEFAULT_ENTRANCE_BUCKET_MINUTES)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    getAllEventsAdmin()
      .then((resp) => {
        if (Array.isArray(resp)) {
          const sorted = [...resp].sort((a, b) => {
            const da = a.date || ""
            const db = b.date || ""
            return da > db ? -1 : da < db ? 1 : 0
          })
          setEvents(sorted)
          if (sorted.length > 0) setSelectedEventId(sorted[0].id || sorted[0].event_id || "")
        }
      })
      .finally(() => setEventsLoading(false))
  }, [])

  const selectedEvent = events.find((e) => (e.id || e.event_id) === selectedEventId) || null
  const selectedEventStartTime = normalizeClock(
    selectedEvent?.start_time || selectedEvent?.startTime || ""
  ) || "22:00"

  // Event-level live data
  const entranceFlow = useLiveData(
    (eventId) => getEntranceFlow(eventId, {
      startTime: selectedEventStartTime,
      spanHours: entranceSpanHours,
      bucketMinutes: entranceBucketMinutes,
    }),
    [selectedEventId, selectedEventStartTime, entranceSpanHours, entranceBucketMinutes, refreshKey]
  )
  const salesOverTime = useLiveData(getSalesOverTime, [selectedEventId, refreshKey])
  const audienceRetention = useLiveData(getAudienceRetention, [selectedEventId, refreshKey])
  const revenueBreakdown = useLiveData(getRevenueBreakdown, [selectedEventId, refreshKey])
  const eventFunnel = useLiveData(getEventFunnel, [selectedEventId, refreshKey])
  const genderDistribution = useLiveData(getGenderDistribution, [selectedEventId, refreshKey])

  // Global: membership trend
  const membershipTrend = useLiveData(getMembershipTrend, [selectedYear, refreshKey])

  const anyLoading = entranceFlow.loading || salesOverTime.loading || audienceRetention.loading ||
    revenueBreakdown.loading || eventFunnel.loading || genderDistribution.loading

  const handleRefresh = () => setRefreshKey((k) => k + 1)

  return (
    <div
      className="space-y-6 bg-[var(--color-black)] p-4 text-[var(--color-white)] sm:p-6"
      style={ADMIN_THEME}
    >
      <AdminPageHeader
        title="Analytics"
        description="Dati live per evento · membership trend globale"
        showBack={true}
        backHref="/admin"
        backLabel="Dashboard"
        actions={
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={anyLoading}
          >
            {anyLoading
              ? <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              : <RefreshCw className="mr-2 h-4 w-4" />
            }
            Aggiorna
          </Button>
        }
      />

      {/* Event selector */}
      <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)]">
        <CardContent className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <p
              className="text-xs uppercase tracking-[0.12em] text-[var(--color-orange)]"
              style={{ fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em" }}
            >
              Evento
            </p>
            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              disabled={eventsLoading || events.length === 0}
              className="mt-2 w-full rounded-none border-2 border-[var(--color-border)] bg-[var(--color-black)] p-2 text-sm text-[var(--color-white)] focus:border-[var(--color-orange)] focus:outline-none"
              style={{ fontFamily: BODY_FONT }}
            >
              {eventsLoading && <option value="">Caricamento eventi…</option>}
              {!eventsLoading && events.length === 0 && <option value="">Nessun evento</option>}
              {events.map((ev) => {
                const id = ev.id || ev.event_id || ""
                return (
                  <option key={id} value={id}>
                    {ev.title || ev.name || id} · {ev.date || "-"}
                  </option>
                )
              })}
            </select>
          </div>

          {selectedEvent && (
            <div className="border-l border-[var(--color-border)] pl-4">
              <p
                className="text-xs uppercase text-[var(--color-orange)]"
                style={{ fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em" }}
              >
                Selezionato
              </p>
              <p className="mt-1 text-sm text-[var(--color-white)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
                {selectedEvent.title || selectedEvent.name || selectedEventId}
              </p>
              <p className="mt-1 text-xs text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                {selectedEvent.date || "-"} · {selectedEvent.start_time || selectedEvent.startTime || "--:--"}
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 border-t border-[var(--color-border)] pt-3 sm:grid-cols-3 lg:col-span-3">
            <div>
              <p
                className="text-xs uppercase text-[var(--color-orange)]"
                style={{ fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em" }}
              >
                Entrance Flow
              </p>
              <p className="mt-1 text-xs text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                Base: {selectedEventStartTime} · default fino a +6h
              </p>
            </div>

            <div>
              <p
                className="text-xs uppercase text-[var(--color-orange)]"
                style={{ fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em" }}
              >
                Span Orario
              </p>
              <select
                value={entranceSpanHours}
                onChange={(e) => setEntranceSpanHours(Number(e.target.value))}
                className="mt-2 w-full rounded-none border-2 border-[var(--color-border)] bg-[var(--color-black)] p-2 text-sm text-[var(--color-white)] focus:border-[var(--color-orange)] focus:outline-none"
                style={{ fontFamily: BODY_FONT }}
              >
                {ENTRANCE_SPAN_OPTIONS.map((h) => (
                  <option key={h} value={h}>
                    {h} ore
                  </option>
                ))}
              </select>
            </div>

            <div>
              <p
                className="text-xs uppercase text-[var(--color-orange)]"
                style={{ fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em" }}
              >
                Granularità
              </p>
              <select
                value={entranceBucketMinutes}
                onChange={(e) => setEntranceBucketMinutes(Number(e.target.value))}
                className="mt-2 w-full rounded-none border-2 border-[var(--color-border)] bg-[var(--color-black)] p-2 text-sm text-[var(--color-white)] focus:border-[var(--color-orange)] focus:outline-none"
                style={{ fontFamily: BODY_FONT }}
              >
                {ENTRANCE_BUCKET_OPTIONS.map((mins) => (
                  <option key={mins} value={mins}>
                    {mins} minuti
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Per-event charts */}
      {selectedEventId ? (
        <EventCharts
          selectedEventId={selectedEventId}
          entranceFlow={entranceFlow}
          salesOverTime={salesOverTime}
          audienceRetention={audienceRetention}
          revenueBreakdown={revenueBreakdown}
          eventFunnel={eventFunnel}
          genderDistribution={genderDistribution}
        />
      ) : (
        <div
          className="border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center text-sm text-[var(--color-off)]"
          style={{ fontFamily: BODY_FONT }}
        >
          Seleziona un evento per visualizzare i grafici
        </div>
      )}

      {/* Global: membership trend */}
      <section>
        <div className="mb-4 flex items-center justify-between border-b border-[var(--color-border)] pb-3">
          <p
            className="uppercase text-[var(--color-orange)]"
            style={{ fontFamily: TITLE_FONT, fontWeight: 800, fontSize: 13, letterSpacing: "0.12em" }}
          >
            Membership Trend
          </p>
          <div className="flex gap-2">
            {YEAR_OPTIONS.map((y) => (
              <button
                key={y}
                onClick={() => setSelectedYear(y)}
                className={`rounded-none border px-3 py-1 text-xs uppercase tracking-wide ${
                  selectedYear === y
                    ? "border-[var(--color-orange)] bg-[var(--color-orange)] text-black"
                    : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-off)] hover:border-[var(--color-orange)]"
                }`}
                style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}
              >
                {y}
              </button>
            ))}
          </div>
        </div>
        <GlobalCharts membershipTrend={membershipTrend} />
      </section>
    </div>
  )
}
