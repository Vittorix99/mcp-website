"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams } from "next/navigation"
import { Send, Clock, Loader2, Edit, Save, X, Eye, Code } from "lucide-react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { routes } from "@/config/routes"
import {
  getSenderCampaign,
  getSenderCampaignStats,
  sendSenderCampaign,
  scheduleSenderCampaign,
  cancelSenderCampaignSchedule,
  updateSenderCampaign,
  listSenderGroups,
} from "@/services/admin/sender"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

// ------------------------------------------------------------------ //
// Helpers
// ------------------------------------------------------------------ //

const STATUS_COLORS = {
  draft:     "bg-zinc-700 text-zinc-200",
  scheduled: "bg-yellow-600/80 text-yellow-100",
  sent:      "bg-green-700/80 text-green-100",
  sending:   "bg-blue-600/80 text-blue-100",
}

function StatCard({ label, value }) {
  return (
    <Card className="bg-zinc-900 border border-zinc-700">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-neutral-400">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">{value ?? "—"}</div>
      </CardContent>
    </Card>
  )
}

function StatSkeleton() {
  return (
    <Card className="bg-zinc-900 border border-zinc-700">
      <CardHeader className="pb-2"><Skeleton className="h-3 w-20 bg-zinc-800" /></CardHeader>
      <CardContent><Skeleton className="h-7 w-12 bg-zinc-800" /></CardContent>
    </Card>
  )
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
        <DialogHeader><DialogTitle>Schedula campagna</DialogTitle></DialogHeader>
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

function extractHtml(campaign) {
  // Sender API returns content inside: campaign.html.html_content
  if (campaign?.html?.html_content) return campaign.html.html_content
  // Fallbacks
  const raw = campaign?.content_html ?? campaign?.content ?? ""
  if (typeof raw === "string") return raw
  if (raw && typeof raw === "object") return raw.html_content ?? raw.html ?? raw.text ?? ""
  return ""
}

// ------------------------------------------------------------------ //
// Main page
// ------------------------------------------------------------------ //

export default function CampaignDetailPage() {
  const { id } = useParams()

  const [campaign, setCampaign] = useState(null)
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [showSchedule, setShowSchedule] = useState(false)

  // Edit state
  const [editMode, setEditMode] = useState(false)
  const [editForm, setEditForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)

  // HTML editor state
  const [htmlEditing, setHtmlEditing] = useState(false)
  const [htmlDraft, setHtmlDraft] = useState("")
  const [htmlSaving, setHtmlSaving] = useState(false)

  // All available groups (for edit modal)
  const [allGroups, setAllGroups] = useState([])
  // Source of truth for selected group IDs — updated locally after save so we
  // don't depend on the API including `groups` in the campaign GET response.
  const [savedGroupIds, setSavedGroupIds] = useState([])

  const extractGroupIds = (groups) => {
    if (!Array.isArray(groups)) return []
    return groups
      .map((g) => (typeof g === "string" ? g : String(g?.id ?? "")))
      .filter(Boolean)
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [c, opens, clicks, unsubs, hardB, softB] = await Promise.allSettled([
        getSenderCampaign(id),
        getSenderCampaignStats(id, "opens"),
        getSenderCampaignStats(id, "clicks"),
        getSenderCampaignStats(id, "unsubscribes"),
        getSenderCampaignStats(id, "bounces_hard"),
        getSenderCampaignStats(id, "bounces_soft"),
      ])
      const camp = c.status === "fulfilled" ? (c.value?.data ?? c.value) : null
      setCampaign(camp)
      // Only initialize savedGroupIds on first load (don't overwrite local edits)
      setSavedGroupIds((prev) => {
        if (prev.length > 0) return prev
        return extractGroupIds(camp?.groups)
      })
      setStats({
        opens:        opens.status  === "fulfilled" ? opens.value  : null,
        clicks:       clicks.status === "fulfilled" ? clicks.value : null,
        unsubscribes: unsubs.status === "fulfilled" ? unsubs.value : null,
        bounces_hard: hardB.status  === "fulfilled" ? hardB.value  : null,
        bounces_soft: softB.status  === "fulfilled" ? softB.value  : null,
      })
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    listSenderGroups().then((res) => {
      const data = res?.data ?? res ?? []
      setAllGroups(Array.isArray(data) ? data : [])
    }).catch(() => {})
  }, [])

  function openEdit() {
    if (!campaign) return
    // Sender returns `from` as a plain string (display name only)
    const fromName = typeof campaign.from === "string" ? campaign.from : (campaign.from?.name ?? "")
    setEditForm({
      title:     campaign.title   ?? "",
      subject:   campaign.subject ?? "",
      from_name: fromName,
      groups:    [...savedGroupIds],
    })
    setSaveError(null)
    setEditMode(true)
  }

  function openHtmlEdit() {
    setHtmlDraft(extractHtml(campaign))
    setHtmlEditing(true)
  }

  async function handleSaveMeta(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError(null)
    try {
      const newGroupIds = editForm.groups ?? []
      await updateSenderCampaign(id, {
        title:     editForm.title     || undefined,
        subject:   editForm.subject   || undefined,
        from_name: editForm.from_name || undefined,
        groups:    newGroupIds,
      })
      setSavedGroupIds(newGroupIds)
      await load()
      setEditMode(false)
    } catch {
      setSaveError("Errore durante il salvataggio.")
    } finally {
      setSaving(false)
    }
  }

  async function handleSaveHtml() {
    setHtmlSaving(true)
    try {
      await updateSenderCampaign(id, { content_html: htmlDraft })
      await load()
      setHtmlEditing(false)
    } catch {
      // silently fail - could add toast here
    } finally {
      setHtmlSaving(false)
    }
  }

  const [sendError, setSendError] = useState(null)

  async function handleSend() {
    if (!campaign) return
    if (!confirm(`Inviare la campagna "${campaign.title || campaign.subject}" ora? L'azione è irreversibile.`)) return
    setSendError(null)
    const res = await sendSenderCampaign(id)
    if (res?.error) {
      setSendError(`Invio fallito: ${res.error}`)
      return
    }
    load()
  }

  const html = campaign ? extractHtml(campaign) : ""

  const statVal = (key) => {
    const s = stats[key]
    if (!s) return null
    // Sender stats return paginated envelope: { data:[], meta:{ total:N } }
    return s?.meta?.total ?? s?.count ?? s?.total ?? null
  }

  return (
    <motion.div
      className="space-y-6 pb-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {showSchedule && campaign && (
        <ScheduleModal campaign={campaign} onClose={() => setShowSchedule(false)} onSaved={load} />
      )}

      <AdminPageHeader
        title={loading ? "Campagna" : (campaign?.title || campaign?.subject || "Campagna")}
        description={!loading && campaign?.subject && campaign?.title ? `Oggetto: ${campaign.subject}` : undefined}
        backHref={routes.admin.sender.campaigns}
        backLabel="Torna alle campagne"
        actions={campaign?.status && (
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[campaign.status] || "bg-zinc-700 text-zinc-300"}`}>
            {campaign.status}
          </span>
        )}
      />

      {sendError && (
        <div className="rounded-md bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
          {sendError}
        </div>
      )}

      {/* Action buttons */}
      {!loading && campaign && (
        <div className="flex gap-2 flex-wrap">
          <Button onClick={handleSend} disabled={campaign.status === "sent"}>
            <Send className="h-4 w-4 mr-2" /> Invia ora
          </Button>
          <Button variant="outline" onClick={() => setShowSchedule(true)} className="border-zinc-700">
            <Clock className="h-4 w-4 mr-2" /> Schedula
          </Button>
          <Button variant="outline" onClick={openEdit} className="border-zinc-700">
            <Edit className="h-4 w-4 mr-2" /> Modifica
          </Button>
          <Button variant="outline" onClick={openHtmlEdit} className="border-zinc-700">
            <Code className="h-4 w-4 mr-2" /> Modifica HTML
          </Button>
        </div>
      )}

      {/* Stats */}
      <div className="grid gap-4 grid-cols-2 md:grid-cols-5">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => <StatSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="Opens"         value={statVal("opens")} />
            <StatCard label="Clicks"        value={statVal("clicks")} />
            <StatCard label="Unsubscribes"  value={statVal("unsubscribes")} />
            <StatCard label="Hard bounces"  value={statVal("bounces_hard")} />
            <StatCard label="Soft bounces"  value={statVal("bounces_soft")} />
          </>
        )}
      </div>

      {/* Metadata card */}
      {!loading && campaign && (
        <Card className="bg-zinc-900 border border-zinc-700">
          <CardHeader className="flex flex-row items-center justify-between gap-2 pb-2">
            <CardTitle className="text-base">Dettagli campagna</CardTitle>
            <Button variant="ghost" size="sm" onClick={openEdit}>
              <Edit className="h-4 w-4 mr-1" /> Modifica
            </Button>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-neutral-500 text-xs uppercase tracking-wide">Subject</p>
              <p className="text-white mt-0.5">{campaign.subject || "—"}</p>
            </div>
            <div>
              <p className="text-neutral-500 text-xs uppercase tracking-wide">From</p>
              <p className="text-white mt-0.5">
                {typeof campaign.from === "string" ? campaign.from : (campaign.from?.name || "—")}
              </p>
            </div>
            {campaign.created_at && (
              <div>
                <p className="text-neutral-500 text-xs uppercase tracking-wide">Creata</p>
                <p className="text-white mt-0.5">{new Date(campaign.created_at).toLocaleString("it-IT")}</p>
              </div>
            )}
            {campaign.scheduled_at && (
              <div>
                <p className="text-neutral-500 text-xs uppercase tracking-wide">Schedulata</p>
                <p className="text-white mt-0.5">{new Date(campaign.scheduled_at).toLocaleString("it-IT")}</p>
              </div>
            )}
            {savedGroupIds.length > 0 && (
              <div className="sm:col-span-2">
                <p className="text-neutral-500 text-xs uppercase tracking-wide mb-1">Gruppi destinatari</p>
                <div className="flex flex-wrap gap-1.5">
                  {savedGroupIds.map((gid, i) => {
                    const match = allGroups.find((g) => String(g?.id ?? "") === gid)
                    const label = match?.title ?? match?.name ?? gid
                    return (
                      <span key={gid || i} className="inline-flex items-center gap-1 text-xs bg-blue-500/15 text-blue-300 border border-blue-500/20 rounded px-2 py-0.5">
                        {label}
                      </span>
                    )
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* HTML Preview / Editor */}
      {!loading && (
        <Card className="bg-zinc-900 border border-zinc-700">
          <CardHeader className="flex flex-row items-center justify-between gap-2 pb-2">
            <CardTitle className="text-base">Contenuto HTML</CardTitle>
            <Button variant="ghost" size="sm" onClick={openHtmlEdit}>
              <Code className="h-4 w-4 mr-1" /> Modifica HTML
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {html ? (
              <iframe
                srcDoc={html}
                sandbox="allow-same-origin"
                className="w-full bg-white border-0 rounded-b-lg"
                style={{ height: 600 }}
                title="Campaign HTML Preview"
              />
            ) : (
              <p className="text-neutral-500 text-sm px-6 py-8">Nessun contenuto HTML disponibile.</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Edit metadata modal */}
      {editMode && (
        <Dialog open onOpenChange={() => setEditMode(false)}>
          <DialogContent className="sm:max-w-lg bg-zinc-900 border-neutral-800 text-white">
            <DialogHeader><DialogTitle>Modifica campagna</DialogTitle></DialogHeader>
            <form onSubmit={handleSaveMeta} className="space-y-4 mt-2">
              <div className="space-y-1">
                <Label>Title <span className="text-neutral-500 text-xs">(opzionale)</span></Label>
                <Input
                  value={editForm.title}
                  onChange={(e) => setEditForm((f) => ({ ...f, title: e.target.value }))}
                  placeholder="Nome interno campagna"
                  className="bg-zinc-800 border-neutral-700 text-white"
                />
              </div>
              <div className="space-y-1">
                <Label>Subject <span className="text-red-400">*</span></Label>
                <Input
                  value={editForm.subject}
                  onChange={(e) => setEditForm((f) => ({ ...f, subject: e.target.value }))}
                  required
                  placeholder="Oggetto email"
                  className="bg-zinc-800 border-neutral-700 text-white"
                />
              </div>
              <div className="space-y-1">
                <Label>From name <span className="text-neutral-500 text-xs">(nome visualizzato)</span></Label>
                <Input
                  value={editForm.from_name}
                  onChange={(e) => setEditForm((f) => ({ ...f, from_name: e.target.value }))}
                  placeholder="Music Connecting People"
                  className="bg-zinc-800 border-neutral-700 text-white"
                />
              </div>
              {allGroups.length > 0 && (
                <div className="space-y-1.5">
                  <Label>Gruppi destinatari</Label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-48 overflow-y-auto border border-neutral-700 rounded p-3 bg-zinc-800">
                    {allGroups.map((g, i) => {
                      const gid = String(g?.id ?? "")
                      const label = g?.title ?? g?.name ?? gid
                      const checked = editForm.groups?.includes(gid)
                      return (
                        <label key={gid || i} className="flex items-center gap-2 cursor-pointer text-sm text-white hover:text-blue-300">
                          <input
                            type="checkbox"
                            checked={!!checked}
                            onChange={(e) => {
                              setEditForm((f) => ({
                                ...f,
                                groups: e.target.checked
                                  ? [...(f.groups ?? []), gid]
                                  : (f.groups ?? []).filter((id) => id !== gid),
                              }))
                            }}
                            className="accent-blue-500"
                          />
                          {label}
                        </label>
                      )
                    })}
                  </div>
                  <p className="text-xs text-neutral-500">
                    {editForm.groups?.length ?? 0} gruppo/i selezionato/i
                  </p>
                </div>
              )}
              {saveError && <p className="text-red-400 text-sm">{saveError}</p>}
              <div className="flex gap-2 pt-1">
                <Button type="submit" disabled={saving}>
                  {saving ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Salvataggio...</> : <><Save className="h-4 w-4 mr-2" />Salva</>}
                </Button>
                <Button type="button" variant="ghost" onClick={() => setEditMode(false)}>Annulla</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {/* HTML editor modal */}
      {htmlEditing && (
        <Dialog open onOpenChange={() => setHtmlEditing(false)}>
          <DialogContent className="sm:max-w-4xl bg-zinc-900 border-neutral-800 text-white max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Modifica HTML</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-2">
              <Tabs defaultValue="editor">
                <TabsList className="bg-zinc-800">
                  <TabsTrigger value="editor"><Code className="h-3.5 w-3.5 mr-1" />Editor</TabsTrigger>
                  <TabsTrigger value="preview"><Eye className="h-3.5 w-3.5 mr-1" />Preview</TabsTrigger>
                </TabsList>
                <TabsContent value="editor" className="mt-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-neutral-500">{(htmlDraft ?? "").length.toLocaleString()} caratteri</span>
                  </div>
                  <textarea
                    value={htmlDraft}
                    onChange={(e) => setHtmlDraft(e.target.value)}
                    rows={20}
                    className="w-full bg-zinc-800 border border-neutral-700 rounded px-3 py-2 text-sm text-white font-mono placeholder-zinc-600 resize-y"
                    style={{ minHeight: 400 }}
                    onKeyDown={(e) => {
                      if (e.key === "Tab") {
                        e.preventDefault()
                        const s = e.target.selectionStart
                        const en = e.target.selectionEnd
                        const v = htmlDraft
                        setHtmlDraft(v.slice(0, s) + "  " + v.slice(en))
                        requestAnimationFrame(() => {
                          e.target.selectionStart = e.target.selectionEnd = s + 2
                        })
                      }
                    }}
                  />
                </TabsContent>
                <TabsContent value="preview" className="mt-3">
                  {htmlDraft ? (
                    <div className="rounded border border-neutral-700 overflow-hidden">
                      <iframe
                        srcDoc={htmlDraft}
                        sandbox="allow-same-origin"
                        className="w-full bg-white border-0"
                        style={{ height: 500 }}
                        title="HTML draft preview"
                      />
                    </div>
                  ) : (
                    <p className="text-neutral-500 text-sm">Nessun contenuto da visualizzare.</p>
                  )}
                </TabsContent>
              </Tabs>

              <div className="flex gap-2 pt-1">
                <Button onClick={handleSaveHtml} disabled={htmlSaving}>
                  {htmlSaving ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Salvataggio...</> : <><Save className="h-4 w-4 mr-2" />Salva HTML</>}
                </Button>
                <Button variant="ghost" onClick={() => setHtmlEditing(false)}>Annulla</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </motion.div>
  )
}
