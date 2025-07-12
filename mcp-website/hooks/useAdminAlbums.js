"use client"
import { useState, useCallback, useEffect } from "react";
import { ref, listAll, deleteObject } from "firebase/storage";
import {
  uploadImageToStorage,
 
  checkFolderExists
} from "@/config/firebaseStorage";

import { storageBucket } from "@/config/firebase";

import {
  getAllEventsAdmin,
  updateEvent as updateEventService
} from "@/services/admin/events";
import { useError } from "@/contexts/errorContext";

const ROOT = "foto";

export function useAdminAlbums() {
  const { setError } = useError();

  const [events, setEvents] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAllEventsAdmin();
      console.log("[DEBUG] Eventi caricati:", data);
      if (data.error) {
        setError(data.error);
        return [];
      }
      setEvents(data);
      return data;
    } catch (err) {
      console.error("[Albums] loadEvents error:", err);
      setError("Errore caricamento eventi");
      return [];
    } finally {
      setLoading(false);
    }
  }, [setError]);

  const updateEvent = useCallback(async (eventId, payload) => {
    try {
      const res = await updateEventService(eventId, payload);
      if (res.error) {
        setError(res.error);
        return false;
      }
      return true;
    } catch (err) {
      console.error("[Albums] updateEvent error:", err);
      setError("Errore aggiornamento evento");
      return false;
    }
  }, [setError]);

  const loadAlbums = useCallback(async () => {
    setLoading(true);
    try {
      const evs = await loadEvents();
      console.log("[DEBUG] Eventi usati per loadAlbums:", evs.map(e => e.photoPath));

      const rootRef = ref(storageBucket, ROOT);
      const list = await listAll(rootRef);
      const paths = list.prefixes.map((p) => p.name);
      console.log("[DEBUG] Cartelle trovate in storage:", paths);

      const result = [];
      for (const photoPath of paths) {
        const folder = `${ROOT}/${photoPath}`;
        if (!await checkFolderExists(folder)) {
          console.warn(`[Albums] Skip folder non esistente: ${folder}`);
          continue;
        }

        const linked = evs.find((e) => e.photoPath === photoPath) || null;
        if (!linked) {
          console.warn(`[DEBUG] Nessun evento collegato per ${photoPath}`);
        } else {
          console.log(`[DEBUG] Evento collegato per ${photoPath}:`, linked.id);
        }

        result.push({ photoPath, folder, event: linked });
      }

      console.log("[DEBUG] Albums finali:", result);
      setAlbums(result);
    } catch (err) {
      console.error("[Albums] loadAlbums error:", err);
      setError("Errore caricamento album");
    } finally {
      setLoading(false);
    }
  }, [loadEvents, setError]);

  const createAlbum = useCallback(async (
    eventId,
    photoPath,
    coverFile,
    photoFiles = [],
    onProgress = (pct) => {}
  ) => {
    setLoading(true);
    try {
      // upload copertina
      await uploadImageToStorage(`${ROOT}/${photoPath}`, "cover.jpg", coverFile);

      // upload foto
      const total = photoFiles.length;
      let uploaded = 0;
      for (const file of photoFiles) {
        if (file.name.toLowerCase() === "cover.jpg") continue;
        await uploadImageToStorage(`${ROOT}/${photoPath}`, file.name, file);
        uploaded++;
        onProgress(Math.round((uploaded / total) * 100));
      }

      // collega evento
      const ok = await updateEvent(eventId, { photoPath });
      if (ok) await loadAlbums();
    } catch (err) {
      console.error("[Albums] createAlbum error:", err);
      setError("Errore creazione album");
    } finally {
      setLoading(false);
    }
  }, [updateEvent, loadAlbums, setError]);

  const deleteAlbum = useCallback(async (photoPath) => {
    setLoading(true);
    try {
      const folderRef = ref(storageBucket, `${ROOT}/${photoPath}`);
      const list = await listAll(folderRef);
      await Promise.all(list.items.map(i => deleteObject(i)));

      const linked = events.find((e) => e.photoPath === photoPath);
      if (linked) await updateEvent(linked.id, { photoPath: null });
      await loadAlbums();
    } catch (err) {
      console.error("[Albums] deleteAlbum error:", err);
      setError("Errore eliminazione album");
    } finally {
      setLoading(false);
    }
  }, [events, updateEvent, loadAlbums, setError]);

const updateAlbumCover = useCallback(
  async (photoPath, newCoverFile) => {
    setLoading(true);
    try {
      const coverRef = ref(storageBucket, `${ROOT}/${photoPath}/cover.jpg`);

      // 🔒 Prova a eliminare la cover, ma ignora l'errore se non esiste
      try {
        await deleteObject(coverRef);
      } catch (err) {
        if (err.code !== "storage/object-not-found") {
          throw err; // rilancia solo se è un errore diverso
        } else {
          console.warn(`[Albums] Nessuna cover da eliminare per: ${photoPath}`);
        }
      }

      await uploadImageToStorage(`${ROOT}/${photoPath}`, "cover.jpg", newCoverFile);
      await loadAlbums();
    } catch (err) {
      console.error("[Albums] updateAlbumCover error:", err);
      setError("Errore aggiornamento copertina");
    } finally {
      setLoading(false);
    }
  },
  [loadAlbums, setError]
);

  useEffect(() => {
    loadAlbums();
  }, [loadAlbums]);

  return {
    albums,
    events,
    loading,
    createAlbum,
    deleteAlbum,
    refresh: loadAlbums,
    loadEvents,
    loadAlbums,
    updateAlbumCover
  };
}