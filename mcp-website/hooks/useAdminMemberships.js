"use client";

import { useState, useCallback, useEffect } from "react";
import { useError } from "@/contexts/errorContext";
import {
  getMemberships,
  getMembershipById,
  getMembershipPurchases,
  getMembershipEvents,
  createMembership as createMembershipService,
  updateMembership as updateMembershipService,
  deleteMembership as deleteMembershipService,
  sendMembershipCard as sendMembershipCardService,
  getMembershipPrice,
  setMembershipFee
} from "@/services/admin/memberships";

export function useAdminMemberships() {
  const { setError } = useError();
  const [memberships, setMemberships] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [membershipPrice, setMembershipPrice] = useState(null); // { price, year }

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getMemberships();
      if (res?.error) {
        setError(res.error);
        setMemberships([]);
      } else {
        setMemberships(
          res.sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
        );
      }


    } catch (e) {
      console.error("loadMemberships error", e);
      setError("Errore caricamento membership.");
    } finally {
      setLoading(false);
    }
  }, [setError]);
  const loadOne = useCallback(async (membershipId) => {
  if (!membershipId) {
    console.warn("⚠️ ID membership mancante");
    return;
  }

  setLoading(true);

  try {
    const res = await getMembershipById(membershipId);

    if (res?.error) {
      setError(res.error);
      setSelected(null);
      return;
    }

    const [purchases, events] = await Promise.all([
      getMembershipPurchases(membershipId),
      getMembershipEvents(membershipId),
    ]);



    setSelected({
      ...res,
      purchases: purchases?.error ? [] : purchases,
      events: events?.error ? [] : events,
    });

  
  } catch (e) {
    setError("Errore caricamento membership.");
    setSelected(null);
  } finally {
    setLoading(false);
  }
}, [setError]);



  const create = useCallback(async (data) => {
    setLoading(true);
    try {
      const res = await createMembershipService(data);
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("createMembership error", e);
      setError("Errore creazione membership.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError]);

  const update = useCallback(async (membershipId, data) => {
    if (!membershipId) return;
    setLoading(true);
    try {
      const res = await updateMembershipService(membershipId, data);
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("updateMembership error", e);
      setError("Errore aggiornamento membership.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError]);

  const remove = useCallback(async (membershipId) => {
    if (!membershipId) return;
    setLoading(true);
    try {
      const res = await deleteMembershipService(membershipId);
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("deleteMembership error", e);
      setError("Errore eliminazione membership.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError]);

  const sendCard = useCallback(async (membershipId) => {
    if (!membershipId) {
      setError("Missing membership_id");
      return;
    }
    setLoading(true);
    try {
      const res = await sendMembershipCardService({ membership_id: membershipId });
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("sendCard error", e);
      setError("Errore invio tessera via email.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError]);

  const fetchMembershipPurchases = useCallback(async (membershipId) => {
    if (!membershipId) return [];
    try {
      const res = await getMembershipPurchases(membershipId);
      if (res?.error) {
        setError(res.error);
        return [];
      }
      return res;
    } catch (e) {
      console.error("getMembershipPurchases error", e);
      setError("Errore recupero acquisti.");
      return [];
    }
  }, [setError]);

  const fetchMembershipEvents = useCallback(async (membershipId) => {
    if (!membershipId) return [];
    try {
      const res = await getMembershipEvents(membershipId);
      if (res?.error) {
        setError(res.error);
        return [];
      }
      return res;
    } catch (e) {
      console.error("getMembershipEvents error", e);
      setError("Errore recupero eventi.");
      return [];
    }
  }, [setError]);

 


const getCurrentYearPrice = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getMembershipPrice();
      if (res?.error) {
        setError(res.error);
        return;
      }
      setMembershipPrice(res); // <--- IMPORTANTE: deve essere questo
    } catch (e) {
      setError("Errore nel recupero del prezzo.");
    } finally {
      setLoading(false);
    }
  }, [setError]);


  const setCurrentYearPrice = useCallback(async (price) => {
  if (typeof price !== "number" || isNaN(price)) {
    setError("⚠️ Prezzo non valido.");
    return;
  }


  setLoading(true);
  try {
    const res = await setMembershipFee(price);
    if (res?.error) {
      setError(res.error);
    } else {
      await loadAll();
      await getCurrentYearPrice(); // 🔁 Ricarica anche il prezzo
    }
  } catch (e) {
    console.error("❌ Errore durante il settaggio del prezzo:", e);
    setError("Errore aggiornamento prezzo.");
  } finally {
    setLoading(false);
  }
}, [loadAll, setError, getCurrentYearPrice]);






  

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  return {
    memberships,
    selected,
    loading,
    loadAll,
    loadOne,
    create,
    update,
    remove,
    sendCard,
    fetchMembershipPurchases,
    fetchMembershipEvents,
    setError,
    setCurrentYearPrice,
    getCurrentYearPrice,
    membershipPrice

  };
}