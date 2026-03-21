"use client"

import { useState, useEffect, useCallback } from "react"
import { Users, Trash2, Info, Loader2 } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { listSenderSegments, deleteSenderSegment, listSenderSegmentSubscribers } from "@/services/admin/sender"

const safeStr = (v) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : "")

function SubscribersModal({ segment, onClose }) {
  const [subs, setSubs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listSenderSegmentSubscribers(segment.id).then((res) => {
      const data = res?.data ?? res ?? []
      setSubs(Array.isArray(data) ? data : [])
    }).catch(() => setSubs([])).finally(() => setLoading(false))
  }, [segment.id])

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg bg-zinc-900 border-neutral-800 text-white max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Subscribers — {segment.title ?? segment.name}</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto space-y-1 mt-2">
          {loading ? <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-neutral-400" /></div>
            : subs.length === 0 ? <p className="text-neutral-500 text-sm text-center py-8">Nessun subscriber.</p>
            : subs.map((s, i) => (
              <div key={s.id ?? i} className="flex justify-between py-1.5 border-b border-neutral-800 last:border-0">
                <span className="text-sm text-white">{safeStr(s.email)}</span>
                <span className="text-xs text-neutral-500">{[safeStr(s.firstname), safeStr(s.lastname)].filter(Boolean).join(" ")}</span>
              </div>
            ))}
        </div>
        <p className="text-xs text-neutral-500 pt-2">{subs.length} subscriber</p>
        <Button variant="ghost" size="sm" onClick={onClose} className="mt-1 self-start">Chiudi</Button>
      </DialogContent>
    </Dialog>
  )
}

export default function SegmentsTab() {
  const [segments, setSegments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleteError, setDeleteError] = useState(null)
  const [viewSegment, setViewSegment] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listSenderSegments()
      const data = res?.data ?? res ?? []
      setSegments(Array.isArray(data) ? data : [])
    } catch {
      setError("Impossibile caricare i segmenti.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleDelete(s) {
    if (!confirm(`Eliminare il segmento "${s.title ?? s.name}"?`)) return
    setDeleteError(null)
    const res = await deleteSenderSegment(s.id)
    if (res?.error) { setDeleteError(res.error); return }
    load()
  }

  return (
    <div className="space-y-4">
      {viewSegment && <SubscribersModal segment={viewSegment} onClose={() => setViewSegment(null)} />}

      <div className="flex items-start gap-3 bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-3">
        <Info className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
        <p className="text-sm text-blue-300">
          I segmenti vengono creati dalla dashboard Sender. Qui puoi visualizzarli ed eliminarli.
        </p>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
      {deleteError && <p className="text-red-400 text-sm">{deleteError}</p>}

      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400">Nome</TableHead>
                <TableHead className="text-neutral-400">Descrizione</TableHead>
                <TableHead className="text-neutral-400 text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i} className="border-neutral-800">
                    <TableCell><Skeleton className="h-4 w-36 bg-zinc-800" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-48 bg-zinc-800" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20 bg-zinc-800" /></TableCell>
                  </TableRow>
                ))
              ) : segments.length === 0 ? (
                <TableRow className="border-neutral-800">
                  <TableCell colSpan={3} className="text-center text-neutral-500 py-12">
                    Nessun segmento trovato.
                  </TableCell>
                </TableRow>
              ) : segments.map((s, si) => (
                <TableRow key={s.id ?? si} className="border-neutral-800 hover:bg-white/5">
                  <TableCell className="text-white font-medium">{s.title ?? s.name}</TableCell>
                  <TableCell className="text-neutral-400 text-sm">{s.description || "—"}</TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => setViewSegment(s)} title="Vedi subscribers" className="text-blue-400 hover:text-blue-300">
                        <Users className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(s)} title="Elimina" className="text-red-400 hover:text-red-300">
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
