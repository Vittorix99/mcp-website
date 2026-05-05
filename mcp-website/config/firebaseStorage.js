
import { getStorage, ref, getDownloadURL, listAll, list, uploadBytes, deleteObject } from "firebase/storage";
import { app, storageBucket } from "@/config/firebase";

const LIST_CACHE_TTL_MS = 5 * 60 * 1000
const LIST_CACHE_MAX = 50
const folderListCache = new Map()

const touchFolderCache = (key, items) => {
  const now = Date.now()
  if (folderListCache.has(key)) folderListCache.delete(key)
  folderListCache.set(key, { items, ts: now })
  if (folderListCache.size > LIST_CACHE_MAX) {
    const oldestKey = folderListCache.keys().next().value
    folderListCache.delete(oldestKey)
  }
}

const listFolderItemsCached = async (folderPath) => {
  const cached = folderListCache.get(folderPath)
  const now = Date.now()
  if (cached && now - cached.ts < LIST_CACHE_TTL_MS) {
    return cached.items
  }
  const folderRef = ref(storageBucket, folderPath)
  const res = await listAll(folderRef)
  const items = res.items || []
  touchFolderCache(folderPath, items)
  return items
}
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

export const getImageUrlsFromBucket = async (folderPath, bucketName) => {
  try {
    const bucket = bucketName ? getStorage(app, `gs://${bucketName}`) : storageBucket
    const folderRef = ref(bucket, folderPath)
    const files = await listAll(folderRef)
    const urls = await Promise.all(
      files.items.map(async (fileRef) => {
        return await getDownloadURL(fileRef)
      })
    )
    return urls
  } catch (error) {
    console.error("Error getting image URLs from bucket:", error)
    return []
  }
}
export const getPageImageUrls = async (folderPath, limit = 24, pageIndex = 0) => {
  try {
    const items = await listFolderItemsCached(folderPath)
    const filteredItems = items.filter((item) => item.name.toLowerCase() !== "cover.jpg")
    const start = pageIndex * limit
    const pageItems = filteredItems.slice(start, start + limit)
    const urls = await Promise.all(
      pageItems.map(async (fileRef) => {
        return await getDownloadURL(fileRef)
      })
    )
    return urls
  } catch (error) {
    console.error("Error getting paged image URLs:", error)
    return []
  }
}

export const getFolderPage = async (folderPath, limit = 24, pageIndex = 0) => {
  try {
    const items = await listFolderItemsCached(folderPath)
    const filteredItems = items.filter((item) => item.name.toLowerCase() !== "cover.jpg")
    const totalLength = filteredItems.length
    const start = pageIndex * limit
    const pageItems = filteredItems.slice(start, start + limit)
    const pageUrls = await Promise.all(
      pageItems.map(async (fileRef) => {
        return await getDownloadURL(fileRef)
      })
    )
    return { totalLength, pageUrls }
  } catch (error) {
    console.error("Error getting folder page:", error)
    return { totalLength: 0, pageUrls: [] }
  }
}

    


export const getFolderLength = async (folderPath) => {
  try {
    const items = await listFolderItemsCached(folderPath)
    return items.filter((item) => item.name.toLowerCase() !== "cover.jpg").length
  } catch (error) {
    console.error("Error getting folder length:", error)
    return 0
  }
}

export const getImageUrlsPage = async (folderPath, limit = 20, pageToken = undefined) => {
  try {
    const folderRef = ref(storageBucket, folderPath)
    const res = await list(folderRef, {
      maxResults: limit,
      pageToken,
    })
    const urls = await Promise.all(
      res.items.map(async (fileRef) => {
        return await getDownloadURL(fileRef)
      })
    )
    return urls
  } catch (error) {
    console.error("Error getting paged image URLs:", error)
    return []
  }
}

export const listImageNames = async (folderPath, options = {}) => {
  try {
    const excludeNames = (options.excludeNames || []).map((name) => name.toLowerCase())
    const items = await listFolderItemsCached(folderPath)
    return items
      .map((item) => item.name)
      .filter((name) => !excludeNames.includes(name.toLowerCase()))
  } catch (error) {
    console.error("Error listing image names:", error)
    return []
  }
}

export const getImageUrlsPageWithToken = async (
  folderPath,
  limit = 24,
  pageToken = undefined,
  options = {}
) => {
  try {
    const folderRef = ref(storageBucket, folderPath)
    const excludeNames = (options.excludeNames || []).map((name) => name.toLowerCase())

    let urls = []
    let token = pageToken
    let nextPageToken = null

    while (urls.length < limit) {
      const remaining = limit - urls.length
      const res = await list(folderRef, {
        maxResults: remaining,
        pageToken: token,
      })

      const filteredItems = excludeNames.length
        ? res.items.filter((item) => !excludeNames.includes(item.name.toLowerCase()))
        : res.items

      const batchUrls = await Promise.all(
        filteredItems.map(async (fileRef) => {
          return await getDownloadURL(fileRef)
        })
      )

      urls = urls.concat(batchUrls)
      token = res.nextPageToken
      nextPageToken = res.nextPageToken || null

      if (!token) break
    }

    return { urls, nextPageToken }
  } catch (error) {
    console.error("Error getting paged image URLs:", error)
    return { urls: [], nextPageToken: null }
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
      cacheControl: "public, max-age=31536000, immutable",
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
  await uploadBytes(fileRef, coverFile, {
    contentType: coverFile.type,
    cacheControl: "public, max-age=31536000, immutable",
  });
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
