"use client";

import { useState } from "react";
import { useAdminAlbums } from "@/hooks/useAdminAlbums";
import {
  Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, PlusCircle, Trash2, AlertTriangle, ImageIcon, Loader2 } from "lucide-react";
import {
  Select, SelectTrigger, SelectContent, SelectItem, SelectValue
} from "@/components/ui/select";
import { AlbumCard } from "@/components/admin/events-foto/AlbumCard";

export default function EventsAlbumsPage() {
  const {
    albums,
    events,
    loading,
    createAlbum,
    deleteAlbum,
    refresh, 
    updateAlbumCover
  } = useAdminAlbums();

  const [selectedEventId, setSelectedEventId] = useState("");
  const [newPhotoPath, setNewPhotoPath] = useState("");
  const [coverFile, setCoverFile] = useState(null);
  const [photoFiles, setPhotoFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleCreate = async () => {
    if (!selectedEventId || !newPhotoPath || !coverFile || photoFiles.length === 0) {
      alert("Completa tutti i campi: evento, cartella, copertina e foto da caricare.");
      return;
    }

    await createAlbum(
      selectedEventId,
      newPhotoPath,
      coverFile,
      photoFiles,
      setUploadProgress
    );

    setSelectedEventId("");
    setNewPhotoPath("");
    setCoverFile(null);
    setPhotoFiles([]);
    setUploadProgress(0);

    const coverInput = document.getElementById("cover-file-input");
    const photosInput = document.getElementById("photos-files-input");
    if (coverInput) coverInput.value = "";
    if (photosInput) photosInput.value = "";
  };

  const unlinkedEvents = events?.filter((ev) => !ev.photoPath && ev.title) || [];

  if (loading && albums.length === 0)
    return (
      <div className="text-center py-6 flex flex-col items-center gap-2 text-white">
        <Loader2 className="animate-spin h-6 w-6" />
        <span>Caricamento...</span>
      </div>
    );

  return (
    <div className="bg-black min-h-screen text-white">
      <main className="p-4 md:p-6 space-y-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-3xl md:text-4xl font-bold">Gestione Album Eventi</h1>
          <Button
            onClick={refresh}
            disabled={loading}
            variant="outline"
            className="bg-transparent border-zinc-600 hover:bg-zinc-800"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Aggiorna
          </Button>
        </div>

        <Card className="bg-zinc-900 border-zinc-700">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <PlusCircle className="mr-3 h-6 w-6 text-orange-500" />
              Crea Nuovo Album
            </CardTitle>
            <CardDescription>Associa un album a un evento esistente.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label htmlFor="event-select">1. Seleziona Evento</Label>
              {unlinkedEvents.length > 0 ? (
                <Select value={selectedEventId} onValueChange={setSelectedEventId} disabled={loading}>
                  <SelectTrigger id="event-select" className="w-full bg-zinc-800 border-zinc-600">
                    <SelectValue placeholder="Scegli un evento..." />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 text-white border-zinc-600">
                    {unlinkedEvents.map((ev) => (
                      <SelectItem key={ev.id} value={ev.id}>{ev.title}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div className="text-sm text-yellow-400 flex items-center p-3 bg-yellow-900/50 rounded-md border border-yellow-400/30 h-10">
                  <AlertTriangle className="h-4 w-4 mr-2 shrink-0" />
                  <span>Nessun evento disponibile.</span>
                </div>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="folder-name">2. Nome Cartella</Label>
              <Input
                id="folder-name"
                value={newPhotoPath}
                onChange={(e) => setNewPhotoPath(e.target.value.toLowerCase().replace(/[^a-z0-9_.-]/g, "_"))}
                placeholder="es: party_maggio_2025"
                className="bg-zinc-800 border-zinc-600"
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cover-file-input">3. Immagine di Copertina</Label>
              <Input
                id="cover-file-input"
                type="file"
                accept="image/jpeg, image/png"
                onChange={(e) => setCoverFile(e.target.files[0])}
                className="bg-zinc-800 border-zinc-600 file:cursor-pointer"
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="photos-files-input">4. Foto Evento (multiple)</Label>
              <Input
                id="photos-files-input"
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => setPhotoFiles(Array.from(e.target.files))}
                className="bg-zinc-800 border-zinc-600 file:cursor-pointer"
                disabled={loading}
              />
            </div>
          </CardContent>
          <CardFooter className="flex-col items-start gap-4 w-full">
            <Button
              onClick={handleCreate}
              disabled={loading || !selectedEventId || !newPhotoPath || !coverFile || photoFiles.length === 0}
              className="bg-orange-600 hover:bg-orange-700 text-white font-bold"
            >
              <PlusCircle className="mr-2 h-4 w-4" />
              Crea e Carica Album
            </Button>
            {uploadProgress > 0 && (
              <div className="w-full h-2 bg-zinc-700 rounded">
                <div
                  className="h-2 bg-orange-500 rounded"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
            <p className="text-sm text-zinc-400 flex items-center">
              <AlertTriangle className="h-4 w-4 mr-2 text-yellow-400 shrink-0" />
              Ricorda di includere una <strong>cover.jpg</strong> tra le foto, o caricala a parte sopra.
            </p>
          </CardFooter>
        </Card>

        <div>
          <h2 className="text-2xl font-bold mb-4">Album Esistenti</h2>
          {albums.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {albums.map((alb) => (
              <AlbumCard
                  key={alb.photoPath}
                  album={alb}
                  onDelete={deleteAlbum}
                  onUpdateCover={updateAlbumCover}
                  isDeleting={loading}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-16 text-zinc-500 bg-zinc-900 rounded-lg border border-dashed border-zinc-700">
              <p className="font-semibold">Nessun album trovato.</p>
              <p className="text-sm mt-1">Crea il tuo primo album usando il modulo sopra.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}