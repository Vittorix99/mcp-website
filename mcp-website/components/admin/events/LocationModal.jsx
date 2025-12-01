"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export function LocationModal({
  isOpen,
  onClose,
  targetName,
  address,
  setAddress,
  link,
  setLink,
  message,
  setMessage,
  onSubmit
}) {
  if (!isOpen) return null;

  const title = targetName
    ? `Invia Location a ${targetName}`
    : "Invia Location a tutti i partecipanti";

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-center">{title}</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={e => {
            e.preventDefault();
            onSubmit({ address: address ?? "", link: link ?? "", message: (message ?? "") });
          }}
          className="space-y-4"
        >
          <div>
            <Label htmlFor="address">Indirizzo</Label>
            <Input
              id="address"
              value={address ?? ""}
              onChange={e => setAddress(e.target.value)}
              placeholder="Via ..."
            />
          </div>
          <div>
            <Label htmlFor="link">Link (es. Google Maps)</Label>
            <Input
              id="link"
              value={link ?? ""}
              onChange={e => setLink(e.target.value)}
              placeholder="https://..."
            />
          </div>
          <div>
            <Label htmlFor="message">Messaggio (opzionale)</Label>
            <Textarea
              id="message"
              value={message ?? ""}
              onChange={e => setMessage(e.target.value)}
              placeholder="Scrivi un messaggio per i partecipanti..."
              rows={4}
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" type="button" onClick={onClose}>Annulla</Button>
            <Button type="submit">Invia</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}