import { getImageUrl } from "@/config/firebaseStorage"
import { parseEventDate } from "@/lib/utils"
import { getAllEvents } from "@/services/events"

const COVER_LOOKUP_CONCURRENCY = 8

async function mapWithConcurrency(items, limit, mapper) {
  const results = new Array(items.length)
  let cursor = 0

  async function worker() {
    while (cursor < items.length) {
      const index = cursor
      cursor += 1
      results[index] = await mapper(items[index], index)
    }
  }

  const workerCount = Math.min(Math.max(1, limit), items.length)
  await Promise.all(Array.from({ length: workerCount }, worker))
  return results
}

export async function getEventPhotoAlbums() {
  try {
    const { success, events: rawEvents, error } = await getAllEvents({ view: "gallery" })

    if (!success || !Array.isArray(rawEvents)) {
      return { events: [], error: error || "Unable to load events." }
    }

    const withCovers = await mapWithConcurrency(
      rawEvents,
      COVER_LOOKUP_CONCURRENCY,
      async (ev) => {
        try {
          const folder = ev?.photoPath
            ? `foto/${ev.photoPath}`
            : ev?.title
              ? `foto/${ev.title}`
              : null

          if (!folder) return null

          const coverPhoto = await getImageUrl(folder, "cover.jpg")
          if (!coverPhoto) return null

          return { ...ev, coverPhoto, hasPhotos: true }
        } catch {
          return null
        }
      }
    )

    const events = withCovers
      .filter(Boolean)
      .sort((a, b) => parseEventDate(b.date) - parseEventDate(a.date))

    return { events, error: null }
  } catch {
    return { events: [], error: "Unable to load event photos." }
  }
}
