"use client"

export default function PaymentBlockedWarning({ price, iban, intestatario }) {
  return (
    <div className="bg-yellow-900 text-yellow-200 p-4 rounded-lg space-y-3 text-center mt-6">
      <h4 className="font-bold text-lg">Sistemi di pagamento in manutenzione</h4>
      <p>
        Per garantire il tuo Early Bird, invia <strong>{price}€</strong> a:
      </p>
      <pre className="bg-gray-800 p-2 rounded text-sm">{iban}</pre>
      <p>
        Intestato a: <strong>{intestatario}</strong>
      </p>
      <p>
        Inserisci in causale: nome, cognome, data nascita ed email di tutti i partecipanti.
      </p>
      <p className="italic">Riceverai tessera/ricevuta appena elaborato.</p>
    </div>
  )
}