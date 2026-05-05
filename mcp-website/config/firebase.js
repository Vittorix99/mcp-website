// firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";
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
const authEmulatorHost = process.env.NEXT_PUBLIC_AUTH_EMULATOR_HOST;
const env = process.env.NEXT_PUBLIC_ENV || "local";
const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
if (typeof window !== "undefined") {
  console.log(`[MCP Frontend] Env: ${env} | Project: ${projectId || "unknown"}`);
}
if (typeof window !== "undefined" && authEmulatorHost && env !== "production") {
  connectAuthEmulator(auth, `http://${authEmulatorHost}`, { disableWarnings: true });
}
const db = getFirestore(app);
const functions = getFunctions(app);
 const storageBucket = getStorage(app);
let analytics = null;
const measurementId = process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID;
const analyticsFlag = process.env.NEXT_PUBLIC_ENABLE_ANALYTICS;
const shouldInitAnalytics =
  analyticsFlag === "true" || (analyticsFlag !== "false" && env === "production");

async function initAnalyticsIfAvailable() {
  if (typeof window === "undefined") {
    return;
  }

  if (!shouldInitAnalytics) {
    console.log("[Firebase Analytics] Disabled for this environment");
    return;
  }

  if (!measurementId) {
    console.warn("[Firebase Analytics] Missing measurement ID, skipping initialization");
    return;
  }

  if (!window.navigator.onLine) {
    console.warn("[Firebase Analytics] Browser offline, deferring initialization");
    window.addEventListener("online", () => {
      void initAnalyticsIfAvailable();
    }, { once: true });
    return;
  }

  try {
    const supported = await isSupported();
    if (!supported) {
      console.warn("[Firebase Analytics] Analytics not supported in this browser");
      return;
    }
    analytics = getAnalytics(app);
    console.log("[Firebase Analytics] Analytics initialized");
  } catch (err) {
    const code = err?.code || "";
    if (code === "installations/app-offline") {
      console.warn("[Firebase Analytics] Installations offline, analytics will retry on next load");
      return;
    }
    console.error("[Firebase Analytics] Initialization failed:", err);
  }
}

if (typeof window !== "undefined") {
  void initAnalyticsIfAvailable();
} else {
  console.log("[Firebase Analytics] Skipping analytics init on server");
}

export async function login(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;

    const token = await user.getIdToken();
    localStorage.setItem('token', token);

    return { user };
  } catch (error) {
    const code = error?.code;
    if (code === "auth/user-not-found" || code === "auth/wrong-password" || code === "auth/invalid-credential") {
      return { error: "Utente o password errati" };
    }
    console.error("Error logging in:", error);
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
