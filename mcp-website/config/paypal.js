const isProd = process.env.NEXT_PUBLIC_PAYPAL_ENV === "production"

// Base SDK options: solo pulsanti PayPal + Apple Pay
const options = {
  "client-id": isProd
    ? process.env.NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID
    : process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID,

  currency: "EUR",
  intent: "capture",

  // Carichiamo solo i componenti necessari
  "enable-funding": "applepay",


  components: "buttons,funding-eligibility", // Include Apple Pay eligibility

  // Disabilita tutti gli altri metodi (lascia solo PayPal + Apple Pay)
  // Nota: alcuni funding potrebbero non apparire comunque se non supportati dall'account/utente
  "disable-funding": [
    "card",
    "venmo",
    "paylater",
    "credit",
    "sepa",
    "bancontact",
    "eps",
    "giropay",
    "ideal",
    "sofort",
    "mybank",
    "blik",
    "p24",
  ].join(","),

  // Optional extras
  "data-page-type": "product-details",
  "data-sdk-integration-source": "developer-studio",
}

// Imposta merchant-id **solo in produzione** (evita mismatch in sandbox)
if (isProd && process.env.NEXT_PUBLIC_PAYPAL_MERCHANT_ID) {
  options["merchant-id"] = process.env.NEXT_PUBLIC_PAYPAL_MERCHANT_ID
}

export const initialOptions = options
