// config/endpoints.js


// Identifica l'ambiente (fallback a 'development' se NEXT_PUBLIC_ENV non è definito)
const isProduction = process.env.NEXT_PUBLIC_ENV === 'production';

// BASE_URL per locale (fallback a un URL statico se la variabile non è definita)
const BASE_URL_LOCAL =
  process.env.NEXT_PUBLIC_BASE_URL || 'http://127.0.0.1:5001/mcp-website-2a1ad/us-central1';

// Definizione degli endpoint in locale
const localEndpoints = {
  contactUs: `${BASE_URL_LOCAL}/contact_us2`,
  createAdmin: `${BASE_URL_LOCAL}/create_admin`,
  createEvent: `${BASE_URL_LOCAL}/create_event`,
  deleteEvent: `${BASE_URL_LOCAL}/delete_event`,
  getAllEvents: `${BASE_URL_LOCAL}/get_all_events`,
  getAllMessages: `${BASE_URL_LOCAL}/get_all_messages`,
  getEventById: `${BASE_URL_LOCAL}/get_event_by_Id`,
  getNextEvent: `${BASE_URL_LOCAL}/get_next_event`,
  newsletterSignup: `${BASE_URL_LOCAL}/newsletter_signup`,
  updateEvent: `${BASE_URL_LOCAL}/update_event`,
  verifyAdmin: `${BASE_URL_LOCAL}/verify_admin`,
  getAllEvents: `${BASE_URL_LOCAL}/get_all_events`,
  p
};

// Definizione degli endpoint in produzione
const productionEndpoints = {
  contactUs: 'https://contact-us2-cgp4ofmn2q-uc.a.run.app',
  createAdmin: 'https://create-admin-cgp4ofmn2q-uc.a.run.app',
  createEvent: 'https://create-event-cgp4ofmn2q-uc.a.run.app',
  deleteEvent: 'https://delete-event-cgp4ofmn2q-uc.a.run.app',
  getAllEvents: 'https://get-all-events-cgp4ofmn2q-uc.a.run.app',
  getAllMessages: 'https://get-all-messages-cgp4ofmn2q-uc.a.run.app',
  getEventById: 'https://get-event-by-id-cgp4ofmn2q-uc.a.run.app',
  getNextEvent: 'https://get-next-event-cgp4ofmn2q-uc.a.run.app',
  newsletterSignup: 'https://newsletter-signup-cgp4ofmn2q-uc.a.run.app',
  updateEvent: 'https://update-event-cgp4ofmn2q-uc.a.run.app',
  verifyAdmin: 'https://verify-admin-cgp4ofmn2q-uc.a.run.app',
  getAllEvents: 'https://get-all-events-cgp4ofmn2q-uc.a.run.app',
};

// Seleziona gli endpoint in base all'ambiente
const endpoints = isProduction ? productionEndpoints : localEndpoints;

// Esporta l'oggetto `endpoints`
export {endpoints};
export default endpoints; // Esportazione di default