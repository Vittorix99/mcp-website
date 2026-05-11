"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MapPin } from "lucide-react";

export function LocationModal({
  isOpen,
  onClose,
  targetName,
  storedAddress,
  storedMapsUrl,
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
            onSubmit({ message: message ?? "" });
          }}
          className="space-y-4"
        >
          {/* Show stored location for reference */}
          {(storedAddress || storedMapsUrl) && (
            <div className="rounded-lg bg-zinc-900 border border-zinc-700 p-3 space-y-1">
              <p className="text-xs uppercase tracking-widest text-orange-400 font-bold flex items-center gap-1">
                <MapPin className="h-3 w-3" /> Location salvata
              </p>
              {storedAddress && <p className="text-sm text-gray-300">{storedAddress}</p>}
              {storedMapsUrl && (
                <a
                  href={storedMapsUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-orange-400 hover:underline"
                >
                  Apri in Maps →
                </a>
              )}
            </div>
          )}

          {!storedAddress && (
            <p className="text-sm text-yellow-400">
              Nessuna location salvata. Imposta prima l&apos;indirizzo nel tab Posizione.
            </p>
          )}

          <div>
            <Label htmlFor="location-message">Messaggio personalizzato (opzionale)</Label>
            <Textarea
              id="location-message"
              value={message ?? ""}
              onChange={e => setMessage(e.target.value)}
              placeholder="Lascia vuoto per usare il messaggio predefinito..."
              rows={3}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" type="button" onClick={onClose}>Annulla</Button>
            <Button type="submit" disabled={!storedAddress}>Invia</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
