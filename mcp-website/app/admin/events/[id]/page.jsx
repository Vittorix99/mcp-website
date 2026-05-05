

// Force SSR in Next.js (important for Firebase Hosting)
export const dynamic = "force-dynamic";

import { Suspense } from "react";
import EventContent from "./content";
import { AdminLoading } from "@/components/admin/AdminPageChrome";

export default async function EventPage({ params }) {
  const { id } = await params;

  return (
    <Suspense fallback={<AdminLoading label="Caricamento evento..." />}>
      <EventContent id={id} />
    </Suspense>
  );
}
