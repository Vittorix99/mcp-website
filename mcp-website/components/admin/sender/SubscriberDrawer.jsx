"use client"

import { useState, useEffect } from "react"
import { X, Loader2, Trash2, UserPlus, UserMinus, Mail, MousePointer, Eye, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  deleteSenderSubscriber,
  updateSenderSubscriber,
  addSenderSubscriberToGroup,
  removeSenderSubscriberFromGroup,
  getSenderSubscriberEvents,
  getSenderSubscriber,
  listSenderGroups,
} from "@/services/admin/sender"

const safeStr = (v) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : "")
const getGroups = (s) => Array.isArray(s?.subscriber_tags) && s.subscriber_tags.length > 0
  ? s.subscriber_tags
  : Array.isArray(s?.groups) ? s.groups : []

function EventRow({ event, icon: Icon, color }) {
  return (
    <div className="flex items-start gap-3 py-2 border-b border-neutral-800 last:border-0">
      <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${color}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">{event.title || event.campaign_id}</p>
        <p className="text-xs text-neutral-500">{event.created_at}</p>
      </div>
    </div>
  )
}

export default function SubscriberDrawer({ subscriber, onClose, onDeleted, onUpdated, onGroupChanged }) {
  const [allGroups, setAllGroups] = useState([])
  const [subGroups, setSubGroups] = useState(getGroups(subscriber))
  const [events, setEvents] = useState(null)
  const [eventsLoading, setEventsLoading] = useState(true)
  // status is nested: { email: "active", temail: "active" }
  const emailStatus = safeStr(subscriber?.status?.email) || safeStr(subscriber?.status) || ""

  const [editForm, setEditForm] = useState({
    firstname: safeStr(subscriber?.firstname),
    lastname: safeStr(subscriber?.lastname),
    phone: safeStr(subscriber?.phone),
    subscriber_status: emailStatus,
  })
  const [saving, setSaving] = useState(false)
  const [assignGroupId, setAssignGroupId] = useState("")
  const [assignLoading, setAssignLoading] = useState(false)
  const [groupsLoading, setGroupsLoading] = useState(true)

  const email = safeStr(subscriber?.email)

  // Fetch fresh subscriber data to get accurate group memberships (Sender returns `subscriber_tags`)
  useEffect(() => {
    getSenderSubscriber(email).then((res) => {
      const data = res?.data ?? res
      const fresh = getGroups(data)
      if (fresh.length > 0) setSubGroups(fresh)
    }).catch(() => {})
  }, [email])

  useEffect(() => {
    setEventsLoading(true)
    getSenderSubscriberEvents(email).then((res) => {
      setEvents(res)
    }).catch(() => setEvents(null)).finally(() => setEventsLoading(false))
  }, [email])

  useEffect(() => {
    setGroupsLoading(true)
    listSenderGroups().then((res) => {
      const data = res?.data ?? res ?? []
      setAllGroups(Array.isArray(data) ? data : [])
    }).catch(() => {}).finally(() => setGroupsLoading(false))
  }, [])

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await updateSenderSubscriber({
        email,
        firstname: editForm.firstname || undefined,
        lastname: editForm.lastname || undefined,
        phone: editForm.phone || undefined,
        subscriber_status: editForm.subscriber_status || undefined,
      })
      onUpdated?.({ ...subscriber, ...editForm })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!confirm(`Eliminare ${email} da Sender?`)) return
    await deleteSenderSubscriber(email)
    onDeleted?.()
  }

  async function handleAssignGroup() {
    if (!assignGroupId) return
    setAssignLoading(true)
    try {
      await addSenderSubscriberToGroup(email, assignGroupId)
      const match = allGroups.find((g) => String(g.id ?? "") === assignGroupId)
      const newGroup = match || { id: assignGroupId }
      setSubGroups((prev) => [...prev, newGroup])
      setAssignGroupId("")
      onGroupChanged?.()
    } finally {
      setAssignLoading(false)
    }
  }

  async function handleRemoveGroup(groupId) {
    await removeSenderSubscriberFromGroup(email, groupId)
    setSubGroups((prev) => prev.filter((g) => String(g.id) !== String(groupId)))
    onGroupChanged?.()
  }

  const availableGroups = allGroups.filter((g) => !subGroups.some((sg) => String(sg.id) === String(g.id)))

  // Event counts
  const emailCampaign = events?.email_campaign ?? {}
  const gotEvents = events?.email?.got ?? []
  const openedEvents = events?.email?.opened ?? []
  const clickedEvents = events?.email?.clicked ?? []

  return (
    <div className="border border-zinc-700 rounded-lg bg-zinc-900 overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-zinc-700">
        <div>
          <p className="text-white font-semibold">{email}</p>
          <p className="text-neutral-400 text-sm">
            {[safeStr(subscriber.firstname), safeStr(subscriber.lastname)].filter(Boolean).join(" ") || "—"}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              emailStatus.toLowerCase() === "active"
                ? "bg-green-700/60 text-green-200"
                : emailStatus
                  ? "bg-zinc-700 text-zinc-400"
                  : "bg-zinc-700 text-zinc-400"
            }`}>
              {emailStatus || "—"}
            </span>
            {subscriber.created && (
              <span className="text-xs text-neutral-500">Creata: {safeStr(subscriber.created).slice(0, 10)}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleDelete} title="Elimina" className="text-red-400 hover:text-red-300">
            <Trash2 className="h-4 w-4" />
          </button>
          <button onClick={onClose} className="text-neutral-500 hover:text-neutral-200">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Email campaign stats */}
      {(events !== null || eventsLoading) && (
        <div className="grid grid-cols-4 divide-x divide-zinc-700 border-b border-zinc-700 text-center">
          {[
            { label: "Inviati", value: emailCampaign.sent_count },
            { label: "Aperti", value: emailCampaign.opened_count },
            { label: "Click", value: emailCampaign.clicked_count },
            { label: "Unsub", value: emailCampaign.unsubscribed },
          ].map(({ label, value }) => (
            <div key={label} className="py-3 px-2">
              <div className="text-lg font-bold text-white">{eventsLoading ? "—" : (value ?? 0)}</div>
              <div className="text-xs text-neutral-500">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="info" className="p-4">
        <TabsList className="bg-zinc-800 mb-4">
          <TabsTrigger value="info">Info</TabsTrigger>
          <TabsTrigger value="gruppi">Gruppi</TabsTrigger>
          <TabsTrigger value="eventi">
            Email ricevute {gotEvents.length > 0 && `(${gotEvents.length})`}
          </TabsTrigger>
        </TabsList>

        {/* Info tab */}
        <TabsContent value="info">
          <form onSubmit={handleSave} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs text-neutral-400">Nome</Label>
                <Input value={editForm.firstname} onChange={(e) => setEditForm((f) => ({ ...f, firstname: e.target.value }))}
                  className="bg-zinc-800 border-neutral-700 text-white h-8 text-sm" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-neutral-400">Cognome</Label>
                <Input value={editForm.lastname} onChange={(e) => setEditForm((f) => ({ ...f, lastname: e.target.value }))}
                  className="bg-zinc-800 border-neutral-700 text-white h-8 text-sm" />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-neutral-400">Telefono</Label>
              <Input value={editForm.phone} onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))}
                className="bg-zinc-800 border-neutral-700 text-white h-8 text-sm" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-neutral-400">Stato email</Label>
              <select
                value={editForm.subscriber_status}
                onChange={(e) => setEditForm((f) => ({ ...f, subscriber_status: e.target.value }))}
                className="w-full bg-zinc-800 border border-neutral-700 rounded-md px-2 h-8 text-sm text-white"
              >
                <option value="">— nessuna modifica —</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="UNSUBSCRIBED">UNSUBSCRIBED</option>
                <option value="BOUNCED">BOUNCED</option>
                <option value="SPAM_REPORTED">SPAM_REPORTED</option>
              </select>
            </div>
            {subscriber.fields && Object.keys(subscriber.fields).length > 0 && (
              <div className="rounded border border-neutral-800 overflow-hidden mt-2">
                <p className="text-xs text-neutral-500 px-3 py-1.5 bg-zinc-800 uppercase tracking-wide">Campi personalizzati</p>
                {Object.entries(subscriber.fields).map(([key, val]) => (
                  <div key={key} className="flex items-center border-b border-neutral-800 last:border-0">
                    <span className="px-3 py-2 text-xs text-neutral-400 w-36 shrink-0">{key}</span>
                    <span className="px-3 py-2 text-xs text-white">{String(val ?? "—")}</span>
                  </div>
                ))}
              </div>
            )}
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
              Salva modifiche
            </Button>
          </form>
        </TabsContent>

        {/* Gruppi tab */}
        <TabsContent value="gruppi" className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {subGroups.length === 0 ? (
              <p className="text-sm text-neutral-500">Nessun gruppo assegnato.</p>
            ) : subGroups.map((g, i) => (
              <span key={g.id ?? i} className="flex items-center gap-1.5 text-xs bg-orange-500/10 border border-orange-500/30 text-orange-300 px-2 py-1 rounded-full">
                {safeStr(g.title ?? g.name ?? g.id)}
                <button onClick={() => handleRemoveGroup(g.id)} className="hover:text-red-400">
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
          {availableGroups.length > 0 && (
            <div className="flex gap-2 pt-1">
              {groupsLoading ? (
                <Loader2 className="h-4 w-4 animate-spin text-neutral-400" />
              ) : (
                <>
                  <Select value={assignGroupId} onValueChange={setAssignGroupId}>
                    <SelectTrigger className="bg-zinc-800 border-neutral-700 text-white h-8 text-sm flex-1">
                      <SelectValue placeholder="Aggiungi a gruppo…" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableGroups.map((g, i) => (
                        <SelectItem key={g.id ?? i} value={String(g.id ?? "")}>
                          {g.title ?? g.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button size="sm" onClick={handleAssignGroup} disabled={!assignGroupId || assignLoading} className="h-8">
                    {assignLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UserPlus className="h-3.5 w-3.5" />}
                  </Button>
                </>
              )}
            </div>
          )}
        </TabsContent>

        {/* Events tab */}
        <TabsContent value="eventi">
          {eventsLoading ? (
            <div className="flex justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-neutral-400" />
            </div>
          ) : gotEvents.length === 0 && openedEvents.length === 0 && clickedEvents.length === 0 ? (
            <p className="text-sm text-neutral-500 py-4 text-center">Nessun evento email disponibile.</p>
          ) : (
            <div className="space-y-4">
              {gotEvents.length > 0 && (
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                    <Mail className="h-3.5 w-3.5" /> Ricevute ({gotEvents.length})
                  </p>
                  <div className="max-h-48 overflow-y-auto">
                    {gotEvents.map((e, i) => (
                      <EventRow key={i} event={e} icon={Mail} color="text-blue-400" />
                    ))}
                  </div>
                </div>
              )}
              {openedEvents.length > 0 && (
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                    <Eye className="h-3.5 w-3.5" /> Aperte ({openedEvents.length})
                  </p>
                  <div className="max-h-36 overflow-y-auto">
                    {openedEvents.map((e, i) => (
                      <EventRow key={i} event={e} icon={Eye} color="text-green-400" />
                    ))}
                  </div>
                </div>
              )}
              {clickedEvents.length > 0 && (
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                    <MousePointer className="h-3.5 w-3.5" /> Click ({clickedEvents.length})
                  </p>
                  <div className="max-h-36 overflow-y-auto">
                    {clickedEvents.map((e, i) => (
                      <EventRow key={i} event={e} icon={MousePointer} color="text-orange-400" />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
