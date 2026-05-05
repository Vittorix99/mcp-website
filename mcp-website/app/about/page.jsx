import { AboutUs } from "@/components/pages/AboutUs"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

const baseUrl = getBaseUrlFromEnv()

export const metadata = {
  title: "About — Music Connecting People",
  description: "Our philosophy, our story, and why we believe music builds real connection.",
  alternates: baseUrl ? { canonical: `${baseUrl}/about` } : undefined,
}

export default function AboutPage() {
  return (
    <div style={{ minHeight: "100svh", background: "#080808", paddingTop: "80px" }}>
      <AboutUs />
    </div>
  )
}
