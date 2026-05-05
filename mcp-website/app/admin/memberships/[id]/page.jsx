// Force SSR in Next.js (important for Firebase Hosting)
export const dynamic = "force-dynamic";

import { Suspense } from "react";
import MembershipContent from "./content";
import { AdminLoading } from "@/components/admin/AdminPageChrome";

export default async function MembershipPage({ params }) {
  const { id } = await params;

  return (
    <Suspense fallback={<AdminLoading label="Caricamento membro..." />}>
      <MembershipContent id={id} />
    </Suspense>
  );
}
