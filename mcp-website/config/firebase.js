// firebase.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";
import { GoogleAuthProvider } from "firebase/auth";
import { getStorage, ref, getDownloadURL, listAll , uploadBytes, deleteObject} from "firebase/storage";
import { getAnalytics, isSupported } from "firebase/analytics";


const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
   measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID

};
import { signInWithEmailAndPassword, signOut } from "firebase/auth";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const functions = getFunctions(app);
 const storageBucket = getStorage(app);
let analytics = null;

if (typeof window !== "undefined") {
  console.log("[Firebase Analytics] Running in browser ✅");

  isSupported().then((supported) => {
    console.log(`[Firebase Analytics] Analytics supported: ${supported}`);

    if (supported) {
      analytics = getAnalytics(app);
      console.log("[Firebase Analytics] Analytics initialized 🎉", analytics);
    } else {
      console.warn("[Firebase Analytics] Analytics not supported on this browser ❌");
    }
  }).catch((err) => {
    console.error("[Firebase Analytics] Error while checking support or initializing:", err);
  });
} else {
  console.log("[Firebase Analytics] Skipping analytics init — running on server ❌");
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

// FUNZIONI PER IMMAGINI // 





const googleProvider = new GoogleAuthProvider();


export { app, auth, db, functions, googleProvider, storageBucket, analytics };