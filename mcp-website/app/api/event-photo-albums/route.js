import { getEventPhotoAlbums } from "@/lib/event-photo-albums"

export const dynamic = "force-dynamic"

export async function GET() {
  const result = await getEventPhotoAlbums()

  return Response.json(result, {
    status: result.error ? 502 : 200,
    headers: {
      "Cache-Control": "private, max-age=300, stale-while-revalidate=300",
    },
  })
}
