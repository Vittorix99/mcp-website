// Backend reads that a release build must be able to perform. An environment with no
// published radio episode is a valid state, so that endpoint may answer 404 (JSON body).
const REQUIRED_BACKEND_READS = [
  'get_all_events', 'get_next_event', 'get_membership_price_public',
  'get_published_radio_episodes', 'get_latest_radio_episode', 'get_radio_seasons',
]
const EMPTY_STATE_ENDPOINTS = new Set(['get_latest_radio_episode'])

function backendReadAcceptable(endpoint, response) {
  return response.ok || (EMPTY_STATE_ENDPOINTS.has(endpoint) && response.status === 404)
}

module.exports = {REQUIRED_BACKEND_READS, backendReadAcceptable}
