
import HomeClient from "./HomeClient"
import { buildOrganizationJsonLd } from "@/lib/seo/jsonld"

export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
}

export default function LandingPage() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.SITE_URL || ""
  const orgJsonLd = buildOrganizationJsonLd({
    siteName: "Music Connecting People",
    siteUrl: baseUrl,
  })

  return (
    <>
      {orgJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
        />
      )}
      <HomeClient />
    </>
  )
}
