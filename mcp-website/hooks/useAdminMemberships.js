"use client";

import { useState, useCallback, useEffect, useRef } from "react";
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
  setMembershipFee,
  getWalletModel,
  setWalletModel,
  createWalletPass as createWalletPassService,
  invalidateWalletPass as invalidateWalletPassService,
} from "@/services/admin/memberships";

const envMembershipPriceRaw =
  process.env.NEXT_PUBLIC_MEMBESHIP_PRICE ?? process.env.NEXT_MEMBESHIP_PRICE;
const parsedEnvMembershipPrice =
  typeof envMembershipPriceRaw === "string"
    ? Number.parseFloat(envMembershipPriceRaw)
    : NaN;
const hasEnvMembershipPrice =
  typeof envMembershipPriceRaw === "string" && !Number.isNaN(parsedEnvMembershipPrice);

const buildEnvMembershipPricePayload = (year) => ({
  price: parsedEnvMembershipPrice,
  year: (year || new Date().getFullYear()).toString(),
});

export function useAdminMemberships(options = {}) {
  const { autoLoadList = true } = options;
  const { setError } = useError();
  const [memberships, setMemberships] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [membershipPrice, setMembershipPrice] = useState(null); // { price, year }
  const [extrasLoading, setExtrasLoading] = useState(false);
  const [walletModelId, setWalletModelId] = useState(null);
  const loadOneReqRef = useRef(0);
  const loadAllInitializedRef = useRef(false);

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

    // token per evitare race conditions se l'utente cambia membership velocemente
    const reqId = ++loadOneReqRef.current;

    // Fase 1: carica dati base (con loading globale)
    setLoading(true);
    try {
      const res = await getMembershipById(membershipId);
      if (res?.error) {
        setError(res.error);
        setSelected(null);
        return;
      }

      // se nel frattempo è partito un altro loadOne, interrompi
      if (reqId !== loadOneReqRef.current) return;

      // Aggiorna subito la UI con i dati base
      setSelected({
        ...res,
        purchases: [],
        events: [],
      });
    } catch (e) {
      console.error("loadOne:getMembershipById error", e);
      setError("Errore caricamento membership.");
      setSelected(null);
      return; // stop qui se la base fallisce
    } finally {
      setLoading(false); // fine fase 1
    }

    // Fase 2: carica acquisti ed eventi in background (senza bloccare la UI)
    setExtrasLoading(true);
    try {
      const [purchases, events] = await Promise.all([
        getMembershipPurchases(membershipId),
        getMembershipEvents(membershipId),
      ]);

      // evita update se nel frattempo è stato lanciato un altro loadOne
      if (reqId !== loadOneReqRef.current) return;

      setSelected((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          purchases: purchases?.error ? [] : purchases,
          events: events?.error ? [] : events,
        };
      });
    } catch (e) {
      console.error("loadOne:extras error", e);
      // opzionale: potresti mostrare un toast non bloccante
    } finally {
      setExtrasLoading(false);
    }
  }, [setError]);



  const create = useCallback(async (data) => {
    setLoading(true);
    try {
      const payload = {
        ...data,
        send_card_on_create: data?.send_card_on_create === true,
      };
      const res = await createMembershipService(payload);
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

 


  const getMembershipPriceForYear = useCallback(async (year) => {
    if (hasEnvMembershipPrice) {
      const currentYear = new Date().getFullYear().toString();
      if (String(year) === currentYear) {
        setMembershipPrice(buildEnvMembershipPricePayload(year));
      } else {
        setMembershipPrice({ year: String(year), price: null });
      }
      return;
    }

    setLoading(true);
    try {
      const res = await getMembershipPrice(year);
      if (res?.error) {
        setError(res.error);
        return;
      }
      setMembershipPrice(res);
    } catch (e) {
      setError("Errore nel recupero del prezzo.");
    } finally {
      setLoading(false);
    }
  }, [setError, hasEnvMembershipPrice]);

  const setMembershipPriceForYear = useCallback(async (year, price) => {
    if (hasEnvMembershipPrice) {
      setError("Il prezzo è gestito dal file .env (NEXT_MEMBESHIP_PRICE). Aggiorna lì il valore.");
      return;
    }

    if (typeof price !== "number" || isNaN(price)) {
      setError("⚠️ Prezzo non valido.");
      return;
    }

    setLoading(true);
    try {
      const res = await setMembershipFee(price, year);
      if (res?.error) {
        setError(res.error);
      } else {
        //await loadAll();
        await getMembershipPriceForYear(year); // 🔁 Ricarica anche il prezzo
      }
    } catch (e) {
      console.error("❌ Errore durante il settaggio del prezzo:", e);
      setError("Errore aggiornamento prezzo.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError, getMembershipPriceForYear, hasEnvMembershipPrice]);






  

  const createWalletPass = useCallback(async (membershipId) => {
    if (!membershipId) { setError("Missing membership_id"); return null; }
    setLoading(true);
    try {
      const res = await createWalletPassService(membershipId);
      if (res?.error) { setError(res.error); return null; }
      setSelected((prev) => prev ? { ...prev, wallet_url: res.wallet_url, wallet_pass_id: res.wallet_pass_id } : prev);
      return res;
    } catch (e) {
      console.error("createWalletPass error", e);
      setError("Errore creazione wallet pass.");
      return null;
    } finally {
      setLoading(false);
    }
  }, [setError]);

  const invalidateWalletPass = useCallback(async (membershipId) => {
    if (!membershipId) { setError("Missing membership_id"); return; }
    setLoading(true);
    try {
      const res = await invalidateWalletPassService(membershipId);
      if (res?.error) setError(res.error);
      else {
        setSelected((prev) => prev ? { ...prev, wallet_url: null, wallet_pass_id: null } : prev);
        await loadAll();
      }
    } catch (e) {
      console.error("invalidateWalletPass error", e);
      setError("Errore invalidazione wallet pass.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError]);

  const fetchWalletModel = useCallback(async () => {
    try {
      const res = await getWalletModel();
      if (res?.error) {
        const message = String(res.error || "");
        const lower = message.toLowerCase();
        const missingConfig =
          lower.includes("internal server error") ||
          lower.includes("membership_settings/current_model") ||
          lower.includes("model_id");

        if (missingConfig) {
          setWalletModelId(null);
          return {
            ok: true,
            missing: true,
            message: "Modello Wallet Pass2U non configurato.",
          };
        }

        setError(res.error);
        return { ok: false, missing: false, message };
      }

      const modelId =
        typeof res?.model_id === "string" ? res.model_id.trim() : "";
      setWalletModelId(modelId || null);
      return {
        ok: true,
        missing: !modelId,
        message: modelId ? "" : "Modello Wallet Pass2U non configurato.",
      };
    } catch (e) {
      console.error("getWalletModel error", e);
      setError("Errore nel recupero del wallet model.");
      return {
        ok: false,
        missing: false,
        message: "Errore nel recupero del wallet model.",
      };
    }
  }, [setError]);

  const saveWalletModel = useCallback(async (model_id) => {
    if (!model_id?.trim()) { setError("Model ID non valido"); return false; }
    setLoading(true);
    try {
      const res = await setWalletModel(model_id.trim());
      if (res?.error) {
        setError(res.error);
        return false;
      }
      setWalletModelId(model_id.trim());
      return true;
    } catch (e) {
      console.error("setWalletModel error", e);
      setError("Errore aggiornamento wallet model.");
      return false;
    } finally {
      setLoading(false);
    }
  }, [setError]);

  const isMembershipPriceReadOnly = hasEnvMembershipPrice;

  useEffect(() => {
    if (!autoLoadList) return;
    if (loadAllInitializedRef.current) return;
    loadAllInitializedRef.current = true;
    loadAll();
  }, [loadAll, autoLoadList]);

  return {
    memberships,
    selected,
    loading,
    refresh: loadAll,
    loadAll,
    loadOne,
    create,
    update,
    remove,
    sendCard,
    fetchMembershipPurchases,
    fetchMembershipEvents,
    setError,
    setMembershipPriceForYear,
    getMembershipPriceForYear,
    extrasLoading,
    membershipPrice,
    isMembershipPriceReadOnly,
    walletModelId,
    fetchWalletModel,
    saveWalletModel,
    createWalletPass,
    invalidateWalletPass,
  };
}
