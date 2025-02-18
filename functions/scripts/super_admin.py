import firebase_admin
from firebase_admin import credentials, firestore, auth
from getpass import getpass
import os
import sys
#Append the path to the directory where the firebase_config.py file is located
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
IS_EMULATOR = os.environ.get("FIRESTORE_EMULATOR_HOST") == 'true'
print("🔥 Firestore emulatore rilevato!" if IS_EMULATOR else "⚠️ Nessuna emulazione Firestore, connessione a Firestore cloud.")

cred = credentials.Certificate("service_account.json")  # Path al file JSON
firebase_admin.initialize_app(cred, {
    'storageBucket': os.environ.get('STORAGE_BUCKET')
})

# Firestore
db = firestore.client()


def create_super_admin():
    email = input("Inserisci l'email del super admin: ")
    password = getpass("Inserisci la password del super admin: ")
    confirm_password = getpass("Conferma la password del super admin: ")
    
    if password != confirm_password:
        print("Le password non corrispondono.")
        return
    
    try:
        user = auth.create_user(email=email, password=password, email_verified=True)
        auth.set_custom_user_claims(user.uid, {"admin":True, 
                                               "super_admin": True})
        db.collection("admin_users").document(user.uid).set({"email": email, 
                                                             'isSuperAdmin': True, 
                                                             'createdAt': firestore.SERVER_TIMESTAMP})
        print("Super admin creato con successo! UID: ", user.uid)
    except Exception as e:
        print("Errore durante la creazione del super admin: ", e)
        
              

    
if __name__ == "__main__":
    create_super_admin()
    
    