// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCgkhR5_WbAYh0gldnBBlS5RCq1355oHyM",
  authDomain: "mcp-website-2a1ad.firebaseapp.com",
  projectId: "mcp-website-2a1ad",
  storageBucket: "mcp-website-2a1ad.firebasestorage.app",
  messagingSenderId: "407185703168",
  appId: "1:407185703168:web:6c75a0d881c86078d6b3e5",
  measurementId: "G-GZGZYE7PPQ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);