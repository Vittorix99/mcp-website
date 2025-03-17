import { charter, helveticaNeue, atlantico } from "./fonts"
import { Navigation } from "@/components/pages/Navigation"
import "./globals.css"
import { Toaster } from "react-hot-toast"
import { UserProvider } from "@/contexts/userContext"
import { AnimatedBackground } from "@/components/pages/AnimatedBackground"
import Script from "next/script"
export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${charter.variable} ${helveticaNeue.variable} ${atlantico.variable} antialiased min-h-screen bg-black text-white`}
      >
        <div className="wave-pattern fixed inset-0 opacity-10 pointer-events-none" />
        <AnimatedBackground />

        <UserProvider>
          <Navigation />
          {children}
          <Toaster position="top-right" />
        </UserProvider>
        <Script
          id="iubenda-widget-script"
          strategy="afterInteractive"
          src="//embeds.iubenda.com/widgets/40b8b87f-b6a1-4a55-af93-2465acfa04c7.js"
        />
      </body>
    </html>
  )
}

