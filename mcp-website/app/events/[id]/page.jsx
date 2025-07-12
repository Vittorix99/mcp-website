import { Suspense } from "react"
import { EventContent } from "./content"
import { getAllEvents } from "@/services/events"

// Force SSR in Next.js (important for Firebase Hosting)
export const dynamic = "force-dynamic"


// Main component with SSR enabled
export default async function EventPage({ params }) {
  // Accedi direttamente a params.id senza await
  const { id } = await params

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black py-24">
          <div className="container mx-auto px-4">
            <div className="text-center gradient-text">Loading...</div>
          </div>
        </div>
      }
    >
      <EventContent id={id} />
    </Suspense>
  )
}

