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

export const listMailerLiteSubscribers = (params = {}) =>
  safeFetch(buildUrl(endpoints.admin.mailerLite.subscribers, params), "GET")

export const createMailerLiteSubscriber = (payload) =>
  safeFetch(endpoints.admin.mailerLite.subscribers, "POST", payload)

export const updateMailerLiteSubscriber = (payload) =>
  safeFetch(endpoints.admin.mailerLite.subscribers, "PUT", payload)

export const deleteMailerLiteSubscriber = (subscriberId) =>
  safeFetch(endpoints.admin.mailerLite.subscribers, "DELETE", { id: subscriberId })

export const forgetMailerLiteSubscriber = (subscriberId) =>
  safeFetch(endpoints.admin.mailerLite.subscriberForget, "POST", { id: subscriberId })

export const listMailerLiteGroups = (params = {}) =>
  safeFetch(buildUrl(endpoints.admin.mailerLite.groups, params), "GET")

export const createMailerLiteGroup = (name) =>
  safeFetch(endpoints.admin.mailerLite.groups, "POST", { name })

export const updateMailerLiteGroup = (groupId, name) =>
  safeFetch(endpoints.admin.mailerLite.groups, "PUT", { id: groupId, name })

export const deleteMailerLiteGroup = (groupId) =>
  safeFetch(endpoints.admin.mailerLite.groups, "DELETE", { id: groupId })

export const listMailerLiteGroupSubscribers = (groupId, params = {}) =>
  safeFetch(
    buildUrl(endpoints.admin.mailerLite.groupSubscribers, { group_id: groupId, ...params }),
    "GET"
  )

export const assignSubscriberToGroup = (subscriberId, groupId) =>
  safeFetch(endpoints.admin.mailerLite.groupAssignSubscriber, "POST", {
    subscriber_id: subscriberId,
    group_id: groupId,
  })

export const unassignSubscriberFromGroup = (subscriberId, groupId) =>
  safeFetch(endpoints.admin.mailerLite.groupUnassignSubscriber, "DELETE", {
    subscriber_id: subscriberId,
    group_id: groupId,
  })

export const listMailerLiteFields = (params = {}) =>
  safeFetch(buildUrl(endpoints.admin.mailerLite.fields, params), "GET")

export const createMailerLiteField = (name, type) =>
  safeFetch(endpoints.admin.mailerLite.fields, "POST", { name, type })

export const updateMailerLiteField = (fieldId, name) =>
  safeFetch(endpoints.admin.mailerLite.fields, "PUT", { id: fieldId, name })

export const deleteMailerLiteField = (fieldId) =>
  safeFetch(endpoints.admin.mailerLite.fields, "DELETE", { id: fieldId })

export const listMailerLiteSegments = (params = {}) =>
  safeFetch(buildUrl(endpoints.admin.mailerLite.segments, params), "GET")

export const updateMailerLiteSegment = (segmentId, name) =>
  safeFetch(endpoints.admin.mailerLite.segments, "PUT", { id: segmentId, name })

export const deleteMailerLiteSegment = (segmentId) =>
  safeFetch(endpoints.admin.mailerLite.segments, "DELETE", { id: segmentId })
