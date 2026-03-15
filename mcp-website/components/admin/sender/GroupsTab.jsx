"use client"

import { useState, useEffect, useCallback } from "react"
import { Plus, Pencil, Trash2, Users, X, Loader2, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  listSenderGroups,
  createSenderGroup,
  renameSenderGroup,
  deleteSenderGroup,
  listSenderGroupSubscribers,
} from "@/services/admin/sender"

const safeStr = (v) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : "")

const PAGE_SIZE = 25

function SubscribersModal({ group, onClose }) {
  const [subs, setSubs] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)

  useEffect(() => {
    setLoading(true)
    listSenderGroupSubscribers(group.id, { limit: PAGE_SIZE, page })
      .then((res) => {
        const data = Array.isArray(res) ? res : Array.isArray(res?.data) ? res.data : []
        setSubs(data)
        const meta = res?.meta
        setHasMore(meta
          ? (meta.current_page ?? page) < (meta.last_page ?? 1)
          : data.length === PAGE_SIZE
        )
      })
      .catch(() => setSubs([]))
      .finally(() => setLoading(false))
  }, [group.id, page])

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg bg-zinc-900 border-neutral-800 text-white max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Subscribers — {group.title ?? group.name}</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto space-y-1 mt-2">
          {loading
            ? <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-neutral-400" /></div>
            : subs.length === 0
              ? <p className="text-neutral-500 text-sm text-center py-8">Nessun subscriber.</p>
              : subs.map((s, i) => (
                <div key={s.id ?? i} className="flex justify-between py-1.5 border-b border-neutral-800 last:border-0">
                  <span className="text-sm text-white">{safeStr(s.email)}</span>
                  <span className="text-xs text-neutral-500">{[safeStr(s.firstname), safeStr(s.lastname)].filter(Boolean).join(" ")}</span>
                </div>
              ))
          }
        </div>
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-neutral-500">Pagina {page} · {subs.length} subscriber</p>
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" disabled={page === 1 || loading} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" disabled={!hasMore || loading} onClick={() => setPage((p) => p + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="mt-1 self-start">Chiudi</Button>
      </DialogContent>
    </Dialog>
  )
}

function RenameModal({ group, onClose, onRenamed }) {
  const [title, setTitle] = useState(group.title ?? group.name ?? "")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!title.trim()) return
    setLoading(true)
    try {
      await renameSenderGroup(group.id, title.trim())
      onRenamed()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-sm bg-zinc-900 border-neutral-800 text-white">
        <DialogHeader><DialogTitle>Rinomina gruppo</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="space-y-1">
            <Label>Nome</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} required
              className="bg-zinc-800 border-neutral-700 text-white" />
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salva"}
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function GroupsTab() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newTitle, setNewTitle] = useState("")
  const [creating, setCreating] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [viewGroup, setViewGroup] = useState(null)
  const [renameGroup, setRenameGroup] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listSenderGroups()
      const data = res?.data ?? res ?? []
      setGroups(Array.isArray(data) ? data : [])
    } catch {
      setError("Impossibile caricare i gruppi.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate(e) {
    e.preventDefault()
    if (!newTitle.trim()) return
    setCreateLoading(true)
    try {
      await createSenderGroup(newTitle.trim())
      setNewTitle("")
      setCreating(false)
      load()
    } finally {
      setCreateLoading(false)
    }
  }

  async function handleDelete(g) {
    if (!confirm(`Eliminare il gruppo "${g.title ?? g.name}"?`)) return
    await deleteSenderGroup(g.id)
    load()
  }

  return (
    <div className="space-y-4">
      {viewGroup && <SubscribersModal group={viewGroup} onClose={() => setViewGroup(null)} />}
      {renameGroup && <RenameModal group={renameGroup} onClose={() => setRenameGroup(null)} onRenamed={load} />}

      <div className="flex items-center justify-between">
        <p className="text-sm text-neutral-400">{groups.length} gruppi</p>
        <Button size="sm" onClick={() => setCreating(true)}>
          <Plus className="h-4 w-4 mr-1" /> Nuovo gruppo
        </Button>
      </div>

      {creating && (
        <form onSubmit={handleCreate} className="flex gap-2">
          <Input value={newTitle} onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Nome gruppo" required autoFocus
            className="bg-zinc-800 border-neutral-700 text-white" />
          <Button type="submit" size="sm" disabled={createLoading}>
            {createLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Crea"}
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={() => setCreating(false)}>
            <X className="h-4 w-4" />
          </Button>
        </form>
      )}

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400">Nome</TableHead>
                <TableHead className="text-neutral-400">Subscriber</TableHead>
                <TableHead className="text-neutral-400 text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i} className="border-neutral-800">
                    <TableCell><Skeleton className="h-4 w-36 bg-zinc-800" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16 bg-zinc-800" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24 bg-zinc-800" /></TableCell>
                  </TableRow>
                ))
              ) : groups.length === 0 ? (
                <TableRow className="border-neutral-800">
                  <TableCell colSpan={3} className="text-center text-neutral-500 py-12">
                    Nessun gruppo. Creane uno per iniziare.
                  </TableCell>
                </TableRow>
              ) : groups.map((g, gi) => (
                <TableRow key={g.id ?? gi} className="border-neutral-800 hover:bg-white/5">
                  <TableCell className="text-white font-medium">{g.title ?? g.name}</TableCell>
                  <TableCell className="text-neutral-400 text-sm">
                    {g.count != null ? g.count.toLocaleString() : "—"}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => setViewGroup(g)} title="Vedi subscribers" className="text-blue-400 hover:text-blue-300">
                        <Users className="h-4 w-4" />
                      </button>
                      <button onClick={() => setRenameGroup(g)} title="Rinomina" className="text-neutral-400 hover:text-neutral-200">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(g)} title="Elimina" className="text-red-400 hover:text-red-300">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
