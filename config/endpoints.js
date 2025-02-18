// config/endpoints.js

import { createOrder } from "@/services/paypal";


// Identifica l'ambiente (fallback a 'development' se NEXT_PUBLIC_ENV non è definito)
const isProduction = process.env.NEXT_PUBLIC_ENV === 'production';

// BASE_URL per locale (fallback a un URL statico se la variabile non è definita)
const BASE_URL_LOCAL =
  process.env.NEXT_PUBLIC_BASE_URL || 'http://127.0.0.1:5002/mcp-website-2a1ad/us-central1';

// Definizione degli endpoint in locale
const localEndpoints = {
  contactUs: `${BASE_URL_LOCAL}/contact_us2`,
  createAdmin: `${BASE_URL_LOCAL}/create_admin`,
  createEvent: `${BASE_URL_LOCAL}/create_event`,
  deleteEvent: `${BASE_URL_LOCAL}/delete_event`,
  getAllEvents: `${BASE_URL_LOCAL}/get_all_events`,
  getAllMessages: `${BASE_URL_LOCAL}/get_all_messages`,
  getEventById: `${BASE_URL_LOCAL}/get_event_by_id`,
  getNextEvent: `${BASE_URL_LOCAL}/get_next_event2`,
  newsletterSignup: `${BASE_URL_LOCAL}/newsletter_signup`,
  updateEvent: `${BASE_URL_LOCAL}/update_event`,
  verifyAdmin: `${BASE_URL_LOCAL}/verify_admin`,
  getAllEvents: `${BASE_URL_LOCAL}/get_all_events`,
  createOrder: `${BASE_URL_LOCAL}/create_order`,
  captureOrder: `${BASE_URL_LOCAL}/capture_order`,
  signupRequest: `${BASE_URL_LOCAL}/signup_request`,
  admin: {
    createAdmin: `${BASE_URL_LOCAL}/create_admin`,
    verifyAdmin: `${BASE_URL_LOCAL}/verify_admin`,
    
    // Events
    createEvent: `${BASE_URL_LOCAL}/create_event`,
    updateEvent: `${BASE_URL_LOCAL}/update_event`,
    deleteEvent: `${BASE_URL_LOCAL}/delete_event`,
    getAllEventsAdmin: `${BASE_URL_LOCAL}/admin/get_all_events`,
    
// Messages
getAllMessages: `${BASE_URL_LOCAL}/get_all_messages`,
    
// Signup requests
getSignupRequests: `${BASE_URL_LOCAL}/get_signup_requests`,
updateSignupRequest: `${BASE_URL_LOCAL}/update_signup_request`,
deleteSignupRequest: `${BASE_URL_LOCAL}/delete_signup_request`,
acceptSignupRequest: `${BASE_URL_LOCAL}/accept_signup_request`,

// Newsletter
getNewsletterSignups: `${BASE_URL_LOCAL}/get_newsletter_signups`,
updateNewsletterSignup: `${BASE_URL_LOCAL}/update_newsletter_signup`,
deleteNewsletterSignup: `${BASE_URL_LOCAL}/delete_newsletter_signup`,

// Tickets
createTicket: `${BASE_URL_LOCAL}/create_ticket`,
getTickets: `${BASE_URL_LOCAL}/get_tickets`,
updateTicket: `${BASE_URL_LOCAL}/update_ticket`,
deleteTicket: `${BASE_URL_LOCAL}/delete_ticket`,
sendPdfTicket: `${BASE_URL_LOCAL}/send_pdf_ticket`,
createNewPdfTicket: `${BASE_URL_LOCAL}/create_new_pdf_ticket`,
deleteExistingPdfTicket: `${BASE_URL_LOCAL}/delete_existing_pdf_ticket`,
}
  
  
  
};

const productionEndpoints = {
  contactUs: "https://contact-us2-cgp4ofmn2q-uc.a.run.app",
  createAdmin: "https://create-admin-cgp4ofmn2q-uc.a.run.app",
  createEvent: "https://create-event-cgp4ofmn2q-uc.a.run.app",
  deleteEvent: "https://delete-event-cgp4ofmn2q-uc.a.run.app",
  getAllEvents: "https://get-all-events-cgp4ofmn2q-uc.a.run.app",
  getAllMessages: "https://get-all-messages-cgp4ofmn2q-uc.a.run.app",
  getEventById: "https://get-event-by-id-cgp4ofmn2q-uc.a.run.app",

  getNextEvent: "https://get-next-event2-cgp4ofmn2q-uc.a.run.app",
  newsletterSignup: "https://newsletter-signup-cgp4ofmn2q-uc.a.run.app",
  updateEvent: "https://update-event-cgp4ofmn2q-uc.a.run.app",
  verifyAdmin: "https://verify-admin-cgp4ofmn2q-uc.a.run.app",
  createOrder: "https://create-order-cgp4ofmn2q-uc.a.run.app",
  captureOrder: "https://capture-order-cgp4ofmn2q-uc.a.run.app",
  signupRequest: "https://signup-request-cgp4ofmn2q-uc.a.run.app",
  admin: {
    createAdmin: "https://create-admin-cgp4ofmn2q-uc.a.run.app",
    verifyAdmin: "https://verify-admin-cgp4ofmn2q-uc.a.run.app",

    // Events
    createEvent: "https://create-event-cgp4ofmn2q-uc.a.run.app",
    updateEvent: "https://update-event-cgp4ofmn2q-uc.a.run.app",
    deleteEvent: "https://delete-event-cgp4ofmn2q-uc.a.run.app",
    getAllEventsAdmin: "https://admin-get-all-events-cgp4ofmn2q-uc.a.run.app",

    // Messages
    getAllMessages: "https://get-all-messages-cgp4ofmn2q-uc.a.run.app",

    // Signup requests
    getSignupRequests: "https://get-signup-requests-cgp4ofmn2q-uc.a.run.app",
    updateSignupRequest: "https://update-signup-request-cgp4ofmn2q-uc.a.run.app",
    deleteSignupRequest: "https://delete-signup-request-cgp4ofmn2q-uc.a.run.app",
    acceptSignupRequest: "https://accept-signup-request-cgp4ofmn2q-uc.a.run.app",

    // Newsletter
    getNewsletterSignups: "https://get-newsletter-signups-cgp4ofmn2q-uc.a.run.app",
    updateNewsletterSignup: "https://update-newsletter-signup-cgp4ofmn2q-uc.a.run.app",
    deleteNewsletterSignup: "https://delete-newsletter-signup-cgp4ofmn2q-uc.a.run.app",

    // Tickets
    createTicket: "https://create-ticket-cgp4ofmn2q-uc.a.run.app",
    getTickets: "https://get-tickets-cgp4ofmn2q-uc.a.run.app",
    updateTicket: "https://update-ticket-cgp4ofmn2q-uc.a.run.app",
    deleteTicket: "https://delete-ticket-cgp4ofmn2q-uc.a.run.app",
    sendPdfTicket: "https://send-pdf-ticket-cgp4ofmn2q-uc.a.run.app",
    createNewPdfTicket: "https://create-new-pdf-ticket-cgp4ofmn2q-uc.a.run.app",
    deleteExistingPdfTicket: "https://delete-existing-pdf-ticket-cgp4ofmn2q-uc.a.run.app",
  },
}

// Definizione degli endpoint in produzione
  
// Seleziona gli endpoint in base all'ambiente
const endpoints = isProduction ? productionEndpoints : localEndpoints;

// Esporta l'oggetto `endpoints`
export {endpoints};
export default endpoints; // Esportazione di default

