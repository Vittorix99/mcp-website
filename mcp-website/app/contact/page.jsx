import { ContactUs } from "@/components/pages/ContactUs"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

const baseUrl = getBaseUrlFromEnv()

export const metadata = {
  title: "Contact — Music Connecting People",
  description: "Get in touch with MCP. Collaborate, play at an event, or just say hello.",
  alternates: baseUrl ? { canonical: `${baseUrl}/contact` } : undefined,
}

export default function ContactPage() {
  return (
    <div style={{ minHeight: "100svh", background: "#080808", paddingTop: "80px" }}>
      <ContactUs />
    </div>
  )
}
