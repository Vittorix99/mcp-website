
import HomeClient from "./HomeClient"
import { buildOrganizationJsonLd } from "@/lib/seo/jsonld"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

const baseUrl = getBaseUrlFromEnv()
export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
  alternates: baseUrl ? { canonical: `${baseUrl}/` } : undefined,
}

export default function LandingPage() {
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
