import { safeFetch } from "@/lib/fetch";
import { endpoints } from "@/config/endpoints";

// CRUD & Azioni extra

export async function getMemberships(year) {
  const url = year
    ? `${endpoints.admin.getMemberships}?year=${encodeURIComponent(year)}`
    : endpoints.admin.getMemberships;
  return safeFetch(url, "GET");
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

export async function mergeMemberships(source_id, target_id) {
  return safeFetch(endpoints.admin.mergeMemberships, "POST", { source_id, target_id });
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
export async function setMembershipFee(membership_fee, year) {
  if (typeof membership_fee !== "number" || isNaN(membership_fee)) {
    console.error(" membership_fee non valido:", membership_fee);
    return { error: "Prezzo non valido" };
  }

  return safeFetch(endpoints.admin.setMembershipPrice, "POST", { membership_fee, year });
}
export async function getMembershipPrice(year) {
  const url = year ? `${endpoints.admin.getMembershipPrice}?year=${encodeURIComponent(year)}` : endpoints.admin.getMembershipPrice;
  return safeFetch(url, "GET");
}

export async function getMembershipsReport(event_id) {
  const endpointUrl = `${endpoints.admin.getMembershipsReport}?event_id=${event_id}`;
  return safeFetch(endpointUrl, "GET");
}

export async function getWalletModel() {
  return safeFetch(endpoints.admin.getWalletModel, "GET");
}

export async function setWalletModel(model_id) {
  return safeFetch(endpoints.admin.setWalletModel, "POST", { model_id });
}

export async function createWalletPass(membership_id) {
  return safeFetch(endpoints.admin.createWalletPass, "POST", { membership_id });
}

export async function invalidateWalletPass(membership_id) {
  return safeFetch(endpoints.admin.invalidateWalletPass, "POST", { membership_id });
}
