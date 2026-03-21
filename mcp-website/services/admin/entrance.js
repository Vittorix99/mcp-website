import { safeFetch } from "@/lib/fetch";
import { endpoints } from "@/config/endpoints";

export async function generateScanToken(event_id) {
  return safeFetch(endpoints.admin.entrance.generateScanToken, "POST", { event_id });
}

export async function verifyScanToken(token) {
  return safeFetch(`${endpoints.admin.entrance.verifyScanToken}?token=${token}`, "GET");
}

export async function deactivateScanToken(token) {
  return safeFetch(endpoints.admin.entrance.deactivateScanToken, "POST", { token });
}
