import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_functions import options

# Regione cloud
region = "us-central1"

# Inizializzazione Firebase solo se non già inizializzato
if not firebase_admin._apps:
    print("🔥 Inizializzazione Firebase...")
    print("🔥 Inizializzazione Firestore...")

    cred = credentials.Certificate("service_account.json")  # Path al file JSON
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.environ.get('STORAGE_BUCKET')
    })

    print("✅ Firebase inizializzato")
else:
    print("ℹ️ Firebase già inizializzato, uso istanza esistente")

# Firestore
db = firestore.client()

# Firebase Storage
bucket = storage.bucket()

# Controllo se è attivo l'emulatore Firestore
if os.environ.get("FIRESTORE_EMULATOR_HOST"):
    print("🔥 Firestore emulatore rilevato!")
else:
    print("⚠️ Nessuna emulazione Firestore, connessione a Firestore cloud.")

# Opzioni CORS per funzioni HTTP
cors = options.CorsOptions(
    cors_origins="*",
    cors_methods=["get", "post", "put", "delete", "options"]
)

# Esportiamo le risorse
__all__ = ['db', 'bucket', 'cors', 'region']