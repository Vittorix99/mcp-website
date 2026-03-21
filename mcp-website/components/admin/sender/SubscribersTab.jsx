"use client"

import { useState, useEffect, useCallback } from "react"
import { Search, Plus, Loader2, ChevronLeft, ChevronRight, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  listSenderSubscribers,
  listSenderGroupSubscribers,
  upsertSenderSubscriber,
  listSenderGroups,
} from "@/services/admin/sender"

const PAGE_SIZE = 25
const safeStr = (v) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : "")
const getGroups = (s) => Array.isArray(s?.subscriber_tags) && s.subscriber_tags.length > 0
  ? s.subscriber_tags
  : Array.isArray(s?.groups) ? s.groups : []

function TableSkeleton() {
  return Array.from({ length: 6 }).map((_, i) => (
    <TableRow key={i} className="border-neutral-800">
      <TableCell><Skeleton className="h-4 w-40 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-24 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-24 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-28 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-16 bg-zinc-800" /></TableCell>
    </TableRow>
  ))
}

function SubscriberRow({ s, selected, onClick, groups, filterGroup }) {
  const raw = getGroups(s)
  const displayed = raw.length === 0 && filterGroup
    ? groups.filter((g) => String(g.id) === filterGroup)
    : raw
  const st = safeStr(s?.status?.email) || safeStr(s?.status) || ""
  return (
    <TableRow
      className={`border-neutral-800 cursor-pointer transition-colors ${selected ? "bg-orange-500/10" : "hover:bg-white/5"}`}
      onClick={onClick}
    >
      <TableCell className="text-white text-sm font-mono">{safeStr(s.email) || "—"}</TableCell>
      <TableCell className="text-neutral-300 text-sm">{safeStr(s.firstname) || "—"}</TableCell>
      <TableCell className="text-neutral-300 text-sm">{safeStr(s.lastname) || "—"}</TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-1">
          {displayed.length === 0
            ? <span className="text-neutral-600 text-xs">—</span>
            : <>
                {displayed.slice(0, 2).map((g, gi) => (
                  <span key={g?.id ?? gi} className="text-xs bg-orange-500/10 border border-orange-500/20 text-orange-300 px-1.5 py-0.5 rounded">
                    {safeStr(g?.title ?? g?.name ?? g?.id) || "—"}
                  </span>
                ))}
                {displayed.length > 2 && <span className="text-xs text-neutral-500">+{displayed.length - 2}</span>}
              </>
          }
        </div>
      </TableCell>
      <TableCell>
        <span className={`text-xs px-2 py-0.5 rounded-full ${st.toLowerCase() === "active" ? "bg-green-700/60 text-green-200" : "bg-zinc-700 text-zinc-400"}`}>
          {st || "—"}
        </span>
      </TableCell>
    </TableRow>
  )
}

function CreateSubscriberModal({ groups, onClose, onCreated }) {
  const [form, setForm] = useState({ email: "", firstname: "", lastname: "", phone: "", groups: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function onInput(e) { setForm((f) => ({ ...f, [e.target.name]: e.target.value })) }
  function toggleGroup(gid) {
    setForm((f) => ({ ...f, groups: f.groups.includes(gid) ? f.groups.filter((id) => id !== gid) : [...f.groups, gid] }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.email.trim()) return
    setLoading(true); setError(null)
    try {
      await upsertSenderSubscriber({
        email: form.email.trim(),
        firstname: form.firstname || undefined,
        lastname: form.lastname || undefined,
        phone: form.phone || undefined,
        groups: form.groups.length ? form.groups : undefined,
      })
      onCreated(); onClose()
    } catch { setError("Errore durante la creazione.") }
    finally { setLoading(false) }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-zinc-900 border-neutral-800 text-white">
        <DialogHeader><DialogTitle>Nuovo subscriber</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="space-y-1">
            <Label>Email <span className="text-red-400">*</span></Label>
            <Input name="email" type="email" value={form.email} onChange={onInput} required
              placeholder="email@esempio.com" className="bg-zinc-800 border-neutral-700 text-white" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Nome</Label>
              <Input name="firstname" value={form.firstname} onChange={onInput} placeholder="Mario" className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
            <div className="space-y-1">
              <Label>Cognome</Label>
              <Input name="lastname" value={form.lastname} onChange={onInput} placeholder="Rossi" className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Telefono</Label>
            <Input name="phone" value={form.phone} onChange={onInput} placeholder="+39..." className="bg-zinc-800 border-neutral-700 text-white" />
          </div>
          {groups.length > 0 && (
            <div className="space-y-1.5">
              <Label>Gruppi</Label>
              <div className="grid grid-cols-2 gap-1 max-h-36 overflow-y-auto border border-neutral-700 rounded p-2 bg-zinc-800">
                {groups.map((g, i) => {
                  const gid = String(g?.id ?? "")
                  return (
                    <label key={gid || i} className="flex items-center gap-2 text-sm text-white cursor-pointer">
                      <input type="checkbox" checked={form.groups.includes(gid)} onChange={() => toggleGroup(gid)} className="accent-orange-500" />
                      {g.title ?? g.name}
                    </label>
                  )
                })}
              </div>
            </div>
          )}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-2 pt-1">
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Crea
            </Button>
            <Button type="button" variant="ghost" onClick={onClose}>Annulla</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function SubscribersTab({ onSelectSubscriber, reloadKey = 0 }) {
  // --- Browse state ---
  const [subscribers, setSubscribers] = useState([])
  const [browseLoading, setBrowseLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)

  // --- Search state ---
  const [searchEmail, setSearchEmail] = useState("")
  const [searchFirstname, setSearchFirstname] = useState("")
  const [searchLastname, setSearchLastname] = useState("")
  const [searchGroup, setSearchGroup] = useState("")
  const [searchStatus, setSearchStatus] = useState("")
  const [searchResults, setSearchResults] = useState(null) // null = not in search mode
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState(null)

  // --- Shared ---
  const [groups, setGroups] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState(null)

  // Load paginated subscribers (browse mode)
  const loadPage = useCallback(async (p = 1) => {
    setBrowseLoading(true)
    setError(null)
    try {
      const res = await listSenderSubscribers({ per_page: PAGE_SIZE, page: p })
      const data = Array.isArray(res) ? res : Array.isArray(res?.data) ? res.data : []
      setSubscribers(data)
      const meta = res?.meta
      setHasMore(meta ? (meta.current_page ?? p) < (meta.last_page ?? 1) : data.length === PAGE_SIZE)
    } catch { setError("Impossibile caricare i subscriber.") }
    finally { setBrowseLoading(false) }
  }, [])

  useEffect(() => { loadPage(page) }, [loadPage, page, reloadKey])

  useEffect(() => {
    listSenderGroups().then((res) => {
      const data = res?.data ?? res ?? []
      setGroups(Array.isArray(data) ? data : [])
    }).catch(() => {})
  }, [])

  // Search: fetch all pages of the relevant endpoint, then filter client-side
  async function handleSearch() {
    const hasFilters = searchEmail.trim() || searchFirstname.trim() || searchLastname.trim() || searchGroup || searchStatus
    if (!hasFilters) return

    setSearchLoading(true)
    setSearchError(null)
    setSelected(null)
    if (onSelectSubscriber) onSelectSubscriber(null)

    try {
      const BATCH = 100
      let allData = []
      let p = 1
      while (true) {
        const res = searchGroup
          ? await listSenderGroupSubscribers(searchGroup, { per_page: BATCH, page: p })
          : await listSenderSubscribers({ per_page: BATCH, page: p })
        const data = Array.isArray(res) ? res : Array.isArray(res?.data) ? res.data : []
        allData = allData.concat(data)
        const meta = res?.meta
        const hasNext = meta ? (meta.current_page ?? p) < (meta.last_page ?? 1) : data.length === BATCH
        if (!hasNext) break
        p++
      }

      // Client-side filter by all filled fields
      const results = allData.filter((s) => {
        if (searchEmail.trim() && !safeStr(s.email).toLowerCase().includes(searchEmail.trim().toLowerCase())) return false
        if (searchFirstname.trim() && !safeStr(s.firstname).toLowerCase().includes(searchFirstname.trim().toLowerCase())) return false
        if (searchLastname.trim() && !safeStr(s.lastname).toLowerCase().includes(searchLastname.trim().toLowerCase())) return false
        if (searchStatus) {
          const st = (safeStr(s?.status?.email) || safeStr(s?.status)).toLowerCase()
          if (st !== searchStatus) return false
        }
        return true
      })

      setSearchResults(results)
    } catch { setSearchError("Errore durante la ricerca.") }
    finally { setSearchLoading(false) }
  }

  function clearSearch() {
    setSearchEmail(""); setSearchFirstname(""); setSearchLastname(""); setSearchGroup(""); setSearchStatus("")
    setSearchResults(null); setSearchError(null)
    setSelected(null)
    if (onSelectSubscriber) onSelectSubscriber(null)
  }

  function handleRowClick(s) {
    const next = selected?.email === s.email ? null : s
    setSelected(next)
    if (onSelectSubscriber) onSelectSubscriber(next)
  }

  const isSearchMode = searchResults !== null
  const displayRows = isSearchMode ? searchResults : subscribers
  const isLoading = isSearchMode ? searchLoading : browseLoading

  return (
    <div className="space-y-4">
      {showCreate && (
        <CreateSubscriberModal
          groups={groups}
          onClose={() => setShowCreate(false)}
          onCreated={() => { clearSearch(); loadPage(page) }}
        />
      )}

      {/* Search panel */}
      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="pt-4 pb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div className="space-y-1">
              <Label className="text-xs text-neutral-400">Email</Label>
              <Input
                value={searchEmail}
                onChange={(e) => setSearchEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="es. cristina..."
                className="bg-zinc-800 border-neutral-700 text-white placeholder-zinc-500 h-8 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-neutral-400">Nome</Label>
              <Input
                value={searchFirstname}
                onChange={(e) => setSearchFirstname(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="es. Mario..."
                className="bg-zinc-800 border-neutral-700 text-white placeholder-zinc-500 h-8 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-neutral-400">Cognome</Label>
              <Input
                value={searchLastname}
                onChange={(e) => setSearchLastname(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="es. Rossi..."
                className="bg-zinc-800 border-neutral-700 text-white placeholder-zinc-500 h-8 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-neutral-400">Gruppo</Label>
              <select
                value={searchGroup}
                onChange={(e) => setSearchGroup(e.target.value)}
                className="w-full bg-zinc-800 border border-neutral-700 rounded-md px-3 h-8 text-sm text-white"
              >
                <option value="">Tutti i gruppi</option>
                {groups.map((g, i) => (
                  <option key={g.id ?? i} value={String(g.id ?? "")}>{g.title ?? g.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-neutral-400">Stato</Label>
              <select
                value={searchStatus}
                onChange={(e) => setSearchStatus(e.target.value)}
                className="w-full bg-zinc-800 border border-neutral-700 rounded-md px-3 h-8 text-sm text-white"
              >
                <option value="">Tutti</option>
                <option value="active">Attivi</option>
                <option value="unsubscribed">Disiscritti</option>
                <option value="bounced">Bounced</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <Button size="sm" onClick={handleSearch} disabled={searchLoading}>
              {searchLoading
                ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Ricerca...</>
                : <><Search className="h-4 w-4 mr-2" />Cerca</>
              }
            </Button>
            {isSearchMode && (
              <Button size="sm" variant="ghost" onClick={clearSearch}>
                <X className="h-4 w-4 mr-1" /> Azzera
              </Button>
            )}
            <Button size="sm" variant="ghost" className="ml-auto" onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-1" /> Nuovo
            </Button>
          </div>
          {searchError && <p className="text-red-400 text-sm mt-2">{searchError}</p>}
        </CardContent>
      </Card>

      {/* Results info */}
      {isSearchMode && !searchLoading && (
        <p className="text-xs text-neutral-500">{searchResults.length} risultat{searchResults.length === 1 ? "o" : "i"} trovati</p>
      )}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {/* Table */}
      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400">Email</TableHead>
                <TableHead className="text-neutral-400">Nome</TableHead>
                <TableHead className="text-neutral-400">Cognome</TableHead>
                <TableHead className="text-neutral-400">Gruppi</TableHead>
                <TableHead className="text-neutral-400">Stato</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading
                ? <TableSkeleton />
                : displayRows.length === 0
                  ? (
                    <TableRow className="border-neutral-800">
                      <TableCell colSpan={5} className="text-center text-neutral-500 py-12">
                        {isSearchMode ? "Nessun subscriber trovato con questi filtri." : "Nessun subscriber."}
                      </TableCell>
                    </TableRow>
                  )
                  : displayRows.map((s, i) => (
                    <SubscriberRow
                      key={s.id ?? safeStr(s.email) ?? i}
                      s={s}
                      selected={selected?.email === s.email}
                      onClick={() => handleRowClick(s)}
                      groups={groups}
                      filterGroup={searchGroup}
                    />
                  ))
              }
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination — only in browse mode */}
      {!isSearchMode && (
        <div className="flex items-center justify-between text-sm text-neutral-500">
          <span>Pagina {page}</span>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" disabled={page === 1}
              onClick={() => { setPage((p) => p - 1); setSelected(null) }}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" disabled={!hasMore}
              onClick={() => { setPage((p) => p + 1); setSelected(null) }}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
