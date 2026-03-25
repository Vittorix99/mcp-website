import { safeFetch } from "@/lib/fetch";
import { endpoints } from "@/config/endpoints";

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function generateScanToken(event_id) {
  return safeFetch(endpoints.admin.entrance.generateScanToken, "POST", { event_id });
}

export async function verifyScanToken(token) {
  return safeFetch(`${endpoints.admin.entrance.verifyScanToken}?token=${token}`, "GET");
}

export async function deactivateScanToken(token) {
  const maxAttempts = 3;
  let lastRes = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const res = await safeFetch(endpoints.admin.entrance.deactivateScanToken, "POST", { token });
    lastRes = res;

    if (!res?.error) {
      return res;
    }

    const isNetworkLikeError = (res?.status || 0) === 0;
    const isLastAttempt = attempt === maxAttempts;
    if (!isNetworkLikeError || isLastAttempt) {
      return res;
    }

    const backoffMs = 250 * Math.pow(2, attempt - 1);
    await wait(backoffMs);
  }

  return lastRes || { error: "Errore di rete o del server.", status: 0 };
}

export async function manualEntry(event_id, membership_id, entered) {
  return safeFetch(endpoints.admin.entrance.manualEntry, "POST", { event_id, membership_id, entered });
}
