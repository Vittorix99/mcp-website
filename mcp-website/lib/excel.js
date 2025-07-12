import * as XLSX from "xlsx";

/**
 * Export participants to Excel with custom headers and total aggregation.
 * @param {Array} participants - Lista dei partecipanti.
 * @param {string} eventTitle - Titolo evento per il nome file.
 * @param {string} eventId - ID evento per il nome file.
 */


export function exportParticipantsToExcel(participants, eventTitle, eventId) {
  const rows = participants.map(p => {
    const purchaseDate = p.createdAt
      ? new Date(p.createdAt).toLocaleDateString("it-IT")
      : "";

    const genderCode = (() => {
      const g = (p.gender || "").toLowerCase().trim();
      return g === "male" ? "M"
           : g === "female" ? "F"
           : "N/A";
    })();

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
    };
  });

  const total = participants
    .reduce((sum, p) => sum + (Number(p.price) || 0), 0)
    .toFixed(2);
  const omaggiCount = participants.filter(p => Number(p.price) === 0).length;

  rows.push(
    {},
    { Nome: "Totale incassato (€)", Genere: "", "Prezzo pagato": total },
    { Nome: "Totale omaggi", Genere: "", Omaggio: omaggiCount.toString() }
  );

  const ws = XLSX.utils.json_to_sheet(rows, {
    header: [
      "Nome", "Cognome", "Email", "Telefono", "Genere",
      "Prezzo pagato", "Omaggio", "Membership ID", "Data acquisto"
    ]
  });

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Partecipanti");
  XLSX.writeFile(wb, `partecipanti_${slugify(eventTitle)}_${eventId}.xlsx`);
}

function slugify(text) {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '_')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '_');
}