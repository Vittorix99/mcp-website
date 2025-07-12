const isProd = process.env.NEXT_PUBLIC_PAYPAL_ENV === "production"

export const initialOptions = {
  "client-id": isProd
    ? process.env.NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID
    : process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID,

  currency: "EUR",
  intent: "capture",

  components: "buttons,funding-eligibility", // Include Apple Pay eligibility
  "enable-funding": "applepay",

  "merchant-id": process.env.NEXT_PUBLIC_PAYPAL_MERCHANT_ID || "",

  // Optional extras
  "data-page-type": "product-details",
  "data-sdk-integration-source": "developer-studio",
}