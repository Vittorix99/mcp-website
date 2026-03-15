"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
import { Search, Plus, Loader2, X, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react"
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
// Sender returns groups as `subscriber_tags`, with fallback to `groups`
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

function CreateSubscriberModal({ groups, onClose, onCreated }) {
  const [form, setForm] = useState({ email: "", firstname: "", lastname: "", phone: "", groups: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function onInput(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  function toggleGroup(gid) {
    setForm((f) => ({
      ...f,
      groups: f.groups.includes(gid) ? f.groups.filter((id) => id !== gid) : [...f.groups, gid],
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.email.trim()) return
    setLoading(true)
    setError(null)
    try {
      await upsertSenderSubscriber({
        email: form.email.trim(),
        firstname: form.firstname || undefined,
        lastname: form.lastname || undefined,
        phone: form.phone || undefined,
        groups: form.groups.length ? form.groups : undefined,
      })
      onCreated()
      onClose()
    } catch {
      setError("Errore durante la creazione.")
    } finally {
      setLoading(false)
    }
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
              <Input name="firstname" value={form.firstname} onChange={onInput}
                placeholder="Mario" className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
            <div className="space-y-1">
              <Label>Cognome</Label>
              <Input name="lastname" value={form.lastname} onChange={onInput}
                placeholder="Rossi" className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Telefono</Label>
            <Input name="phone" value={form.phone} onChange={onInput}
              placeholder="+39..." className="bg-zinc-800 border-neutral-700 text-white" />
          </div>
          {groups.length > 0 && (
            <div className="space-y-1.5">
              <Label>Gruppi</Label>
              <div className="grid grid-cols-2 gap-1 max-h-36 overflow-y-auto border border-neutral-700 rounded p-2 bg-zinc-800">
                {groups.map((g, i) => {
                  const gid = String(g?.id ?? "")
                  return (
                    <label key={gid || i} className="flex items-center gap-2 text-sm text-white cursor-pointer">
                      <input type="checkbox" checked={form.groups.includes(gid)}
                        onChange={() => toggleGroup(gid)} className="accent-orange-500" />
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
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
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
  const [subscribers, setSubscribers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [groups, setGroups] = useState([])
  const [filterText, setFilterText] = useState("")
  const [filterGroup, setFilterGroup] = useState("")
  const [showCreate, setShowCreate] = useState(false)
  const [selected, setSelected] = useState(null)

  const load = useCallback(async (p = 1, groupId = "") => {
    setLoading(true)
    setError(null)
    try {
      const params = { per_page: PAGE_SIZE, page: p }
      const res = groupId
        ? await listSenderGroupSubscribers(groupId, params)
        : await listSenderSubscribers(params)
      const data = Array.isArray(res) ? res : Array.isArray(res?.data) ? res.data : []
      setSubscribers(data)
      const meta = res?.meta
      const hasNext = meta
        ? (meta.current_page ?? p) < (meta.last_page ?? 1)
        : data.length === PAGE_SIZE
      setHasMore(hasNext)
    } catch {
      setError("Impossibile caricare i subscriber.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load(page, filterGroup) }, [load, page, filterGroup, reloadKey])

  useEffect(() => {
    listSenderGroups().then((res) => {
      const data = res?.data ?? res ?? []
      setGroups(Array.isArray(data) ? data : [])
    }).catch(() => {})
  }, [])

  const filtered = useMemo(() => {
    const q = filterText.trim().toLowerCase()
    if (!q) return subscribers
    return subscribers.filter((s) => {
      return safeStr(s.email).toLowerCase().includes(q) ||
        safeStr(s.firstname).toLowerCase().includes(q) ||
        safeStr(s.lastname).toLowerCase().includes(q)
    })
  }, [subscribers, filterText])

  function handleGroupChange(e) {
    setFilterGroup(e.target.value)
    setPage(1)
    setSelected(null)
  }

  function handleRowClick(s) {
    const next = selected?.email === s.email ? null : s
    setSelected(next)
    if (onSelectSubscriber) onSelectSubscriber(next)
  }

  return (
    <div className="space-y-4">
      {showCreate && (
        <CreateSubscriberModal
          groups={groups}
          onClose={() => setShowCreate(false)}
          onCreated={() => load(page, filterGroup)}
        />
      )}

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500" />
          <Input
            placeholder="Cerca per email, nome o cognome..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="bg-zinc-800 border-neutral-700 text-white placeholder-zinc-500 pl-9"
          />
        </div>
        <select
          value={filterGroup}
          onChange={handleGroupChange}
          className="bg-zinc-800 border border-neutral-700 rounded-md px-3 py-2 text-sm text-white sm:w-48"
        >
          <option value="">Tutti i gruppi</option>
          {groups.map((g, i) => (
            <option key={g.id ?? i} value={String(g.id ?? "")}>{g.title ?? g.name}</option>
          ))}
        </select>
        <Button variant="ghost" size="sm" onClick={() => { setFilterText(""); setFilterGroup(""); setPage(1); load(1, "") }}>
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1" /> Nuovo
        </Button>
      </div>

      {filterText && (
        <p className="text-xs text-neutral-500">{filtered.length} su {subscribers.length} caricati</p>
      )}
      {error && <p className="text-red-400 text-sm">{error}</p>}

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
              {loading ? <TableSkeleton /> : filtered.length === 0 ? (
                <TableRow className="border-neutral-800">
                  <TableCell colSpan={5} className="text-center text-neutral-500 py-12">
                    Nessun subscriber trovato.
                  </TableCell>
                </TableRow>
              ) : filtered.map((s, i) => (
                <TableRow
                  key={s.id ?? safeStr(s.email) ?? i}
                  className={`border-neutral-800 cursor-pointer transition-colors ${
                    selected?.email === s.email ? "bg-orange-500/10" : "hover:bg-white/5"
                  }`}
                  onClick={() => handleRowClick(s)}
                >
                  <TableCell className="text-white text-sm font-mono">{safeStr(s.email) || "—"}</TableCell>
                  <TableCell className="text-neutral-300 text-sm">{safeStr(s.firstname) || "—"}</TableCell>
                  <TableCell className="text-neutral-300 text-sm">{safeStr(s.lastname) || "—"}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {(() => {
                        const raw = getGroups(s)
                        const displayed = raw.length === 0 && filterGroup
                          ? groups.filter((g) => String(g.id) === filterGroup)
                          : raw
                        if (displayed.length === 0) return <span className="text-neutral-600 text-xs">—</span>
                        return <>
                          {displayed.slice(0, 2).map((g, gi) => (
                            <span key={g?.id ?? gi} className="text-xs bg-orange-500/10 border border-orange-500/20 text-orange-300 px-1.5 py-0.5 rounded">
                              {safeStr(g?.title ?? g?.name ?? g?.id) || "—"}
                            </span>
                          ))}
                          {displayed.length > 2 && (
                            <span className="text-xs text-neutral-500">+{displayed.length - 2}</span>
                          )}
                        </>
                      })()}
                    </div>
                  </TableCell>
                  <TableCell>
                    {(() => {
                      const st = safeStr(s?.status?.email) || safeStr(s?.status) || ""
                      return (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          st.toLowerCase() === "active" ? "bg-green-700/60 text-green-200" : "bg-zinc-700 text-zinc-400"
                        }`}>
                          {st || "—"}
                        </span>
                      )
                    })()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between text-sm text-neutral-500">
        <span>Pagina {page} · {filtered.length} subscriber</span>
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
    </div>
  )
}
