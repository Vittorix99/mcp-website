import { endpoints } from "@/config/endpoints"
import { safeFetch } from "@/lib/fetch"

export const getNewsletterSignups = (signupId = null) =>
  safeFetch(
    signupId
      ? `${endpoints.admin.newsletter.getSignups}?id=${signupId}`
      : endpoints.admin.newsletter.getSignups,
    "GET"
  )

export const getNewsletterConsents = () =>
  safeFetch(endpoints.admin.newsletter.getConsents, "GET")

export const updateNewsletterSignup = (signupId, data) =>
  safeFetch(endpoints.admin.newsletter.getSignups, "PUT", { id: signupId, ...data })

export const deleteNewsletterSignup = (signupId) =>
  safeFetch(`${endpoints.admin.newsletter.getSignups}?id=${signupId}`, "DELETE")
