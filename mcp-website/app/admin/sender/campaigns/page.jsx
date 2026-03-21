"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Plus, Send, Copy, Trash2, Clock, Loader2, BarChart2, ArrowLeft } from "lucide-react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { routes } from "@/config/routes"
import { getAllEventsAdmin } from "@/services/admin/events"
import { buildEventCampaignTemplate, getEventTemplateTypes, getEventPublicUrl } from "@/lib/event-email-templates"
import {
  listSenderCampaigns,
  listSenderGroups,
  createSenderCampaign,
  sendSenderCampaign,
  scheduleSenderCampaign,
  cancelSenderCampaignSchedule,
  deleteSenderCampaign,
  copySenderCampaign,
} from "@/services/admin/sender"

// ------------------------------------------------------------------ //
// Status badge
// ------------------------------------------------------------------ //

/** Returns the first HTTP URL found in event.photoPath or event.image */
function getEventImageUrl(event) {
  const candidates = [event?.photoPath, event?.image]
  for (const v of candidates) {
    const s = String(v ?? "").trim()
    if (/^https?:\/\//i.test(s)) return s
  }
  return ""
}

const STATUS_COLORS = {
  draft:     "bg-zinc-700 text-zinc-200",
  scheduled: "bg-yellow-600/80 text-yellow-100",
  sent:      "bg-green-700/80 text-green-100",
  sending:   "bg-blue-600/80 text-blue-100",
}
const EVENT_TEMPLATE_TYPES = getEventTemplateTypes()

function StatusBadge({ status }) {
  const key = (status || "").toLowerCase()
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[key] || "bg-zinc-700 text-zinc-300"}`}>
      {status || "—"}
    </span>
  )
}

// ------------------------------------------------------------------ //
// Skeleton rows
// ------------------------------------------------------------------ //

function TableSkeleton() {
  return Array.from({ length: 5 }).map((_, i) => (
    <TableRow key={i} className="border-neutral-800">
      <TableCell><Skeleton className="h-4 w-40 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-48 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-20 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-28 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-32 bg-zinc-800" /></TableCell>
    </TableRow>
  ))
}

// ------------------------------------------------------------------ //
// Schedule modal
// ------------------------------------------------------------------ //

function ScheduleModal({ campaign, onClose, onSaved }) {
  const [datetime, setDatetime] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onClose])

  async function handleSchedule(e) {
    e.preventDefault()
    if (!datetime) return
    setLoading(true)
    setError(null)
    const res = await scheduleSenderCampaign(campaign.id, new Date(datetime).toISOString())
    setLoading(false)
    if (res?.error) {
      setError(`Schedulazione fallita: ${res.error}`)
      return
    }
    onSaved()
    onClose()
  }

  async function handleCancel() {
    if (!confirm("Annullare la schedulazione?")) return
    setLoading(true)
    try {
      await cancelSenderCampaignSchedule(campaign.id)
      onSaved()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-zinc-900 border-neutral-800 text-white">
        <DialogHeader>
          <DialogTitle>Schedula campagna</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-neutral-400 truncate">{campaign.title}</p>
        <form onSubmit={handleSchedule} className="space-y-4 mt-2">
          <div className="space-y-1">
            <Label>Data e ora di invio</Label>
            <input
              type="datetime-local"
              required
              value={datetime}
              onChange={(e) => setDatetime(e.target.value)}
              className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white"
            />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Schedula"}
            </Button>
            {campaign.status === "scheduled" && (
              <Button type="button" variant="destructive" size="sm" onClick={handleCancel} disabled={loading}>
                Annulla schedulazione
              </Button>
            )}
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>Chiudi</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ------------------------------------------------------------------ //
// Create campaign modal
// ------------------------------------------------------------------ //

function CreateCampaignModal({
  onClose, onCreated,
  groups, events,
  form, setForm,
  selectedEventId, setSelectedEventId,
  templateType, setTemplateType,
  ctaUrl, setCtaUrl,
  eventImageUrl, setEventImageUrl,
  logoUrl, setLogoUrl,
  unsubscribeUrl, setUnsubscribeUrl,
  includeLineup, setIncludeLineup,
}) {
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

  function toggleGroup(id) {
    setForm((f) => ({
      ...f,
      selectedGroups: f.selectedGroups.includes(id)
        ? f.selectedGroups.filter((g) => g !== id)
        : [...f.selectedGroups, id],
    }))
  }

  function handleEventChange(eventId) {
    setSelectedEventId(eventId)
    const selected = events.find((evt) => String(evt.id) === String(eventId))
    if (!selected) return
    // Always update CTA URL and image when user explicitly changes the event
    setCtaUrl(getEventPublicUrl(selected))
    setEventImageUrl(getEventImageUrl(selected))
  }

  function handleGenerateTemplate() {
    const selected = events.find((evt) => String(evt.id) === String(selectedEventId))
    if (!selected) {
      setError("Seleziona un evento per generare il template.")
      return
    }

    const built = buildEventCampaignTemplate({
      type: templateType,
      event: selected,
      ctaUrl: ctaUrl || getEventPublicUrl(selected),
      imageUrl: eventImageUrl,
      logoUrl,
      unsubscribeUrl,
      includeLineup,
    })

    setForm((prev) => ({
      ...prev,
      title: built.title,
      subject: built.subject,
      content_html: built.html,
    }))
    setError(null)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.subject || !form.from_name || !form.content_html) {
      setError("Compila tutti i campi obbligatori.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      await createSenderCampaign({
        title: form.title || undefined,
        subject: form.subject,
        from_name: form.from_name,
        from_email: "no-reply@musiconnectingpeople.com",
        reply_to: "no-reply@musiconnectingpeople.com",
        content_html: form.content_html,
        groups: form.selectedGroups.length ? form.selectedGroups : undefined,
      })
      setForm({ title: "", subject: "", from_name: "Music Connecting People", from_email: "", reply_to: "", content_html: "", selectedGroups: [] })
      onCreated()
      onClose()
    } catch {
      setError("Errore durante la creazione della campagna.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-zinc-900 border-neutral-800 text-white max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nuova campagna</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label>Title <span className="text-neutral-500 text-xs">(opzionale)</span></Label>
              <Input name="title" value={form.title} onChange={onInput}
                placeholder="Nome interno campagna"
                className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
            <div className="space-y-1">
              <Label>Subject <span className="text-red-400">*</span></Label>
              <Input name="subject" value={form.subject} onChange={onInput} required
                placeholder="Oggetto email"
                className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
            <div className="space-y-1 col-span-2">
              <Label>From name <span className="text-neutral-500 text-xs">(nome visualizzato dal destinatario)</span> <span className="text-red-400">*</span></Label>
              <Input name="from_name" value={form.from_name} onChange={onInput} required
                placeholder="Music Connecting People"
                className="bg-zinc-800 border-neutral-700 text-white" />
            </div>
          </div>

          {/* Groups multi-select */}
          {groups.length > 0 && (
            <div className="space-y-2">
              <Label>Gruppi destinatari</Label>
              <div className="flex flex-wrap gap-2">
                {groups.map((g) => {
                  const selected = form.selectedGroups.includes(g.id)
                  return (
                    <button
                      key={g.id}
                      type="button"
                      onClick={() => toggleGroup(g.id)}
                      className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                        selected
                          ? "bg-orange-500/20 border-orange-500 text-orange-300"
                          : "bg-zinc-800 border-neutral-700 text-neutral-400 hover:border-neutral-500"
                      }`}
                    >
                      {g.title ?? g.name}
                      {g.count != null && <span className="ml-1 text-neutral-500">({g.count})</span>}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          <div className="rounded border border-neutral-700 bg-zinc-950/60 p-3 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <Label className="text-white">Template builder evento</Label>
              <span className="text-xs text-neutral-500">Genera HTML predefinito con variabili subscriber/evento</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Evento</Label>
                <select
                  value={selectedEventId}
                  onChange={(e) => handleEventChange(e.target.value)}
                  className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white"
                >
                  <option value="">Seleziona evento</option>
                  {events.map((evt) => (
                    <option key={evt.id} value={evt.id}>
                      {evt.title || evt.id}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Template</Label>
                <select
                  value={templateType}
                  onChange={(e) => setTemplateType(e.target.value)}
                  className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white"
                >
                  {EVENT_TEMPLATE_TYPES.map((tpl) => (
                    <option key={tpl.id} value={tpl.id}>{tpl.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1 md:col-span-2">
                <Label>CTA URL evento</Label>
                <Input
                  value={ctaUrl}
                  onChange={(e) => setCtaUrl(e.target.value)}
                  placeholder="https://musiconnectingpeople.com/events/slug-evento"
                  className="bg-zinc-800 border-neutral-700 text-white"
                />
              </div>
              <div className="space-y-1 md:col-span-2">
                <Label>Immagine evento URL</Label>
                <Input
                  value={eventImageUrl}
                  onChange={(e) => setEventImageUrl(e.target.value)}
                  placeholder="https://.../flyer.jpg"
                  className="bg-zinc-800 border-neutral-700 text-white"
                />
              </div>
              <div className="space-y-1">
                <Label>Logo URL</Label>
                <Input
                  value={logoUrl}
                  onChange={(e) => setLogoUrl(e.target.value)}
                  placeholder="https://.../logo.png"
                  className="bg-zinc-800 border-neutral-700 text-white"
                />
              </div>
              <div className="space-y-1">
                <Label>Unsubscribe URL / merge tag</Label>
                <Input
                  value={unsubscribeUrl}
                  onChange={(e) => setUnsubscribeUrl(e.target.value)}
                  placeholder="{{unsubscribe_url}}"
                  className="bg-zinc-800 border-neutral-700 text-white"
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-neutral-300 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={includeLineup}
                  onChange={(e) => setIncludeLineup(e.target.checked)}
                  className="accent-orange-500"
                />
                Includi lineup
              </label>
              <Button type="button" variant="secondary" onClick={handleGenerateTemplate} disabled={!selectedEventId}>
                Genera template evento
              </Button>
            </div>
          </div>

          {/* HTML content */}
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
              rows={14}
              placeholder="<!DOCTYPE html><html>..."
              className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white font-mono placeholder-zinc-600 resize-y"
              style={{ minHeight: 400 }}
              onKeyDown={(e) => {
                if (e.key === "Tab") {
                  e.preventDefault()
                  const start = e.target.selectionStart
                  const end = e.target.selectionEnd
                  const val = form.content_html
                  setForm((f) => ({ ...f, content_html: val.slice(0, start) + "  " + val.slice(end) }))
                  requestAnimationFrame(() => {
                    e.target.selectionStart = e.target.selectionEnd = start + 2
                  })
                }
              }}
            />
          </div>

          {/* Live preview */}
          {form.content_html && (
            <div className="rounded border border-neutral-700 overflow-hidden">
              <p className="text-xs text-neutral-500 px-3 py-1 bg-zinc-800">Preview</p>
              <iframe
                srcDoc={form.content_html}
                sandbox="allow-same-origin"
                className="w-full bg-white border-0"
                style={{ height: 300 }}
                title="HTML preview"
              />
            </div>
          )}

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={loading}>
              {loading ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Creazione...</> : "Crea campagna"}
            </Button>
            <Button type="button" variant="ghost" onClick={onClose}>Annulla</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ------------------------------------------------------------------ //
// Main page
// ------------------------------------------------------------------ //

export default function SenderCampaignsPage() {
  const router = useRouter()
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [scheduleTarget, setScheduleTarget] = useState(null)

  // Persistent modal state — survives open/close
  const [modalGroups, setModalGroups] = useState([])
  const [modalEvents, setModalEvents] = useState([])
  const [modalForm, setModalForm] = useState({
    title: "", subject: "",
    from_name: "Music Connecting People",
    from_email: "", reply_to: "",
    content_html: "", selectedGroups: [],
  })
  const [modalSelectedEventId, setModalSelectedEventId] = useState("")
  const [modalTemplateType, setModalTemplateType] = useState("event_announcement")
  const [modalCtaUrl, setModalCtaUrl] = useState("")
  const [modalEventImageUrl, setModalEventImageUrl] = useState("")
  const [modalLogoUrl, setModalLogoUrl] = useState("https://musiconnectingpeople.com/logo_white.png")
  const [modalUnsubscribeUrl, setModalUnsubscribeUrl] = useState("{{unsubscribe_link}}")
  const [modalIncludeLineup, setModalIncludeLineup] = useState(true)

  useEffect(() => {
    Promise.all([listSenderGroups(), getAllEventsAdmin()]).then(([groupsRes, eventsRes]) => {
      const groupsData = groupsRes?.data ?? groupsRes ?? []
      setModalGroups(Array.isArray(groupsData) ? groupsData : [])

      const eventsData = Array.isArray(eventsRes) ? eventsRes : []
      setModalEvents(eventsData)
      if (eventsData.length && !modalSelectedEventId) {
        const first = eventsData[0]
        setModalSelectedEventId(String(first.id))
        setModalCtaUrl(getEventPublicUrl(first))
        setModalEventImageUrl(getEventImageUrl(first))
      }
    }).catch(() => {})
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listSenderCampaigns()
      const data = res?.data ?? res ?? []
      setCampaigns(Array.isArray(data) ? data : [])
    } catch {
      setError("Impossibile caricare le campagne.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleSend(c) {
    if (!confirm(`Inviare la campagna "${c.title || c.subject}" ora? L'azione è irreversibile.`)) return
    const res = await sendSenderCampaign(c.id)
    if (res?.error) {
      setError(`Invio fallito: ${res.error}`)
      return
    }
    load()
  }

  async function handleDelete(c) {
    if (!confirm(`Eliminare la campagna "${c.title || c.subject}"?`)) return
    const res = await deleteSenderCampaign(c.id)
    if (res?.error) {
      alert(res.error)
      return
    }
    load()
  }

  async function handleCopy(c) {
    await copySenderCampaign(c.id)
    load()
  }

  return (
    <motion.div
      className="space-y-6 pb-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {showCreate && (
        <CreateCampaignModal
          onClose={() => setShowCreate(false)}
          onCreated={load}
          groups={modalGroups}
          events={modalEvents}
          form={modalForm}
          setForm={setModalForm}
          selectedEventId={modalSelectedEventId}
          setSelectedEventId={setModalSelectedEventId}
          templateType={modalTemplateType}
          setTemplateType={setModalTemplateType}
          ctaUrl={modalCtaUrl}
          setCtaUrl={setModalCtaUrl}
          eventImageUrl={modalEventImageUrl}
          setEventImageUrl={setModalEventImageUrl}
          logoUrl={modalLogoUrl}
          setLogoUrl={setModalLogoUrl}
          unsubscribeUrl={modalUnsubscribeUrl}
          setUnsubscribeUrl={setModalUnsubscribeUrl}
          includeLineup={modalIncludeLineup}
          setIncludeLineup={setModalIncludeLineup}
        />
      )}
      {scheduleTarget && (
        <ScheduleModal
          campaign={scheduleTarget}
          onClose={() => setScheduleTarget(null)}
          onSaved={load}
        />
      )}

      <div>
        <Button variant="ghost" onClick={() => router.push(routes.admin.dashboard)}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Torna admin
        </Button>
        <h1 className="text-3xl md:text-4xl font-bold gradient-text mt-2">Campagne Email</h1>
        <p className="text-gray-300">Crea, schedula e gestisci le campagne Sender.</p>
      </div>
      <div className="flex gap-2">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" /> Nuova campagna
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
        <Card className="bg-zinc-900 border border-zinc-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-400">Campagne</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{campaigns.length}</div>
          </CardContent>
        </Card>
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
                  <TableHead className="text-neutral-400">Status</TableHead>
                  <TableHead className="text-neutral-400">Creata</TableHead>
                  <TableHead className="text-neutral-400 text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableSkeleton />
                ) : campaigns.length === 0 ? (
                  <TableRow className="border-neutral-800">
                    <TableCell colSpan={5} className="text-center text-neutral-500 py-12">
                      Nessuna campagna. Creane una per iniziare.
                    </TableCell>
                  </TableRow>
                ) : (
                  campaigns.map((c) => (
                    <TableRow key={c.id} className="border-neutral-800 hover:bg-white/5">
                      <TableCell className="text-white font-medium max-w-[160px] truncate">
                        {c.title || <span className="text-neutral-500 italic">—</span>}
                      </TableCell>
                      <TableCell className="text-neutral-300 max-w-[200px] truncate">{c.subject}</TableCell>
                      <TableCell><StatusBadge status={c.status} /></TableCell>
                      <TableCell className="text-neutral-400 text-sm">
                        {(c.created_at || c.created) ? new Date(c.created_at || c.created).toLocaleDateString("it-IT") : "—"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => router.push(routes.admin.sender.campaignDetail(c.id))}
                            title="Statistiche"
                            className="text-purple-400 hover:text-purple-300"
                          >
                            <BarChart2 className="h-4 w-4" />
                          </button>
                          <button onClick={() => setScheduleTarget(c)} title="Schedula" className="text-yellow-400 hover:text-yellow-300">
                            <Clock className="h-4 w-4" />
                          </button>
                          <button onClick={() => handleSend(c)} title="Invia ora" className="text-blue-400 hover:text-blue-300">
                            <Send className="h-4 w-4" />
                          </button>
                          <button onClick={() => handleCopy(c)} title="Duplica" className="text-neutral-400 hover:text-neutral-200">
                            <Copy className="h-4 w-4" />
                          </button>
                          <button onClick={() => handleDelete(c)} title="Elimina" className="text-red-400 hover:text-red-300">
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
