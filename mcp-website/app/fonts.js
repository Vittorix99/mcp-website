import localFont from "next/font/local"

// Charter font family with all variants
export const charter = localFont({
  variable: "--font-charter",
  display: "swap",
  fallback: ["Times New Roman", "serif"],
  src: [
    {
      path: "./fonts/Charter-Roman-01.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "./fonts/Charter-Italic-02.ttf",
      weight: "400",
      style: "italic",
    },
    {
      path: "./fonts/Charter-Bold-04.ttf",
      weight: "700",
      style: "normal",
    },
    {
      path: "./fonts/Charter-BoldItalic-03.ttf",
      weight: "700",
      style: "italic",
    },
    {
      path: "./fonts/Charter-Black-06.ttf",
      weight: "900",
      style: "normal",
    },
    {
      path: "./fonts/Charter-BlackItalic-05.ttf",
      weight: "900",
      style: "italic",
    },
  ],
})

// Helvetica Neue font family with all variants
export const helveticaNeue = localFont({
  variable: "--font-helvetica",
  display: "swap",
  fallback: ["Arial", "sans-serif"],
  src: [
    {
      path: "./fonts/HelveticaNeue-Thin-13.ttf",
      weight: "100",
      style: "normal",
    },
    {
      path: "./fonts/HelveticaNeue-ThinItalic-14.ttf",
      weight: "100",
      style: "italic",
    },
    {
      path: "./fonts/HelveticaNeue-UltraLight-06.ttf",
      weight: "200",
      style: "normal",
    },
    {
      path: "./fonts/HelveticaNeue-UltraLightItalic-07.ttf",
      weight: "200",
      style: "italic",
    },
    {
      path: "./fonts/HelveticaNeue-Light-08.ttf",
      weight: "300",
      style: "normal",
    },
    {
      path: "./fonts/HelveticaNeue-LightItalic-09.ttf",
      weight: "300",
      style: "italic",
    },
    {
      path: "./fonts/HelveticaNeue-01.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "./fonts/HelveticaNeue-Italic-03.ttf",
      weight: "400",
      style: "italic",
    },
    {
      path: "./fonts/HelveticaNeue-Medium-11.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "./fonts/HelveticaNeue-MediumItalic-12.ttf",
      weight: "500",
      style: "italic",
    },
    {
      path: "./fonts/HelveticaNeue-Bold-02.ttf",
      weight: "700",
      style: "normal",
    },
    {
      path: "./fonts/HelveticaNeue-BoldItalic-04.ttf",
      weight: "700",
      style: "italic",
    },
    {
      path: "./fonts/HelveticaNeue-CondensedBold-05.ttf",
      weight: "700",
      style: "normal",
    },
    {
      path: "./fonts/HelveticaNeue-CondensedBlack-10.ttf",
      weight: "900",
      style: "normal",
    },
  ],
})

// Atlantico font (still using the OTF as it wasn't converted)
export const atlantico = localFont({
  src: "./fonts/AtlanticoFont-Demo.otf",
  variable: "--font-atlantico",
  display: "swap",
  fallback: ["Arial", "sans-serif"],
})

