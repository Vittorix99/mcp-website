async function downloadAsExcel(filename, sheets) {
  const { default: ExcelJS } = await import("exceljs")
  const wb = new ExcelJS.Workbook()

  for (const { name, rows, headers } of sheets) {
    const ws = wb.addWorksheet(name)
    const firstRow = rows.find(r => Object.keys(r).length > 0)
    const cols = headers || (firstRow ? Object.keys(firstRow) : [])
    if (cols.length) {
      ws.columns = cols.map(h => ({ header: h, key: h, width: 20 }))
    }
    ws.addRows(rows)
  }

  const buffer = await wb.xlsx.writeBuffer()
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export { downloadAsExcel }

export async function exportParticipantsToExcel(participants, eventTitle, eventId) {
  const rows = participants.map(p => {
    const purchaseDate = p.createdAt
      ? new Date(p.createdAt).toLocaleDateString("it-IT")
      : ""

    const genderCode = (() => {
      const g = (p.gender || "").toLowerCase().trim()
      return g === "male" ? "M" : g === "female" ? "F" : "N/A"
    })()

    return {
      Nome: p.name || "",
      Cognome: p.surname || "",
      Email: p.email || "",
      Telefono: p.phone || "",
      Genere: genderCode,
      "Prezzo pagato": p.price != null ? Number(p.price).toFixed(2) : "",
      Omaggio: Number(p.price) === 0 ? "Sì" : "No",
      "Membership ID": p.membershipId || "",
      "Data acquisto": purchaseDate,
    }
  })

  const total = participants
    .reduce((sum, p) => sum + (Number(p.price) || 0), 0)
    .toFixed(2)
  const omaggiCount = participants.filter(p => Number(p.price) === 0).length

  rows.push(
    {},
    { Nome: "Totale incassato (€)", "Prezzo pagato": total },
    { Nome: "Totale omaggi", Omaggio: omaggiCount.toString() }
  )

  await downloadAsExcel(`partecipanti_${slugify(eventTitle)}_${eventId}.xlsx`, [
    {
      name: "Partecipanti",
      rows,
      headers: [
        "Nome", "Cognome", "Email", "Telefono", "Genere",
        "Prezzo pagato", "Omaggio", "Membership ID", "Data acquisto",
      ],
    },
  ])
}

function slugify(text) {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "_")
    .replace(/[^\w\-]+/g, "")
    .replace(/--+/g, "_")
}
