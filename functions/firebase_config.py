import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_functions import options

# Inizializzazione Firebase
cred = credentials.Certificate("service_account.json")  # Path al file JSON
firebase_admin.initialize_app(cred, {
    'storageBucket': os.environ.get('STORAGE_BUCKET')
})

# Firestore
db = firestore.client()

# Controllo se è attivo l'emulatore Firestore
if os.environ.get("FIRESTORE_EMULATOR_HOST"):
    print("🔥 Firestore emulatore rilevato!")
else:
    print("⚠️ Nessuna emulazione Firestore, connessione a Firestore cloud.")

# Firebase Storage
bucket = storage.bucket()

# Opzioni CORS
cors = options.CorsOptions(
    cors_origins="*",
    cors_methods=["get", "post", "options"]
)

# Esportiamo le risorse
__all__ = ['db', 'bucket', 'cors']