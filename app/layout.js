import localFont from "next/font/local"
import { Navigation } from "@/components/pages/Navigation"
import "./globals.css"
import { Toaster } from "react-hot-toast"
import { UserProvider } from "@/contexts/userContext"
import { AnimatedBackground } from "@/components/pages/AnimatedBackground"

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
})

export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} antialiased min-h-screen bg-black text-white`}>
        <div className="wave-pattern fixed inset-0 opacity-10 pointer-events-none" />
        <AnimatedBackground />

        <UserProvider>
          <Navigation />
          {children}
          <Toaster position="top-right" />
        </UserProvider>
      </body>
    </html>
  )
}

