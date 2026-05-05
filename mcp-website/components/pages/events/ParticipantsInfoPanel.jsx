"use client"

import { PURCHASE_MODES, resolvePurchaseMode } from "@/config/events-utils"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

function PanelBox({ children }) {
  return (
    <div
      style={{
        borderTop: "1px solid rgba(245,243,239,0.07)",
        borderBottom: "1px solid rgba(245,243,239,0.07)",
        padding: "18px 0",
        marginBottom: "30px",
      }}
    >
      <p
        style={{
          fontFamily: HN,
          fontSize: "8px",
          fontWeight: 700,
          letterSpacing: "0.35em",
          textTransform: "uppercase",
          color: ACC,
          margin: "0 0 12px",
        }}
      >
        Informazioni
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>{children}</div>
    </div>
  )
}

const mainText = {
  fontFamily: CH,
  fontSize: "14px",
  lineHeight: 1.72,
  color: "rgba(245,243,239,0.58)",
  margin: 0,
}

const mutedText = {
  ...mainText,
  color: "rgba(245,243,239,0.42)",
}

function PublicPanel() {
  return (
    <PanelBox>
      <p style={mainText}>
        Evento aperto ai soci MCP e a chi desidera tesserarsi. Dopo il pagamento riceverai biglietto e istruzioni via
        email.
      </p>
      <p style={mutedText}>
        Ti verranno richiesti nome, cognome, numero di telefono, email e data di nascita per ogni partecipante.
      </p>
    </PanelBox>
  )
}

function OnlyMembersPanel() {
  return (
    <PanelBox>
      <p style={mainText}>
        Questo evento è <strong>riservato ai membri già registrati</strong>. L'idoneità viene verificata automaticamente
        al checkout.
      </p>
      <p style={mutedText}>Inserisci gli stessi dati (nome, cognome, email) usati per il tesseramento MCP.</p>
    </PanelBox>
  )
}

function MembershipIncludedPanel() {
  return (
    <PanelBox>
      <p style={mainText}>
        I partecipanti non ancora membri <strong>diventeranno soci MCP</strong> contestualmente all’acquisto.
      </p>
      <p style={mutedText}>
        La tessera MCP è già inclusa nel prezzo finale, quindi i nuovi membri non pagano costi aggiuntivi oltre al biglietto.
      </p>
      <p style={mutedText}>
        Tutti i partecipanti riceveranno biglietto, tessera digitale (se necessaria) e informazioni sulla location.
      </p>
    </PanelBox>
  )
}

export default function ParticipantsInfoPanel({ event, purchaseMode }) {
  const mode = purchaseMode || resolvePurchaseMode(event)

  if (mode === PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS) {
    return <OnlyMembersPanel />
  }

  if (mode === PURCHASE_MODES.ONLY_MEMBERS) {
    return <MembershipIncludedPanel />
  }

  if (mode === PURCHASE_MODES.PUBLIC) {
    return <PublicPanel />
  }

  return null
}
