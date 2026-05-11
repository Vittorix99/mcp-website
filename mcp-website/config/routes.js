/**
 * Application routes configuration
 */

export const routes = {
  // Public routes
  home: '/',


  events: {
    foto: {
      gallery: '/events-foto',
      details: (slug) => `/events-foto/${slug}`,
    },
    details: (slug) => `/events/${slug}`,
    allevents: '/events',
  },


  radio: '/radio',
  about: '/about',
  contact: '/contact',

  error: {
    notAdmin: '/error/not-admin',
    generic: '/error',
  },

  // Admin routes
  admin: {
    dashboard: '/admin',
    analytics: '/admin/analytics',
    events: '/admin/events',
    eventDetails: (id) => `/admin/events/${id}`,

    memberships: '/admin/memberships',
    membershipDetails: (id) => `/admin/memberships/${id}`,

    purchases: '/admin/purchases',
    purchasesDetails: (id) => `/admin/purchases/${id}`,
    eventsPhotos: '/admin/events-photos',
    settings: '/admin/settings',
    subscribers: '/admin/subscribers',
    campaigns: '/admin/campaigns',
    automations: '/admin/automations',
    signupRequests: '/admin/signup-requests',
    messages: '/admin/messages',

    radio: {
      index:          '/admin/radio',
      newSeason:      '/admin/radio/seasons/new',
      editSeason:     (id) => `/admin/radio/seasons/${id}/edit`,
      newEpisode:     '/admin/radio/episodes/new',
      editEpisode:    (id) => `/admin/radio/episodes/${id}/edit`,
    },

    sender: {
      campaigns: '/admin/sender/campaigns',
      campaignDetail: (id) => `/admin/sender/campaigns/${id}`,
      subscribers: '/admin/sender/subscribers',
      groups: '/admin/sender/groups',
      segments: '/admin/sender/segments',
      fields: '/admin/sender/fields',
      transactional: '/admin/sender/transactional',
      optinOptout: '/admin/sender/optin-optout',
    },
  },

  user: {
    profile: '/',
  },

  // Member auth & dashboard
  login: '/login',
  loginVerify: '/login/verify',
  dashboard: '/dashboard',

  // Event guide
  eventGuide: (slug) => `/events/${slug}/guide`,
}

// Helper function to get URL with ID
export const getRoute = (route, id) => {
  if (typeof route === 'function') {
    return route(id)
  }
  return route
}
