"use client"

import { useState, useEffect, useCallback } from "react"
import { Plus, Trash2, AlertTriangle, Loader2, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { listSenderFields, createSenderField, deleteSenderField } from "@/services/admin/sender"

const FIELD_TYPES = ["string", "number", "date", "boolean"]

function CreateFieldModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ title: "", type: "string" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.title.trim()) return
    setLoading(true)
    setError(null)
    try {
      await createSenderField({ title: form.title.trim(), type: form.type })
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
      <DialogContent className="sm:max-w-sm bg-zinc-900 border-neutral-800 text-white">
        <DialogHeader><DialogTitle>Nuovo campo personalizzato</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="space-y-1">
            <Label>Titolo <span className="text-red-400">*</span></Label>
            <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              required placeholder="es. membership_id" className="bg-zinc-800 border-neutral-700 text-white" />
          </div>
          <div className="space-y-1">
            <Label>Tipo</Label>
            <select value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
              className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white">
              {FIELD_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Crea"}
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function FieldsTab() {
  const [fields, setFields] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listSenderFields()
      const data = res?.data ?? res ?? []
      setFields(Array.isArray(data) ? data : [])
    } catch {
      setError("Impossibile caricare i campi.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleDelete(f) {
    if (!confirm(`Eliminare il campo "${f.title}"?\n\nAttenzione: viene rimosso da tutti i subscriber.`)) return
    await deleteSenderField(f.id)
    load()
  }

  return (
    <div className="space-y-4">
      {showCreate && <CreateFieldModal onClose={() => setShowCreate(false)} onCreated={load} />}

      <div className="flex items-center justify-between">
        <p className="text-sm text-neutral-400">{fields.length} campi personalizzati</p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1" /> Nuovo campo
        </Button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400">Titolo</TableHead>
                <TableHead className="text-neutral-400">Tipo</TableHead>
                <TableHead className="text-neutral-400 text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i} className="border-neutral-800">
                    <TableCell><Skeleton className="h-4 w-36 bg-zinc-800" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20 bg-zinc-800" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16 bg-zinc-800" /></TableCell>
                  </TableRow>
                ))
              ) : fields.length === 0 ? (
                <TableRow className="border-neutral-800">
                  <TableCell colSpan={3} className="text-center text-neutral-500 py-12">
                    Nessun campo personalizzato.
                  </TableCell>
                </TableRow>
              ) : fields.map((f, fi) => (
                <TableRow key={f.id ?? fi} className="border-neutral-800 hover:bg-white/5">
                  <TableCell className="text-white font-medium font-mono text-sm">{f.title}</TableCell>
                  <TableCell>
                    <span className="text-xs bg-zinc-800 text-neutral-300 px-2 py-0.5 rounded font-mono">
                      {f.type ?? "string"}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end">
                      <button onClick={() => handleDelete(f)} title="Elimina" className="text-red-400 hover:text-red-300">
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

      {fields.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-yellow-500/80">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          Eliminare un campo lo rimuove da tutti i subscriber in Sender.
        </div>
      )}
    </div>
  )
}
