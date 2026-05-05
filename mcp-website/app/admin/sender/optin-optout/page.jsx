"use client"

import { useState, useEffect, useMemo } from "react"
import { motion } from "framer-motion"
import { Search, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { routes } from "@/config/routes"
import { getNewsletterSignups, getNewsletterConsents } from "@/services/admin/newsletter"
import { getAllEventsAdmin } from "@/services/admin/events"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

const safeStr = (v) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : "")
const resolveEventTitle = (row, eventTitleById = {}) => {
  const directTitle = safeStr(row?.event_title) || safeStr(row?.event_name) || safeStr(row?.title)
  if (directTitle) return directTitle
  const mappedTitle = eventTitleById[safeStr(row?.event_id)]
  return mappedTitle || "Evento senza titolo"
}

function TableSkeleton({ cols = 4 }) {
  return Array.from({ length: 5 }).map((_, i) => (
    <TableRow key={i} className="border-neutral-800">
      {Array.from({ length: cols }).map((__, j) => (
        <TableCell key={j}><Skeleton className="h-4 w-full bg-zinc-800" /></TableCell>
      ))}
    </TableRow>
  ))
}

function StatusBadge({ active }) {
  return active
    ? <span className="text-xs px-2 py-0.5 rounded-full bg-green-700/60 text-green-200">Attivo</span>
    : <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-700 text-zinc-400">Inattivo</span>
}

function formatDate(v) {
  if (!v) return "—"
  try {
    const d = typeof v === "object" && v._seconds
      ? new Date(v._seconds * 1000)
      : new Date(v)
    return d.toLocaleDateString("it-IT")
  } catch { return "—" }
}

// ── Consents table ────────────────────────────────────────────────── //

function ConsentsTable({ rows, loading, filterEvent, eventTitleById }) {
  const [search, setSearch] = useState("")

  const filtered = useMemo(() => {
    let data = rows
    if (filterEvent) data = data.filter((r) => safeStr(r.event_id) === filterEvent)
    const q = search.trim().toLowerCase()
    if (q) data = data.filter((r) =>
      safeStr(r.email).toLowerCase().includes(q) ||
      safeStr(r.name).toLowerCase().includes(q) ||
      safeStr(r.surname).toLowerCase().includes(q)
    )
    return data
  }, [rows, filterEvent, search])

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500" />
        <Input
          placeholder="Cerca email o nome..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-zinc-800 border-neutral-700 text-white placeholder-zinc-500 pl-9"
        />
      </div>
      <p className="text-xs text-neutral-500">{filtered.length} record</p>
      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400">Email</TableHead>
                <TableHead className="text-neutral-400">Nome</TableHead>
                <TableHead className="text-neutral-400">Evento</TableHead>
                <TableHead className="text-neutral-400">Data</TableHead>
                <TableHead className="text-neutral-400">Stato</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? <TableSkeleton cols={5} /> : filtered.length === 0 ? (
                <TableRow className="border-neutral-800">
                  <TableCell colSpan={5} className="text-center text-neutral-500 py-10">
                    Nessun record trovato.
                  </TableCell>
                </TableRow>
              ) : filtered.map((r, i) => (
                <TableRow key={r.id ?? i} className="border-neutral-800 hover:bg-white/5">
                  <TableCell className="text-white text-sm font-mono">{safeStr(r.email) || "—"}</TableCell>
                  <TableCell className="text-neutral-300 text-sm">
                    {[safeStr(r.name), safeStr(r.surname)].filter(Boolean).join(" ") || "—"}
                  </TableCell>
                  <TableCell className="text-neutral-400 text-sm">{resolveEventTitle(r, eventTitleById)}</TableCell>
                  <TableCell className="text-neutral-400 text-sm">{formatDate(r.timestamp)}</TableCell>
                  <TableCell><StatusBadge active={r.active !== false} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

// ── Signups table ─────────────────────────────────────────────────── //

function SignupsTable({ rows, loading }) {
  const [search, setSearch] = useState("")

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return rows
    return rows.filter((r) => safeStr(r.email).toLowerCase().includes(q))
  }, [rows, search])

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500" />
        <Input
          placeholder="Cerca email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-zinc-800 border-neutral-700 text-white placeholder-zinc-500 pl-9"
        />
      </div>
      <p className="text-xs text-neutral-500">{filtered.length} record</p>
      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400">Email</TableHead>
                <TableHead className="text-neutral-400">Fonte</TableHead>
                <TableHead className="text-neutral-400">Data</TableHead>
                <TableHead className="text-neutral-400">Stato</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? <TableSkeleton cols={4} /> : filtered.length === 0 ? (
                <TableRow className="border-neutral-800">
                  <TableCell colSpan={4} className="text-center text-neutral-500 py-10">
                    Nessun record trovato.
                  </TableCell>
                </TableRow>
              ) : filtered.map((r, i) => (
                <TableRow key={r.id ?? i} className="border-neutral-800 hover:bg-white/5">
                  <TableCell className="text-white text-sm font-mono">{safeStr(r.email) || "—"}</TableCell>
                  <TableCell className="text-neutral-400 text-sm">{safeStr(r.source) || "—"}</TableCell>
                  <TableCell className="text-neutral-400 text-sm">{formatDate(r.timestamp)}</TableCell>
                  <TableCell><StatusBadge active={r.active !== false} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────── //

export default function OptInOptOutPage() {
  const [signups, setSignups] = useState([])
  const [consents, setConsents] = useState([])
  const [eventTitleById, setEventTitleById] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterEvent, setFilterEvent] = useState("")

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [s, c, events] = await Promise.all([getNewsletterSignups(), getNewsletterConsents(), getAllEventsAdmin()])
      setSignups(Array.isArray(s?.signups) ? s.signups : [])
      setConsents(Array.isArray(c?.consents) ? c.consents : [])
      const eventRows = Array.isArray(events) ? events : []
      const mappedTitles = eventRows.reduce((acc, event) => {
        const id = safeStr(event?.id)
        const title = safeStr(event?.title)
        if (id && title) acc[id] = title
        return acc
      }, {})
      setEventTitleById(mappedTitles)
    } catch (e) {
      setError("Impossibile caricare i dati.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const filterEvents = useMemo(() => {
    const byId = new Map()
    consents.forEach((row) => {
      const id = safeStr(row?.event_id)
      if (!id) return
      if (!byId.has(id)) byId.set(id, resolveEventTitle(row, eventTitleById))
    })
    return Array.from(byId.entries()).map(([id, title]) => ({ id, title }))
  }, [consents, eventTitleById])

  const optInConsents = useMemo(() => consents.filter((r) => r.active !== false), [consents])
  const optOutConsents = useMemo(() => consents.filter((r) => r.active === false), [consents])
  const optInSignups = useMemo(() => signups.filter((r) => r.active !== false), [signups])
  const optOutSignups = useMemo(() => signups.filter((r) => r.active === false), [signups])

  return (
    <motion.div
      className="space-y-6 pb-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <AdminPageHeader
        title="Opt In / Opt Out"
        description="Newsletter consents e signups dal database."
        backHref={routes.admin.sender.subscribers}
        backLabel="Torna al CRM Sender"
        actions={(
          <Button variant="ghost" size="sm" onClick={load} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        )}
      />

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <Tabs defaultValue="optin">
        <TabsList className="bg-zinc-800">
          <TabsTrigger value="optin">
            Opt In
            {!loading && <Badge variant="secondary" className="ml-2 bg-green-700/40 text-green-300 text-xs">{optInConsents.length + optInSignups.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="optout">
            Opt Out
            {!loading && <Badge variant="secondary" className="ml-2 bg-zinc-600 text-zinc-300 text-xs">{optOutConsents.length + optOutSignups.length}</Badge>}
          </TabsTrigger>
        </TabsList>

        {/* ── Opt In ── */}
        <TabsContent value="optin" className="mt-4">
          <Tabs defaultValue="consents">
            <div className="flex items-center gap-4 mb-4 flex-wrap">
              <TabsList className="bg-zinc-800/60">
                <TabsTrigger value="consents">
                  Consents
                  {!loading && <span className="ml-1.5 text-xs text-neutral-400">({optInConsents.length})</span>}
                </TabsTrigger>
                <TabsTrigger value="signups">
                  Signups
                  {!loading && <span className="ml-1.5 text-xs text-neutral-400">({optInSignups.length})</span>}
                </TabsTrigger>
              </TabsList>

              {/* Event filter — only meaningful for consents */}
              {filterEvents.length > 0 && (
                <select
                  value={filterEvent}
                  onChange={(e) => setFilterEvent(e.target.value)}
                  className="bg-zinc-800 border border-neutral-700 rounded-md px-3 py-1.5 text-sm text-white"
                >
                  <option value="">Tutti gli eventi</option>
                  {filterEvents.map((event) => (
                    <option key={event.id} value={event.id}>{event.title}</option>
                  ))}
                </select>
              )}
            </div>

            <TabsContent value="consents">
              <ConsentsTable rows={optInConsents} loading={loading} filterEvent={filterEvent} eventTitleById={eventTitleById} />
            </TabsContent>
            <TabsContent value="signups">
              <SignupsTable rows={optInSignups} loading={loading} />
            </TabsContent>
          </Tabs>
        </TabsContent>

        {/* ── Opt Out ── */}
        <TabsContent value="optout" className="mt-4">
          <Tabs defaultValue="consents">
            <TabsList className="bg-zinc-800/60 mb-4">
              <TabsTrigger value="consents">
                Consents
                {!loading && <span className="ml-1.5 text-xs text-neutral-400">({optOutConsents.length})</span>}
              </TabsTrigger>
              <TabsTrigger value="signups">
                Signups
                {!loading && <span className="ml-1.5 text-xs text-neutral-400">({optOutSignups.length})</span>}
              </TabsTrigger>
            </TabsList>
            <TabsContent value="consents">
              <ConsentsTable rows={optOutConsents} loading={loading} filterEvent="" eventTitleById={eventTitleById} />
            </TabsContent>
            <TabsContent value="signups">
              <SignupsTable rows={optOutSignups} loading={loading} />
            </TabsContent>
          </Tabs>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
