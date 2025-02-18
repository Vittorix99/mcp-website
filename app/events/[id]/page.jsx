import { Suspense } from "react";
import { EventContent } from "./content";
import { getAllEvents } from "@/services/events";

// Force SSR in Next.js (important for Firebase Hosting)
export const dynamic = "force-dynamic";

// Generate static params for optional preloading
export async function generateStaticParams() {
  try {
    const events = await getAllEvents();

    if (!events?.success || !events?.events?.length) {
      return [];
    }

    // Return the list of event IDs
    return events.events.map(event => ({
      id: event.id.toString(),
    }));
  } catch (error) {
    console.error("Errore nel recupero degli eventi:", error);
    return []; // Avoid pre-rendering if there's an error
  }
}

// Main component with SSR enabled
export default async function EventPage({ params }) {
  const id = params.id; // Directly get the dynamic ID from params

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
  );
}