"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Loader2, ArrowLeft, Eye, Send, Trash2 } from "lucide-react"
import { motion } from "framer-motion"
import { Badge } from "@/components/ui/badge"


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
    return messages.filter(m =>
      m.name?.toLowerCase().includes(q) ||
      m.email?.toLowerCase().includes(q) ||
      m.message?.toLowerCase().includes(q)
    )
  }, [messages, search])

  // Handler per eliminazione e risposta
  const handleReplySend = async ({ email, subject, body, message_id }) => {
    await replyToMessage({ email, subject, body, message_id })
    reload()
  }



  return (
    <TooltipProvider>
      <motion.div className="mx-auto space-y-6 p-4" initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.5 }}>
        <Button variant="ghost" onClick={() => router.push("/admin")}>
          <ArrowLeft className="mr-2 h-4 w-4"/> Torna indietro
        </Button>

        <h1 className="text-3xl font-bold">Gestione Messaggi</h1>
        <MessagesStats total={total} last24h={last24h} answered={answeredCount} />

        <Card className="bg-zinc-900 border border-zinc-700">
          <CardContent className="p-4">
            <Input placeholder="Cerca per nome, email o testo..." value={search} onChange={e => setSearch(e.target.value)} />
          </CardContent>
        </Card>

        {/* Desktop View */}
        <Card className="bg-zinc-900 border border-zinc-700 hidden md:block">
          <Table>
            <TableHeader>
              <TableRow>
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
                ? (<TableRow><TableCell colSpan={6} className="py-12 text-center"><Loader2 className="animate-spin h-8 w-8 mx-auto"/></TableCell></TableRow>)
                : filtered.length
                  ? filtered.map(m => (
                    <TableRow key={m.id}>
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
                  : (<TableRow><TableCell colSpan={6} className="py-12 text-center text-gray-500">Nessun messaggio trovato.</TableCell></TableRow>)
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