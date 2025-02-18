// firebase.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";
import { GoogleAuthProvider } from "firebase/auth";
import { getStorage, ref, getDownloadURL, listAll } from "firebase/storage";
import { useRouter } from 'next/router'

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,

};
import { signInWithEmailAndPassword, signOut } from "firebase/auth";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const functions = getFunctions(app);
const storageBucket = getStorage(app);
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
    console.error("Error getting image URL:", error);
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

export async function login(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    const token = await user.getIdToken();

    
    localStorage.setItem('token', token);
    return user;
  } catch (error) {
    console.error('Error logging in:', error);
    throw error;
  }
}

export async function logout() {

  try {
    await signOut(auth);
    window.location.replace("/");

 
    localStorage.removeItem('token');

  } catch (error) {
    console.error('Error logging out:', error);
    throw error;
  }
}

export async function getToken() {
  const user = auth.currentUser;
  if (user) {
    return user.getIdToken();
  }
  return null;
}
export async function getIdTokenResult(){
  const user = auth.currentUser;
  if(user){
    return user.getIdTokenResult();
  }
  return null;
  

}



const googleProvider = new GoogleAuthProvider();


export { app, auth, db, functions, googleProvider, storageBucket };