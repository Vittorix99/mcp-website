# WS2 — Review indipendente e correzioni

Revisore: agente distinto `gpt-6.1-sol`, effort high, contesto fresco.
Una sola review del branch da `d8ac90e8`, inclusi i file non ancora committati.
Esito originale: tre Important, nessun altro rilievo riportato.

| Rilievo riprodotto | Correzione del coordinatore | Prova |
|---|---|---|
| Mutazioni come `endpoints.extra = make("missing_new_endpoint")` erano escluse dall'inventario. | Il parser rifiuta riferimenti a `endpoints` fuori dall'inizializzatore statico, compresi alias e `Object.assign`. | `rejects endpoint mutations and aliases outside the static map`: RED prima, GREEN dopo. |
| Un export Python sovrascritto da `None` o una seconda definizione era ancora contato come HTTP. | Verifica dei binding di modulo per funzioni esportate, definizioni decorate e alias dei decoratori; riassegnazioni rifiutate. | `Python extraction rejects rebound export names and overwritten decorated definitions`: RED prima, GREEN dopo. |
| Una risposta 401 contenente metadati evento senza `id` superava la verifica. | Una risposta JSON di rifiuto deve contenere solo una stringa `error`. Sono ammessi anche i due messaggi testuali già emessi da `require_admin`. | `rejects event metadata leaked in 401 responses even without an event ID`: RED prima, GREEN dopo. |

I tre nuovi test fallivano tutti insieme; dopo le correzioni passa la suite
frontend completa di 39 test. Inventario corrente invariato: 130 riferimenti,
128 export HTTP, quattro eccezioni legacy note, nessun nuovo errore.
Il coordinatore ha accettato i rilievi e verificato le correzioni; non è
stata simulata una seconda review indipendente.

Il backend mantiene i messaggi 401 legacy in testo semplice; nessun contratto
applicativo di errore viene modificato per adattarlo al verificatore.
La prova completa Firebase è separata dai test del verificatore. Il proprietario
ha riportato PASS e exit code 0 dopo le correzioni della review; risultato
registrato come owner-reported nella verifica WS2.
