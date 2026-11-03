const mode = process.env.NEXT_PUBLIC_PAYPAL_ENV
const environment = process.env.NEXT_PUBLIC_ENV
export const isFakePayment = mode === "fake"
const offline = environment === "local" || environment === "test"
const expectedMode = offline ? "fake" : environment === "staging" ? "sandbox" : environment === "production" ? "production" : null
if (!expectedMode || mode !== expectedMode) throw new Error("Invalid PayPal browser mode")
const isProd = mode === "production"
const clientId = isProd ? process.env.NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID : process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID
if (!offline && (!clientId?.trim() || clientId.trim() === "sb")) throw new Error("Missing or invalid PayPal browser client ID")

// Base SDK options: solo pulsanti PayPal + Apple Pay
const options = {
  "client-id": clientId,

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

export const initialOptions = isFakePayment ? null : options
