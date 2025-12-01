import os
import firebase_admin
from firebase_admin import credentials, firestore
import random
import string

# Facoltativo: carica variabili da .env se usi un file .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Imposta variabili per l'emulatore. Se sono già definite, non vengono sovrascritte.
# FIRESTORE_EMULATOR_HOST indica al client dove gira l'emulatore (di default su localhost:8080).
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")
# GCLOUD_PROJECT è richiesto dal client Admin SDK quando si usa l'emulatore.
# Se è già definito (o se GOOGLE_CLOUD_PROJECT è definito), si usa quel valore,
# altrimenti si imposta un ID di progetto fittizio.
os.environ.setdefault(
    "GCLOUD_PROJECT",
    os.environ.get("GOOGLE_CLOUD_PROJECT", "demo-project")
)

# Inizializza Firebase solo una volta, senza specificare storageBucket
# per evitare di puntare allo Storage di produzione.
if not firebase_admin._apps:
    cred = credentials.Certificate("service_account.json")  # sostituisci con il tuo percorso
    firebase_admin.initialize_app(cred, {
        "projectId": os.environ["GCLOUD_PROJECT"]
    })

# Ottieni il client Firestore (connesso all'emulatore se le variabili sono presenti)
db = firestore.client()

def seed_participants(event_id: str, count: int, email: str) -> None:
    """
    Popola la sottocollezione participants_event con `count` partecipanti di debug.
    Distribuisce equamente maschi e femmine e li suddivide in quattro fasce di età.
    """
    participants_ref = (
        db.collection("participants")
          .document(event_id)
          .collection("participants_event")
    )

    # Distribuzione di genere (metà maschi, metà femmine)
    male_count = count // 2
    female_count = count - male_count

    # Fasce d’età: (min, max) — per esempio 18–20, 21–25, 26–30 e 31+ (fino a 65)
    age_bins = [
        (18, 20),
        (21, 25),
        (26, 30),
        (31, 65),
    ]
    num_bins = len(age_bins)

    # Ripartizione maschi/femmine per fascia d’età
    male_bin_counts = [male_count // num_bins] * num_bins
    for i in range(male_count % num_bins):
        male_bin_counts[i] += 1
    female_bin_counts = [female_count // num_bins] * num_bins
    for i in range(female_count % num_bins):
        female_bin_counts[i] += 1

    def random_birthdate(age: int) -> str:
        """Ritorna una data di nascita fittizia (1° gennaio dell’anno in cui si compie `age`)."""
        current_year = 2025  # puoi usare datetime.datetime.now().year se preferisci
        year = current_year - age
        return f"01-01-{year}"

    # Crea partecipanti maschi
    male_index = 0
    for bin_idx, (age_min, age_max) in enumerate(age_bins):
        for _ in range(male_bin_counts[bin_idx]):
            age = random.randint(age_min, age_max)
            purchase_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            doc_id = f"male-debug-{male_index}"
            participants_ref.document(doc_id).set({
                "name": f"TestM{male_index}",
                "surname": f"UserM{male_index}",
                "email": email,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "gender": "male",
                "birthdate": random_birthdate(age),
                "event_id": event_id,
                "location_sent": False,
                "membership_included": False,
                "phone": f"000000{male_index:04d}",
                "price": 0,
                "purchase_id": purchase_id,
                "ticket_sent": False,
                "ticket_pdf_url": "",
                "send_ticket_on_create":False
            })
            male_index += 1

    # Crea partecipanti femmine
    female_index = 0
    for bin_idx, (age_min, age_max) in enumerate(age_bins):
        for _ in range(female_bin_counts[bin_idx]):
            age = random.randint(age_min, age_max)
            purchase_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            doc_id = f"female-debug-{female_index}"
            participants_ref.document(doc_id).set({
                "name": f"TestF{female_index}",
                "surname": f"UserF{female_index}",
                "email": email,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "gender": "female",
                "birthdate": random_birthdate(age),
                "event_id": event_id,
                "location_sent": False,
                "membership_included": False,
                "phone": f"000000{female_index:04d}",
                "price": 0,
                "purchase_id": purchase_id,
                "ticket_sent": False,
                "ticket_pdf_url": "",
                "age": age,
                
            })
            female_index += 1

    print(f"Inseriti {count} partecipanti nell’evento {event_id} con email {email}.")

if __name__ == "__main__":
    # Esempio: popola 100 partecipanti nell’evento specificato usando l’emulatore Firestore
    seed_participants("EexnCTGLfmmPa968sHtJ", 100, "vittorio.digiorgio@hotmail.it")