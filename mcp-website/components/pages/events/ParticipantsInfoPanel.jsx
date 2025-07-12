"use client"

import { Info } from "lucide-react"

export default function ParticipantsInfoPanel({ quantity = 1, membershipFee = 10 }) {
  const totalMembership = quantity * membershipFee

  return (
    <div className="bg-black/30 border border-mcp-orange/30 rounded-lg p-4 space-y-4 mt-6">
      <div className="flex items-start text-mcp-orange">
        <Info className="w-5 h-5 mt-1 mr-2 flex-shrink-0" />
        <p className="text-sm font-helvetica text-white">
          Questo evento è riservato esclusivamente ai soci dell'associazione culturale <strong>Music Connecting People ETS</strong>.
        </p>
      </div>

      <p className="text-sm text-gray-300 font-helvetica">
        Per ogni partecipante è inclusa una quota associativa obbligatoria di <strong className="text-mcp-orange">{membershipFee}€</strong>, per un totale di <strong className="text-mcp-orange">{totalMembership.toFixed(2)}€</strong>.
      </p>

      <p className="text-sm text-gray-300 font-helvetica">
        Dopo il pagamento, ogni partecipante riceverà via email:
        </p>
        <ul className="list-disc list-inside mt-1 text-gray-400">
          <li>La tessera associativa digitale</li>
          <li>Il biglietto dell'evento</li>
          <li>Le informazioni per raggiungere la location in un secondo momento</li>
        </ul>
      

      <p className="text-sm text-gray-300 font-helvetica">
        Ti verranno richiesti nome, cognome, numero di telefono e email per ciascun partecipante.
      </p>
    </div>
  )
}