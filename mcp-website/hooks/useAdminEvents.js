import { useState, useCallback, useEffect } from "react";
import {
  getAllEventsAdmin,
  createEvent as createEventService,
  updateEvent as updateEventService,
  deleteEvent as deleteEventService,
} from "@/services/admin/events";
import { uploadImageToStorage } from "@/config/firebaseStorage"
import { useError } from "@/contexts/errorContext";

export function useAdminEvents() {
  const { setError } = useError();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAllEventsAdmin();
      if (data?.error) {
        setError(data.error);
      } else {
        setEvents(data || []);
      }
    } catch (err) {
      console.error("Errore caricamento eventi:", err);
      setError("Impossibile caricare gli eventi.");
    } finally {
      setLoading(false);
    }
  }, [setError]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const prepareEventData = (eventData) => {
    const output = { ...eventData };

    if (eventData.date) {
      const [year, month, day] = eventData.date.split("-");
      output.date = `${day}-${month}-${year}`;
    }

    if (typeof eventData.lineup === "string") {
      output.lineup = eventData.lineup
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);
    }

    if (eventData.price !== undefined) {
      output.price = eventData.price !== "" ? parseFloat(eventData.price) : null;
    }

    if (eventData.membershipFee !== undefined) {
      output.membershipFee =
        eventData.membershipFee !== "" ? parseFloat(eventData.membershipFee) : null;
    }

    if (eventData.active !== undefined) {
      output.active = eventData.active;
    }

    return output;
  };

const maybeUploadImage = async (eventData) => {
  if (eventData.image instanceof File) {
    const originalName = eventData.image.name; // Esempio: "mcp_09.jpg"
    const baseName = originalName.replace(/\.[^/.]+$/, ""); // Rimuove estensione

    
    const filename = `${baseName}.jpg`;
    const folder = `events`;

    const url = await uploadImageToStorage(folder, filename, eventData.image);
    if (!url) throw new Error("Errore upload immagine");

    eventData.image = baseName; // ✅ Esempio: "mcp_09"
  }

  return eventData;
};

  const createEvent = useCallback(
    async (eventData) => {
      setLoading(true);
      try {
        const withImage = await maybeUploadImage({ ...eventData });
        const payload = prepareEventData(withImage);
        const res = await createEventService(payload);
        if (res?.error) {
          setError(res.error);
        } else {
          await loadEvents();
        }
      } catch (err) {
        console.error("Errore creazione evento:", err);
        setError("Errore durante la creazione dell’evento.");
      } finally {
        setLoading(false);
      }
    },
    [loadEvents, setError]
  );

  const updateEvent = useCallback(
    async (eventId, eventData) => {
      setLoading(true);
      try {
        const withImage = await maybeUploadImage({ ...eventData });
        const payload = prepareEventData(withImage);
        const res = await updateEventService(eventId, payload);
        if (res?.error) {
          setError(res.error);
        } else {
          // Aggiorna subito i campi critici (active/price) per avere feedback istantaneo
          setEvents((prev) =>
            prev.map((ev) => {
              if (ev.id !== eventId) return ev;
              const patch = {};
              if (Object.prototype.hasOwnProperty.call(payload, "active")) {
                patch.active = payload.active;
              }
              if (Object.prototype.hasOwnProperty.call(payload, "price")) {
                patch.price = payload.price;
              }
              if (Object.prototype.hasOwnProperty.call(payload, "fee")) {
                patch.fee = payload.fee;
              }
              if (Object.prototype.hasOwnProperty.call(payload, "purchaseMode")) {
                patch.purchaseMode = payload.purchaseMode;
              }
              return Object.keys(patch).length ? { ...ev, ...patch } : ev;
            })
          );
          await loadEvents();
        }
      } catch (err) {
        console.error("Errore aggiornamento evento:", err);
        setError("Errore durante l’aggiornamento dell’evento.");
      } finally {
        setLoading(false);
      }
    },
    [loadEvents, setError]
  );

  const deleteEvent = useCallback(
    async (eventId) => {
      setLoading(true);
      try {
        const res = await deleteEventService(eventId);
        if (res?.error) {
          setError(res.error);
        } else {
          await loadEvents();
        }
      } catch (err) {
        console.error("Errore eliminazione evento:", err);
        setError("Errore durante l’eliminazione dell’evento.");
      } finally {
        setLoading(false);
      }
    },
    [loadEvents, setError]
  );

  return {
    events,
    loading,
    refreshEvents: loadEvents,
    createEvent,
    updateEvent,
    deleteEvent,
  };
}
