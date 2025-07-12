
import { getStorage, ref, getDownloadURL, listAll , uploadBytes, deleteObject} from "firebase/storage";
import { storageBucket } from "@/config/firebase";
export async function checkFolderExists(path) {
  try {
    const folderRef = ref(storageBucket, path)
    const result = await listAll(folderRef)
    return result.items.length > 0 || result.prefixes.length > 0
  } catch (error) {
    console.error("Error checking folder existence:", error)
    return false
  }
}

export const getImageUrl = async (folder, fileName) => {
  try {
    const fileRef = ref(storageBucket, `${folder}/${fileName}`);
    const url = await getDownloadURL(fileRef);
    return url;
  } catch (error) {
    //console.error("Error getting image URL:", error);
    return null;
  }
};
export const getImageUrls = async(folderPath)=>{
  try{
    const folderRef = ref(storageBucket, folderPath);
    const files = await listAll(folderRef);
    const urls = await Promise.all(files.items.map(async (fileRef)=>{
      return await getDownloadURL(fileRef);
    }));
    return urls;
  }catch(error){
    console.error("Error getting image URLs:", error);
    return [];
  }
}






/**
 * Carica un'immagine nel Firebase Storage.
 * @param {string} folderPath - Il percorso della cartella (es: "events/MioEvento").
 * @param {string} fileName - Il nome desiderato del file (es: "copertina.jpg").
 * @param {File} file - Il file immagine da caricare (di tipo File).
 * @returns {Promise<string|null>} - L'URL pubblico dell'immagine, oppure null in caso di errore.
 */
export async function uploadImageToStorage(folderPath, fileName, file) {
  try {
    const filePath = `${folderPath}/${fileName}`;
    const fileRef = ref(storageBucket, filePath);

    const snapshot = await uploadBytes(fileRef, file, {
      contentType: file.type,
    });

    const downloadURL = await getDownloadURL(snapshot.ref);
    return downloadURL;
  } catch (error) {
    console.error("❌ Errore durante upload dell'immagine:", error);
    return null;
  }
}
/**
 * Estrae il percorso interno di Firebase Storage da un URL pubblico.
 * @param {string} downloadUrl - L'URL generato da getDownloadURL().
 * @returns {string|null} - Il percorso da usare in `ref()`, oppure null se non valido.
 */
export function getStoragePathFromDownloadURL(downloadUrl) {
  try {
    const match = downloadUrl.match(/firebasestorage\.app\/([^?]+)/);
    if (!match) return null;

    const pathEncoded = match[1];
    return decodeURIComponent(pathEncoded);
  } catch (error) {
    console.error("❌ Errore estraendo il percorso da downloadURL:", error);
    return null;
  }
}

export async function listFolder(path) {
  const folderRef = ref(storageBucket, path);
  const res = await listAll(folderRef);
  return res;
}

export async function deleteFiles(refs) {
  await Promise.all(refs.map(r => deleteObject(r)));
}

export async function uploadCover(folderPath, coverFile) {
  const fileRef = ref(storageBucket, `${folderPath}/cover.jpg`);
  await uploadBytes(fileRef, coverFile, { contentType: coverFile.type });
  return getDownloadURL(fileRef);
}



/**
 * Scarica un file dal Firebase Storage usando URL autenticato.
 * @param {string} url - L'URL pubblico (non funzionante direttamente).
 */
export async function downloadStorageFile(url) {
  const storagePath = getStoragePathFromDownloadURL(url);
  if (!storagePath) {
    const msg = "⚠️ Impossibile estrarre il path dallo Storage URL";
    console.error(msg);
    throw new Error(msg);
  }

  try {
    const fileRef = ref(storageBucket, storagePath);
    const downloadUrl = await getDownloadURL(fileRef);

    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = storagePath.split("/").pop(); // nome file
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch (error) {
    console.error("❌ Errore durante il download autenticato:", error);
    throw error;
  }
}