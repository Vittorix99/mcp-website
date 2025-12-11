

// Force SSR in Next.js (important for Firebase Hosting)
export const dynamic = "force-dynamic";

import { Suspense } from "react";
import EventContent from "./content";

export default async function EventPage({ params }) {
  const { id } = await params;

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black py-24">
          <div className="container mx-auto px-4">
            <div className="text-center gradient-text text-white">Loading...</div>
          </div>
        </div>
      }
    >
      <EventContent id={id} />
    </Suspense>
  );
}
