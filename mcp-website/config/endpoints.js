const ENV = process.env.NEXT_PUBLIC_ENV || "local";

const SERVER_BASE_URL =
  ENV === "production"
    ? "https://us-central1-mcp-website-2a1ad.cloudfunctions.net"
    : process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:5001/mcp-website-2a1ad/us-central1";

// Use same-origin proxy for browser requests to avoid CORS preflight.
const CLIENT_BASE_URL = "/api/proxy";
const BASE_URL = typeof window === "undefined" ? SERVER_BASE_URL : CLIENT_BASE_URL;

// Utility per costruire endpoint completi
const make = (slug) => `${BASE_URL}/${slug}`;

export const endpoints = {
  // Public endpoints
  contactUs: make("contact_us"),
  getNextEvent: make("get_next_event"),
  newsletterSignup: make("newsletter_signup"),
  newsletterParticipantsSignup: make("newsletter_participants"),
  createEventOrder: make("create_order_event"),
  captureEventOrder: make("capture_order_event"),
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
    getMembershipsReport: make("get_memberships_report"),
    getWalletModel: make("get_wallet_model"),
    setWalletModel: make("set_wallet_model"),
    createWalletPass: make("create_wallet_pass"),
    invalidateWalletPass: make("invalidate_wallet_pass"),

    getAllPurchases: make("get_all_purchases"),
    getPurchase: make("get_purchase"),
    createPurchase: make("create_purchase"),
    deletePurchase: make("delete_purchase"),
    getGeneralStats:make("admin_get_general_stats"),
    errorLogs: make("admin_error_logs"),

    entrance: {
      generateScanToken: make("entrance_generate_scan_token"),
      verifyScanToken: make("entrance_verify_scan_token"),
      deactivateScanToken: make("entrance_deactivate_scan_token"),
      manualEntry: make("entrance_manual_entry"),
    },
    
    
    getAllMessages: make("get_messages"),
    deleteMessage: make("delete_message"),
    replyToMessage: make("reply_to_message"),
        // ✅ Settings endpoints
    getSetting: make("get_settings"),
    setSetting: make("set_settings"),

    mailerLite: {
      subscribers: make("admin_mailerlite_subscribers"),
      subscriberForget: make("admin_mailerlite_subscriber_forget"),
      groups: make("admin_mailerlite_groups"),
      groupSubscribers: make("admin_mailerlite_group_subscribers"),
      groupAssignSubscriber: make("admin_mailerlite_group_assign_subscriber"),
      groupUnassignSubscriber: make("admin_mailerlite_group_unassign_subscriber"),
      fields: make("admin_mailerlite_fields"),
      segments: make("admin_mailerlite_segments"),
      segmentSubscribers: make("admin_mailerlite_segment_subscribers"),
      campaigns: make("admin_mailerlite_campaigns"),
      campaignSchedule: make("admin_mailerlite_campaign_schedule"),
      campaignCancelReady: make("admin_mailerlite_campaign_cancel_ready"),
      automations: make("admin_mailerlite_automations"),
      automationActivity: make("admin_mailerlite_automation_activity"),
    },

    newsletter: {
      getSignups: make("admin_get_newsletter_signups"),
      getConsents: make("admin_get_newsletter_consents"),
      update: make("admin_update_newsletter_signup"),
      delete: make("admin_delete_newsletter_signup"),
    },

    sender: {
      subscribers: make("admin_sender_subscribers"),
      subscriberGroups: make("admin_sender_subscriber_groups"),
      subscriberEvents: make("admin_sender_subscriber_events"),
      groups: make("admin_sender_groups"),
      groupSubscribers: make("admin_sender_group_subscribers"),
      campaigns: make("admin_sender_campaigns"),
      campaignSend: make("admin_sender_campaign_send"),
      campaignSchedule: make("admin_sender_campaign_schedule"),
      campaignCopy: make("admin_sender_campaign_copy"),
      campaignStats: make("admin_sender_campaign_stats"),
      fields: make("admin_sender_fields"),
      segments: make("admin_sender_segments"),
      segmentSubscribers: make("admin_sender_segment_subscribers"),
      transactional: make("admin_sender_transactional"),
      transactionalSend: make("admin_sender_transactional_send"),
    },


  
  },
};
