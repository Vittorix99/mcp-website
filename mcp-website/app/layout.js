
import { charter, helveticaNeue, atlantico } from "./fonts"
import { Navigation } from "@/components/Navigation"
import "./globals.css"
import { Toaster } from "react-hot-toast"
import { UserProvider } from "@/contexts/userContext"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { Footer } from "@/components/Footer"
import Script from "next/script"
import { ConsoleErrorSilencer } from "./suppress-errors"
import { MetaPixel } from "@/config/metaPixel"

export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
}

export default function RootLayout({ children }) {


  
  return (
    <html lang="en" className={`dark ${charter.variable} ${helveticaNeue.variable} ${atlantico.variable}`}>
      <body className="antialiased min-h-screen bg-black text-white">
         <MetaPixel />
        <div className="wave-pattern fixed inset-0 opacity-10 pointer-events-none" />

        
        <AnimatedBackground />
        

        <UserProvider>
            <ConsoleErrorSilencer />
          <Navigation />
          
          <div className="min-h-screen pb-0">{children}</div>
          <Footer />
          <Toaster position="top-right" />
        </UserProvider>
        <Script
          id="iubenda-widget-script"
          strategy="afterInteractive"
          src="//embeds.iubenda.com/widgets/40b8b87f-b6a1-4a55-af93-2465acfa04c7.js"
        />


        <Script
          id="apple-pay-sdk"
          strategy="afterInteractive"
          src="https://applepay.cdn-apple.com/jsapi/v1/apple-pay-sdk.js"
        />
      

            <Script
        id="iubenda-widget-script"
        strategy="afterInteractive"
        src="//embeds.iubenda.com/widgets/40b8b87f-b6a1-4a55-af93-2465acfa04c7.js"
      />
      </body>
    </html>
  )
}

