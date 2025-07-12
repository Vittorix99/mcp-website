"use client"

import React from "react"
import {
  Dialog,
  DialogHeader,
  DialogContent,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { formatFirestoreTimestamp } from "@/lib/utils"

export function PreviewMessageModal({ isOpen, onClose, message }) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader className="flex justify-between items-center">
          <DialogTitle className="text-xl ">Messaggio da {message?.name}</DialogTitle>
     
        </DialogHeader>

        <div className="space-y-4">
          <p><strong>Email:</strong> {message?.email}</p>
          <p><strong>Ricevuto:</strong> {formatFirestoreTimestamp(message?.timestamp)}</p>
          <hr />
          <div>
            <label className="block text-sm font-medium mb-1">Contenuto:</label>
            <textarea
              readOnly
              value={message?.message || ""}
              className="w-full p-2 border border-gray-700 rounded-md bg-neutral-900 text-white resize-none"
              rows={6}
            />
          </div>
        </div>

        <DialogFooter className="pt-4">
          <Button onClick={onClose}>Chiudi</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}