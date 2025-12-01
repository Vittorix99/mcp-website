"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Loader2, X } from "lucide-react"
import { EVENT_TYPES } from "@/config/events-utils"
import { useMediaQuery } from "@/hooks/useMediaQuery"

export function EventModal({
  isOpen,
  form = {},
  loading = false,
  isEditMode = false,
  onClose,
  onSubmit,
  onInput,
  onCheckbox,
  onSelectType,
  onFileChange,
}) {
  const isMobile = !useMediaQuery("(min-width: 768px)")
  const [internalLoading, setInternalLoading] = useState(false)
  const isLoading = loading || internalLoading

  const handleSubmit = async (e) => {
    e.preventDefault()
    setInternalLoading(true)
    await onSubmit(e)
    setInternalLoading(false)
  }

  const renderFields = () => (
    <>
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="title">Titolo</Label>
          <Input id="title" name="title" value={form.title || ""} onChange={onInput} required />
        </div>
        <div>
          <Label htmlFor="location">Luogo</Label>
          <Input id="location" name="location" value={form.location || ""} onChange={onInput} required />
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        <div>
          <Label htmlFor="date">Data</Label>
          <Input type="date" id="date" name="date" value={form.date || ""} onChange={onInput} required />
        </div>
        <div>
          <Label htmlFor="startTime">Ora Inizio</Label>
          <Input type="time" id="startTime" name="startTime" value={form.startTime || ""} onChange={onInput} required />
        </div>
        <div>
          <Label htmlFor="endTime">Ora Fine</Label>
          <Input id="endTime" name="endTime" value={form.endTime || ""} onChange={onInput} placeholder="es: 05:00 o TILL THE END" />
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        <div>
          <Label htmlFor="price">Prezzo (€)</Label>
          <Input id="price" name="price" type="number" step="0.01" value={form.price || ""} onChange={onInput} />
        </div>
        <div>
          <Label htmlFor="membershipFee">Tessera (€)</Label>
          <Input id="membershipFee" name="membershipFee" type="number" step="0.01" value={form.membershipFee || ""} onChange={onInput} />
        </div>
        <div>
          <Label htmlFor="fee">Commissione (€)</Label>
          <Input id="fee" name="fee" type="number" step="0.01" value={form.fee || ""} onChange={onInput} />
        </div>
      </div>

      <div>
        <Label htmlFor="note">Note</Label>
        <Textarea id="note" name="note" value={form.note || ""} onChange={onInput} rows={2} />
      </div>

      <div>
        <Label htmlFor="lineup">Lineup (una per riga)</Label>
        <Textarea id="lineup" name="lineup" value={form.lineup || ""} onChange={onInput} rows={3} />
      </div>

      <div>
        <Label htmlFor="image">Immagine</Label>
        <Input type="file" id="image" name="image" accept="image/*" onChange={onFileChange} />
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.active || false}
            onChange={(e) => onCheckbox("active", e.target.checked)}
          />
          <span>Evento attivo</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.onlyMembers || false}
            onChange={(e) => onCheckbox("onlyMembers", e.target.checked)}
          />
          <span>Vendita riservata ai Membri</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.allowDuplicates || false}
            onChange={(e) => onCheckbox("allowDuplicates", e.target.checked)}
          />
          <span>Consenti duplicati</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.over21Only || false}
            onChange={(e) => onCheckbox("over21Only", e.target.checked)}
          />
          <span>Solo Over 21</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.onlyFemales || false}
            onChange={(e) => onCheckbox("onlyFemales", e.target.checked)}
          />
          <span>Solo Donne</span>
        </label>
      </div>

      <div className="w-full">
        <Label htmlFor="type">Tipo Evento</Label>
        <select
          id="type"
          name="type"
          value={form.type || ""}
          onChange={onSelectType}
          className="w-full bg-gray-800 border border-gray-600 text-white rounded px-2 py-1"
        >
          {Object.values(EVENT_TYPES).map((val) => (
            <option key={val} value={val}>{val}</option>
          ))}
        </select>
      </div>
    </>
  )

  const renderFooter = () => (
    <div className="flex justify-end gap-2 pt-4 mr-6">
      <Button type="button" variant="outline" onClick={onClose}>
        Annulla
      </Button>
      <Button type="submit" disabled={isLoading} className="h-12 px-6 text-base font-semibold">
        {isLoading ? (
          <span className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Salvataggio...
          </span>
        ) : isEditMode ? "Aggiorna" : "Crea"}
      </Button>
    </div>
  )

  if (isMobile && isOpen) {
    return (
      <div className="fixed inset-0 z-50 bg-black no-nav">
        <form onSubmit={handleSubmit} className="flex flex-col h-full">
          <div className="flex items-center justify-between p-4 border-b border-gray-700 shrink-0">
            <h2 className="text-xl font-bold">{isEditMode ? "Modifica" : "Nuovo"} Evento</h2>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5 text-white" />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">{renderFields()}</div>
          <div className="border-t border-gray-700 p-4 shrink-0">{renderFooter()}</div>
        </form>
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] bg-black border border-gray-700 rounded-xl">
        <DialogHeader>
          <DialogTitle className="text-center text-2xl font-semibold gradient-text">
            {isEditMode ? "Modifica Evento" : "Nuovo Evento"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          {renderFields()}
          {renderFooter()}
        </form>
      </DialogContent>
    </Dialog>
  )
}