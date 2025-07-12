const ENV = process.env.NEXT_PUBLIC_ENV || "local";

const BASE_URL =
  ENV === "production"
    ? "https://us-central1-mcp-website-2a1ad.cloudfunctions.net"
    : process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:5001/mcp-website-2a1ad/us-central1";

// Utility per costruire endpoint completi
const make = (slug) => `${BASE_URL}/${slug}`;

export const endpoints = {
  // Public endpoints
  contactUs: make("contact_us"),
  getNextEvent: make("get_next_event"),
  newsletterSignup: make("newsletter_signup"),
  newsletterParticipantsSignup: make("newsletter_participants"),
  createOrder: make("create_order"),
  captureOrder: make("capture_order"),
  signupRequest: make("signup_request"),
  checkParticipants: make("check_participants"),

  // Public Events
  getAllEvents: make("get_all_events"),
  getEventById: make("get_event_by_id"),

  // Questions
  questions: {
    getAll: make("get_all_questions"),
  },

  // Admin endpoints grouped by domain
 admin: {
    createEvent: make("admin_create_event"),
    updateEvent: make("admin_update_event"),
    deleteEvent: make("admin_delete_event"),
    getAllEvents: make("admin_get_all_events"),
    getEventById: make("admin_get_event_by_id"),
    uploadEventPhoto: make("admin_upload_event_photo"),
    
    
    
    getParticipantsByEvent: make("get_participants_by_event"),
    getParticipantById: make("get_participant"),
    createParticipant: make("create_participant"),
    updateParticipant: make("update_participant"),
    deleteParticipant: make("delete_participant"),
    sendLocation: make("send_location"),
    sendLocationToAll: make("send_location_to_all"),
    sendTicket: make("send_ticket"),
    
    
    
    getMemberships: make("get_memberships"),
    getMembershipById: make("get_membership"),
    createMembership: make("create_membership"),
    updateMembership: make("update_membership"),
    deleteMembership: make("delete_membership"),
    sendMembershipCard: make("send_membership_card"),
      getMembershipPurchases: make("get_membership_purchases"),
    getMembershipEvents: make("get_membership_events"),
    setMembershipPrice: make("set_membership_price"),
    getMembershipPrice: make("get_membership_price"),

    getAllPurchases: make("get_all_purchases"),
    getPurchase: make("get_purchase"),
    createPurchase: make("create_purchase"),
    deletePurchase: make("delete_purchase"),
    getGeneralStats:make("admin_get_general_stats"),
    
    
    getAllMessages: make("get_messages"),
    deleteMessage: make("delete_message"),
    replyToMessage: make("reply_to_message"),
        // ✅ Settings endpoints
    getSetting: make("get_settings"),
    setSetting: make("set_settings"),


  
  },
};