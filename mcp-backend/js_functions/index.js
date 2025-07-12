const functions = require("firebase-functions");
const express = require("express");
const next = require("next");
const path = require("path");

const dev = false;

const nextApp = next({ 
  dev, 
  conf: { distDir: path.join(__dirname, ".next") } 
});

const handle = nextApp.getRequestHandler();
const app = express();

// Middleware di logging per debug
app.use((req, res, next) => {
  console.log("🔵 [Request Debug]");
  console.log("Method:", req.method);
  console.log("URL:", req.url);
  console.log("Headers:", JSON.stringify(req.headers, null, 2));
  console.log("Query Params:", req.query);
  console.log("Cookies:", req.headers.cookie || "None");
  console.log("----------------------------");
  next();
});

// Caching middleware
app.use((req, res, next) => {
  if (req.url.startsWith("/admin/")) {
    res.setHeader("Cache-Control", "no-store");
  } else {
    res.setHeader("Cache-Control", "public, max-age=300, s-maxage=300");
  }
  next();
});

// Forward requests to Next.js
app.get("/", async (req, res) => {
  await nextApp.prepare();
  return handle(req, res);
});

// Export the Firebase HTTPS Function
exports.app = functions.https.onRequest(app);