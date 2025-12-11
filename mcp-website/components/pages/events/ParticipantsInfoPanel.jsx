"use client"

import { Info } from "lucide-react"
import { PURCHASE_MODES, resolvePurchaseMode } from "@/config/events-utils"

function PanelBox({ children }) {
  return (
    <div className="bg-black/30 border border-mcp-orange/30 rounded-lg p-4 space-y-4 mt-6">
      <div className="flex items-start text-mcp-orange">
        <Info className="w-5 h-5 mt-1 mr-2 flex-shrink-0" />
        <div className="text-sm font-helvetica text-white space-y-2">{children}</div>
      </div>
    </div>
  )
}

function PublicPanel() {
  return (
    <PanelBox>
      <p>
        Evento aperto ai soci MCP e a chi desidera tesserarsi. Dopo il pagamento riceverai biglietto e istruzioni via
        email.
      </p>
      <p className="text-gray-300">
        Ti verranno richiesti nome, cognome, numero di telefono, email e data di nascita per ogni partecipante.
      </p>
    </PanelBox>
  )
}

function OnlyMembersPanel() {
  return (
    <PanelBox>
      <p>
        Questo evento è <strong>riservato ai membri già registrati</strong>. L'idoneità viene verificata automaticamente
        al checkout.
      </p>
      <p className="text-gray-300">Inserisci gli stessi dati (nome, cognome, email) usati per il tesseramento MCP.</p>
    </PanelBox>
  )
}

function MembershipIncludedPanel({ membershipFee, quantity }) {
  return (
    <PanelBox>
      <p>
        I partecipanti non ancora membri <strong>diventeranno soci MCP</strong> contestualmente all’acquisto.
      </p>
      <p className="text-gray-300">
        La tessera MCP è già inclusa nel prezzo finale, quindi i nuovi membri non pagano costi aggiuntivi oltre al biglietto.
      </p>
      <p className="text-gray-300">
        Tutti i partecipanti riceveranno biglietto, tessera digitale (se necessaria) e informazioni sulla location.
      </p>
    </PanelBox>
  )
}

export default function ParticipantsInfoPanel({ event, quantity = 1, purchaseMode }) {
  const mode = purchaseMode || resolvePurchaseMode(event)

  if (mode === PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS) {
    return <OnlyMembersPanel />
  }

  if (mode === PURCHASE_MODES.ONLY_MEMBERS) {
    return <MembershipIncludedPanel membershipFee={event?.membershipFee} quantity={quantity} />
  }

  if (mode === PURCHASE_MODES.PUBLIC) {
    return <PublicPanel />
  }

  return null
}
