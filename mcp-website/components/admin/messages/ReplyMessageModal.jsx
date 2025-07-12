"use client"

import React, { useState } from "react"
import {
  Dialog,
  DialogHeader,
  DialogContent,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { X , Loader2} from "lucide-react"

export function ReplyMessageModal({ isOpen, onClose, message, onSend }) {
  const [subject, setSubject] = useState("Risposta al tuo messaggio")
  const [body, setBody] = useState("")
  const [loading, setLoading] = useState(false)


  const handleSubmit = async () => {
    if (!body.trim()) return;
    setLoading(true);
    await onSend({ email: message.email, subject, body, message_id: message.id });
    setLoading(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader className="flex justify-between items-center">
          <DialogTitle className="text-lg font-medium">Rispondi a {message?.name}</DialogTitle>

        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Email</label>
            <Input value={message?.email} readOnly className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">Oggetto</label>
            <Input value={subject} onChange={(e) => setSubject(e.target.value)} className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">Messaggio</label>
            <Textarea
              rows={6}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="mt-1"
              placeholder="Scrivi la tua risposta..."
            />
          </div>
          {/* <div>
            <label className="text-sm font-medium">Allegato</label>
            <Input type="file" className="mt-1" disabled />
            <p className="text-xs text-gray-500">Funzionalità in arrivo.</p>
          </div> */}
        </div>
        <DialogFooter>
                <Button variant="ghost" onClick={onClose} disabled={loading}>Annulla</Button>
                <Button onClick={handleSubmit} disabled={loading || !body.trim()}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2"/> : null}
                  {loading ? "Invio..." : "Invia Risposta"}
                </Button>
              </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}