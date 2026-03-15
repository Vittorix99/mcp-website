"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Loader2, RefreshCw, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { routes } from "@/config/routes"
import { listErrorLogs, createErrorLog, updateErrorLog, deleteErrorLog } from "@/services/admin/errorLogs"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

const SERVICE_OPTIONS = ["PayPal", "MailerSend", "Pass2U", "Sender"]

const formatDate = (value) => {
  if (!value) return "—"
  try {
    const parsed = new Date(value)
    if (isNaN(parsed.getTime())) return String(value)
    return parsed.toLocaleString("it-IT")
  } catch {
    return String(value)
  }
}

const prettyJson = (value) => {
  if (value === undefined || value === null || value === "") return ""
  if (typeof value === "string") return value
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

export default function ErrorLogsPage() {
  const router = useRouter()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [savingId, setSavingId] = useState(null)

  const [serviceFilter, setServiceFilter] = useState("")
  const [resolvedFilter, setResolvedFilter] = useState("all")
  const [search, setSearch] = useState("")

  const [newService, setNewService] = useState("Pass2U")
  const [newMessage, setNewMessage] = useState("")
  const [newOperation, setNewOperation] = useState("")
  const [newSource, setNewSource] = useState("")
  const [newStatusCode, setNewStatusCode] = useState("")
  const [newPayload, setNewPayload] = useState("")
  const [newContext, setNewContext] = useState("")

  const resolvedFilterValue = useMemo(() => {
    if (resolvedFilter === "resolved") return true
    if (resolvedFilter === "open") return false
    return undefined
  }, [resolvedFilter])

  const loadLogs = async () => {
    setLoading(true)
    const response = await listErrorLogs({
      limit: 200,
      service: serviceFilter || undefined,
      resolved: resolvedFilterValue,
    })
    if (response.error) {
      toast.error(response.error)
      setLoading(false)
      return
    }
    setLogs(Array.isArray(response.error_logs) ? response.error_logs : [])
    setLoading(false)
  }

  useEffect(() => {
    loadLogs()
  }, [serviceFilter, resolvedFilter])

  const filteredLogs = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return logs
    return logs.filter((entry) => {
      const joined = [
        entry.service,
        entry.operation,
        entry.source,
        entry.message,
        prettyJson(entry.payload),
        prettyJson(entry.context),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return joined.includes(q)
    })
  }, [logs, search])

  const handleCreate = async () => {
    if (!newService || !newMessage.trim()) {
      toast.error("Service e messaggio sono obbligatori.")
      return
    }

    let parsedPayload = newPayload.trim()
    let parsedContext = newContext.trim()
    try {
      if (parsedPayload.startsWith("{") || parsedPayload.startsWith("[")) {
        parsedPayload = JSON.parse(parsedPayload)
      }
      if (parsedContext.startsWith("{") || parsedContext.startsWith("[")) {
        parsedContext = JSON.parse(parsedContext)
      }
    } catch {
      toast.error("Payload/Context JSON non validi.")
      return
    }

    setCreating(true)
    const response = await createErrorLog({
      service: newService,
      message: newMessage.trim(),
      operation: newOperation || undefined,
      source: newSource || undefined,
      status_code: newStatusCode ? Number(newStatusCode) : undefined,
      payload: parsedPayload || undefined,
      context: parsedContext || undefined,
    })
    setCreating(false)

    if (response.error) {
      toast.error(response.error)
      return
    }

    toast.success("Errore loggato correttamente.")
    setNewMessage("")
    setNewOperation("")
    setNewSource("")
    setNewStatusCode("")
    setNewPayload("")
    setNewContext("")
    loadLogs()
  }

  const toggleResolved = async (entry) => {
    if (!entry?.id) return
    setSavingId(entry.id)
    const response = await updateErrorLog(entry.id, { resolved: !entry.resolved })
    setSavingId(null)
    if (response.error) {
      toast.error(response.error)
      return
    }
    loadLogs()
  }

  const handleDelete = async (entryId) => {
    if (!entryId) return
    if (!window.confirm("Eliminare questo log errore?")) return
    setDeletingId(entryId)
    const response = await deleteErrorLog(entryId)
    setDeletingId(null)
    if (response.error) {
      toast.error(response.error)
      return
    }
    loadLogs()
  }

  return (
    <div className="mx-auto space-y-6 p-4">
      <Button variant="ghost" onClick={() => router.push(routes.admin.dashboard)}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Torna indietro
      </Button>

      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Error Logs</h1>
          <p className="text-sm text-zinc-400">Log centralizzati degli errori esterni (PayPal, MailerSend, Pass2U, Sender).</p>
        </div>
        <Button onClick={loadLogs} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          Aggiorna
        </Button>
      </div>

      <Card className="bg-zinc-900 border-zinc-700">
        <CardHeader>
          <CardTitle className="text-lg">Nuovo Log Manuale</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-3">
            <select className="rounded-md bg-zinc-800 border border-zinc-700 px-3 py-2" value={newService} onChange={(e) => setNewService(e.target.value)}>
              {SERVICE_OPTIONS.map((service) => (
                <option key={service} value={service}>{service}</option>
              ))}
            </select>
            <Input placeholder="Operation (es. create_order_event)" value={newOperation} onChange={(e) => setNewOperation(e.target.value)} />
            <Input placeholder="Source (es. services.payments...)" value={newSource} onChange={(e) => setNewSource(e.target.value)} />
          </div>
          <Input placeholder="Messaggio errore *" value={newMessage} onChange={(e) => setNewMessage(e.target.value)} />
          <div className="grid gap-3 md:grid-cols-3">
            <Input placeholder="Status code" value={newStatusCode} onChange={(e) => setNewStatusCode(e.target.value)} />
            <Input placeholder='Payload (string o JSON)' value={newPayload} onChange={(e) => setNewPayload(e.target.value)} />
            <Input placeholder='Context (string o JSON)' value={newContext} onChange={(e) => setNewContext(e.target.value)} />
          </div>
          <Button onClick={handleCreate} disabled={creating}>
            {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Crea Log
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-zinc-900 border-zinc-700">
        <CardHeader>
          <CardTitle className="text-lg">Filtri</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <Input placeholder="Cerca testo..." value={search} onChange={(e) => setSearch(e.target.value)} />
          <select className="rounded-md bg-zinc-800 border border-zinc-700 px-3 py-2" value={serviceFilter} onChange={(e) => setServiceFilter(e.target.value)}>
            <option value="">Tutti i servizi</option>
            {SERVICE_OPTIONS.map((service) => (
              <option key={service} value={service}>{service}</option>
            ))}
          </select>
          <select className="rounded-md bg-zinc-800 border border-zinc-700 px-3 py-2" value={resolvedFilter} onChange={(e) => setResolvedFilter(e.target.value)}>
            <option value="all">Tutti</option>
            <option value="open">Aperti</option>
            <option value="resolved">Risolti</option>
          </select>
        </CardContent>
      </Card>

      <Card className="bg-zinc-900 border-zinc-700">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Servizio</TableHead>
                <TableHead>Messaggio</TableHead>
                <TableHead>Operazione</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead className="text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto" />
                  </TableCell>
                </TableRow>
              ) : filteredLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-zinc-500">
                    Nessun errore trovato.
                  </TableCell>
                </TableRow>
              ) : (
                filteredLogs.map((entry) => (
                  <TableRow key={entry.id || `${entry.service}-${entry.created_at}`}>
                    <TableCell>{entry.service || "—"}</TableCell>
                    <TableCell className="max-w-[380px] truncate" title={entry.message || ""}>
                      {entry.message || "—"}
                    </TableCell>
                    <TableCell>{entry.operation || "—"}</TableCell>
                    <TableCell>{entry.status_code ?? "—"}</TableCell>
                    <TableCell>{formatDate(entry.created_at)}</TableCell>
                    <TableCell>
                      {entry.resolved ? (
                        <Badge className="bg-green-700/40 text-green-200">Risolto</Badge>
                      ) : (
                        <Badge variant="secondary">Aperto</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button variant="outline" size="sm" onClick={() => toggleResolved(entry)} disabled={savingId === entry.id}>
                        {savingId === entry.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : entry.resolved ? "Riapri" : "Risolvi"}
                      </Button>
                      <Button variant="destructive" size="icon" onClick={() => handleDelete(entry.id)} disabled={deletingId === entry.id}>
                        {deletingId === entry.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
