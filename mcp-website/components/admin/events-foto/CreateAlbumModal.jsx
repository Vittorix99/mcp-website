"use client"

import React, { useState } from "react"
import { Dialog, DialogHeader, DialogContent, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"

export default function CreateAlbumModal({ isOpen, onClose, onSubmit }) {
  const [photoPath, setPhotoPath] = useState("")
  const [eventId, setEventId] = useState("")
  const [file, setFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handle = async () => {
    if (!photoPath || !eventId || !file) return
    setSubmitting(true)
    await onSubmit({ photoPath, eventId, file })
    setSubmitting(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader className="flex justify-between items-center">
          <h3 className="text-lg">Crea Nuovo Album</h3>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4"/>
          </Button>
        </DialogHeader>
        <div className="space-y-4 p-4">
          <div>
            <label>Photo Path*</label>
            <Input value={photoPath} onChange={e=>setPhotoPath(e.target.value)} />
          </div>
          <div>
            <label>Event ID*</label>
            <Input value={eventId} onChange={e=>setEventId(e.target.value)} />
          </div>
          <div>
            <label>Cover*</label>
            <Input type="file" accept="image/*" onChange={e=>setFile(e.target.files[0])}/>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={submitting}>Annulla</Button>
          <Button onClick={handle} disabled={submitting || !photoPath || !eventId || !file}>
            {submitting ? "Creazione..." : "Crea Album"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}