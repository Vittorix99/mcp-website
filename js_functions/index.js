/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const functions = require("firebase-functions");
const next = require("next");
const path = require("path");
console.log("path", path.join(__dirname, ".next"));
//print tutti i file e cartelle presenti
const fs = require("fs");
fs.readdirSync(__dirname).forEach((file) => {
  console.log(file);
});


const app = next({
  dev: false,
  conf: { distDir: path.join(__dirname, ".next") }, // Correctly points to .next/
});

const handle = app.getRequestHandler();

exports.nextjsFunc = functions.https.onRequest(async (req, res) => {
  await app.prepare();
  return handle(req, res);
});
// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

// exports.helloWorld = onRequest((request, response) => {
//   logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });
