"use client";

import { useState, useCallback, useEffect } from "react";
import { useError } from "@/contexts/errorContext";
import {
  getParticipantsByEvent,
  getParticipantById,
  createParticipant as createParticipantService,
  updateParticipant as updateParticipantService,
  deleteParticipant as deleteParticipantService,
  sendLocationToParticipant,
  sendLocationToAllParticipants,
  sendTicketToParticipant
} from "@/services/admin/participants"; // Assicurati di esportare queste funzioni

export function useAdminParticipants(eventId) {
  const { setError } = useError();
  const [participants, setParticipants] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadAll = useCallback(async () => {
    if (!eventId) return;
    setLoading(true);
    try {
      const res = await getParticipantsByEvent(eventId);
      if (res?.error) {
        setError(res.error);
        setParticipants([]);
      } else {
        // ordina per creation timestamp crescente
        const sorted = (res || []).sort((a, b) => {
          const ta = a.createdAt?.seconds || 0;
          const tb = b.createdAt?.seconds || 0;
          return ta - tb;
        });
        setParticipants(sorted.map(p => ({
          ...p,
          isMember: !!p.membership_included
        })));
      }
    } catch (e) {
      console.error("loadParticipants error", e);
      setError("Errore caricamento partecipanti.");
    } finally {
      setLoading(false);
    }
  }, [eventId, setError]);

  const loadOne = useCallback(async (id) => {
    setLoading(true);
    try {
      const res = await getParticipantById(id);
      if (res?.error) {
        setError(res.error);
        setSelected(null);
      } else {
        setSelected({ ...res, isMember: !!res.membership_included });
      }
    } catch (e) {
      console.error("loadParticipant error", e);
      setError("Errore caricamento partecipante.");
    } finally {
      setLoading(false);
    }
  }, [setError]);

const create = useCallback(async (data) => {
  setLoading(true);
  try {
    const payload = { ...data, event_id: eventId };
    const res = await createParticipantService(payload);
    if (res?.error) setError(res.error);
    else await loadAll();
  } catch (e) {
    console.error("createParticipant error", e);
    setError("Errore creazione partecipante.");
  } finally {
    setLoading(false);
  }
}, [eventId, loadAll, setError]);

const update = useCallback(async (id, data) => {
  setLoading(true);
  try {
    const payload = {
      ...data,
      event_id: eventId,
    };
    const res = await updateParticipantService(id, payload); // ✅ PASSA id come PRIMO ARG
    if (res?.error) setError(res.error);
    else await loadAll();
  } catch (e) {
    console.error("updateParticipant error", e);
    setError("Errore aggiornamento partecipante.");
  } finally {
    setLoading(false);
  }
}, [loadAll, eventId, setError]);

  const remove = useCallback(async (id) => {
    setLoading(true);
    try {
      const res = await deleteParticipantService(id, { event_id: eventId }); // ✅ Include event_id
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("deleteParticipant error", e);
      setError("Errore eliminazione partecipante.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError, eventId]);

  const sendLocation = useCallback(async (participantId, { address, link }) => {
    if (!eventId || !participantId) {
      setError("Missing eventId or participantId");
      return;
    }
    setLoading(true);
    try {
      const res = await sendLocationToParticipant({
        eventId,
        participantId,
        address,
        link,
      });
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("sendLocation error", e);
      setError("Errore invio location.");
    } finally {
      setLoading(false);
    }
  }, [eventId, loadAll, setError]);

  const sendLocationToAll = useCallback(async ({ address, link }) => {
    if (!eventId) {
      setError("Missing eventId");
      return;
    }
    setLoading(true);
    try {
      const res = await sendLocationToAllParticipants({
        eventId,
        address,
        link,
      });
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("sendLocationToAll error", e);
      setError("Errore invio location a tutti.");
    } finally {
      setLoading(false);
    }
  }, [eventId, loadAll, setError]);

const sendTicket = useCallback(async (participantId) => {
  setLoading(true);
  try {
    const res = await sendTicketToParticipant(participantId, eventId);
    if (res?.error) setError(res.error);
    else await loadAll();
  } catch (e) {
    console.error("sendTicket error", e);
    setError("Errore invio ticket.");
  } finally {
    setLoading(false);
  }
}, [eventId, loadAll, setError]);

  useEffect(() => { loadAll() }, [loadAll]);

  return {
    participants,
    selected,
    loading,
    loadAll,
    loadOne,
    create,
    update,
    remove,
    sendLocation,
    sendLocationToAll,
    sendTicket
  };
}