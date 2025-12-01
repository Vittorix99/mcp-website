"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Loader2, ArrowLeft, Eye, Send, Trash2 } from "lucide-react"
import { motion } from "framer-motion"
import { Badge } from "@/components/ui/badge"
import { routes } from "@/config/routes"


import { MessagesStats } from "@/components/admin/messages/MessagesStats"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { TooltipProvider } from "@/components/ui/tooltip"

import { useAdminMessages } from "@/hooks/useAdminMessages"
import { PreviewMessageModal } from "@/components/admin/messages/PreviewMessageModal"
import { ReplyMessageModal } from "@/components/admin/messages/ReplyMessageModal"
import { MessagesMobileView } from "@/components/mobile/messages/MessagesMobileView"
import { formatFirestoreTimestamp } from "@/lib/utils"

export default function MessagesPage() {
  const router = useRouter()
  const { messages, loading, reload, deleteMessage, replyToMessage, total, last24h, answeredCount } = useAdminMessages()

  const [search, setSearch] = useState("")
  const [previewMsg, setPreviewMsg] = useState(null)
  const [replyMsg, setReplyMsg] = useState(null)
  const [deletingId, setDeletingId] = useState(null);

  const [nameFilter, setNameFilter] = useState("")
  const [surnameFilter, setSurnameFilter] = useState("")
  const [answeredFilter, setAnsweredFilter] = useState("all") // all | answered | unanswered
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)

  const getMillis = (ts) => {
    if (!ts) return 0
    if (typeof ts?.toMillis === 'function') return ts.toMillis()
    if (typeof ts?.seconds === 'number') return ts.seconds * 1000
    const d = new Date(ts)
    return isNaN(d.getTime()) ? 0 : d.getTime()
  }

  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }
  const selectAllVisible = () => {
    setSelectedIds(new Set(filtered.map(m => m.id)))
  }
  const clearSelection = () => setSelectedIds(new Set())

  const handleBulkDelete = async () => {
    if (!selectedIds.size) return
    if (!confirm(`Eliminare ${selectedIds.size} messaggio/i?`)) return
    setBulkDeleting(true)
    try {
      for (const id of selectedIds) {
        await deleteMessage(id)
      }
      await reload()
      clearSelection()
    } finally {
      setBulkDeleting(false)
    }
  }

  const handleDelete = async (id) => {
  if (confirm("Sei sicuro di voler eliminare questo messaggio?")) {
    setDeletingId(id);
    await deleteMessage(id);
    await reload();
    setDeletingId(null);
  }
};

  useEffect(() => { reload() }, [])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    const nf = nameFilter.trim().toLowerCase()
    const sf = surnameFilter.trim().toLowerCase()

    const list = messages.filter(m => {
      const nameOk = nf ? (m.name || '').toLowerCase().includes(nf) : true
      const surnameOk = sf ? (m.surname || '').toLowerCase().includes(sf) : true
      const answeredOk = answeredFilter === 'all' ? true : answeredFilter === 'answered' ? !!m.answered : !m.answered
      const searchOk = q
        ? ((m.name || '').toLowerCase().includes(q) ||
           (m.email || '').toLowerCase().includes(q) ||
           (m.message || '').toLowerCase().includes(q))
        : true
      return nameOk && surnameOk && answeredOk && searchOk
    })

    // sort by timestamp desc
    return list.sort((a,b) => getMillis(b.timestamp) - getMillis(a.timestamp))
  }, [messages, search, nameFilter, surnameFilter, answeredFilter])

  // Handler per eliminazione e risposta
  const handleReplySend = async ({ email, subject, body, message_id }) => {
    await replyToMessage({ email, subject, body, message_id })
    reload()
  }



  return (
    <TooltipProvider>
      <motion.div className="mx-auto space-y-6 p-4" initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.5 }}>
        <Button variant="ghost" onClick={() => router.push(routes.admin.dashboard)}>
          <ArrowLeft className="mr-2 h-4 w-4"/> Torna indietro
        </Button>

        <h1 className="text-3xl font-bold">Gestione Messaggi</h1>
        <MessagesStats total={total} last24h={last24h} answered={answeredCount} />

        <Card className="bg-zinc-900 border border-zinc-700">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <Input placeholder="Cerca testo / email..." value={search} onChange={e => setSearch(e.target.value)} />
              <Input placeholder="Filtra Nome" value={nameFilter} onChange={e => setNameFilter(e.target.value)} />
              <Input placeholder="Filtra Cognome" value={surnameFilter} onChange={e => setSurnameFilter(e.target.value)} />
              <select
                className="w-full rounded-md bg-zinc-800 border border-zinc-700 px-3 py-2"
                value={answeredFilter}
                onChange={(e) => setAnsweredFilter(e.target.value)}
              >
                <option value="all">Tutti</option>
                <option value="unanswered">Non risposto</option>
                <option value="answered">Risposto</option>
              </select>
            </div>
            <div className="flex flex-wrap items-center gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={reload}>
                <Loader2 className="mr-2 h-4 w-4" /> Aggiorna
              </Button>
              <Button variant="secondary" size="sm" onClick={clearSelection} disabled={!selectedIds.size}>
                Pulisci selezione
              </Button>
              <Button variant="destructive" size="sm" onClick={handleBulkDelete} disabled={!selectedIds.size || bulkDeleting}>
                {bulkDeleting ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin"/>Elimino...</>) : `Elimina selezionati (${selectedIds.size || 0})`}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Desktop View */}
        <Card className="bg-zinc-900 border border-zinc-700 hidden md:block">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <input
                    type="checkbox"
                    aria-label="Seleziona tutti"
                    onChange={(e) => e.target.checked ? selectAllVisible() : clearSelection()}
                    checked={filtered.length > 0 && selectedIds.size === filtered.length}
                    className="h-4 w-4 accent-orange-500"
                  />
                </TableHead>
                <TableHead>Nome e Cognome</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Messaggio</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Risposto?</TableHead>
                <TableHead className="text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading
                ? (<TableRow><TableCell colSpan={7} className="py-12 text-center"><Loader2 className="animate-spin h-8 w-8 mx-auto"/></TableCell></TableRow>)
                : filtered.length
                  ? filtered.map(m => (
                    <TableRow key={m.id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(m.id)}
                          onChange={() => toggleSelect(m.id)}
                          className="h-4 w-4 accent-orange-500"
                          aria-label={`Seleziona messaggio ${m.id}`}
                        />
                      </TableCell>
                      <TableCell>{m.name}</TableCell>
                      <TableCell>{m.email}</TableCell>
                      <TableCell className="truncate max-w-sm" title={m.message}>{m.message}</TableCell>
                      <TableCell>{m.timestamp ? formatFirestoreTimestamp(m.timestamp) : "-"}</TableCell>
                      <TableCell>
                          {m.answered ? (
                            <Badge variant="success" className="text-xs p-2">Risposto</Badge>
                          ) : (
                            <Badge variant="secondary" className="text-xs p-2 text-gray-400">Non Risposto</Badge>
                          )}
                        </TableCell>
                      <TableCell className="text-right space-x-2">
                        {deletingId === m.id ? (
                          <Loader2 className="h-4 w-4 animate-spin text-red-500 mx-auto" />
                        ) : (
                          <>
                            <Button size="icon" variant="ghost" onClick={() => setPreviewMsg(m)}><Eye className="h-4 w-4" /></Button>
                            <Button size="icon" variant="ghost" onClick={() => setReplyMsg(m)}><Send className="h-4 w-4" /></Button>
                            <Button size="icon" variant="destructive" onClick={() => handleDelete(m.id)}><Trash2 className="h-4 w-4" /></Button>
                          </>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                  : (<TableRow><TableCell colSpan={7} className="py-12 text-center text-gray-500">Nessun messaggio trovato.</TableCell></TableRow>)
              }
            </TableBody>
          </Table>
        </Card>

        {/* Mobile View */}
        <div className="block md:hidden">
          <MessagesMobileView
            messages={filtered}
            loading={loading}
            onPreview={setPreviewMsg}
            onReply={setReplyMsg}
            onDelete={handleDelete}
          />
        </div>

        {!!previewMsg && <PreviewMessageModal isOpen onClose={() => setPreviewMsg(null)} message={previewMsg} />}
        {!!replyMsg && <ReplyMessageModal isOpen onClose={() => setReplyMsg(null)} message={replyMsg} onSend={handleReplySend} />}
      </motion.div>
    </TooltipProvider>
  )
}