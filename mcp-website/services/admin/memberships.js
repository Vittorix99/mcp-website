import { safeFetch, safeFetchId } from "@/lib/fetch";
import { endpoints } from "@/config/endpoints";

// CRUD & Azioni extra

export async function getMemberships() {
  return safeFetch(endpoints.admin.getMemberships, "GET");
}

export async function getMembershipById(membership_id) {
  const endpointUrl = `${endpoints.admin.getMembershipById}?id=${membership_id}`;
  return safeFetch(endpointUrl, "GET");
}

export async function createMembership(data) {
  return safeFetch(endpoints.admin.createMembership, "POST", data);
}

export async function updateMembership(membership_id, data) {
  return safeFetch(endpoints.admin.updateMembership, "PUT", { membership_id, ...data });
}

export async function deleteMembership(membership_id) {
  return safeFetch(endpoints.admin.deleteMembership, "DELETE", { membership_id });
}

export async function sendMembershipCard({ membership_id }) {
  return safeFetch(endpoints.admin.sendMembershipCard, "POST", { membership_id });
}
//  Recupera tutti gli acquisti associati al membro
export async function getMembershipPurchases(membership_id) {
  const endpointUrl = `${endpoints.admin.getMembershipPurchases}?id=${membership_id}`;
  return safeFetch(endpointUrl, "GET");
}

export async function getMembershipEvents(membership_id) {
  const endpointUrl = `${endpoints.admin.getMembershipEvents}?id=${membership_id}`;
  return safeFetch(endpointUrl, "GET");
}
export async function setMembershipFee(membership_fee) {
  if (typeof membership_fee !== "number" || isNaN(membership_fee)) {
    console.error(" membership_fee non valido:", membership_fee);
    return { error: "Prezzo non valido" };
  }

  return safeFetch(endpoints.admin.setMembershipPrice, "POST", { membership_fee });
}
export async function getMembershipPrice() {
  return safeFetch(endpoints.admin.getMembershipPrice, "GET");
}
