/**
 * @typedef {Object} RadioSeason
 * @property {string} id
 * @property {string} name
 * @property {number} year
 * @property {string} createdAt
 * @property {string} updatedAt
 */

/**
 * @typedef {Object} RadioEpisode
 * @property {string} id
 * @property {string} soundcloudTrackId
 * @property {string} title
 * @property {string} soundcloudUrl
 * @property {string|null} soundcloudArtworkUrl
 * @property {string|null} soundcloudStreamUrl
 * @property {string|null} soundcloudWaveformUrl
 * @property {number} duration        - millisecondi
 * @property {string} access
 * @property {string} seasonId
 * @property {number} episodeNumber
 * @property {string|null} description
 * @property {string[]} artistIds
 * @property {string[]} videoUrls     - max 3
 * @property {string[]} genres        - da SoundCloud, read-only
 * @property {string|null} recordedAt
 * @property {string|null} publishedAt
 * @property {boolean} isPublished
 * @property {string} createdAt
 * @property {string} updatedAt
 */
