import { endpoints } from "@/config/endpoints"
import { safeFetch } from "@/lib/fetch"

const buildUrl = (base, params = {}) => {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return
    if (typeof value === "object") {
      search.set(key, JSON.stringify(value))
      return
    }
    search.set(key, String(value))
  })
  const query = search.toString()
  return query ? `${base}?${query}` : base
}

// ---- Subscribers ----

export const listSenderSubscribers = (params = {}) =>
  safeFetch(buildUrl(endpoints.admin.sender.subscribers, params), "GET")

export const getSenderSubscriber = (email) =>
  safeFetch(buildUrl(endpoints.admin.sender.subscribers, { email }), "GET")

export const upsertSenderSubscriber = (payload) =>
  safeFetch(endpoints.admin.sender.subscribers, "POST", payload)

export const updateSenderSubscriber = (payload) =>
  safeFetch(endpoints.admin.sender.subscribers, "PUT", payload)

export const deleteSenderSubscriber = (email) =>
  safeFetch(buildUrl(endpoints.admin.sender.subscribers, { email }), "DELETE")

export const addSenderSubscriberToGroup = (email, groupId) =>
  safeFetch(endpoints.admin.sender.subscriberGroups, "POST", { email, group_id: groupId })

export const removeSenderSubscriberFromGroup = (email, groupId) =>
  safeFetch(buildUrl(endpoints.admin.sender.subscriberGroups, { email, group_id: groupId }), "DELETE")

export const getSenderSubscriberEvents = (emailOrId, actions = ["got", "opened", "clicked", "unsubscribed", "bounced"]) =>
  safeFetch(buildUrl(endpoints.admin.sender.subscriberEvents, { email: emailOrId, actions: JSON.stringify(actions) }), "GET")

// ---- Groups ----

export const listSenderGroups = () =>
  safeFetch(endpoints.admin.sender.groups, "GET")

export const createSenderGroup = (title) =>
  safeFetch(endpoints.admin.sender.groups, "POST", { title })

export const renameSenderGroup = (groupId, title) =>
  safeFetch(endpoints.admin.sender.groups, "PUT", { id: groupId, title })

export const deleteSenderGroup = (groupId) =>
  safeFetch(buildUrl(endpoints.admin.sender.groups, { id: groupId }), "DELETE")

export const listSenderGroupSubscribers = (groupId, params = {}) =>
  safeFetch(buildUrl(endpoints.admin.sender.groupSubscribers, { group_id: groupId, ...params }), "GET")

// ---- Campaigns ----

export const listSenderCampaigns = (params = {}) =>
  safeFetch(buildUrl(endpoints.admin.sender.campaigns, params), "GET")

export const getSenderCampaign = (campaignId) =>
  safeFetch(buildUrl(endpoints.admin.sender.campaigns, { id: campaignId }), "GET")

export const createSenderCampaign = (payload) =>
  safeFetch(endpoints.admin.sender.campaigns, "POST", payload)

export const updateSenderCampaign = (campaignId, payload) =>
  safeFetch(endpoints.admin.sender.campaigns, "PUT", { id: campaignId, ...payload })

export const deleteSenderCampaign = (campaignId) =>
  safeFetch(buildUrl(endpoints.admin.sender.campaigns, { id: campaignId }), "DELETE")

export const sendSenderCampaign = (campaignId) =>
  safeFetch(endpoints.admin.sender.campaignSend, "POST", { id: campaignId })

export const scheduleSenderCampaign = (campaignId, scheduledAt) =>
  safeFetch(endpoints.admin.sender.campaignSchedule, "POST", {
    id: campaignId,
    scheduled_at: scheduledAt,
  })

export const cancelSenderCampaignSchedule = (campaignId) =>
  safeFetch(buildUrl(endpoints.admin.sender.campaignSchedule, { id: campaignId }), "DELETE")

export const copySenderCampaign = (campaignId) =>
  safeFetch(endpoints.admin.sender.campaignCopy, "POST", { id: campaignId })

export const getSenderCampaignStats = (campaignId, type = "opens") =>
  safeFetch(buildUrl(endpoints.admin.sender.campaignStats, { id: campaignId, type }), "GET")

// ---- Fields ----

export const listSenderFields = () =>
  safeFetch(endpoints.admin.sender.fields, "GET")

export const createSenderField = ({ title, type }) =>
  safeFetch(endpoints.admin.sender.fields, "POST", { title, type })

export const deleteSenderField = (fieldId) =>
  safeFetch(buildUrl(endpoints.admin.sender.fields, { id: fieldId }), "DELETE")

// ---- Segments ----

export const listSenderSegments = () =>
  safeFetch(endpoints.admin.sender.segments, "GET")

export const getSenderSegment = (segmentId) =>
  safeFetch(buildUrl(endpoints.admin.sender.segments, { id: segmentId }), "GET")

export const deleteSenderSegment = (segmentId) =>
  safeFetch(buildUrl(endpoints.admin.sender.segments, { id: segmentId }), "DELETE")

export const listSenderSegmentSubscribers = (segmentId) =>
  safeFetch(buildUrl(endpoints.admin.sender.segmentSubscribers, { segment_id: segmentId }), "GET")

// ---- Transactional ----

export const listSenderTransactionalCampaigns = () =>
  safeFetch(endpoints.admin.sender.transactional, "GET")

export const createSenderTransactionalCampaign = (payload) =>
  safeFetch(endpoints.admin.sender.transactional, "POST", payload)

export const deleteSenderTransactionalCampaign = (campaignId) =>
  safeFetch(buildUrl(endpoints.admin.sender.transactional, { id: campaignId }), "DELETE")

export const sendSenderTransactionalCampaign = (campaignId, { to_email, to_name, variables }) =>
  safeFetch(endpoints.admin.sender.transactionalSend, "POST", {
    id: campaignId,
    to_email,
    to_name,
    variables,
  })
