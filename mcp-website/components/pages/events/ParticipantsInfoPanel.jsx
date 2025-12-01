"use client"

import { Info } from "lucide-react"
import { EVENT_TYPES } from "@/config/events-utils"
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

// --- Child: EP12 ---
function EP12Panel({ quantity = 1, membershipFee = 10 }) {
  const totalMembership = (Number(quantity) || 0) * (Number(membershipFee) || 0)
  return (
    <PanelBox>
      <p>
        Questo evento è riservato esclusivamente ai soci dell'associazione culturale
        <strong> Music Connecting People ETS</strong>.
      </p>
      <p className="text-sm text-gray-300 font-helvetica">
        Per ogni partecipante è inclusa una quota associativa obbligatoria di
        <strong className="text-mcp-orange"> {Number(membershipFee).toFixed(2)}€</strong>, per un totale di
        <strong className="text-mcp-orange"> {totalMembership.toFixed(2)}€</strong>.
      </p>
      <p className="text-sm text-gray-300 font-helvetica">Dopo il pagamento, ogni partecipante riceverà via email:</p>
      <ul className="list-disc list-inside mt-1 text-gray-400">
        <li>La tessera associativa digitale</li>
        <li>Il biglietto dell'evento</li>
        <li>Le informazioni per raggiungere la location in un secondo momento</li>
      </ul>
      <p className="text-sm text-gray-300 font-helvetica">
        Ti verranno richiesti nome, cognome, numero di telefono e email per ciascun partecipante.
      </p>
    </PanelBox>
  )
}

// --- Child: EP13 (onlyMembers = true) ---
function EP13OnlyMembersPanel() {
  return (
    <PanelBox>
      <p>
        Questo evento è <strong>riservato esclusivamente ai membri</strong> dell'associazione culturale
        <strong> Music Connecting People ETS</strong>. L'idoneità viene verificata al checkout.
      </p>
      <p className="text-gray-300">
        Assicurati di inserire <em>nome, cognome ed email</em> con cui sei tesserato.
      </p>
    </PanelBox>
  )
}

// --- Child: EP13 (onlyMembers = false) ---
function EP13OpenPanel() {
  return (
    <PanelBox>
      <p>
        Prezzo <strong>uguale per tutti</strong>. Se un partecipante non è ancora membro, procedendo con l'acquisto
        <strong> accetta di diventare membro MCP ETS</strong> e di aderire allo Statuto dell'associazione.
      </p>
      <ul className="list-disc list-inside mt-1 text-gray-300">
        <li>Biglietto digitale inviato via email</li>
        <li>Per i non membri: attivazione della tessera associativa (senza costi extra oltre il prezzo indicato)</li>
        <li>Informazioni per raggiungere la location inviate in seguito</li>
      </ul>
      <p className="text-gray-300">
        Ti verranno richiesti nome, cognome, telefono ed email per ciascun partecipante.
      </p>
    </PanelBox>
  )
}

export default function ParticipantsInfoPanel({ event, quantity = 1, membershipFee = 10 }) {
  const type = (event?.type || "").toLowerCase()
  const onlyMembers = !!event?.onlyMembers
    // Debug: log what the component sees
    // eslint-disable-next-line no-console
    console.log("[ParticipantsInfoPanel] type=", type, "onlyMembers=", onlyMembers, "EVENT_TYPES=", EVENT_TYPES)
  

  if (type === EVENT_TYPES.CUSTOM_EP13) {
    return onlyMembers ? <EP13OnlyMembersPanel /> : <EP13OpenPanel />
  }

  if (type === EVENT_TYPES.CUSTOM_EP12) {
    return <EP12Panel quantity={quantity} membershipFee={membershipFee} />
  }

  return null
}