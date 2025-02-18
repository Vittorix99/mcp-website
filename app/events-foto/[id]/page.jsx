import { Suspense } from "react";
import { EventContent } from "./content";
import { Loader2 } from "lucide-react";
import { getAllEvents } from "@/services/events";

// Force Next.js to use SSR for this page
export const dynamic = "force-dynamic";

// Generate static params for preloading (optional)
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
    return []; // Fallback to no pre-rendering if there's an error
  }
}

// Main component with SSR enabled
export default async function EventPhotosDetailPage({ params }) {
  const id = params.id; // Directly get the dynamic ID from params

  if (!id) {
    return (
      <Suspense fallback={<div>Caricamento...</div>} />
    );
  }

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
        </div>
      }
    >
      <EventContent id={id} />
    </Suspense>
  );
}