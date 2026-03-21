export const dynamic = "force-dynamic";

export async function GET(_request, { params }) {
  const { token } = await params;
  const html = getScannerHTML(token);
  return new Response(html, {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

function getScannerHTML(token) {
  return `<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black" />
<title>MCP Scanner</title>
<script src="/qr-scanner.umd.min.js"></script>
<style>
:root {
  --color-black:  #0a0a0a;
  --color-orange: #e8820c;
  --color-white:  #ffffff;
  --color-off:    #b0b0b0;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
  background: var(--color-black);
  color: var(--color-white);
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  height: 100dvh;
  overflow: hidden;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

/* ── States ── */
.state { display: none; }
.state.active { display: flex; }

/* ── LOADING ── */
#state-loading {
  position: fixed; inset: 0;
  flex-direction: column;
  align-items: center; justify-content: center;
  gap: 20px;
  background: var(--color-black);
  z-index: 50;
}
#state-loading img { width: 80px; opacity: 0.9; }
#state-loading p {
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-off);
}

/* ── ERROR ── */
#state-error {
  position: fixed; inset: 0;
  flex-direction: column;
  align-items: center; justify-content: center;
  gap: 16px;
  background: var(--color-black);
  text-align: center;
  padding: 24px;
  z-index: 50;
}
#state-error .err-symbol {
  font-size: clamp(80px, 25vw, 140px);
  font-weight: 100;
  line-height: 1;
  color: #e8241a;
}
#state-error .err-title {
  font-size: clamp(24px, 6vw, 36px);
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.02em;
}
#state-error .err-sub {
  font-size: 13px;
  color: var(--color-off);
  max-width: 280px;
  line-height: 1.5;
}

/* ── TAP TO START ── */
#state-tap {
  position: fixed; inset: 0;
  flex-direction: column;
  align-items: center; justify-content: center;
  gap: 24px;
  background: var(--color-black);
  text-align: center;
  padding: 24px;
  z-index: 50;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
#state-tap img { width: 72px; opacity: 0.9; }
#tap-btn {
  margin-top: 8px;
  padding: 16px 40px;
  background: var(--color-orange);
  color: var(--color-black);
  font-size: 15px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
#tap-sub {
  font-size: 12px;
  color: var(--color-off);
  max-width: 260px;
  line-height: 1.6;
}
#tap-event {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-white);
}

/* ── HEADER ── */
#header {
  position: fixed; top: 0; left: 0; right: 0;
  height: 56px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px;
  background: rgba(10,10,10,0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 10;
  border-bottom: 1px solid #1e1e1e;
}
#header img { height: 28px; }
#event-name {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-white);
  flex: 1;
  text-align: center;
  padding: 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
#entrance-count {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-orange);
  white-space: nowrap;
}

/* ── CAMERA VIDEO ── */
#video {
  position: fixed; top: 0; left: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  z-index: 0;
}

/* ── VIEWFINDER ── */
#viewfinder {
  position: fixed;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 240px; height: 240px;
  pointer-events: none;
  z-index: 5;
}
.corner {
  position: absolute;
  width: 28px; height: 28px;
  border-color: var(--color-orange);
  border-style: solid;
}
.corner-tl { top: 0; left: 0;     border-width: 3px 0 0 3px; }
.corner-tr { top: 0; right: 0;    border-width: 3px 3px 0 0; }
.corner-bl { bottom: 0; left: 0;  border-width: 0 0 3px 3px; }
.corner-br { bottom: 0; right: 0; border-width: 0 3px 3px 0; }
#scan-hint {
  position: fixed;
  top: calc(50% + 136px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.7);
  white-space: nowrap;
  pointer-events: none;
  z-index: 5;
}

/* ── OVERLAY FEEDBACK ── */
#overlay {
  position: fixed; inset: 0;
  flex-direction: column;
  align-items: center; justify-content: center;
  z-index: 20;
  display: none;
  text-align: center;
  padding: 24px;
}
#overlay.active { display: flex; }
#overlay-symbol {
  font-size: clamp(120px, 35vw, 200px);
  font-weight: 100;
  line-height: 1;
  margin-bottom: 20px;
}
#overlay-name {
  font-size: clamp(22px, 5.5vw, 38px);
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}
#overlay-detail {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(255,255,255,0.7);
  margin-bottom: 6px;
}
#overlay-status {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: rgba(255,255,255,0.5);
}

/* ── CAMERA PERMISSION ERROR ── */
#cam-error {
  display: none;
  position: fixed; inset: 0;
  flex-direction: column;
  align-items: center; justify-content: center;
  background: var(--color-black);
  gap: 16px;
  text-align: center;
  padding: 24px;
  z-index: 50;
}
#cam-error.active { display: flex; }
#retry-btn {
  margin-top: 8px;
  padding: 12px 32px;
  background: var(--color-orange);
  color: var(--color-black);
  font-size: 14px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: none;
  border-radius: 10px;
  cursor: pointer;
}
</style>
</head>
<body>

<!-- LOADING -->
<div id="state-loading" class="state active">
  <img src="/logo_white.png" alt="MCP" />
  <p>Verifica accesso...</p>
</div>

<!-- ERROR (terminal) -->
<div id="state-error" class="state">
  <div class="err-symbol">✕</div>
  <div class="err-title">Link non valido</div>
  <div class="err-sub">Chiedi un nuovo link all'organizzatore</div>
</div>

<!-- TAP TO START -->
<div id="state-tap" class="state">
  <img src="/logo_white.png" alt="MCP" />
  <div id="tap-event"></div>
  <button id="tap-btn">Avvia scanner</button>
  <div id="tap-sub">Tocca per attivare la fotocamera e iniziare a scansionare i QR delle tessere.</div>
</div>

<!-- IDLE: camera scanner -->
<div id="state-idle" style="display:none;position:fixed;inset:0;">
  <div id="header">
    <img src="/logo_white.png" alt="MCP" />
    <span id="event-name">—</span>
    <span id="entrance-count">0 entrati</span>
  </div>

  <video id="video" playsinline muted></video>

  <div id="viewfinder">
    <div class="corner corner-tl"></div>
    <div class="corner corner-tr"></div>
    <div class="corner corner-bl"></div>
    <div class="corner corner-br"></div>
  </div>
  <div id="scan-hint">Inquadra la tessera</div>
</div>

<!-- OVERLAY FEEDBACK -->
<div id="overlay">
  <div id="overlay-symbol"></div>
  <div id="overlay-name"></div>
  <div id="overlay-detail"></div>
  <div id="overlay-status"></div>
</div>

<!-- CAMERA PERMISSION ERROR -->
<div id="cam-error">
  <div class="cam-icon" style="font-size:48px;color:#e8241a;">⚠</div>
  <div class="cam-title" style="font-size:18px;font-weight:900;text-transform:uppercase;letter-spacing:-0.01em;"></div>
  <p class="cam-msg" style="font-size:13px;color:#b0b0b0;max-width:280px;line-height:1.6;"></p>
  <button id="retry-btn" onclick="retryCam()">Riprova</button>
</div>

<script>
const SCAN_TOKEN = ${JSON.stringify(token)};

// ── DOM refs ──
const stateLoading = document.getElementById('state-loading');
const stateError   = document.getElementById('state-error');
const stateTap     = document.getElementById('state-tap');
const stateIdle    = document.getElementById('state-idle');
const overlay      = document.getElementById('overlay');
const camError     = document.getElementById('cam-error');
const videoEl      = document.getElementById('video');
const eventNameEl  = document.getElementById('event-name');
const tapEventEl   = document.getElementById('tap-event');
const countEl      = document.getElementById('entrance-count');
const overlaySymbol = document.getElementById('overlay-symbol');
const overlayName   = document.getElementById('overlay-name');
const overlayDetail = document.getElementById('overlay-detail');
const overlayStatus = document.getElementById('overlay-status');

// ── State ──
let isScanning    = false;
let entranceCount = 0;
let overlayTimer  = null;
let qrScanner     = null;

// ── Helpers ──
function showState(name) {
  stateLoading.classList.toggle('active', name === 'loading');
  stateError.classList.toggle('active',   name === 'error');
  stateTap.classList.toggle('active',     name === 'tap');
  stateIdle.style.display = name === 'idle' ? 'block' : 'none';
  if (name !== 'cam-error') camError.classList.remove('active');
}

function showCamErrorMsg(icon, title, msg) {
  showState('loading');
  stateLoading.style.display = 'none';
  camError.querySelector('.cam-icon').textContent = icon;
  camError.querySelector('.cam-title').textContent = title;
  camError.querySelector('.cam-msg').textContent = msg;
  camError.classList.add('active');
}

function retryCam() {
  camError.classList.remove('active');
  stateLoading.style.display = '';
  showState('tap');
}

function updateCounter() {
  countEl.textContent = entranceCount + ' entr' + (entranceCount === 1 ? 'ato' : 'ati');
}

function vibrate(type) {
  if (!navigator.vibrate) return;
  if (type === 'scan')    navigator.vibrate(50);
  if (type === 'success') navigator.vibrate(200);
  if (type === 'error')   navigator.vibrate([100, 50, 100]);
}

function showOverlay(data) {
  const result = data.result;
  const name = data.membership
    ? ((data.membership.name || '') + ' ' + (data.membership.surname || '')).trim().toUpperCase()
    : '';

  if (result === 'valid') {
    overlay.style.background = '#1a4a1a';
    overlaySymbol.textContent = '✓';
    overlaySymbol.style.color = '#4ade80';
    overlayName.textContent = name;
    overlayDetail.textContent = '';
    overlayStatus.textContent = 'Accesso consentito';
  } else if (result === 'already_scanned') {
    overlay.style.background = '#4a3a00';
    overlaySymbol.textContent = '!';
    overlaySymbol.style.color = '#f0d44a';
    overlayName.textContent = name;
    const time = data.scanned_at
      ? new Date(data.scanned_at).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
      : '';
    overlayDetail.textContent = time ? 'Già entrato alle ' + time : '';
    overlayStatus.textContent = 'Già registrato';
  } else if (result === 'invalid_token') {
    overlay.style.display = 'none';
    showState('error');
    stateError.querySelector('.err-title').textContent = 'Sessione scaduta';
    stateError.querySelector('.err-sub').textContent = "Chiedi un nuovo link all'organizzatore";
    return;
  } else {
    overlay.style.background = '#4a0a0a';
    overlaySymbol.textContent = '✕';
    overlaySymbol.style.color = '#e8241a';
    overlayName.textContent = name || '—';
    const msgs = {
      invalid_no_purchase:      'Evento non acquistato',
      invalid_member_not_found: 'Tessera non riconosciuta',
    };
    overlayDetail.textContent = '';
    overlayStatus.textContent = (msgs[result] || result.replace(/_/g, ' ')).toUpperCase();
  }

  overlay.classList.add('active');
  clearTimeout(overlayTimer);
  overlayTimer = setTimeout(hideOverlay, 3000);
}

function hideOverlay() {
  overlay.classList.remove('active');
  isScanning = false;
  if (qrScanner) qrScanner.start();
}

// ── Init ──
async function init() {
  showState('loading');
  try {
    const res = await fetch('/api/proxy/entrance_verify_scan_token?token=' + encodeURIComponent(SCAN_TOKEN));
    if (!res.ok) { showState('error'); return; }
    const data = await res.json();
    if (!data.valid) { showState('error'); return; }
    const title = data.event_title || '';
    eventNameEl.textContent = title;
    tapEventEl.textContent  = title;
    showState('tap');
  } catch {
    showState('error');
  }
}

// ── Tap to start ──
document.getElementById('tap-btn').addEventListener('click', startCamera);
stateTap.addEventListener('click', function(e) {
  if (e.target === stateTap) startCamera();
});

async function startCamera() {
  if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    showCamErrorMsg('⚠', 'Connessione non sicura', 'Il browser richiede HTTPS per accedere alla fotocamera.');
    return;
  }
  showState('loading');

  try {
    // Set worker path before instantiating
    QrScanner.WORKER_PATH = '/qr-scanner-worker.min.js';

    qrScanner = new QrScanner(
      videoEl,
      result => onQrResult(result.data),
      {
        preferredCamera: 'environment',
        highlightScanRegion: false,
        highlightCodeOutline: false,
        returnDetailedScanResult: true,
      }
    );

    await qrScanner.start();
    showState('idle');
  } catch (err) {
    console.error('QrScanner error:', err);
    if (err && (err.name === 'NotAllowedError' || String(err).includes('permission'))) {
      showCamErrorMsg('⚠', 'Permesso negato', 'Vai nelle impostazioni del browser, consenti la fotocamera per questo sito e riprova.');
    } else {
      showCamErrorMsg('⚠', 'Errore fotocamera', String(err) || 'Impossibile avviare la fotocamera.');
    }
  }
}

// ── QR result handler ──
function onQrResult(data) {
  if (isScanning) return;
  isScanning = true;
  qrScanner.stop();
  vibrate('scan');
  handleScan(data);
}

// ── Validate ──
async function handleScan(membershipId) {
  try {
    const res = await fetch('/api/proxy/entrance_validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ membership_id: membershipId, scan_token: SCAN_TOKEN }),
    });

    if (!res.ok) {
      if (res.status === 401) { showState('error'); return; }
      vibrate('error');
      showOverlay({ result: 'network_error', membership: null, scanned_at: null });
      return;
    }

    const data = await res.json();

    if (data.result === 'valid') {
      entranceCount++;
      updateCounter();
      vibrate('success');
    } else if (data.result === 'already_scanned') {
      vibrate('scan');
    } else {
      vibrate('error');
    }

    showOverlay(data);
  } catch {
    vibrate('error');
    showOverlay({ result: 'network_error', membership: null, scanned_at: null });
  }
}

// ── Desktop guard ──
function isDesktop() {
  const ua = navigator.userAgent || '';
  const hasMobileUA = /Android|iPhone|iPad|iPod|Mobile|BlackBerry|IEMobile|Opera Mini/i.test(ua);
  const narrowScreen = window.innerWidth <= 1024;
  return !hasMobileUA && !narrowScreen;
}

if (isDesktop()) {
  document.body.innerHTML = \`
    <div style="position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0a0a0a;color:#fff;font-family:Helvetica Neue,sans-serif;text-align:center;padding:24px;gap:16px;">
      <div style="font-size:64px;line-height:1;">📱</div>
      <div style="font-size:22px;font-weight:900;text-transform:uppercase;letter-spacing:-0.02em;">Solo su mobile</div>
      <div style="font-size:13px;color:#b0b0b0;max-width:280px;line-height:1.6;">Questa applicazione è progettata esclusivamente per dispositivi mobili. Aprila sul tuo smartphone.</div>
    </div>
  \`;
} else {
  init();
}
</script>
</body>
</html>`;
}
