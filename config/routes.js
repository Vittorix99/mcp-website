/**
 * Application routes configuration
 */


export const routes = {
    // Public routes
    home: '/',

    
    events: {
      foto:{
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
      tickets: '/admin/tickets',
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
  
  // Example usage:
  // import { routes, getRoute } from '@/lib/routes'
  // 
  // // Get static route
  // const homePage = routes.home
  // const subscribePage = routes.subscribe
  // 
  // // Get dynamic route
  // const eventDetails = getRoute(routes.events.details, '123')
  // 
  // // Get admin route
  // const adminDashboard = routes.admin.dashboard
  // const adminEvents = routes.admin.events