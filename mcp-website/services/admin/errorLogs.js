import { endpoints } from "@/config/endpoints"
import { safeFetch } from "@/lib/fetch"

const buildUrl = (params = {}) => {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return
    search.set(key, String(value))
  })
  const query = search.toString()
  return query ? `${endpoints.admin.errorLogs}?${query}` : endpoints.admin.errorLogs
}

export const listErrorLogs = (params = {}) =>
  safeFetch(buildUrl(params), "GET")

export const getErrorLog = (id) =>
  safeFetch(buildUrl({ id }), "GET")

export const createErrorLog = (payload) =>
  safeFetch(endpoints.admin.errorLogs, "POST", payload)

export const updateErrorLog = (id, payload) =>
  safeFetch(endpoints.admin.errorLogs, "PUT", { id, ...payload })

export const deleteErrorLog = (id) =>
  safeFetch(buildUrl({ id }), "DELETE")
