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


  error: {
    notAdmin: '/error/not-admin',
    generic: '/error',
  },

  // Admin routes
  admin: {
    dashboard: '/admin',
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
}

// Helper function to get URL with ID
export const getRoute = (route, id) => {
  if (typeof route === 'function') {
    return route(id)
  }
  return route
}
