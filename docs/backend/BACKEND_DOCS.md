# MCP Backend — Documentazione Tecnica

> **Stack**: Python · Pydantic · Firebase Cloud Functions · Firestore · Firebase Admin SDK  
> **Regione**: `us-central1`  
> **Aggiornata**: Maggio 2026

---

## Indice

0. [Come Orientarsi Velocemente](#0-come-orientarsi-velocemente)
1. [Struttura del Progetto](#1-struttura-del-progetto)
2. [Entry Point e Inizializzazione](#2-entry-point-e-inizializzazione)
3. [Layer API](#3-layer-api)
   - [Endpoint Pubblici](#31-endpoint-pubblici)
   - [Endpoint Admin](#32-endpoint-admin)
   - [API Admin Sender.net](#33-api-admin-sendernet)
   - [Sync Automatico Sender.net](#34-sync-automatico-sendernet)
   - [Sistema Entrata (Entrance)](#35-sistema-entrata-entrance)
   - [API Area Soci (Member)](#36-api-area-soci-member)
4. [Layer Services](#4-layer-services)
5. [Layer Domain](#5-layer-domain)
6. [Models](#6-models)
7. [Repositories](#7-repositories)
8. [DTO (Data Transfer Objects)](#8-dto-data-transfer-objects)
9. [Triggers](#9-triggers)
10. [Configurazione](#10-configurazione)
11. [Autenticazione e Autorizzazione](#11-autenticazione-e-autorizzazione)
12. [Gestione Errori](#12-gestione-errori)
13. [Dipendenze Esterne](#13-dipendenze-esterne)
14. [Flussi Principali](#14-flussi-principali)
15. [Pattern Architetturali](#15-pattern-architetturali)

---

## 0. Come Orientarsi Velocemente

Questa codebase è leggibile se la si affronta nel verso giusto. Il backend non è organizzato per framework "magico", ma per layer abbastanza netti:

1. `main.py` espone le Cloud Functions importando i moduli endpoint e trigger.
2. `api/*` espone HTTP, applica auth/decorator e valida input con DTO Pydantic.
3. `dto/*` definisce contratti di request/response, tipizzati e validati.
4. `services/*` contiene business logic e orchestrazione.
5. `models/*` rappresenta i documenti di dominio persistiti.
6. `repositories/*` parla con Firestore.
7. `domain/*` contiene regole pure riusabili nei flussi più complessi.
8. `mappers/*` converte DTO <-> Domain Model <-> Response DTO.
9. `triggers/*` aggiunge side effect asincroni dopo la scrittura su Firestore.

### Regola architetturale corrente

Ogni nuovo flusso backend deve rispettare questo schema:

```text
Request JSON
  -> Pydantic Request DTO
  -> Service
  -> Domain Model
  -> Repository
  -> DB

DB
  -> Domain Model
  -> Pydantic Response DTO
  -> JSON Response
```

Questa regola serve a mantenere indipendenti i tre layer principali:

- **Presentation layer**: file in `api/`. Gestisce HTTP, auth, status code e validazione Pydantic.
- **Business layer**: file in `services/` e `domain/`. Contiene regole, conflitti, orchestrazione e side effect applicativi.
- **Data layer**: file in `repositories/`. Nasconde Firestore al resto del codice.

I DTO non devono contenere logica di business e non devono sapere come si scrive su Firestore. I model non devono validare request HTTP. I repository non devono conoscere Flask, request o response JSON.

### Percorso di lettura consigliato

Se prendi il progetto oggi, questo è l'ordine più utile:

1. `functions/main.py`
2. `functions/config/firebase_config.py` e `functions/config/environment.py`
3. `functions/models/` + `functions/dto/`
4. `functions/api/admin/participants_api.py`, `functions/api/admin/members_api.py`, `functions/api/public/event_payment_api.py`
5. `functions/services/events/participants_service.py`
6. `functions/services/memberships/memberships_service.py`
7. `functions/services/payments/event_payment_service.py`
8. `functions/triggers/registration_trigger.py`

### Lifecycle di una request

```text
HTTP request
  -> api/* handler
  -> decorator @public_endpoint / @admin_endpoint
  -> PydanticDTO.model_validate(...)
  -> service method
  -> mapper DTO -> Domain Model, quando serve creare/aggiornare dati
  -> repository read/write di Domain Model
  -> mapper Domain Model -> Response DTO
  -> response_dto.model_dump(...) / to_payload()
  -> eventuale trigger Firestore post-write
```

### Convenzioni che confondono se non le sai prima

- Il backend usa sia `snake_case` sia `camelCase`.
  - Nei payload HTTP in ingresso vengono accettate spesso entrambe.
  - Nei model Python i campi sono normalmente `snake_case`.
  - In Firestore alcuni campi storici restano `camelCase` (`membershipId`, `createdAt`, `newsletterConsent`).
- I repository devono tendere a restituire model di dominio, non DTO.
  - Se trovi repository che restituiscono dict/DTO, è codice da rifattorizzare progressivamente.
- Le conversioni tra DTO e model stanno in `mappers/`.
  - Evitare metodi come `dto.to_model()` o `ResponseDTO.from_model()` dentro i DTO.
  - La regola è: DTO = contratto dati, mapper = conversione, service = business logic.
- `main.py` non contiene logica applicativa.
  - Serve soprattutto a registrare funzioni Cloud importando i moduli giusti.
  - Se aggiungi un endpoint e non lo importi in `main.py`, Firebase non lo espone.
- I trigger fanno side effect importanti.
  - Ticket email, wallet pass, gender enrichment e sync Sender partono dopo la scrittura, non dentro ogni endpoint.
- `membership_included` sul partecipante non significa solo "tessera venduta in questo flusso".
  - In pratica viene usato anche come flag di "partecipante associato a una membership".
  - Se un partecipante viene collegato a un socio esistente, il campo può risultare `true` anche senza creazione/rinnovo membership nello stesso endpoint.

### Flussi da conoscere prima di toccare il codice

- Acquisto evento: `event_payment_api.py` -> `EventPaymentService` -> `ParticipantRules` -> `registration_trigger.py`
- Admin partecipanti: `participants_api.py` -> `ParticipantsService` -> `ParticipantRepository`
- Admin membership: `members_api.py` -> `MembershipsService` -> `registration_trigger.py`
- Entrance QR: `api/entrance/` -> `EntranceService` / `ParticipantRepository`

### Diagramma dati

La mappa UML aggiornata dei model e delle relazioni Firestore è in:

- [`docs/backend/DATA_MODEL_UML.md`](./DATA_MODEL_UML.md)
- [`docs/backend/DATA_MODEL_UML.png`](./DATA_MODEL_UML.png)

---

## 1. Struttura del Progetto

```
mcp-backend/functions/
├── api/
│   ├── public/                   # Endpoint senza autenticazione
│   ├── admin/                    # Endpoint riservati ad admin
│   │   └── sender/               # Proxy API Sender.net
│   ├── member/                   # Endpoint area soci (idToken membro)
│   ├── entrance/                 # Sistema scansione QR entrata eventi
│   └── decorators/               # Decoratori HTTP (@public_endpoint, @admin_endpoint, @member_endpoint)
├── config/
│   ├── firebase_config.py        # Inizializzazione Firebase
│   ├── environment.py            # Caricamento variabili d'ambiente
│   ├── external_services.py      # Chiavi e URL servizi esterni
│   └── location_config.py        # Parametri retry invio posizione
├── domain/
│   ├── event_rules.py            # Regole date/stato eventi
│   ├── membership_rules.py       # Regole di business iscrizioni
│   └── participant_rules.py      # Validazione partecipanti
├── dto/                          # Data Transfer Objects
├── errors/
│   └── service_errors.py         # Gerarchia eccezioni custom
├── interfaces/
│   ├── repositories.py           # Protocol per repositories
│   └── services.py               # Protocol per services
├── mappers/                      # Conversioni DTO <-> Domain Model <-> Response
├── models/                       # Documenti Firestore
├── repositories/                 # Accesso dati Firestore
├── services/
│   ├── core/                     # Auth, Stats, Settings, logging errori esterni
│   ├── communications/           # Mail, Newsletter, Messaggi
│   ├── events/                   # Gestione eventi e partecipanti
│   ├── memberships/              # Iscrizioni, merge, wallet pass
│   ├── payments/                 # PayPal, acquisti
│   ├── sender/                   # Sync con Sender.net
│   └── templates/                # Rendering template email/PDF
├── triggers/                     # Cloud Function triggers Firestore
├── scripts/                      # Script di migrazione/utility (non deployati)
│   └── migrate_locations.py      # Migra events.location → event_locations
├── tests/unit/                   # Suite test pytest
├── utils/                        # Funzioni di utilità
└── main.py                       # Entry point dell'applicazione
```

---

## 2. Entry Point e Inizializzazione

**File**: `functions/main.py`

### Sequenza di avvio

1. `load_environment()` — carica `.env` (prod) o `.env.integration` (test) tramite `python-dotenv`
2. Configurazione logging a livello `DEBUG`
3. `init_mail_service()` — inizializza il client MailerSend
4. Inizializzazione Firebase Admin SDK (`firebase_config.py`):
   - Ricerca credenziali service account in più percorsi
   - Fallback su Application Default Credentials
   - Creazione client Firestore (`db`) e bucket Storage (`bucket`)
5. Import e registrazione di tutti gli endpoint pubblici e admin
6. Registrazione dei Firestore triggers

### Nota pratica su `main.py`

- Firebase esporta come Cloud Functions tutti i simboli top-level importati nel modulo.
- Per questo `main.py` sembra soprattutto un grande file di import.
- Quando aggiungi un nuovo endpoint o trigger:
  1. definisci la funzione nel modulo corretto;
  2. importala in `main.py`;
  3. solo a quel punto verrà deployata.

### Variabili d'ambiente chiave

| Variabile | Valore tipico | Scopo |
|---|---|---|
| `MCP_ENV` | `prod` / `test` | Seleziona l'ambiente |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path file JSON | Credenziali service account |
| `FIRESTORE_EMULATOR_HOST` | `localhost:8080` | Emulatore locale |
| `STORAGE_BUCKET` | `my-project.appspot.com` | Bucket Cloud Storage |
| `GCLOUD_PROJECT` | ID progetto GCP | Project ID |

### Oggetti globali esposti da `firebase_config.py`

| Oggetto | Tipo | Utilizzo |
|---|---|---|
| `db` | `firestore.Client` | Tutte le operazioni Firestore |
| `bucket` | `storage.Bucket` | Upload/download file |
| `cors` | CORS config | Permette GET, POST, PUT, DELETE, OPTIONS |
| `region` | `str` | `"us-central1"` |

---

## 3. Layer API

Tutti gli endpoint sono Firebase Cloud Functions (`@https_fn.on_request`).

Gli endpoint non devono contenere business logic. Il loro compito è:

1. esporre la funzione HTTP tramite `@public_endpoint(...)` o `@admin_endpoint(...)`;
2. leggere `req.get_json()` o `req.args`;
3. validare con `PydanticDTO.model_validate(...)`;
4. chiamare un service;
5. serializzare un Response DTO con `model_dump(...)` o `to_payload()`;
6. tradurre eccezioni applicative in status code HTTP.

Esempio standard:

```python
@admin_endpoint(methods=("POST",))
def create_membership(req):
    try:
        dto = CreateMembershipRequestDTO.model_validate(req.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "Invalid request data", "details": exc.errors()}), 400

    try:
        response = memberships_service.create(dto, admin_uid=req.admin_token.get("uid"))
        return jsonify(response.to_payload()), 201
    except Exception as err:
        return _handle_service_error(err)
```

Nota: `@admin_endpoint` registra la Cloud Function, valida il metodo HTTP e applica `require_admin`. `@public_endpoint` registra la Cloud Function e valida solo il metodo HTTP.

### 3.1 Endpoint Pubblici

> Nessuna autenticazione richiesta.

#### Events — `api/public/events_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/get_all_events` | Lista tutti gli eventi pubblici. Query param: `view` (`card`, `gallery`, `ids`) |
| `GET` | `/get_next_event` | Prossimo evento imminente |
| `GET` | `/get_event_by_id` | Dettaglio evento. Query: `id` o `slug` |

#### Acquisto Biglietti — `api/public/event_payment_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/create_order_event` | Crea ordine PayPal. Decoratore: `@require_active_event`. Body: `PreOrderDTO` |
| `POST` | `/capture_order_event` | Cattura il pagamento. Body: `OrderCaptureDTO` con `orderId` |

#### Validazione Partecipanti — `api/public/events_tickets_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/check_participants` | Valida partecipanti prima dell'acquisto. Body: `{eventId, participants[]}` |

#### Form Contatti — `api/public/contact_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/contact_us` | Invio form di contatto. Body: `{name, email, phone, message, subject, send_copy}` |

#### Newsletter — `api/public/newsletter_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/newsletter_signup` | Iscrizione newsletter. Body: `{email, name}` |

#### Sender Webhook — `api/public/sender_webhook_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/sender_webhook` | Riceve eventi da Sender.net (unsubscribe, bounce, spam). Header: `X-Sender-Token` |

---

### 3.2 Endpoint Admin

> Tutti richiedono `Authorization: Bearer <id_token>` con claim `admin: true`.

#### Gestione Eventi — `api/admin/events_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/admin_create_event` | Crea nuovo evento |
| `PUT` | `/admin_update_event` | Aggiorna evento esistente |
| `DELETE` | `/admin_delete_event` | Elimina evento |
| `GET` | `/admin_get_all_events` | Lista tutti gli eventi con contatori partecipanti |
| `GET` | `/admin_get_event_by_id` | Dettaglio evento. Query: `id` o `slug` |

**Campi obbligatori per la creazione**: `title`, `date`, `startTime`, `locationHint`. (`location` rimosso — gestito via `event_locations`.)

#### Gestione Location Evento — `api/admin/location_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/admin_get_event_location` | Legge la location di un evento. Query: `event_id` |
| `PUT` | `/admin_update_event_location` | Aggiorna location. Body: `{event_id, label, address, maps_url, maps_embed_url, message}` |
| `PATCH` | `/admin_toggle_location_published` | Pubblica/nasconde la location. Body: `{event_id, published}` |

Note: quando `published=true` la location diventa visibile ai soci tramite `/member_get_event_location`. L'aggiornamento denormalizza `locationLabel` sull'evento padre.

#### Provisioning Account Soci — `api/admin/members_auth_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/provision_member_accounts` | Crea account Firebase Auth per tutti i soci senza `uid`. Batch da 50, pausa 1s tra batch. |
| `POST` | `/provision_single_member_account` | Crea account Firebase Auth per un singolo socio. Body: `{membership_id}` |

Note: usare questi endpoint per abilitare il login passwordless (magic link) per i soci già esistenti nel DB prima dell'introduzione del flusso di autenticazione.

#### Gestione Partecipanti — `api/admin/participants_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/get_participants_by_event` | Lista partecipanti di un evento |
| `POST` | `/get_participant` | Dettaglio singolo partecipante |
| `POST` | `/create_participant` | Crea partecipante manualmente |
| `PUT` | `/update_participant` | Aggiorna partecipante |
| `DELETE` | `/delete_participant` | Rimuove partecipante |
| `POST` | `/send_location` | Invia posizione a un partecipante |
| `POST` | `/send_location_to_all` | Invio asincrono posizione a tutti (202 Accepted) |
| `POST` | `/send_ticket` | Reinvia email biglietto |
| `POST` | `/send_omaggio_emails` | Invia email dedicate agli omaggi (`payment_method=omaggio`) |

#### Gestione Iscrizioni (Membership) — `api/admin/members_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/get_memberships` | Lista iscrizioni. Query opzionale: `year`; filtro basato su `membership_years[]` |
| `GET` | `/get_membership` | Dettaglio iscrizione. Query: `id` o `slug` |
| `POST` | `/create_membership` | Crea nuova iscrizione |
| `PUT` | `/update_membership` | Aggiorna iscrizione |
| `POST` | `/merge_memberships` | Unisce due profili duplicati. Body: `{source_id, target_id}` |
| `DELETE` | `/delete_membership` | Elimina iscrizione |
| `POST` | `/renew_membership` | Rinnova la membership per l'anno corrente |
| `POST` | `/send_membership_card` | Invia tessera associativa via email |
| `GET` | `/get_membership_purchases` | Lista acquisti del socio |
| `GET` | `/get_membership_events` | Lista eventi frequentati |
| `POST` | `/set_membership_price` | Imposta quota annuale |
| `GET` | `/get_membership_price` | Recupera quota annuale |
| `POST` | `/create_wallet_pass` | Genera Apple/Google Wallet pass |
| `POST` | `/invalidate_wallet_pass` | Revoca wallet pass |
| `GET` | `/get_wallet_model` | Template ID del wallet attuale |
| `POST` | `/set_wallet_model` | Imposta template wallet |
| `GET` | `/get_memberships_report` | Report presenze e ricavi per evento |

#### Gestione Acquisti — `api/admin/purchases_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/get_all_purchases` | Lista tutti gli acquisti |
| `GET` | `/get_purchase` | Dettaglio acquisto |
| `POST` | `/create_purchase` | Crea acquisto manuale |
| `DELETE` | `/delete_purchase` | Elimina acquisto |

#### Newsletter Admin — `api/admin/newsletter_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/admin_get_newsletter_signups` | Lista iscritti newsletter |
| `PUT` | `/admin_update_newsletter_signup` | Aggiorna iscrizione |
| `DELETE` | `/admin_delete_newsletter_signup` | Rimuove iscrizione |
| `GET` | `/admin_get_newsletter_consents` | Lista consensi GDPR |

#### Messaggi — `api/admin/messages_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/get_messages` | Lista messaggi dal form contatti |
| `DELETE` | `/delete_message` | Elimina messaggio |
| `POST` | `/reply_to_message` | Invia risposta via email |

#### Statistiche — `api/admin/stats_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/admin_get_general_stats` | Stats globali: `events_count`, `participants_count`, `memberships_count`, `revenue_total` |

#### Impostazioni — `api/admin/setting_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/get_settings` | Lista impostazioni (opz. `key` specifico) |
| `POST` | `/set_settings` | Crea o aggiorna impostazione. Body: `{key, value}` |

### 3.3 API Admin Sender.net

> `api/admin/sender/` — proxy verso le API Sender.net usato dall'admin per subscriber, gruppi, campagne e invii transazionali.

| Area | Endpoint disponibili |
|---|---|
| Subscribers | `admin_sender_subscribers`, `groups`, `events` |
| Gruppi | `admin_sender_groups`, `group_subscribers` |
| Campagne | `admin_sender_campaigns`, `send`, `schedule`, `copy`, `stats` |
| Campi | `admin_sender_fields` |
| Segmenti | `admin_sender_segments`, `segment_subscribers` |
| Transazionale | `admin_sender_transactional`, `transactional_send` |

---

### 3.4 Sync Automatico Sender.net

> `services/sender/sender_sync.py` — sincronizzazione automatica verso Sender a valle di trigger o signup pubblici.

Regole principali attuali:

- `sync_membership_to_sender()` -> gruppo `Memberships`
- `sync_participant_to_sender()` -> gruppo `Newsletter` e gruppo dinamico `Participant-{event_title}` se c'è consenso newsletter
- `sync_newsletter_signup_to_sender()` -> gruppo `Newsletter`
- `sender_webhook` -> riceve unsubscribe/bounce/spam e aggiorna Firestore

Tutte queste integrazioni sono best-effort: loggano e non bloccano il flusso principale.

---

### 3.5 Sistema Entrata (Entrance)

> `api/entrance/` — Gestione accessi agli eventi via QR code.

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/entrance_generate_scan_token` | Genera token QR per un evento. Body: `{event_id}` |
| `GET` | `/entrance_verify_scan_token` | Verifica validità token. Query: `token` |
| `POST` | `/entrance_deactivate_scan_token` | Revoca token. Body: `{token}` |
| `POST` | `/entrance_manual_entry` | Segna entrata/uscita manuale. Body: `{event_id, membership_id, entered}` |
| `POST` | `/entrance_validate` | Valida accesso da scansione QR. Body: `{membership_id, scan_token}` |

### 3.6 API Area Soci (Member)

> Tutti richiedono `Authorization: Bearer <id_token>` di un socio (Firebase Auth). Il decorator `@member_endpoint` verifica l'idToken e risolve la membership dalla email del token.

#### Profilo e Dashboard — `api/member/member_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/member_get_me` | Profilo socio: `name`, `subscription_valid`, `end_date`, `renewals`, `card_url`, `wallet_url`, `newsletter_consent`. |
| `GET` | `/member_get_events` | Lista eventi a cui il socio ha partecipato (da `attended_events[]`). |
| `GET` | `/member_get_purchases` | Lista acquisti del socio (da `purchases[]`), con `event_title` per acquisti evento. |
| `GET` | `/member_get_ticket` | Ticket del socio per un evento. Query: `event_id`. Ritorna `ticket_pdf_url` e `wallet_url`. |
| `PATCH` | `/member_patch_preferences` | Aggiorna `newsletter_consent`. Body: `{newsletter_consent}`. Sincronizza su Sender.net (best-effort). |

#### Location Evento — `api/member/location_api.py`

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/member_get_event_location` | Location di un evento. Query: `event_id`. Ritorna 404 se `published=false`. |

---

## 4. Layer Services

### Core Services

#### `AuthService` — `services/core/auth_service.py`
- `verify_admin_token(id_token)` — Valida token Firebase e controlla claim `admin`
- `require_admin(handler)` — Decoratore per endpoint admin
- `verify_admin_service(req)` — Verifica helper

#### `StatsService` — `services/core/stats_service.py`
- `get_general_stats()` — Aggrega statistiche da tutti i repository

#### `SettingsService` — `services/core/settings_service.py`
- `get_setting(key)` / `get_all_settings()` / `set_setting(key, value)`

#### `ErrorLogsService` — `services/core/error_logs_service.py`
- `log_external_error(service, error, details)` — Helper interno per loggare errori di servizi esterni.
- Non esiste piu una API admin dedicata alla lettura degli error log: per ora e un supporto operativo interno.

---

### Communication Services

#### `MailService` — `services/communications/mail_service.py`
- Astrae l'invio email tramite **MailerSend API**
- `send(EmailMessage)` — Invia email con allegati opzionali
- Supporta mittenti per categoria (es. `MAILERSEND_FROM_EMAIL_MEMBERSHIPS`)

#### `NewsletterService` — `services/communications/newsletter_service.py`
- `signup(data)` / `get_all()` / `get_all_consents()` / `update(id, data)` / `delete(id)`
- `add_participants(participants)` — Import bulk da evento

#### `MessagesService` — `services/communications/messages_service.py`
- `submit_contact_message(dto)` / `get_all()` / `delete_by_id(id)` / `reply(email, subject, body, message_id)`

---

### Event Services

#### `EventsService` — `services/events/events_service.py`
- CRUD completo: `create_event`, `update_event`, `delete_event`
- Query: `get_all_events`, `get_event_by_id`, `list_public_events`, `get_next_public_event`
- `get_event_participants_count(event_id)`

#### `ParticipantsService` — `services/events/participants_service.py`
- CRUD: `create`, `get_all`, `get_by_id`, `update`, `delete`
- `check_participants(event_id, participants)` — Validazione pre-acquisto
- `send_ticket(event_id, participant_id)` — Reinvia biglietto
- `send_omaggio_emails(event_id, entry_time, participant_id?, skip_already_sent?)` — Invio email dedicata agli omaggi

Comportamenti non banali di `create()`:

- Se arriva `membership_id`, il partecipante viene collegato esplicitamente a quella membership e il backend non prova a creare o rinnovare nulla.
- Se `membership_id` non arriva, il backend prova comunque a trovare una membership esistente via email o telefono.
- Se `membership_included=true` e trova una membership attiva, alza `ConflictError`.
- Se `membership_included=true` e trova una membership scaduta, la rinnova.
- Se `membership_included=true` e non trova nessuna membership, ne crea una nuova.
- Se `membership_included=false` ma trova una membership esistente via email/telefono, collega comunque il partecipante a quel socio.

Comportamenti non banali di `update()`:

- Se il payload contiene `membership_id`, questo valore viene trattato come override manuale.
- Se il payload non contiene `membership_id` ma cambia l'email, il backend ricalcola il collegamento membership in automatico.

#### `LocationService` — `services/events/location_service.py`
- `get_admin_location(dto)` — Legge la location da `event_locations` (per admin, senza controllo `published`)
- `get_member_location(event_id)` — Legge la location da `event_locations`; ritorna `NotFoundError` se `published=false`
- `update_location(dto)` — Aggiorna `event_locations/{event_id}` e denormalizza `locationLabel` su `events/{event_id}`
- `set_location_published(dto)` — Togola il flag `published` su `event_locations/{event_id}`
- `send_location(event_id, participant_id, link, message)` — Sincrono, invia la location a un partecipante; legge `label` e `address` da `event_locations`
- `start_send_location_job(event_id, link, message)` — Asincrono, tutti; carica `event_locations` una volta prima del loop

#### `TicketService` — `services/events/ticket_service.py`
- `generate_ticket_pdf()` — Genera PDF biglietto con `reportlab`/`weasyprint`
- `send_ticket_email()` — Invia via `MailService`

#### `DocumentsService` — `services/events/documents_service.py`
- `generate_membership_card()` — Genera PDF tessera associativa

---

### Membership Services

#### `MembershipsService` — `services/memberships/memberships_service.py`
- CRUD: `create`, `get_all`, `get_by_id`, `update`, `delete`
- `send_card(membership_id)` / `get_purchases(id)` / `get_events(id)`
- `set_membership_price(fee, year?)` / `get_membership_price(year?)`
- `create_wallet_pass(id)` / `invalidate_wallet_pass(id)`

#### `MergeService` — `services/memberships/merge_service.py`
- `merge(source_id, target_id)` — Trasferisce eventi, acquisti e rinnovi da `source` a `target`, poi elimina `source`

#### `Pass2UService` — `services/memberships/pass2u_service.py`
- Integrazione **Pass2U API** per generare Apple/Google Wallet pass
- Usa `PASS2U_API_KEY` e `PASS2U_BASE_URL`

#### `MembershipReportsService` — `services/memberships/membership_reports_service.py`
- `get_memberships_report(event_id)` — Report presenze e ricavi per evento

---

### Payment Services

#### `EventPaymentService` — `services/payments/event_payment_service.py`
- Integrazione **PayPal Server SDK** con OAuth2
- `create_order_event_service(PreOrderDTO, EventDTO?)` — Crea ordine PayPal, salva su Firestore
- `capture_order_event_service(OrderCaptureDTO)` — Cattura pagamento, crea partecipanti, aggiorna membership, invia biglietti

#### `PurchasesService` — `services/payments/purchases_service.py`
- `create` / `get_all` / `get_by_id` / `delete`

---

### Email Integration Services

#### `SenderSync` — `services/sender/sender_sync.py`
- `sync_newsletter_signup_to_sender()` — Sincronizza iscritto newsletter
- `sync_participant_to_sender()` — Sincronizza partecipante
- `sync_membership_to_sender()` — Sincronizza socio

---

## 5. Layer Domain

Regole di business pure, senza dipendenze I/O.

### `MembershipRules` — `domain/membership_rules.py`

| Funzione | Descrizione |
|---|---|
| `get_minor_validation_error(birthdate)` | Verifica che il socio sia maggiorenne (18+) |
| `get_missing_contact_validation_error(email, phone)` | Richiede almeno email o telefono |
| `resolve_membership_contact_conflict()` | Rileva duplicati email/telefono |
| `parse_membership_year()` | Estrae anno dal campo rinnovo |
| `build_renewal_record()` | Costruisce record rinnovo |
| `membership_years_from_renewals()` | Calcola anni attivi |
| `is_membership_renewable()` | Verifica se rinnovabile |
| `dedupe_renewals_by_year()` | Consolida rinnovi duplicati per anno |

### `ParticipantRules` — `domain/participant_rules.py`

`run_basic_checks(event_id, participants, event_data)` — Validazione completa pre-registrazione:

- **Age check**: 18+ obbligatorio, 21+ se `over21Only`
- **Gender check**: chiamata a `genderize.io` per verifica nome
- **Duplicate check**: email/telefono duplicati nel form o nel database
- **Membership check**: verifica stato iscrizione
- **Access restrictions**: eventi solo donne (`onlyFemales`), solo soci, ecc.

Restituisce `ParticipantCheckResult` con:
- `errors[]` — Problemi bloccanti
- `members[]` — Soci verificati
- `non_members[]` — Non soci
- `membership_docs` — Dati socio per email

---

## 6. Models

Schemi documenti Firestore, implementati come dataclass Python in `models/`.

I model rappresentano il dominio persistibile. Non validano request HTTP e non dipendono da Flask/Pydantic. La conversione da/verso Firestore resta tecnica (`to_firestore`, `from_firestore`), mentre la conversione da/verso DTO deve stare nei mapper.

La mappa visuale aggiornata è in [`DATA_MODEL_UML.md`](./DATA_MODEL_UML.md).

### `Event` — `models/event.py`

```
title, slug, date, startTime, endTime
locationHint, locationLabel, price, fee
maxParticipants, status, image, lineup, note
photoPath, type/purchaseMode, allowDuplicates
over21Only, onlyFemales, participantsCount, externalLink
createdAt, createdBy, updatedAt, updatedBy
```

Note: `location` field rimosso. `locationHint` è il teaser pubblico; `locationLabel` è il nome venue denormalizzato da `event_locations`.

### `EventLocation` — `models/event_location.py`

```
label, address, maps_url, maps_embed_url, message, published
```

Document id = event id. Gestito tramite `EventLocationRepository`. Letto da `LocationService` per l'invio email e dalle API area soci.

### `EventParticipant` — `models/event_participant.py`

```
event_id, name, surname, email, phone, birthdate
membershipId, membership_included
entered, entered_at
ticket_pdf_url, ticket_sent, send_ticket_on_create
location_sent, location_sent_at, location_job_id
payment_method, purchase_id, riduzione
newsletterConsent, gender, gender_probability
createdAt
```

### `Membership` — `models/membership.py`

```
name, surname, slug, email, phone, birthdate
start_date, end_date, subscription_valid
membership_type, purchase_id, purchases[]
attended_events[], renewals[], membership_years[]
membership_sent, card_url, card_storage_path
send_card_on_create, membership_fee
wallet_pass_id, wallet_url
```

### `Purchase` — `models/purchase.py`

```
payer_name, payer_surname, payer_email
amount_total, currency, paypal_fee, net_amount
transaction_id, order_id, status, timestamp
type, ref_id, payment_method, capture_status
```

### `EventPurchase` — `models/event_purchase.py`

```
Estende Purchase.
event_id, eventPurchaseType, participants_count, membership_ids[]
```

### `EventOrder` — `models/order.py`

```
orderId, orderStatus, purchase_type, cart, total
reference_id, eventId, participants[]
eventPrice, eventFee, membershipTargets[]
membershipFee, purchaseMode, membershipLookup
eventMeta, captured, payment_method, purchase_id
```

### `EntranceScan` — `models/entrance_scan.py`

```
scanned_at, scan_token, manual, operator
```

### `Job` — `models/job.py`

```
type, event_id, status, address, link, message
total, sent, failed, percent, created_at, error
```

### `Setting` — `models/settings.py`

```
key, value
```

### `Enums` — `models/enums.py`

| Enum | Valori |
|---|---|
| `EventStatus` | `coming_soon`, `active`, `sold_out`, `ended` |
| `EventPurchaseAccessType` | `PUBLIC`, `ONLY_ALREADY_REGISTERED_MEMBERS`, `ONLY_MEMBERS`, `ON_REQUEST` |
| `PaymentMethod` | `website`, `private_paypal`, `iban`, `cash`, `omaggio` |
| `PurchaseTypes` | `event`, `membership` |

---

## 7. Repositories

Accesso dati Firestore tramite classe base generica.

### `BaseRepository` — `repositories/base.py`

CRUD generico: `get`, `create`, `update`, `delete`, `stream`. Il repository converte solo tra `Domain Model` e payload Firestore.

Il repository non deve restituire response DTO e non deve conoscere request HTTP.

### `EventRepository` — `repositories/event_repository.py`

| Metodo | Descrizione |
|---|---|
| `stream_models()` | Itera tutti gli eventi |
| `get_model(event_id)` | Recupera modello evento |
| `get_model_by_slug(slug)` | Cerca per slug URL |
| `create_from_model(event, slug_seed)` | Genera slug e salva |
| `update_from_model(event_id, event)` | Aggiorna modello |
| `update_fields(event_id, payload)` | Aggiornamento parziale |

### `MembershipRepository` — `repositories/membership_repository.py`

| Metodo | Descrizione |
|---|---|
| `get_all()` / `get(id)` | Lettura |
| `find_by_email(email)` / `find_by_phone(phone)` | Lookup per contatto |
| `create_from_model(membership)` | Crea e ritorna ID |
| `append_purchase(id, purchase_id)` | Collega acquisto |
| `add_attended_event(id, event_id)` | Registra presenza |
| `add_renewal(id, renewal_dict)` | Registra rinnovo annuale |
| `find_by_year(year)` | Query per anno rinnovo |

### `ParticipantRepository` — `repositories/participant_repository.py`

| Metodo | Descrizione |
|---|---|
| `list(event_id)` / `get(event_id, participant_id)` | Lettura |
| `create` / `update` / `delete` | Scrittura |
| `count(event_id)` | Conteggio registrati |
| `any_with_contacts(event_id, emails, phones)` | Verifica duplicati |
| `set_membership` / `clear_membership_reference` / `update_membership_reference` | Gestione link membership |

### `PurchaseRepository` — `repositories/purchase_repository.py`

| Metodo | Descrizione |
|---|---|
| `create_from_model(purchase)` | Crea e ritorna ID |
| `stream_models()` / `get_model(id)` | Lettura |
| `get_last_by_timestamp()` | Acquisto più recente |
| `list_models_by_ref_id(event_id)` | Acquisti per evento |

### `NewsletterRepository` — `repositories/newsletter_repository.py`

| Metodo | Descrizione |
|---|---|
| `get_all_signups()` / `get_signup(id)` | Lettura |
| `create_signup(email, name)` | Nuovo iscritto |
| `delete_signup(id)` / `unsubscribe_by_email(email)` | Disiscrizione |
| `get_all_consents()` | Lista consensi |

---

## 8. DTO (Data Transfer Objects)

Strutture dati per request/response con validazione Pydantic.

Regola corrente:

```text
Request JSON -> Pydantic Request DTO -> Service
Service -> Domain Model -> Mapper -> Pydantic Response DTO -> JSON
```

I DTO devono:

- validare tipi, campi obbligatori, alias `camelCase`/`snake_case` e normalizzazioni semplici;
- rifiutare campi inattesi con `extra="forbid"` quando possibile;
- usare `model_validate(...)` per input e `model_dump(...)` per output;
- restare privi di logica di business;
- non accedere a repository, Firestore, Flask o servizi esterni.

I DTO non devono:

- decidere se una membership è rinnovabile;
- sapere come si crea un model Firestore;
- chiamare repository;
- contenere metodi `to_model()` o `from_model()` per logica di mapping strutturale.

Le conversioni stanno in `mappers/`.

### Request DTO principali

| File | Scopo |
|---|---|
| `dto/event_api.py` | Request/response per eventi admin e pubblici |
| `dto/membership_api.py` | CRUD membership, renewal, wallet, prezzo annuale |
| `dto/participant_api.py` | Partecipanti admin, update, location, omaggi |
| `dto/preorder.py` | Preordine evento e capture PayPal |
| `dto/purchase.py` | Acquisti admin/manuali |
| `dto/message_api.py` | Messaggi contatto e risposte |
| `dto/newsletter_api.py` | Newsletter pubblica/admin |
| `dto/setting_api.py` | Settings key/value |
| `dto/entrance_api.py` | Token scan, manual entry, validate entrance |

### Mapper principali

| File | Scopo |
|---|---|
| `mappers/event_mappers.py` | Event DTO -> `Event`, `Event` -> response admin/pubblica |
| `mappers/membership_mappers.py` | Membership DTO -> `Membership`, renewal response |
| `mappers/participant_mappers.py` | Participant DTO -> `EventParticipant` |
| `mappers/payment_mappers.py` | Preorder/capture DTO -> `EventOrder` / payment payload |
| `mappers/purchase_mappers.py` | Purchase DTO -> `Purchase` / `EventPurchase` |
| `mappers/message_mappers.py` | Contact/reply DTO -> `ContactMessage` |
| `mappers/newsletter_mappers.py` | Newsletter DTO -> newsletter model |

### Esempio

```python
dto = CreateEventRequestDTO.model_validate(req.get_json(silent=True) or {})
event = create_event_dto_to_model(dto, admin_uid)
created = events_service.create_event(event)
response = event_to_admin_response(created)
return jsonify(response.model_dump(by_alias=True)), 201
```

### Alias e compatibilità payload

Quando serve accettare sia `camelCase` sia `snake_case`, usare Pydantic:

```python
membership_id: str = Field(
    validation_alias=AliasChoices("membership_id", "membershipId", "id")
)
```

La compatibilità di naming è accettabile ai bordi HTTP. Non deve propagarsi nel service layer: dopo la validazione il service riceve attributi Python puliti e tipizzati.

### Response DTO

Le response DTO sono Pydantic e possono avere `to_payload()` solo come wrapper di serializzazione, non come punto di business logic.

Esempio accettabile:

```python
def to_payload(self) -> dict:
    return self.model_dump(by_alias=True, exclude_none=True)
```

---

## 9. Triggers

Funzioni Firebase reattive a eventi Firestore.

### `registration_trigger.py`

- **`on_participant_created`** (Firestore `on_document_created`) — Al completamento acquisto biglietto:
  - Aggiunge partecipante agli eventi frequentati del socio
  - Sincronizza su Sender.net

- **`on_membership_created`** (Firestore `on_document_created`) — Alla creazione nuovo socio:
  - Invia email di benvenuto con tessera
  - Crea Wallet pass (Pass2U)
  - Sincronizza su Sender.net

### `jobs_trigger.py`

- **`process_send_location_job`** (Firestore listener su collezione `jobs`) — Processa invio posizione massivo:
  - Monitora documenti con `status = "pending"`
  - Chiama `LocationService.send_location()` per ogni partecipante
  - Aggiorna stato job a `"completed"` o `"failed"`

### `new_year_trigger.py`

- **`invalidate_memberships_new_year`** (Scheduled — 1° Gennaio):
  - Trova soci con rinnovo nell'anno precedente
  - Marca `subscription_valid = False` per i non rinnovati
  - Invia email notifica rinnovo
  - Archivia Wallet pass scaduti

---

## 10. Configurazione

### `config/environment.py`

Risolve il file `.env` corretto in base a `MCP_ENV`:
- `"prod"` → `.env`
- qualsiasi altro valore → `.env.integration`

### `config/external_services.py`

```python
# Email
MAILERSEND_API_KEY, MAILERSEND_BASE_URL
MAILERLITE_API_KEY, MAILERLITE_BASE_URL

# Marketing
SENDER_API_KEY, SENDER_BASE_URL
SENDER_WEBHOOK_SECRET
SENDER_GROUP_NEWSLETTER, SENDER_GROUP_MEMBERS, SENDER_GROUP_TICKET_BUYERS

# Wallet
PASS2U_API_KEY, PASS2U_BASE_URL

# API Esterne
GENDER_API_URL = "https://api.genderize.io"
GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
```

### `config/location_config.py`

```python
LOCATION_MIN_INTERVAL = 0.8   # Secondi minimi tra notifiche
LOCATION_MAX_RETRIES = 5      # Tentativi massimi
LOCATION_BASE_DELAY = 1.0     # Ritardo iniziale retry
LOCATION_MAX_DELAY = 30.0     # Ritardo massimo retry
```

---

## 11. Autenticazione e Autorizzazione

### Flusso Admin Auth

```
Client → Authorization: Bearer <id_token>
         │
         ▼
auth.verify_id_token(id_token)   [Firebase Admin SDK]
         │
         ▼
decoded_token["admin"] == True ?
         │
    Sì ──┘  ──── No → 401 Unauthorized
         │
         ▼
req.admin_token = decoded_token
         │
         ▼
Esegui handler
```

**Implementato in**: `services/core/auth_service.py` + decoratore `@require_admin`

**Accesso frontend**: `LoginModal` con `signInWithEmailAndPassword` (email + password). Pulsante "Staff" visibile ma discreto nel nav.

### Flusso Member Auth — Passwordless (Magic Link)

```
Socio → /login (inserisce email)
  │
  ▼
Firebase: sendSignInLinkToEmail()
  │ email con magic link
  ▼
Socio clicca link → /login/verify
  │
  ▼
Firebase: signInWithEmailLink()  → idToken
  │
  ▼
Set cookie mcp_auth_token = idToken
  │
  ▼
Redirect /dashboard
  │ (middleware.js verifica cookie)
  ▼
Chiamate API: memberFetch() usa auth.currentUser.getIdToken()
  │
  ▼
@member_endpoint: verifica idToken → lookup memberships.where(email=token.email)
```

**Implementato in**: `api/decorators/__init__.py` (`@member_endpoint`), `mcp-website/app/login/`, `mcp-website/middleware.js`.

**Prerequisito**: abilitare "Email link (passwordless sign-in)" in Firebase Console → Authentication → Sign-in methods (secondo toggle sotto Email/Password).

### Claim Token

| Claim | Tipo | Obbligatorio |
|---|---|---|
| `uid` | string | Sì |
| `admin` | boolean | Solo endpoint admin |
| `email` | string | Sì per endpoint member |

### Entrance Scanning Auth

- Token QR generato dall'admin per ogni evento
- Token monouso / temporaneo salvato su Firestore
- Verificato a ogni scansione con `entrance_verify_scan_token`
- Revocabile tramite `entrance_deactivate_scan_token`

### Sender Webhook Auth

- Header `X-Sender-Token` o `X-Webhook-Token` verificato contro `SENDER_WEBHOOK_SECRET`
- Se il segreto non è configurato, il webhook viene accettato (fail-open)

---

## 12. Gestione Errori

### Gerarchia Eccezioni — `errors/service_errors.py`

```
ServiceError (base)
├── ValidationError    → HTTP 400
├── NotFoundError      → HTTP 404
├── ConflictError      → HTTP 409
├── ForbiddenError     → HTTP 403
└── ExternalServiceError → HTTP 502
```

### Pattern risposta errore

```python
if isinstance(err, ValidationError):
    return jsonify({"error": str(err)}), 400
if isinstance(err, NotFoundError):
    return jsonify({"error": str(err)}), 404
# ...
return jsonify({"error": "Internal server error"}), 500
```

### Error Logging

Gli errori dei servizi esterni possono essere loggati internamente:

```python
log_external_error(service="PayPal", error=e, details={...})
```

Non esiste al momento una API admin pubblicata per consultarli. La scelta attuale è mantenere il logging come supporto operativo interno e introdurre strumenti migliori in futuro.

---

## 13. Dipendenze Esterne

### `requirements.txt`

| Pacchetto | Versione | Scopo |
|---|---|---|
| `firebase-admin` | 6.2.0 | Firebase SDK |
| `firebase-functions` | 0.4.3 | Cloud Functions |
| `google-auth` | 2.22.0 | Auth Google |
| `pydantic[email]` | >=2.0,<3.0 | DTO request/response e validazione payload |
| `mailersend` | latest | Invio email transazionale |
| `requests` | 2.32.3 | Client HTTP generico |
| `paypal-server-sdk` | 0.6.1 | Pagamenti PayPal |
| `reportlab` | 4.0.4 | Generazione PDF |
| `pillow` | 10.3.0 | Elaborazione immagini |
| `weasyprint` | latest | HTML → PDF |
| `python-dotenv` | latest | Variabili d'ambiente |

### API/Servizi Esterni

| Servizio | Scopo |
|---|---|
| **Firebase / Firestore** | Database primario e autenticazione |
| **PayPal Server SDK** | Elaborazione pagamenti eventi |
| **MailerSend** | Invio email transazionali (biglietti, tessere) |
| **Sender.net** | Email marketing, subscriber management |
| **Pass2U** | Generazione Apple / Google Wallet pass |
| **Genderize.io** | Predizione genere da nome (validazione partecipanti) |

---

## 14. Flussi Principali

### Acquisto Biglietto Evento

```
POST /create_order_event
  │
  ├─ @require_active_event → verifica evento attivo
  ├─ PreOrderDTO.model_validate()
  ├─ ParticipantRules.run_basic_checks()
  │    ├─ Età (18+, 21+ se richiesto)
  │    ├─ Genere → genderize.io
  │    ├─ Duplicati (email/tel nel form e nel DB)
  │    └─ Stato membership
  ├─ EventPaymentService.create_order_event_service()
  │    ├─ mapper PreOrderDTO -> EventOrder
  │    ├─ PayPal OrdersController.create()
  │    └─ OrderRepository salva EventOrder su Firestore
  └─ → { orderId }

POST /capture_order_event
  │
  ├─ OrderCaptureDTO.model_validate()
  ├─ EventPaymentService.capture_order_event_service()
  │    ├─ ensure_event_is_active() anche al momento capture
  │    ├─ PayPal OrdersController.capture()
  │    ├─ mapper capture/order -> EventPurchase
  │    ├─ PurchaseRepository crea acquisto
  │    ├─ ParticipantsService crea EventParticipant
  │    ├─ Aggiorna Membership (rinnovi, acquisti)
  │    └─ Invia email biglietto via MailService
  ├─ Trigger: on_participant_created
  │    └─ Sync Sender.net
  └─ → { message }
```

### Creazione Iscrizione (Membership)

```
POST /create_membership
  │
  ├─ @admin_endpoint(methods=("POST",))
  ├─ CreateMembershipRequestDTO.model_validate()
  ├─ MembershipsService.create()
  │    ├─ membership_mappers.create_membership_dto_to_model()
  │    ├─ MembershipRules: età 18+, contatto obbligatorio, conflitti
  │    └─ MembershipRepository.create_from_model() → Firestore
  ├─ Trigger: on_membership_created
  │    ├─ Email benvenuto + tessera
  │    ├─ Pass2U: crea Wallet pass
  │    └─ Sync Sender.net
  └─ → { message, membershipId }
```

### Rinnovo Membership

```text
POST /renew_membership
  │
  ├─ @admin_endpoint(methods=("POST",))
  ├─ RenewMembershipRequestDTO.model_validate()
  ├─ MembershipsService.renew()
  │    ├─ MembershipRepository.get_model()
  │    ├─ MembershipRules verifica anno corrente e rinnovabilità
  │    ├─ crea renewal record per l'anno corrente
  │    ├─ aggiorna membership_years aggiungendo l'anno corrente
  │    ├─ aggiorna start_date/end_date della validità corrente
  │    ├─ collega eventuale purchase_id
  │    └─ aggiorna/revoca wallet pass se richiesto dal flusso
  └─ → MembershipActionResponseDTO
```

Regola dati del rinnovo:

- `membership_years[]` è la fonte canonica degli anni in cui una persona è stata socia.
- `start_date` e `end_date` descrivono solo la validità corrente della tessera.
- `renewals[]` conserva lo storico leggibile dei rinnovi.
- Un socio che ha `membership_years = [2025, 2026]` deve comparire sia nella tabella 2025 sia nella tabella 2026.

### Creazione Partecipante Admin

```text
POST /create_participant
  │
  ├─ @admin_endpoint(methods=("POST",))
  ├─ CreateParticipantRequestDTO.model_validate()
  ├─ ParticipantsService.create()
  │    ├─ participant_mappers.create_participant_dto_to_model()
  │    ├─ valida età, email, payment_method
  │    ├─ se membership_id presente:
  │    │    └─ collega il partecipante alla membership esplicita
  │    ├─ altrimenti prova lookup membership via email / telefono
  │    ├─ se membership_included=true:
  │    │    ├─ membership attiva -> ConflictError
  │    │    ├─ membership scaduta -> rinnovo
  │    │    └─ nessuna membership -> creazione nuova membership
  │    ├─ crea EventParticipant
  │    └─ se membership_id esiste -> add_attended_event()
  ├─ Trigger: on_participant_created
  │    ├─ gender enrichment
  │    ├─ eventuale invio ticket
  │    └─ eventuale sync Sender se newsletter_consent=true
  └─ → { message, id }
```

### Invio Posizione a Tutti i Partecipanti

```
POST /send_location_to_all   (202 Accepted)
  │
  ├─ LocationService.start_send_location_job()
  │    ├─ Legge event_locations/{eventId} (label, address, maps_url)
  │    └─ Crea Job document su Firestore (status: queued)
  └─ → { jobId, total }

Trigger: process_send_location_job
  │
  ├─ Legge event_locations/{eventId} (label, address — caricato una volta)
  ├─ Legge partecipanti evento (location_sent=false)
  ├─ Per ogni partecipante:
  │    └─ LocationService._send_one() con retry (label + address + link + message in email)
  ├─ Aggiorna job progress
  └─ Job status: "completed" | "failed"
```

### Webhook Sender.net (Unsubscribe)

```
POST /sender_webhook
  │
  ├─ Verifica X-Sender-Token header
  ├─ Parsa evento: subscriber.unsubscribed | .bounced | .spam_reported
  ├─ NewsletterRepository.unsubscribe_by_email()
  │    ├─ Marca newsletter_signups inactive
  │    └─ Marca newsletter_consents inactive
  └─ → 200 (sempre)
```

### Rinnovo Annuale Membership (Trigger schedulato)

```
Trigger: invalidate_memberships_new_year   (1° Gennaio)
  │
  ├─ MembershipRepository.find_by_year(anno_precedente)
  ├─ Per ogni membership:
  │    ├─ Se membership_years non contiene anno corrente → subscription_valid = False
  │    ├─ Invia email notifica rinnovo
  │    └─ Archivia Wallet pass
  └─ Salva aggiornamenti su Firestore
```

---

## 15. Pattern Architetturali

| Pattern | Implementazione |
|---|---|
| **Repository Pattern** | `BaseRepository` + protocol interfaces in `interfaces/repositories.py` |
| **Service Layer** | Business logic in `*Service`, mai negli API handler |
| **Pydantic DTO Pattern** | Validazione input/output con `BaseModel.model_validate()` e `model_dump()` |
| **Mapper Pattern** | Conversioni DTO <-> Domain Model <-> Response DTO in `mappers/` |
| **Dependency Injection** | Services accettano repository/service opzionali (testabilità) |
| **Protocol Interfaces** | `@Protocol` per contratti mockabili in test |
| **Decorator Pattern** | `@public_endpoint`, `@admin_endpoint`, `@require_active_event` |
| **Domain-Driven Design** | Regole business pure in `domain/`, senza I/O |
| **Event-Driven** | Firestore triggers per flussi asincroni |
| **Layered Architecture** | Request → Pydantic DTO → Service → Domain Model → Repository → DB |

### Regole di programmazione da rispettare

- Gli API handler non fanno business logic: validano DTO, chiamano service, gestiscono status code.
- I service non fanno parsing HTTP: ricevono DTO o valori già validati.
- I service sono unici: non creare service separati per admin/pubblico se cambia solo l'autorizzazione.
- I model rappresentano dati di dominio persistibili, non request payload.
- I repository parlano con Firestore e restituiscono model, non response JSON.
- I mapper sono l'unico posto in cui convertire DTO <-> model.
- Le funzioni utility vanno in `utils/` separate per concern.
- Le regole pure senza I/O vanno in `domain/`.
- I contratti sostituibili vanno mantenuti in `interfaces/` con `Protocol`.

---

*Documentazione generata dall'analisi del codice sorgente — `mcp-backend/functions/`*
