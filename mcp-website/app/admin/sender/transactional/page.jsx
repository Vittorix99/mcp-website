"use client"

import { useState, useEffect, useCallback } from "react"
import { Plus, Send, Trash2, Info, Loader2, ArrowLeft } from "lucide-react"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { routes } from "@/config/routes"
import {
  listSenderTransactionalCampaigns,
  createSenderTransactionalCampaign,
  sendSenderTransactionalCampaign,
  deleteSenderTransactionalCampaign,
} from "@/services/admin/sender"

function TableSkeleton() {
  return Array.from({ length: 3 }).map((_, i) => (
    <TableRow key={i} className="border-neutral-800">
      <TableCell><Skeleton className="h-4 w-32 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-40 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-28 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-20 bg-zinc-800" /></TableCell>
    </TableRow>
  ))
}

// Create transactional campaign modal
function CreateModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ title: "", subject: "", from_name: "", from_email: "", content_html: "" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const charCount = form.content_html.length

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onClose])

  function onInput(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.title || !form.subject || !form.from_name || !form.from_email || !form.content_html) {
      setError("Compila tutti i campi obbligatori.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      await createSenderTransactionalCampaign(form)
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
      <DialogContent className="sm:max-w-2xl bg-zinc-900 border-neutral-800 text-white max-h-[90vh] overflow-y-auto">
        <DialogHeader><DialogTitle>Nuova campagna transazionale</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="grid grid-cols-2 gap-4">
            {[
              { name: "title", label: "Title", placeholder: "Es. Biglietto evento" },
              { name: "subject", label: "Subject", placeholder: "Oggetto email" },
              { name: "from_name", label: "From name", placeholder: "Music Connecting People" },
              { name: "from_email", label: "From email", type: "email", placeholder: "info@mcp.com" },
            ].map(({ name, label, placeholder, type }) => (
              <div key={name} className="space-y-1">
                <Label>{label} <span className="text-red-400">*</span></Label>
                <Input name={name} type={type || "text"} value={form[name]} onChange={onInput} required
                  placeholder={placeholder}
                  className="bg-zinc-800 border-neutral-700 text-white" />
              </div>
            ))}
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label>HTML Content <span className="text-red-400">*</span></Label>
              <span className="text-xs text-neutral-500">{charCount.toLocaleString()} caratteri</span>
            </div>
            <p className="text-xs text-neutral-500">Incolla qui il tuo template HTML completo</p>
            <textarea
              name="content_html"
              value={form.content_html}
              onChange={onInput}
              required
              rows={12}
              placeholder="<!DOCTYPE html><html>..."
              className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white font-mono placeholder-zinc-600 resize-y"
              style={{ minHeight: 400 }}
              onKeyDown={(e) => {
                if (e.key === "Tab") {
                  e.preventDefault()
                  const s = e.target.selectionStart
                  const en = e.target.selectionEnd
                  const v = form.content_html
                  setForm((f) => ({ ...f, content_html: v.slice(0, s) + "  " + v.slice(en) }))
                  requestAnimationFrame(() => { e.target.selectionStart = e.target.selectionEnd = s + 2 })
                }
              }}
            />
          </div>

          {form.content_html && (
            <div className="rounded border border-neutral-700 overflow-hidden">
              <p className="text-xs text-neutral-500 px-3 py-1 bg-zinc-800">Preview</p>
              <iframe srcDoc={form.content_html} sandbox="allow-same-origin"
                className="w-full bg-white border-0" style={{ height: 260 }} title="preview" />
            </div>
          )}

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="flex gap-2 pt-1">
            <Button type="submit" disabled={loading}>
              {loading ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Creazione...</> : "Crea"}
            </Button>
            <Button type="button" variant="ghost" onClick={onClose}>Annulla</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// Send test modal
function SendTestModal({ campaign, onClose }) {
  const [form, setForm] = useState({ to_email: "", to_name: "", variables: "" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sent, setSent] = useState(false)

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onClose])

  function onInput(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      let variables = undefined
      if (form.variables.trim()) {
        try { variables = JSON.parse(form.variables) }
        catch { setError("Variables non è un JSON valido."); setLoading(false); return }
      }
      await sendSenderTransactionalCampaign(campaign.id, {
        to_email: form.to_email,
        to_name: form.to_name,
        variables,
      })
      setSent(true)
    } catch {
      setError("Errore durante l'invio.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-zinc-900 border-neutral-800 text-white">
        <DialogHeader>
          <DialogTitle>Invia test — {campaign.title}</DialogTitle>
        </DialogHeader>
        {sent ? (
          <div className="py-4 space-y-3">
            <p className="text-green-400 text-sm">Email inviata con successo a {form.to_email}.</p>
            <Button variant="ghost" size="sm" onClick={onClose}>Chiudi</Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 mt-2">
            <div className="space-y-1">
              <Label>Email destinatario <span className="text-red-400">*</span></Label>
              <Input name="to_email" type="email" value={form.to_email} onChange={onInput} required
                placeholder="test@esempio.com"
                className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
            <div className="space-y-1">
              <Label>Nome destinatario</Label>
              <Input name="to_name" value={form.to_name} onChange={onInput}
                placeholder="Mario Rossi"
                className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
            <div className="space-y-1">
              <Label>Variables <span className="text-neutral-500 text-xs">(JSON opzionale)</span></Label>
              <textarea
                name="variables"
                value={form.variables}
                onChange={onInput}
                rows={3}
                placeholder='{"firstname": "Mario", "event_name": "Opening Night"}'
                className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white font-mono placeholder-zinc-600"
              />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Send className="h-4 w-4 mr-1" />Invia</>}
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default function SenderTransactionalPage() {
  const router = useRouter()
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [testTarget, setTestTarget] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listSenderTransactionalCampaigns()
      const data = res?.data ?? res ?? []
      setCampaigns(Array.isArray(data) ? data : [])
    } catch {
      setError("Impossibile caricare le campagne transazionali.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleDelete(c) {
    if (!confirm(`Eliminare "${c.title}"?`)) return
    await deleteSenderTransactionalCampaign(c.id)
    load()
  }

  return (
    <motion.div
      className="space-y-6 pb-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {showCreate && <CreateModal onClose={() => setShowCreate(false)} onCreated={load} />}
      {testTarget && <SendTestModal campaign={testTarget} onClose={() => setTestTarget(null)} />}

      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <Button variant="ghost" onClick={() => router.push(routes.admin.sender.campaigns)} className="mb-1 -ml-2">
            <ArrowLeft className="mr-2 h-4 w-4" /> Campagne
          </Button>
          <h1 className="text-3xl md:text-4xl font-bold gradient-text mt-2">Email Transazionali</h1>
          <p className="text-gray-300">Template per email automatiche via API.</p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)} className="mt-1 md:mt-10">
          <Plus className="h-4 w-4 mr-1" /> Nuova campagna
        </Button>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-3">
        <Info className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
        <p className="text-sm text-blue-300">
          Le email transazionali vengono inviate singolarmente via API dal backend.
          Usa questa sezione per gestire e testare i template.
        </p>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <div className="rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-neutral-800 hover:bg-transparent">
                  <TableHead className="text-neutral-400">Title</TableHead>
                  <TableHead className="text-neutral-400">Subject</TableHead>
                  <TableHead className="text-neutral-400">From</TableHead>
                  <TableHead className="text-neutral-400 text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableSkeleton />
                ) : campaigns.length === 0 ? (
                  <TableRow className="border-neutral-800">
                    <TableCell colSpan={4} className="text-center text-neutral-500 py-12">
                      Nessuna campagna transazionale. Creane una per iniziare.
                    </TableCell>
                  </TableRow>
                ) : (
                  campaigns.map((c) => (
                    <TableRow key={c.id} className="border-neutral-800 hover:bg-white/5">
                      <TableCell className="text-white font-medium">{c.title}</TableCell>
                      <TableCell className="text-neutral-300 text-sm">{c.subject}</TableCell>
                      <TableCell className="text-neutral-400 text-sm">
                        {c.from?.name ?? c.from_name ?? "—"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-2">
                          <button onClick={() => setTestTarget(c)} title="Invia test"
                            className="text-blue-400 hover:text-blue-300">
                            <Send className="h-4 w-4" />
                          </button>
                          <button onClick={() => handleDelete(c)} title="Elimina"
                            className="text-red-400 hover:text-red-300">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
