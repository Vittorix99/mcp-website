
import { charter, helveticaNeue, atlantico } from "./fonts";
import { Navigation } from "@/components/Navigation";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import { UserProvider } from "@/contexts/userContext";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { Footer } from "@/components/Footer";
import Script from "next/script";
import { ConsoleErrorSilencer } from "./suppress-errors";
import { MetaPixel } from "@/config/metaPixel";

// Next.js App Router: viewport metadata (include viewport-fit=cover)
export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
};
export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`dark ${charter.variable} ${helveticaNeue.variable} ${atlantico.variable}`}
    >
      <body
        // usa 100dvh dove supportato; fallback alla var --vh (settata sotto)
        className="antialiased bg-black text-white min-h-[calc(var(--vh,1vh)*100)]"
        style={{ minHeight: "100dvh" }}
      >
        <MetaPixel />

        {/* pattern sottile opzionale */}
        <div className="wave-pattern fixed inset-0 opacity-10 pointer-events-none" />

        {/* Background animato full-viewport */}
        <AnimatedBackground />

        <UserProvider>
          <ConsoleErrorSilencer />
          <Navigation />

          <div className="min-h-[calc(var(--vh,1vh)*100)] pb-0">{children}</div>

          <Footer />
          <Toaster position="top-right" />
        </UserProvider>

        {/* Iubenda */}
        <Script
          id="iubenda-widget-script"
          strategy="afterInteractive"
          src="//embeds.iubenda.com/widgets/40b8b87f-b6a1-4a55-af93-2465acfa04c7.js"
        />

        {/* Apple Pay */}
        <Script
          id="apple-pay-sdk"
          strategy="afterInteractive"
          src="https://applepay.cdn-apple.com/jsapi/v1/apple-pay-sdk.js"
        />

        {/* Fallback JS per --vh su device che non supportano 100dvh */}
        <Script id="set-vh-var" strategy="afterInteractive">
          {`
            function setVh() {
              const vh = window.innerHeight * 0.01;
              document.documentElement.style.setProperty('--vh', \`\${vh}px\`);
            }
            setVh();
            window.addEventListener('resize', setVh);
            // iOS URL bar show/hide
            window.addEventListener('orientationchange', setVh);
          `}
        </Script>
      </body>
    </html>
  );
}