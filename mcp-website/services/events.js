import { safePublicFetch } from "@/lib/fetch"; // la versione senza token
import { endpoints } from "@/config/endpoints";

// Ritorna { success, data?, error? }
export async function getNextEvent() {
  const res = await safePublicFetch(endpoints.getNextEvent, "GET");

  if (!res.success || !res.data) {
    console.warn("getNextEvent: No data received or request failed");
    return { success: false, event: null };
  }

  try {
    const normalized = normalizeEvent(res.data, res.data.id);
    return { success: true, event: normalized };
  } catch (err) {
    console.error("getNextEvent: Error normalizing event", err);
    return { success: false, event: null };
  }
}

const DEFAULTS = {
  title: "",
  date: "",
  startTime: "",
  endTime: "",
  location: "",
  lineup: [],
  note: "",
  active: false,
  image: null,
  type: "standard",
  ticketUrl: null,
  price: null,
  membershipFee: null,
  fee:null,

  photoPath: null,
};

// Converte raw event, applica DEFAULTS e tipi corretti
const normalizeEvent = (raw, eventId) => {
  const ev = {
    id: raw.id ?? eventId,
    ...Object.fromEntries(
      Object.entries(DEFAULTS).map(([key, defaultVal]) => {
        let val = raw[key] ?? defaultVal;
        if (key === "lineup" && Array.isArray(val)) {
          val = val.filter(a => !!a?.trim());
        }
        if (typeof defaultVal === "boolean") val = Boolean(val);
        if (typeof defaultVal === "number" && val != null) val = Number(val);
        return [key, val];
      })
    ),
  };
  if (ev.paypalActive && !ev.paymentMethods.includes("paypal")) {
    ev.paymentMethods.push("paypal");
  }
  return ev;
};

export async function getEventById(eventId) {
  const url = `${endpoints.getEventById}?id=${encodeURIComponent(eventId)}`;
  const res = await safePublicFetch(url, "GET");
  if (!res.success) return { success: false, error: res.error };

  const raw = res.data;
  if (!raw) return { success: false, error: "Evento non trovato" };
  console.log(raw)
  const event = normalizeEvent(raw, eventId);
  console.log(event)
  return { success: true, event };
}

export async function getAllEvents() {
  const res = await safePublicFetch(endpoints.getAllEvents, "GET");
  if (!res.success) return { success: false, error: res.error };

  // endpoints.getAllEvents restituisce un array di raw events
  const evs = Array.isArray(res.data) ? res.data : [];
  const events = evs.map(raw => normalizeEvent(raw, raw.id));
  return { success: true, events };
}