"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Loader2, RefreshCw, ArrowRight, CalendarDays, ChartNoAxesCombined } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { routes } from "@/config/routes"
import { getDashboardSnapshot, rebuildAnalytics } from "@/services/admin/stats"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

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

function fmtCurrency(value) {
  const amount = Number(value || 0)
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(amount)
}

function fmtPercent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function fmtDateTime(value) {
  if (!value) return "-"
  const dt = new Date(value)
  if (Number.isNaN(dt.getTime())) return "-"
  return dt.toLocaleString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function mapActivityLabel(type) {
  if (type === "purchase") return "Acquisto"
  if (type === "participant") return "Partecipante"
  if (type === "membership") return "Tessera"
  if (type === "message") return "Messaggio"
  return "Attività"
}

function KPI({ label, value, sub }) {
  return (
    <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)]">
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-[0.08em] text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
          {label}
        </p>
        <p className="mt-2 text-2xl text-[var(--color-white)]" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>
          {value}
        </p>
        {sub ? <p className="mt-1 text-xs text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>{sub}</p> : null}
      </CardContent>
    </Card>
  )
}

function SkeletonCard() {
  return (
    <div className="h-[112px] animate-pulse rounded-none border border-[var(--color-border)] bg-[var(--color-surface)]" />
  )
}

export default function AdminDashboardPage() {
  const { toast } = useToast()

  const [snapshot, setSnapshot] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [clock, setClock] = useState(new Date())

  const loadDashboard = async ({ soft = false } = {}) => {
    if (soft) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }

    try {
      const payload = await getDashboardSnapshot()
      if (payload?.error) {
        throw new Error(payload.error)
      }
      setSnapshot(payload)
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Errore dashboard",
        description: err?.message || "Impossibile caricare lo snapshot dashboard.",
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 60000)
    return () => clearInterval(id)
  }, [])

  const kpis = snapshot?.kpis || {}
  const globalCards = snapshot?.global_cards || {}
  const upcomingEvents = snapshot?.upcoming_events || []
  const recentActivity = snapshot?.recent_activity || []

  const genderQuick = useMemo(() => {
    const split = globalCards.gender_split || {}
    return `M ${split.male || 0} · F ${split.female || 0} · U ${split.unknown || 0}`
  }, [globalCards])

  const triggerRebuild = async () => {
    setRefreshing(true)
    try {
      const response = await rebuildAnalytics("all")
      if (response?.error) {
        throw new Error(response.error)
      }
      toast({
        title: "Rebuild avviato",
        description: `Job ${response.job_id || "queued"} messo in coda.`,
      })
      await loadDashboard({ soft: true })
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Rebuild non avviato",
        description: err?.message || "Errore durante il rebuild analytics.",
      })
      setRefreshing(false)
    }
  }

  return (
    <div className="space-y-6 bg-[var(--color-black)] p-4 text-[var(--color-white)] sm:p-6" style={ADMIN_THEME}>
      <AdminPageHeader
        title="Admin"
        description="Snapshot-first dashboard"
        showBack={false}
        actions={
          <>
            <span className="text-sm text-muted-foreground">
              {clock.toLocaleString("it-IT", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            <Button
              variant="outline"
              onClick={() => loadDashboard({ soft: true })}
              disabled={refreshing}
            >
              {refreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Aggiorna
            </Button>
            <Button
              onClick={triggerRebuild}
              disabled={refreshing}
            >
              Rebuild Snapshot
            </Button>
          </>
        }
      />

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-6">
        {loading ? (
          Array.from({ length: 6 }).map((_, idx) => <SkeletonCard key={`kpi-${idx}`} />)
        ) : (
          <>
            <KPI label="Total Revenue (net)" value={fmtCurrency(kpis.total_revenue_net)} />
            <KPI label="Events" value={kpis.events ?? 0} />
            <KPI label="Members attivi" value={kpis.active_members ?? 0} />
            <KPI label="Participants unici" value={kpis.unique_participants ?? 0} />
            <KPI label="Avg Fill Rate" value={fmtPercent(kpis.avg_fill_rate)} />
            <KPI label="This Month Revenue" value={fmtCurrency(kpis.this_month_revenue)} />
          </>
        )}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)] lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg uppercase tracking-wide" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <Link href={routes.admin.events} className="flex items-center justify-between border border-[var(--color-border)] p-3 text-sm hover:border-[var(--color-orange)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
              Eventi <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href={routes.admin.purchases} className="flex items-center justify-between border border-[var(--color-border)] p-3 text-sm hover:border-[var(--color-orange)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
              Acquisti <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href={routes.admin.memberships} className="flex items-center justify-between border border-[var(--color-border)] p-3 text-sm hover:border-[var(--color-orange)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
              Tessere <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href={routes.admin.messages} className="flex items-center justify-between border border-[var(--color-border)] p-3 text-sm hover:border-[var(--color-orange)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
              Messaggi <ArrowRight className="h-4 w-4" />
            </Link>
          </CardContent>
        </Card>

        <Card className="rounded-none border-[var(--color-orange)] bg-[var(--color-surface)]">
          <CardContent className="flex h-full flex-col justify-between gap-4 p-4">
            <div>
              <p className="text-sm uppercase text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
                Analytics Snapshot
              </p>
              <p className="mt-2 text-sm text-[var(--color-white)]" style={{ fontFamily: BODY_FONT }}>
                Usa grafici evento/global già pre-aggregati per dataset grandi.
              </p>
            </div>
            <Link href={routes.admin.analytics}>
              <Button className="w-full rounded-none bg-[var(--color-orange)] text-black hover:opacity-90">
                Vai ad Analytics <ChartNoAxesCombined className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </section>

      <section className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <KPI label="Avg Unit Payment" value={fmtCurrency(globalCards.avg_unit_payment)} />
        <KPI label="Omaggi Totali" value={globalCards.omaggi_total ?? 0} />
        <KPI label="Gender Split" value={genderQuick} />
        <KPI label="Age Band Dominante" value={globalCards.age_band_dominant || "unknown"} />
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)] xl:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg uppercase" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>
              Upcoming Events
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {upcomingEvents.length === 0 ? (
              <p className="text-sm text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                Nessun evento imminente nello snapshot.
              </p>
            ) : (
              upcomingEvents.slice(0, 3).map((event) => (
                <Link
                  key={event.id}
                  href={routes.admin.eventDetails(event.id)}
                  className="block border border-[var(--color-border)] p-3 hover:border-[var(--color-orange)]"
                >
                  <p className="text-sm" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>{event.title}</p>
                  <p className="mt-1 text-xs text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                    <CalendarDays className="mr-1 inline h-3 w-3" />
                    {event.date || "-"} · {event.start_time || "--:--"}
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                    {event.participants || 0}/{event.max_participants || 0} · Fill {fmtPercent(event.fill_rate)}
                  </p>
                </Link>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)] xl:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg uppercase" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentActivity.length === 0 ? (
              <p className="text-sm text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                Nessuna attività recente nello snapshot.
              </p>
            ) : (
              <div className="space-y-2">
                {recentActivity.slice(0, 10).map((item) => (
                  <div key={`${item.type}-${item.id}`} className="flex items-start justify-between gap-4 border-b border-[var(--color-border)] py-2 last:border-b-0">
                    <div>
                      <p className="text-sm" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>
                        {mapActivityLabel(item.type)}
                      </p>
                      <p className="text-sm text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                        {item.subtitle || "-"}
                        {typeof item.amount === "number" ? ` · ${fmtCurrency(item.amount)}` : ""}
                      </p>
                    </div>
                    <p className="text-xs text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
                      {fmtDateTime(item.timestamp)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
