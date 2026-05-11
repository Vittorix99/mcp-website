export function getServerBaseUrl() {
  return (process.env.NEXT_PUBLIC_BASE_URL || process.env.BACKEND_BASE_URL || "").replace(/\/$/, "");
}

// Use same-origin proxy for browser requests to avoid CORS preflight.
const CLIENT_BASE_URL = "/api/proxy";
const SERVER_BASE_URL = getServerBaseUrl();
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
  getEventGuide: make("get_event_guide"),

  // Public Radio
  radio: {
    getPublishedEpisodes: make("get_published_radio_episodes"),
    getLatestEpisode:     make("get_latest_radio_episode"),
    getEpisode:           make("get_radio_episode"),
    getSeasons:           make("get_radio_seasons"),
  },

  // Public Settings
  getSetting: make("get_setting"),
  getMembershipPrice: make("get_membership_price_public"),

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
    sendOmaggioEmails: make("send_omaggio_emails"),
    
    
    
    getMemberships: make("get_memberships"),
    getMembershipById: make("get_membership"),
    createMembership: make("create_membership"),
    updateMembership: make("update_membership"),
    mergeMemberships: make("merge_memberships"),
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
    renewMembership: make("renew_membership"),

    getAllPurchases: make("get_all_purchases"),
    getPurchase: make("get_purchase"),
    createPurchase: make("create_purchase"),
    updatePurchaseStatus: make("update_purchase_status"),
    deletePurchase: make("delete_purchase"),
    getGeneralStats: make("admin_get_general_stats"),
    getDashboardSnapshot: make("admin_get_dashboard_snapshot"),
    getAnalyticsEventSnapshot: make("admin_get_analytics_event_snapshot"),
    getAnalyticsGlobalSnapshot: make("admin_get_analytics_global_snapshot"),
    getAnalyticsEventsIndex: make("admin_get_analytics_events_index"),
    rebuildAnalytics: make("admin_rebuild_analytics"),
    getEntranceFlow: make("admin_get_entrance_flow"),
    getSalesOverTime: make("admin_get_sales_over_time"),
    getAudienceRetention: make("admin_get_audience_retention"),
    getRevenueBreakdown: make("admin_get_revenue_breakdown"),
    getEventFunnel: make("admin_get_event_funnel"),
    getGenderDistribution: make("admin_get_gender_distribution"),
    getAgeDistribution: make("admin_get_age_distribution"),
    getMembershipTrend: make("admin_get_membership_trend"),
    getDashboardKpis: make("admin_get_dashboard_kpis"),

    entrance: {
      generateScanToken: make("entrance_generate_scan_token"),
      verifyScanToken: make("entrance_verify_scan_token"),
      deactivateScanToken: make("entrance_deactivate_scan_token"),
      manualEntry: make("entrance_manual_entry"),
    },
    
    
    getAllMessages: make("get_messages"),
    deleteMessage: make("delete_message"),
    replyToMessage: make("reply_to_message"),
    getSettings: make("get_settings"),
    setSetting: make("set_settings"),

    radio: {
      getSeasons:       make("admin_get_radio_seasons"),
      createSeason:     make("admin_create_radio_season"),
      getSeason:        make("admin_get_radio_season"),
      updateSeason:     make("admin_update_radio_season"),
      deleteSeason:     make("admin_delete_radio_season"),
      getEpisodes:      make("admin_get_radio_episodes"),
      createEpisode:    make("admin_create_radio_episode"),
      getEpisode:       make("admin_get_radio_episode"),
      updateEpisode:    make("admin_update_radio_episode"),
      deleteEpisode:    make("admin_delete_radio_episode"),
      publishEpisode:   make("admin_publish_radio_episode"),
      unpublishEpisode: make("admin_unpublish_radio_episode"),
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

    events: {
      getGuide: make("admin_get_event_guide"),
      updateGuide: make("admin_update_event_guide"),
      toggleGuidePublished: make("admin_toggle_guide_published"),
      getLocation: make("admin_get_event_location"),
      updateLocation: make("admin_update_event_location"),
      toggleLocationPublished: make("admin_toggle_location_published"),
    },

    members: {
      provisionAll: make("provision_member_accounts"),
      provisionSingle: make("provision_single_member_account"),
    },
  },

  // Member (authenticated) endpoints
  member: {
    me: make("member_get_me"),
    events: make("member_get_events"),
    purchases: make("member_get_purchases"),
    ticket: make("member_get_ticket"),
    preferences: make("member_patch_preferences"),
    getEventLocation: make("member_get_event_location"),
  },
};
