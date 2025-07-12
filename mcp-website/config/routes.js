/**
 * Application routes configuration
 */

export const routes = {
  // Public routes
  home: '/',

  events: {
    foto: {
      gallery: '/events-foto',
      details: (id) => `/events-foto/${id}`,
    },
    details: (id) => `/events/${id}`,
    allevents: '/events',
  },

  subscribe: '/subscribe',

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
    eventsPhotos:'/admin/events-photos',
    settings:'/admin/settings',

    
    newsletter: '/admin/newsletter',
    signupRequests: '/admin/signup-requests',
    messages: '/admin/messages',
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