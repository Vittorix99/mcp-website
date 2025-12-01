"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useError } from "@/contexts/errorContext";
import {
  getParticipantsByEvent,
  getParticipantById,
  createParticipant as createParticipantService,
  updateParticipant as updateParticipantService,
  deleteParticipant as deleteParticipantService,
  sendLocationToParticipant,
  sendTicketToParticipant,
  startSendLocationJobService
} from "@/services/admin/participants"; // Assicurati di esportare queste funzioni
import { db } from "@/config/firebase"; 
import { doc, onSnapshot } from "firebase/firestore";

const DBG = "[useAdminParticipants]";

export function useAdminParticipants(eventId) {
  const { setError } = useError();
  const [participants, setParticipants] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState("idle");
  const [jobPercent, setJobPercent] = useState(0);
  const [jobSent, setJobSent] = useState(0);
  const [jobFailed, setJobFailed] = useState(0);
  const jobUnsubRef = useRef(null);

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
      setError("Errore eliminazione partecipante.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError, eventId]);

  const sendLocation = useCallback(async (participantId, { address, link }) => {
    console.debug(DBG, "sendLocation:start", { participantId, address, link });
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
      console.debug(DBG, "sendLocation:response", res);
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("sendLocation error", e);
      console.debug(DBG, "sendLocation:catch", e);
      setError("Errore invio location.");
    } finally {
      console.debug(DBG, "sendLocation:end");
      setLoading(false);
    }
  }, [eventId, loadAll, setError]);

  const sendLocationToAll = useCallback(async ({ address, link, message }) => {
    console.debug(DBG, "sendLocationToAll:start", { address, link, message, eventId });
    if (!eventId) {
      setError("Missing eventId");
      return;
    }
    try {
      const res = await startSendLocationJobService({ eventId, address, link, message });
      console.debug(DBG, "sendLocationToAll:jobCreated", res);
      if (res?.error) {
        setError(res.error);
        return;
      }
      setJobId(res.jobId);
      setJobStatus(res.status || "running");
      setJobPercent(0);
      setJobSent(0);
      setJobFailed(0);
  
      // Detach previous listener if any, then attach a fresh one
      try { if (jobUnsubRef.current) { jobUnsubRef.current(); jobUnsubRef.current = null; } } catch {}
      console.debug(DBG, "sendLocationToAll:listener:attach", { jobId: res.jobId });
      const jobDocRef = doc(db, "jobs", res.jobId);
      jobUnsubRef.current = onSnapshot(jobDocRef, (snapshot) => {
        const data = snapshot.data();
        console.debug(DBG, "sendLocationToAll:snapshot", data);
        if (!data) return;
        setJobStatus(data.status || "running");
        setJobPercent(data.percent || 0);
        setJobSent(data.sent || 0);
        setJobFailed(data.failed || 0);
  
        if (data.status === "completed" || data.status === "failed") {
          console.debug(DBG, "sendLocationToAll:completed", { status: data.status, sent: data.sent, failed: data.failed });
          const unsub = jobUnsubRef.current;
          jobUnsubRef.current = null;
          if (unsub) unsub();
          loadAll();
        }
      });
    } catch (e) {
      console.error("sendLocationToAll error", e);
      console.debug(DBG, "sendLocationToAll:catch", e);
      setError("Errore invio location a tutti.");
    }
  }, [eventId, loadAll, setError]);

const sendTicket = useCallback(async (participantId) => {
  setLoading(true);
  try {
    const res = await sendTicketToParticipant(participantId, eventId);
    if (res?.error) setError(res.error);
    else await loadAll();
  } catch (e) {
    setError("Errore invio ticket.");
  } finally {
    setLoading(false);
  }
}, [eventId, loadAll, setError]);

  useEffect(() => { 
    loadAll() 
  }, [loadAll]);

  useEffect(() => {
    return () => {
      try { if (jobUnsubRef.current) { jobUnsubRef.current(); jobUnsubRef.current = null; } } catch {}
    };
  }, [eventId]);

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
    sendTicket,
    jobId,
    jobStatus,
    jobPercent,
    jobSent,
    jobFailed
  };
}