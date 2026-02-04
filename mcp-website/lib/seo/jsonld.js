export function toIsoDateTime(dateStr, timeStr) {
  if (!dateStr) return null
  let day, month, year
  const value = String(dateStr).trim()
  if (value.includes("-")) {
    const parts = value.split("-").map((p) => p.trim())
    if (parts.length === 3 && parts[0].length === 2) {
      ;[day, month, year] = parts
    } else if (parts.length === 3 && parts[0].length === 4) {
      ;[year, month, day] = parts
    }
  } else if (value.includes("/")) {
    const parts = value.split("/").map((p) => p.trim())
    if (parts.length === 3) {
      ;[day, month, year] = parts
    }
  }

  if (!day || !month || !year) return null
  const datePart = `${year.padStart(4, "0")}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`
  if (!timeStr) return datePart

  const timeRaw = String(timeStr).split("-")[0].trim()
  if (!timeRaw) return datePart
  const [hh, mm = "00"] = timeRaw.split(":")
  if (!hh) return datePart
  return `${datePart}T${hh.padStart(2, "0")}:${mm.padStart(2, "0")}:00`
}

export function buildEventJsonLd({ event, url, siteName = "Music Connecting People", siteUrl = "" }) {
  const startDate = toIsoDateTime(event?.date, event?.startTime)
  const locationName = event?.locationHint
  const addressText = event?.locationHint

  const payload = {
    "@context": "https://schema.org",
    "@type": "Event",
    name: event?.title || "Event",
    url,
    startDate: startDate || undefined,
    location: locationName
      ? {
          "@type": "Place",
          name: locationName,
          address: addressText || locationName,
        }
      : undefined,
    organizer: {
      "@type": "Organization",
      name: siteName,
      url: siteUrl || undefined,
    },
  }

  return JSON.parse(JSON.stringify(payload))
}

export function buildOrganizationJsonLd({ siteName = "Music Connecting People", siteUrl = "", logoUrl = "" }) {
  const payload = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: siteName,
    url: siteUrl || undefined,
    logo: logoUrl || undefined,
  }

  return JSON.parse(JSON.stringify(payload))
}

export function buildEventsItemListJsonLd({ items = [], baseUrl = "", listUrl = "" }) {
  const list = items
    .filter((item) => item?.slug)
    .map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      url: baseUrl ? `${baseUrl}/events/${item.slug}` : undefined,
      name: item.title || undefined,
    }))

  const payload = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    itemListElement: list,
    url: listUrl || undefined,
  }

  return JSON.parse(JSON.stringify(payload))
}

export function buildEventPhotosCollectionJsonLd({ items = [], baseUrl = "", listUrl = "" }) {
  const collection = items
    .filter((item) => item?.slug)
    .map((item) => ({
      "@type": "CollectionPage",
      name: item.title || "Event Photos",
      url: baseUrl ? `${baseUrl}/events-foto/${item.slug}` : undefined,
    }))

  const payload = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Event Photos",
    url: listUrl || undefined,
    hasPart: collection,
  }

  return JSON.parse(JSON.stringify(payload))
}
