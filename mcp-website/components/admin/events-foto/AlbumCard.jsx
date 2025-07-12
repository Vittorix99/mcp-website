import { useState,useEffect } from "react";
import { getImageUrl } from "@/config/firebaseStorage";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Trash2, ImageIcon, UploadCloud } from "lucide-react";

export function AlbumCard({ album, onDelete, isDeleting, onUpdateCover }) {
  const [coverUrl, setCoverUrl] = useState(null);
  const [loadingCover, setLoadingCover] = useState(true);
  const [newCover, setNewCover] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const loadCover = async () => {
      setLoadingCover(true);
      try {
        const url = await getImageUrl(`foto/${album.photoPath}`, "cover.jpg");
        if (isMounted) setCoverUrl(url);
      } catch {
        console.warn(`Nessuna cover trovata per: ${album.photoPath}`);
      } finally {
        if (isMounted) setLoadingCover(false);
      }
    };
    loadCover();
    return () => { isMounted = false; };
  }, [album.photoPath]);

  const handleUpdateCover = () => {
    if (!newCover) return;
    onUpdateCover(album.photoPath, newCover);
    setNewCover(null);
  };

  return (
    <div className="border border-zinc-700 rounded-lg bg-zinc-900 flex flex-col overflow-hidden">
      <div className="relative">
        {loadingCover ? (
          <Skeleton className="h-48 w-full" />
        ) : coverUrl ? (
          <img src={coverUrl} alt={`Cover ${album.photoPath}`} className="w-full h-48 object-cover" />
        ) : (
          <div className="w-full h-48 bg-zinc-800 flex flex-col items-center justify-center text-zinc-500">
            <ImageIcon className="w-12 h-12 mb-2" />
            <span>Nessuna cover</span>
          </div>
        )}
      </div>
      <div className="p-4 space-y-2">
        <h4 className="font-semibold text-lg truncate">{album.event?.title || "Album senza evento"}</h4>
        <p className="text-sm text-zinc-400">{album.photoPath}</p>
        <input
          type="file"
          accept="image/jpeg, image/png"
          onChange={(e) => setNewCover(e.target.files?.[0] || null)}
          className="text-sm"
        />
        <Button
          size="sm"
          onClick={handleUpdateCover}
          disabled={!newCover || isDeleting}
          className="bg-blue-600 hover:bg-blue-700 w-full"
        >
          <UploadCloud className="mr-2 h-4 w-4" />
          Cambia Copertina
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={() => onDelete(album.photoPath)}
          disabled={isDeleting}
          className="w-full"
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Elimina Album
        </Button>
      </div>
    </div>
  );
}