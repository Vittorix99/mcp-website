"use client";

import { useState, useCallback, useEffect } from "react";
import { useError } from "@/contexts/errorContext";
import {
  getAllPurchases,
  getPurchase,
  createPurchase as createPurchaseService,
  deletePurchase as deletePurchaseService
} from "@/services/admin/purchases";

export function useAdminPurchases() {
  const { setError } = useError();
  const [purchases, setPurchases] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getAllPurchases();
      if (res?.error) {
        setError(res.error);
        setPurchases([]);
      } else {
        setPurchases(res);
      }
    } catch (e) {
      console.error("loadAllPurchases error", e);
      setError("Errore caricamento acquisti.");
    } finally {
      setLoading(false);
    }
  }, [setError]);

  const loadOne = useCallback(async (purchaseId) => {
    if (!purchaseId) {
      console.warn("⚠️ purchaseId mancante");
      return;
    }
    setLoading(true);
    try {
      const res = await getPurchase(purchaseId);
      if (res?.error) {
        setError(res.error);
        setSelected(null);
      } else {
        setSelected(res);
      }
    } catch (e) {
      console.error("loadPurchase error", e);
      setError("Errore caricamento acquisto.");
    } finally {
      setLoading(false);
    }
  }, [setError]);

  const create = useCallback(async (data) => {
    setLoading(true);
    try {
      const res = await createPurchaseService(data);
      if (res?.error) setError(res.error);
      else await loadAll();
    } catch (e) {
      console.error("createPurchase error", e);
      setError("Errore creazione acquisto.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError]);

  const remove = useCallback(async (purchaseId) => {
    if (!purchaseId) return;
    setLoading(true);
    try {
      const res = await deletePurchaseService(purchaseId);
      if (res?.error) setError(res.error);
      else {
        // se stiamo visualizzando l'acquisto corrente, resetta
        if (selected?.id === purchaseId) setSelected(null);
        await loadAll();
      }
    } catch (e) {
      console.error("deletePurchase error", e);
      setError("Errore eliminazione acquisto.");
    } finally {
      setLoading(false);
    }
  }, [loadAll, setError, selected]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  return {
    purchases,
    selected,
    loading,
    loadAll,
    loadOne,
    create,
    remove,
  };
}