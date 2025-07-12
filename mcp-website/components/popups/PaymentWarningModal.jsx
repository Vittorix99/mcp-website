"use client"

import { X } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function PaymentWarningModal({ open, onClose, price, iban, intestatario }) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-white text-black max-w-md w-full p-6 rounded-lg space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">Attenzione</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X />
          </Button>
        </div>
        <p>
          PayPal non è attualmente disponibile come metodo di pagamento per motivi esterni a noi.
        </p>
        <p>
          Per garantire il tuo Early Bird, invia <strong>{price}€</strong> all’IBAN:
        </p>
        <pre className="bg-gray-100 text-sm p-2 rounded">{iban}</pre>
        {intestatario && (
          <p>
            Intestato a <strong>{intestatario}</strong>.
          </p>
        )}
        <p>
          Nella causale inserisci nome, cognome, data di nascita ed email di tutti i partecipanti.
        </p>
        <p className="italic">
          Riceverai tessera e ricevuta entro poche ore o appena elaboriamo il pagamento.
        </p>
        <div className="text-right">
          <Button onClick={onClose}>Chiudi</Button>
        </div>
      </div>
    </div>
  )
}